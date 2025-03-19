import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Literal

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from utils.configs import EvaluationConfig, ModelConfig
from utils.conversation import ConversationHandler
from utils.evaluation import EvaluationStats, LLMHelper, Loader
from z3 import *  # noqa: F403


class Experiment:
    """
    A class to handle the experiment.
    """

    def __init__(
        self,
        model: ModelConfig,
        data: str,
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

        data_path = Path(data)
        self.data = Loader.load_data(file=str(data_path))

        self.configs = evaluationconfig
        self.configs.set_dirs()
        self.stats = EvaluationStats()

        self.evaluate()

    def evaluate(self) -> None:
        """
        Evaluate the model.
        """
        self.conversation = ConversationHandler()
        for _, problem in self.data.sort_values("problem").iterrows():
            # Conversation for each problem
            self.__test_values(problem=problem)
        self.conversation.save(path=self.configs.logs_dir)
        self.__calculate_results()

    # problem is a dataframe row
    def __test_values(self, problem: pd.Series) -> None:
        """
        Test the values for the experiment.
        """
        results = {}
        history = str(problem["question"])
        self.conversation.print_and_save(new_message=history)
        result = {"result": False, "reason": "Failed to extract answer from response."}
        for _ in range(self.configs.attempts):
            response = self.model.get_response(history=history)
            self.conversation.print_and_save(new_message=response)
            try:
                extracted_response = Loader.extract_response(response=response)
                self.conversation.load(f"Extracting response. Extracted:\n{extracted_response}")

                self.conversation.print_and_save(new_message="Evaluating response using Z3...")
                result = self.__z3__(
                    response=extracted_response,
                    truth=problem["answer"],
                    constants=problem["constants"],
                )

                if result.get("result"):
                    break
            except IndexError:
                self.conversation.load(f"Could not extract answer from response: \n \n {response}")
            # If the result is False, provide feedback
            self.conversation.load("Failed to evaluate response. Providing feedback.")
            feedback = Loader.make_feedback(instruct=self.modelconfig.is_instruct)
            self.conversation.load(feedback)
            history += f"\n{feedback}"

        results[problem.question_index] = {
            "result": result.get("result"),
            "reason": result.get("reason", None),
            "expected": problem["answer"],
            "extracted": Loader.extract_response(response=response)
            if result.get("result")
            else f"Raw Output: {response}",
            "response": response,
        }
        self.stats.add_stat({problem.problem: results})

    def __z3__(self, response: str, truth: str, constants: str) -> dict[str, str]:
        """
        Evaluate the response using Z3.
        """
        result = {}
        smt2 = Loader.load_z3_template(constants=constants, original_assertions=truth, generated_assertions=response)
        if len(smt2) > self.configs.max_file_size:
            result["result"] = False
            result["reason"] = "File size too large"
            return result

        try:
            proc = subprocess.run(["z3", "-in"], input=smt2, capture_output=True, text=True, check=False)  # noqa: S603, S607
            output = proc.stdout.strip()
            self.conversation.load(f"Z3 Output:\n{output}")

            result["reason"] = " ".join(out for out in output.splitlines() if out.startswith("(error"))

            results = [line for line in output.splitlines() if line in ("sat", "unsat", "unknown")]

            if len(results) < 2:
                self.conversation.load("Could not parse results correctly.")
                result["result"] = False
                return result

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
        Calculate and save the results of the experiment.
        """
        self.stats.calculate_results()
        self.stats.save(file=self.configs.stats_dir / "individual_stats.json")


if __name__ == "__main__":
    load_dotenv()

    arguments = argparse.ArgumentParser(description="SPF Constraint Generalization Experiment")
    arguments.add_argument("data", help="Data file (parquet) to evaluate")
    arguments.add_argument("--model", help="Model identifier")
    arguments.add_argument("-q", "--quantization", choices=["4bit"], help="Quantization type (Optional)", default=None)
    arguments.add_argument("--instruct", action="store_true", help="Enable instruct prompt template (Optional)", default=False)

    args = arguments.parse_args()

    model = ModelConfig(
        model_name=args.model,
        quantization_mode=args.quantization,
        token=os.getenv("HUGGINGFACE_TOKEN"),
        instruct=args.instruct
    )

    experiment_config = EvaluationConfig(
        results_dir=f"./{args.model}-{'full' if args.quantization is None else args.quantization}",
    )

    Experiment(model=model, data=args.data, evaluationconfig=experiment_config)