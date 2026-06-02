import tempfile
import unittest
from pathlib import Path

from harness.privacy import is_sensitive_path, redact_text


class PrivacyTests(unittest.TestCase):
    def test_redacts_common_pii_and_secrets(self) -> None:
        text = "Email me at owner@example.com or 416-555-1212 with sk-testsecret123456"
        redacted = redact_text(text)
        self.assertIn("[REDACTED_EMAIL]", redacted)
        self.assertIn("[REDACTED_PHONE]", redacted)
        self.assertIn("[REDACTED_SECRET]", redacted)
        self.assertNotIn("owner@example.com", redacted)

    def test_sensitive_path_uses_ignore_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".piiignore").write_text("private/*\n", encoding="utf-8")
            self.assertTrue(is_sensitive_path(root / "private" / "notes.md", root))
            self.assertTrue(is_sensitive_path(root / ".env", root))
            self.assertFalse(is_sensitive_path(root / "workspace" / "contracts" / "current_sprint.md", root))


if __name__ == "__main__":
    unittest.main()
