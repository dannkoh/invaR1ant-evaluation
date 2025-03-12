import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from z3 import *  # noqa: F403

from utils.configs import EvaluationConfig, ModelConfig
from utils.conversation import ConversationHandler
from utils.evaluation import EvaluationStats, LLMHelper, Loader


class Experiment:
    """
    A class to handle the experiment.
    """

    def __init__(
        self,
        model: ModelConfig,
        data,
        evaluationconfig: EvaluationConfig,
    ) -> None:
        """
        Initialize the experiment.

        Args:
            model: The model to evaluate.
            data: The data's filepath to evaluate.
            evaluationconfig: The evaluation configuration.

        """
        self.modelconfig = model
        self.model = LLMHelper(modelconfig=self.modelconfig)
        self.data = Loader.load_data(file=data)
        self.configs = evaluationconfig
        self.configs.set_dirs()
        self.stats = EvaluationStats()
        self.prompts = Loader.load_prompts()

        self.evaluate()

    def evaluate(self) -> None:
        """
        Evaluate the model.

        Args:
            file: The file to evaluate.

        """
        for problem in self.__discover_data():
            # Conversation for each problem
            self.conversation = ConversationHandler()
            prompt = self.__get_initial_prompt(problem=problem)
            self.__test_values(prompt=prompt, problem=problem)
        self.__calculate_results()

    def __get_initial_prompt(self, problem: str) -> str:
        """
        Get the initial prompt for the experiment.

        Args:
            problem: The problem to evaluate.

        Returns:
            str: The initial prompt for the experiment.

        """
        prompt = self.prompts.get("user_prompt_start")

        for key, value, _ in self.__get_constriants(problem=problem, dataset="examples"):
            prompt += f"N={key}: {str(value)}\n\n"

        prompt += self.prompts.get("user_prompt_end")

        return prompt

    def __get_constriants(
        self, problem: str, dataset: Literal["test", "examples"]
    ) -> list[tuple[str, str, str | None]]:
        """
        Get the constraints for the experiment.

        Args:
            problem: The problem to evaluate.
            dataset: The dataset to collect from.

        Returns:
            list[tuple[str,str]]: The constraints for the experiment.

        """
        problem = self.data.get(problem)

        example_keys = problem.get(dataset).keys()

        return [
            (
                constraint,
                problem.get(dataset).get(constraint).get("solution"),
                problem.get(dataset).get(constraint).get("constants", None),
            )
            for constraint in example_keys
        ]

    def __discover_data(self) -> None:
        """
        Discover the data for the experiment.

        """
        return self.data.keys()

    def __test_values(self, prompt: str, problem: str) -> None:
        """
        Test the values for the experiment.

        Args:
            prompt: The prompt to test.
            problem: The problem to evaluate.

        """
        results = {}
        for testcase, truth, constants in self.__get_constriants(problem=problem, dataset="test"):
            testcase_prompt = prompt + testcase
            sys_prompt = Loader.format_system_prompt(text=self.prompts.get("system_prompt_start"))
            self.conversation.print_and_save(new_message=testcase_prompt)
            user_prompt = Loader.format_user_prompt(text=testcase_prompt)
            history = [sys_prompt, user_prompt]

            result = {"result": False, "reason": "Failed to extract answer from response."}
            for _ in range(self.configs.attempts):
                response = self.model.get_response(history=history, think=self.modelconfig.think)
                self.conversation.print_and_save(new_message=response)
                try:
                    extracted_response = Loader.extract_response(response=response)
                    self.conversation.load(f"Extracting response. Extracted: {extracted_response}")

                    self.conversation.print_and_save(new_message="Evaluating response using Z3...")
                    result = self.__z3__(
                        response=extracted_response,
                        truth=truth,
                        constants=constants,
                        problem=problem,
                        testcase=testcase,
                    )

                    if result.get("result"):
                        break
                except IndexError:
                    self.conversation.load(f"Could not extract answer from response: TRUNCATED \n \n {response[-300:]}")
                # If the result is False, we need to provide feedback
                self.conversation.load("Failed to evaluate response. Providing feedback.")
                assistant_response = Loader.format_assistant_prompt(text=response)
                feedback = Loader.format_user_prompt(text=self.prompts.get("user_prompt_feedback"))
                history.extend([assistant_response, feedback])

            results[testcase] = {
                "result": result.get("result"),
                "reason": result.get("reason", None),
                "expected": truth,
                "extracted": Loader.extract_response(response=response)
                if result.get("result")
                else f"Raw Output: {response}",
                "response": response,
            }
        self.conversation.save(path=self.configs.logs_dir, problem=problem)
        self.stats.add_stat({problem: {"test": results}})

    def __z3__(self, response: str, truth: str, constants: str, problem: str, testcase: str) -> dict[str, str]:
        """
        Evaluate the response using Z3.

        Args:
            response: The response to evaluate.
            truth: The ground truth to evaluate.
            constants: The constants to evaluate.
            problem: The problem name.
            testcase: The value of N to evaluate.

        Returns:
            result: The result of the evaluation.

        """
        result = {}
        smt2 = Loader.load_z3_template(constants=constants, original_assertions=truth, generated_assertions=response)
        if len(smt2) > self.configs.max_file_size:
            result["result"] = False
            result["reason"] = "File size too large"
            return result

        file = Path(self.configs.generals) / problem / f"{problem}_{testcase}.smt2"
        file.parent.mkdir(parents=True, exist_ok=True)
        with Path.open(file, "w") as f:
            f.write(smt2)

        self.conversation.load(f"Saved Z3 file to: {file}")

        try:
            proc = subprocess.run(["z3", file], capture_output=True, text=True, check=False)  # noqa: S603, S607
            output = proc.stdout.strip()
            self.conversation.load(f"Z3 Output:\n{output}")

            result["reason"] = " ".join(out for out in output.splitlines() if out.startswith("(error"))

            # The output order after each (check-sat) is the order we see logically:
            #   1) A => B fail
            #   2) B => A fail
            # So parse line by line
            results = [line for line in output.splitlines() if line in ("sat", "unsat", "unknown")]

            if len(results) < 2:
                self.conversation.load("Could not parse results correctly.")
                result["result"] = False
                return result

            # If either check is 'sat', it means it found a counterexample => not equivalent
            # i.e. A=>B fails => results[0] == sat
            # i.e. B=>A fails => results[1] == sat
            if results[0] == "sat":
                self.conversation.load("Original does not imply generated. Not equivalent.")
                result["reason"] = "Original does not imply generated."
                result["result"] = False
                return result
            if results[1] == "sat":
                self.conversation.load("Generated does not imply original. Not equivalent.")
                result["reason"] = "Generated does not imply original."
                result["result"] = False
                return result

            self.conversation.load("Constraints are logically equivalent.")
            result["result"] = True
        except Exception as e:  # noqa: BLE001
            self.conversation.load(f"Error running Z3: {e}")
            result["reason"] = str(e)
            result["result"] = False

        return result

    def __calculate_results(self) -> None:
        """
        Calculate the results of the experiment.

        """
        self.stats.calculate_results()
        self.stats.save(file=self.configs.stats_dir / "individual_stats.json")


if __name__ == "__main__":
    load_dotenv()

    arguments = argparse.ArgumentParser(description="SPF Constraint Generalization Experiment")
    arguments.add_argument("data", help="Data file to evaluate")
    arguments.add_argument("--model", help="Model identifier")
    arguments.add_argument("-q", "--quantization", choices=["4bit"], help="Quantization type (Optional)", default=None)
    arguments.add_argument("--think", action="store_true", help="Enable think mode (Optional)", default=False)

    args = arguments.parse_args()

    model = ModelConfig(
        model_name=args.model,
        quantization_mode=args.quantization,
        token=os.getenv("HUGGINGFACE_TOKEN"),
        think=args.think,
    )

    experiment = EvaluationConfig(
        results_dir=f"./{args.model}-{"full" if args.quantization is None else args.quantization}",
    )

    experiment = Experiment(model=model, data=args.data, evaluationconfig=experiment)
