import importlib.util
import tempfile
import unittest
from pathlib import Path

from harness.api import create_app
from harness.workspace import Workspace
from tests.test_workspace import config_for


class ApiTests(unittest.TestCase):
    @unittest.skipIf(importlib.util.find_spec("fastapi") is None, "FastAPI is optional")
    def test_fastapi_job_routes(self) -> None:
        from fastapi.testclient import TestClient

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = config_for(root)
            Workspace(config).initialize()
            client = TestClient(create_app(config))

            created = client.post(
                "/jobs",
                json={
                    "name": "Scheduled posts",
                    "kind": "scheduled_goal",
                    "payload": {"goal": "Draft three posts."},
                    "schedule": "0 9,13,17 * * *",
                },
            )
            self.assertEqual(created.status_code, 200)
            self.assertEqual(created.json()["schedule"], "0 9,13,17 * * *")

            listed = client.get("/jobs")
            self.assertEqual(listed.status_code, 200)
            self.assertEqual(len(listed.json()), 1)

            health = client.get("/health")
            self.assertEqual(health.status_code, 200)
            self.assertTrue(health.json()["ok"])


if __name__ == "__main__":
    unittest.main()

