import tempfile
import unittest
from pathlib import Path

from tests.test_workspace import config_for
from harness.agents.evaluator_agent import EvaluatorAgent
from harness.agents.generator_agent import GeneratorAgent
from harness.tools.file_tools import FileTools
from harness.workspace import Workspace


class ContractHandshakeTests(unittest.TestCase):
    def test_generator_proposal_is_accepted_by_evaluator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = config_for(root)
            Workspace(config).initialize()
            files = FileTools(root)
            files.write_file("specs/sprint_plan.md", "# Sprint Plan\n\nBuild the harness.")

            GeneratorAgent(config, files).propose_test_plan()
            accepted = EvaluatorAgent(config, files).critique_test_plan()

            self.assertTrue(accepted)
            critique = files.read_file("feedback/critique.md")
            self.assertIn("Accepted for Contract: YES", critique)


if __name__ == "__main__":
    unittest.main()
