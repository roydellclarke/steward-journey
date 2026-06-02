import tempfile
import unittest
from pathlib import Path

from harness.job_registry import FAILED, PAUSED, PENDING, RUNNING, SUCCEEDED, JobRegistry
from harness.workspace import Workspace
from tests.test_workspace import config_for


class JobRegistryTests(unittest.TestCase):
    def test_creates_persistent_job_with_schedule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            registry = JobRegistry(root)
            job = registry.create_job(
                name="Daily content",
                kind="scheduled_goal",
                payload={"goal": "Draft three posts per day."},
                schedule="RRULE:FREQ=DAILY;COUNT=3",
            )

            loaded = JobRegistry(root).get_job(job.job_id)
            self.assertEqual(loaded.name, "Daily content")
            self.assertEqual(loaded.status, PENDING)
            self.assertEqual(loaded.schedule, "RRULE:FREQ=DAILY;COUNT=3")

    def test_tracks_run_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            registry = JobRegistry(root)
            job = registry.create_job(name="Build app", kind="harness_goal", payload={"goal": "Build."})
            run = registry.start_run(job.job_id)
            self.assertEqual(JobRegistry(root).get_job(job.job_id).status, RUNNING)

            registry.finish_run(job.job_id, run.run_id, status=SUCCEEDED, output="done", artifacts=["reports/completion_report.md"])
            loaded = JobRegistry(root).get_job(job.job_id)
            self.assertEqual(loaded.status, SUCCEEDED)
            self.assertEqual(len(loaded.runs), 1)
            self.assertEqual(loaded.runs[0].artifacts, ["reports/completion_report.md"])

    def test_approval_required_job_cannot_start_until_approved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            registry = JobRegistry(root)
            job = registry.create_job(
                name="Publish Facebook posts",
                kind="meta_publish",
                payload={"access_token": "secret-token"},
                approval_required=True,
            )
            self.assertEqual(job.status, PAUSED)
            with self.assertRaises(PermissionError):
                registry.start_run(job.job_id)

            registry.approve_job(job.job_id)
            run = registry.start_run(job.job_id)
            registry.finish_run(job.job_id, run.run_id, status=FAILED, error="network unavailable")
            loaded = registry.get_job(job.job_id)
            self.assertEqual(loaded.status, FAILED)

    def test_redacts_secrets_at_rest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            registry = JobRegistry(root)
            registry.create_job(
                name="Secret job",
                kind="connector",
                payload={"api_key": "sk-testsecret123456", "note": "email me@example.com"},
            )
            raw = (root / "state" / "jobs.json").read_text(encoding="utf-8")
            self.assertIn("[REDACTED]", raw)
            self.assertNotIn("sk-testsecret123456", raw)
            self.assertNotIn("me@example.com", raw)


if __name__ == "__main__":
    unittest.main()

