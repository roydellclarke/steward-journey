import tempfile
import unittest
from pathlib import Path

from harness.a2a_policy import A2APolicy
from harness.workspace import Workspace
from tests.test_workspace import config_for


class A2APolicyTests(unittest.TestCase):
    def test_records_allowed_artifact_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            message = A2APolicy(root).record_message(
                sender="planner",
                recipient="generator",
                message_type="sprint_spec",
                artifact_path="specs/sprint_plan.md",
            )
            self.assertEqual(message.message_type, "sprint_spec")
            self.assertTrue((root / "state" / "a2a_messages.jsonl").exists())

    def test_rejects_freeform_or_escaping_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = A2APolicy(Path(tmp))
            with self.assertRaises(ValueError):
                policy.record_message(sender="a", recipient="b", message_type="chat", artifact_path="notes.md")
            with self.assertRaises(ValueError):
                policy.record_message(sender="a", recipient="b", message_type="critique", artifact_path="../outside.md")


if __name__ == "__main__":
    unittest.main()
