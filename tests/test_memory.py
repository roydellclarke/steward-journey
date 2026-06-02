import tempfile
import unittest
from pathlib import Path

from harness.memory import MemoryIndex
from harness.tools.file_tools import FileTools
from harness.workspace import Workspace
from tests.test_workspace import config_for


class MemoryTests(unittest.TestCase):
    def test_manifest_skips_sensitive_files_and_redacts_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            tools = FileTools(root)
            tools.write_file("contracts/current_sprint.md", "contact owner@example.com")
            tools.write_file(".env", "DEEPSEEK_API_KEY=sk-secret123456789")
            docs = MemoryIndex(root).build_manifest()
            paths = {doc.path for doc in docs}
            self.assertIn("contracts/current_sprint.md", paths)
            self.assertNotIn(".env", paths)
            contract = next(doc for doc in docs if doc.path == "contracts/current_sprint.md")
            self.assertIn("[REDACTED_EMAIL]", contract.preview)


if __name__ == "__main__":
    unittest.main()
