import tempfile
import unittest
from pathlib import Path

from harness.tools.file_tools import FileTools
from harness.trust import GENERATED, TrustStore, USER_PROVIDED
from harness.workspace import Workspace
from tests.test_workspace import config_for


class TrustTests(unittest.TestCase):
    def test_file_tool_writes_are_labeled_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            FileTools(root).write_file("src/index.html", "<h1>Hi</h1>")
            record = TrustStore(root).get("src/index.html")
            self.assertIsNotNone(record)
            self.assertEqual(record.label, GENERATED)

    def test_saved_goals_are_labeled_user_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            goal = root / "goal.md"
            goal.write_text("build a thing", encoding="utf-8")
            workspace = Workspace(config_for(root / "workspace"))
            workspace.initialize()
            workspace.save_goals(goal)
            record = TrustStore(workspace.root).get("goals/user_goals.md")
            self.assertIsNotNone(record)
            self.assertEqual(record.label, USER_PROVIDED)


if __name__ == "__main__":
    unittest.main()
