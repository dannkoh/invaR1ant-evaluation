import json
import os
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
import torch

from utils.configs import ModelConfig

try:
    from vllm.vllm import LLM, RequestOutput, SamplingParams
except ImportError:
    from vllm import LLM, RequestOutput, SamplingParams


class EvaluationStats:
    """
    A class to handle evaluation statistics.
    """

    def __init__(self) -> None:
        """
        Initialize the evaluation statistics.
        """
        self.stats = {}

    def add_stat(self, stats: dict[str, any]) -> None:
        """
        Add a statistic to the evaluation statistics.
        """
        self.stats.update(stats)

    def save(self, file: str) -> None:
        """
        Save the evaluation statistics.
        """
        Path(file).parent.mkdir(parents=True, exist_ok=True)

        with Path(file).open("w") as f:
            json.dump(self.stats, f)

    def calculate_results(self) -> None:
        """
        Calculate the results of the evaluation.
        """
        for key, value in self.stats.items():
            total_tests = len(value["test"])
            successful_tests = sum(1 for test in value["test"] if test["result"])
            self.stats[key] = {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "accuracy": successful_tests / total_tests,
                "test": value["test"],
            }

class Loader:
    """
    A class to load data for the experiment.
    """

    @staticmethod
    def load_data(file: str) -> pd.DataFrame:
        """
        Load the data from a file.
        """
        return pd.read_parquet(file).reset_index(drop=True).sort_values(
            by=["problem", "question_index"],
            ascending=[True, True]
            )

    @staticmethod
    def make_feedback(instruct: bool) -> str:
        """
        Build the initial prompt prefix. For instruct mode, returns a list of message dictionaries;
        for base models, returns a single formatted string.
        The prompt includes a placeholder {testcase} to be replaced with the actual test case.
        """
        feedback = (
            "Your previous answer was incorrect. Please re-read the constraints and try again, "
            "including your step-by-step reasoning in <think> </think> and the final answer in <answer> </answer>."
        )
        if instruct:
            return (f"\n<|im_start|>user\n{feedback}<|im_end|>")
        return f"\nUser: {feedback}"

    @staticmethod
    def load_z3_template(constants: str, original_assertions: str, generated_assertions) -> str:
        """
        Load the Z3 template for the experiment.
        """
        return f"""; Combined SMT for checking equivalence
; Original constants:
{constants}

; Original constraints (A):
(push)
{original_assertions}
(pop)

; Generated constraints (B):
(push)
{generated_assertions}
(pop)

; Now do two checks:
; 1) A => B fails means we push A and then (not B)
(push)
{original_assertions}
(assert (not
{Loader.__parse_constraints(generated_assertions)}
))
(check-sat)
(pop)

; 2) B => A fails means we push B and then (not A)
(push)
{generated_assertions}
(assert (not
{Loader.__parse_constraints(original_assertions)}
))
(check-sat)
(pop)
"""

    @staticmethod
    def __parse_constraints(constraints: str) -> str:
        """
        Parse raw SMT-LIB2 constraints into a single conjunctive form.
        """
        # Extract all individual assertions
        assertions = [line.strip()[8:-1] for line in constraints.splitlines() if line.startswith("(assert")]
        # Combine into a single conjunctive expression
        return f"(and {' '.join(assertions)})"

    @staticmethod
    def extract_response(response: str) -> str:
        """
        Extract the response from the experiment.
        """
        try:
            return response.split("<answer>")[1].split("</answer>")[0].strip()
        except IndexError as e:
            raise IndexError from e

class BaseLLMHelper(ABC):
    """
    An abstract class to handle the LLM model.
    """

    @abstractmethod
    def _get_response(self, history: list[dict[str, str]], think: bool | None = None) -> str:
        """
        Get the response from the model.
        """
        pass


class _VLLMHelper(BaseLLMHelper):
    """
    A class to handle the VLLM model.
    """

    def __init__(self, modelconfig: ModelConfig) -> None:
        """
        Initialize the VLLM Helper.

        Args:
            modelconfig: The model configuration

        """
        self.model = modelconfig.model
        self.quantization = modelconfig.quantization

        os.environ["HF_TOKEN"] = modelconfig.token

        self.pipeline = LLM(
            model=self.model,
            trust_remote_code=True,
            tensor_parallel_size=int(torch.cuda.device_count()) if torch.cuda.is_available() else 1,
            enforce_eager=True,
            dtype="auto",
            quantization=self.quantization,
            disable_custom_all_reduce=True,
            distributed_executor_backend="ray"
        )

        self.sampling_params = SamplingParams(
            max_tokens=8000,
        )

    def __reduce_context(self, history: str) -> str:
        """
        Reduce the conversation history by removing the oldest non-system message.

        Preserves system message and recent conversation history for context.

        Args:
            history: List of conversation messages
            think: Whether think mode is enabled

        Returns:
            List[Dict[str, str]]: History with oldest non-system message removed

        Raises:
            ValueError: If only system + latest message remain

        """
        if "<|im_start|>" in history:
            size = history.count("<|im_start|>")
            if size != 1:
                return history.split("<|im_end|>", maxsplit=1)[-1]
            return ValueError
        size = history.count("User:")
        if size >= 2:
            return history.split("Assistant:", maxsplit=1)[-1]
        return ValueError


    def _get_response(self, history: str) -> str:
        """
        Get the response from the model.
        """
        try:
            response = self.pipeline.generate(
                prompts=self.__generation_prompt(history),
                sampling_params=self.sampling_params,
            )
            return self.__process_response(response)
        except Exception as e:  # noqa: BLE001
            error_msg = str(e)
            if (
                "CUDA out of memory" in error_msg
                or "maximum context length" in error_msg
                or "exceeds max tokens" in error_msg
            ):
                try:
                    reduced_history = self.__reduce_context(history)
                    return self._get_response(reduced_history)
                except ValueError:
                    return "Error: Context too long and cannot be reduced further."
            else:
                return f"Error: {error_msg}"

    def __generation_prompt(self, history: str) -> str:
        """
        Generate the prompt for the generation.
        """
        if isinstance(history, str):
            return history + "Assistant:"
        return history + "<|im_start|>assistant\n"


    def __process_response(self, response: RequestOutput) -> str:
        try:
            response = response[0].outputs[0].text
        except Exception as e:  # noqa: BLE001
            return f"Error: {e!s}"
        return response


class LLMHelper:
    """
    A class to handle the LLM model.
    """

    def __init__(self, modelconfig: ModelConfig) -> None:
        """
        Initialize the LLM Helper.

        Args:
            modelconfig: The model configuration

        """
        self.modelconfig = modelconfig
        self.__setup()

    def __setup(self) -> None:
        """
        Choose the appropriate helper based on the model name.
        """
        if self.modelconfig.model.startswith(("gpt", "o1", "o3")):
            msg = "GPT models are not supported in this version."
            raise ValueError(msg)
        self.helper = _VLLMHelper(modelconfig=self.modelconfig)

    def get_response(self, history: str) -> str:
        """
        Get the response from the model.
        """
        return self.helper._get_response(history)  # noqa: SLF001
