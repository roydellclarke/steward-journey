"""Tests for the action plan: prioritized steps, and the loop where completing
a step raises the deterministic readiness score.

Unit tests need no web stack. API tests skip without FastAPI, like the rest.

Run:  python -m unittest discover -s backend/tests
"""

from __future__ import annotations

import importlib
import os
import tempfile
import unittest

from app.services.action_plan import RULES, build_action_plan, complete_action
from app.storage.intake_state import field_value, migrate_profile_to_intake_state


try:
    from fastapi.testclient import TestClient  # noqa: F401
    import slowapi  # noqa: F401
    import itsdangerous  # noqa: F401
    HAS_STACK = True
except Exception:  # pragma: no cover
    HAS_STACK = False


def _empty_state():
    return migrate_profile_to_intake_state(None, None)


class ActionPlanUnitTestCase(unittest.TestCase):
    def test_empty_state_opens_every_step(self):
        plan = build_action_plan(_empty_state())
        self.assertEqual(plan["summary"]["total"], len(RULES))
        self.assertEqual(plan["summary"]["open"], len(RULES))
        self.assertEqual(plan["summary"]["done"], 0)
        # Every action carries a field reference and guidance.
        for a in plan["actions"]:
            self.assertTrue(a["section"] and a["field"] and a["guidance"])

    def test_completing_a_step_raises_readiness_and_marks_done(self):
        state = _empty_state()
        before = build_action_plan(state)["summary"]["readiness"]

        updated = complete_action(state, "books-current")
        self.assertIsNotNone(updated)
        self.assertIs(field_value(updated, "financialClarity", "booksUpToDate"), True)

        after_plan = build_action_plan(updated)
        self.assertGreater(after_plan["summary"]["readiness"], before)
        self.assertEqual(after_plan["summary"]["done"], 1)
        done = next(a for a in after_plan["actions"] if a["id"] == "books-current")
        self.assertEqual(done["status"], "done")

    def test_open_steps_sort_before_done(self):
        state = complete_action(_empty_state(), "books-current")
        actions = build_action_plan(state)["actions"]
        statuses = [a["status"] for a in actions]
        # No "open" appears after a "done" (done sinks to the bottom).
        self.assertNotIn("open", statuses[statuses.index("done"):] if "done" in statuses else [])

    def test_text_step_needs_owner_input(self):
        # 'name-motivation' has no fixed good value, so it cannot be one-clicked.
        self.assertIsNone(complete_action(_empty_state(), "name-motivation"))

    def test_unknown_action_id_is_safe(self):
        self.assertIsNone(complete_action(_empty_state(), "nope"))


def _reload_app():
    root = tempfile.mkdtemp()
    os.environ["STEWARDPATH_DATA_ROOT"] = root
    os.environ["STEWARDPATH_AUTH_DB_PATH"] = os.path.join(root, "auth", "auth.db")
    os.environ["STEWARDPATH_SECRET_KEY"] = "test-secret-key"
    os.environ["STEWARDPATH_COOKIE_SECURE"] = "false"
    os.environ["STEWARDPATH_FRONTEND_ORIGIN"] = "http://localhost:3000"
    for key in ("STEWARDPATH_RESEND_API_KEY", "STEWARDPATH_RESEND_FROM", "STEWARDPATH_LOG_AUTH_EMAILS"):
        os.environ[key] = ""
    import app.main as main_module
    importlib.reload(main_module)
    return main_module


@unittest.skipUnless(HAS_STACK, "FastAPI/slowapi/itsdangerous not installed in this environment")
class ActionPlanApiTestCase(unittest.TestCase):
    def setUp(self):
        self.main = _reload_app()
        self.client = TestClient(self.main.app)
        self.pid = self.client.post("/projects", json={"name": "Plan", "profile": {}}).json()["project"]["id"]

    def test_get_action_plan(self):
        body = self.client.get(f"/projects/{self.pid}/action-plan").json()
        self.assertEqual(body["summary"]["total"], len(RULES))
        self.assertGreater(body["summary"]["open"], 0)

    def test_complete_loop_raises_readiness(self):
        before = self.client.get(f"/projects/{self.pid}/action-plan").json()["summary"]
        # Complete a step on the weakest driver (financial), so the weakest-link
        # readiness score visibly moves.
        after = self.client.post(f"/projects/{self.pid}/action-plan/books-current/complete").json()
        self.assertEqual(after["summary"]["open"], before["open"] - 1)
        self.assertGreater(after["summary"]["readiness"], before["readiness"])
        # And it persisted: a fresh read still shows the step done.
        reread = self.client.get(f"/projects/{self.pid}/action-plan").json()
        self.assertEqual(reread["summary"]["done"], 1)

    def test_complete_text_step_returns_400(self):
        resp = self.client.post(f"/projects/{self.pid}/action-plan/name-motivation/complete")
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
