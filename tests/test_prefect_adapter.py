import tempfile
import unittest
from pathlib import Path

from harness.job_registry import JobRegistry
from harness.prefect_adapter import prefect_capability
from harness.workspace import Workspace
from tests.test_workspace import config_for


class PrefectAdapterTests(unittest.TestCase):
    def test_capability_reports_without_requiring_prefect(self) -> None:
        capability = prefect_capability()
        self.assertIsInstance(capability.available, bool)
        self.assertTrue(capability.detail)

    def test_scheduled_job_can_be_registered_for_prefect_worker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            job = JobRegistry(root).create_job(
                name="Three daily posts",
                kind="scheduled_goal",
                payload={"goal": "Draft three posts about local AI tools."},
                schedule="0 9,13,17 * * *",
            )
            self.assertEqual(job.schedule, "0 9,13,17 * * *")


if __name__ == "__main__":
    unittest.main()

