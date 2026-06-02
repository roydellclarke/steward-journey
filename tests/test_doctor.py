import tempfile
import unittest
from pathlib import Path

from harness.doctor import Doctor
from tests.test_workspace import config_for


class DoctorTests(unittest.TestCase):
    def test_doctor_reports_checks_without_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checks = Doctor(config_for(Path(tmp))).run()
            names = {check.name for check in checks}
            self.assertIn("workspace_writable", names)
            self.assertIn("llm_keys", names)
            self.assertTrue(all("sk-" not in check.detail for check in checks))


if __name__ == "__main__":
    unittest.main()
