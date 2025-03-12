import json
import os
from abc import ABC, abstractmethod
from pathlib import Path

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

    def add_stat(self, **kwargs: dict[str, any]) -> None:
        """
        Add a statistic to the evaluation statistics.
        """
        self.stats.update(kwargs)

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
    def load_data(file: str) -> dict:
        """
        Load the data for the experiment.

        Args:
            file: filepath to the data.

        Returns:
            The loaded data.

        """
        with Path(file).open() as f:
            return json.load(f)

    @staticmethod
    def load_prompts() -> dict[str, str]:
        """
        Load the prompts for the experiment.

        Returns:
            dict: The loaded prompts.

        """
        return {
            "system_prompt_start": (
                "You are a neurosymbolic constraint generalization engine. Your role is to take a known pattern of symbolic constraints that represent the longest execution path of a program and generalize it for any given input size N."
                "When you receive an input value N, you must generate a canonical SMT-LIB constraint string that adheres to the following rules:\n"
                "(assert (op (op (op var_1 var_2)) (op (op var_3 var_4)) (op (op var_5 var_6)) (op var_7 var_8))) where op is a logical operator (e.g., 'and', 'or', 'not') and var_i are variables or constants.\n"
                "All per-variable constraints must be combined using a top-level (assert (and ...)) clause.\n"
                "• The output must be in exact, canonical SMT-LIB format without extra commentary in the constraint string.\n"
                "Show your work in <think> </think> tags. And return the final SMT-LIB constraint string in <answer> </answer> tags.\n"
                "For example <answer> (assert (= in0 37)) </answer>.\n"
            ),
            "user_prompt_start": (
                "You are given a set of symbolic constraints that define the longest execution path of a given program. Your task is to generalize these constraints to produce a canonical, neurosymbolic representation that applies to any input size N. In the canonical form, each input variable in{i} (for i from 0 to N-1) must satisfy a specific pattern (for example, it should not equal certain forbidden values and must equal a target value).\n"
                "For instance, if the known constraints for N=3 are: \n\n"
                "(assert (and (and (and (and (and (and (and (and (and (and (and (not ( = in0 64)) (not ( = in0 35))) (not ( = in0 36)))  ( =  in0 37)) (not ( = in1 64))) (not ( = in1 35))) (not ( = in1 36)))  ( =  in1 37)) (not ( = in2 64))) (not ( = in2 35))) (not ( = in2 36)))  ( =  in2 37)))"
                " then you must generalize this pattern for any given N. \n\n"
                "Your work should be shown in <think> </think> tags. And the final SMT-LIB constraint string should be returned in <answer> </answer> tags. For example <answer> (assert true) </answer>."
                "Here are the set of constraints:\n"
            ),
            "user_prompt_end": ("What is the constraint for N="),
            "user_prompt_feedback": (
                "Your answer is wrong. Please try again. Remeber to show your work in <think> </think> tags. And only return the final SMT-LIB constraint string in <answer> </answer> tags. For example <think>It is constant for all N</think> <answer>(assert (= in0 64))</answer>."
            ),
        }

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
    def format_user_prompt(text: str) -> str:
        """
        Load the user prompt for the experiment.
        """
        return {"role": "user", "content": text}

    @staticmethod
    def format_system_prompt(text: str) -> str:
        """
        Load the system prompt for the experiment.
        """
        return {"role": "assistant", "content": text}

    @staticmethod
    def format_assistant_prompt(text: str) -> str:
        """
        Load the assistant prompt for the experiment.
        """
        return {"role": "assistant", "content": text}

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
        )

        self.sampling_params = SamplingParams(
            max_tokens=16_000,
        )

    def __reduce_context(self, history: list[dict[str, str]], think: bool | None = None) -> list[dict[str, str]]:
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
        min_length = 3 if think else 2
        if len(history) <= min_length:
            msg = "Cannot reduce context further - at minimum context"
            raise ValueError(msg)

        # Keep system message [0] and remove oldest non-system message
        # This preserves all recent context while reducing size incrementally
        return [history[0]] + history[2:]

    def _get_response(self, history: list[dict[str, str]], think: bool | None = None) -> str:
        """
        Get the response from the model.
        """
        if think:
            history = self.__think(history)

        try:
            response = self.pipeline.chat(
                messages=history,
                sampling_params=self.sampling_params,
                continue_final_message=bool(think),
                add_generation_prompt=not think,
            )
            return self.__process_response(response, think)
        except Exception as e:  # noqa: BLE001
            error_msg = str(e)
            if (
                "CUDA out of memory" in error_msg
                or "maximum context length" in error_msg
                or "exceeds max tokens" in error_msg
            ):
                try:
                    reduced_history = self.__reduce_context(history)
                    return self._get_response(reduced_history, think=think)
                except ValueError:
                    return "Error: Context too long and cannot be reduced further."
            else:
                return f"Error: {error_msg}"

    def __think(self, history: list[dict[str, str]]) -> list[dict[str, str]]:
        """
        Format the history for thinking.
        """
        return [*history, {"role": "assistant", "content": "I will think step by step.\n<think>\n"}]

    def __process_response(self, response: RequestOutput, think: bool | None = None) -> str:
        try:
            response = response[0].outputs[0].text
            if think:
                # Add the initial prefix back to the response
                response = f"I will think step by step.\n<think>\n{response}"
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

    def get_response(self, history: list[dict[str, str]], think: bool | None = None) -> str:
        """
        Get the response from the model.
        """
        return self.helper._get_response(history, think=think)  # noqa: SLF001
