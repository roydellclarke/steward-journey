"""Cross-site request forgery guard on state-changing routes.

Before this guard, a page on another site could POST to the API with the
owner's session cookie attached and the write landed: CORS only blocks reading
the response, and a form-encoded POST is a "simple request" that skips the
preflight. These tests pin the three cases that matter: a foreign Origin is
refused, the real frontend Origin still works, and a request with no Origin at
all (Stripe's webhook, our own server-side fetches) is untouched.

Run:  python -m unittest discover -s backend/tests
"""

from __future__ import annotations

import importlib
import os
import re
import tempfile
import unittest


try:
    from fastapi.testclient import TestClient  # noqa: F401
    import slowapi  # noqa: F401
    import itsdangerous  # noqa: F401
    HAS_STACK = True
except Exception:  # pragma: no cover
    HAS_STACK = False


FRONTEND = "http://localhost:3000"
EVIL = "https://evil.example"
_CODE_RE = re.compile(r"Your code: (\d{6})")


def _reload_app():
    root = tempfile.mkdtemp()
    os.environ["STEWARDPATH_DATA_ROOT"] = root
    os.environ["STEWARDPATH_AUTH_DB_PATH"] = os.path.join(root, "auth", "auth.db")
    os.environ["STEWARDPATH_USE_LLM"] = "false"
    os.environ["STEWARDPATH_SECRET_KEY"] = "test-secret-key"
    os.environ["STEWARDPATH_COOKIE_SECURE"] = "false"
    os.environ["STEWARDPATH_FRONTEND_ORIGIN"] = FRONTEND
    # Keep the suite hermetic: no provider keys means the in-memory sender.
    os.environ["STEWARDPATH_RESEND_API_KEY"] = ""
    os.environ["STEWARDPATH_RESEND_FROM"] = ""
    os.environ["STEWARDPATH_POSTMARK_TOKEN"] = ""
    os.environ["STEWARDPATH_POSTMARK_FROM"] = ""
    os.environ["STEWARDPATH_LOG_AUTH_EMAILS"] = "false"
    import app.main as main_module
    importlib.reload(main_module)
    return main_module


@unittest.skipUnless(HAS_STACK, "FastAPI/slowapi/itsdangerous not installed in this environment")
class OriginGuardTestCase(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        self.main = _reload_app()
        self.client = TestClient(self.main.app)
        self.sender = self.main.email_sender

    def _signed_in_project(self) -> str:
        """Create a project and claim it with a real session cookie."""

        pid = self.client.post("/projects", json={"name": "H", "profile": {}}).json()["project"]["id"]
        self.client.post("/auth/request", json={"email": "owner@example.com", "projectId": pid, "gate": "save"})
        code = _CODE_RE.search(self.sender.sent[-1].text_body).group(1)
        verify = self.client.post("/auth/verify", json={"email": "owner@example.com", "code": code})
        self.assertEqual(verify.status_code, 200)
        return pid

    def _analysis_count(self, pid: str) -> int:
        return len(self.client.get(f"/projects/{pid}/analyses").json()["analyses"])

    # ------------------------------------------------------------- refused
    def test_foreign_origin_cannot_write_to_a_signed_in_project(self):
        pid = self._signed_in_project()
        before = self._analysis_count(pid)

        # Form-encoded on purpose: this is the shape that escapes the preflight.
        refused = self.client.post(
            f"/projects/{pid}/intake/analyze",
            headers={"Origin": EVIL, "Content-Type": "application/x-www-form-urlencoded"},
            content="x=1",
        )

        self.assertEqual(refused.status_code, 403)
        self.assertEqual(self._analysis_count(pid), before)

    def test_foreign_origin_cannot_destroy_the_session(self):
        self._signed_in_project()

        self.assertEqual(self.client.post("/auth/logout", headers={"Origin": EVIL}).status_code, 403)

        self.assertTrue(self.client.get("/auth/me").json()["authenticated"])

    def test_foreign_origin_cannot_create_a_project(self):
        refused = self.client.post("/projects", json={"name": "H", "profile": {}}, headers={"Origin": EVIL})
        self.assertEqual(refused.status_code, 403)

    # ------------------------------------------------------------- allowed
    def test_frontend_origin_still_writes(self):
        pid = self._signed_in_project()
        before = self._analysis_count(pid)

        allowed = self.client.post(f"/projects/{pid}/intake/analyze", headers={"Origin": FRONTEND})

        self.assertEqual(allowed.status_code, 201)
        self.assertEqual(self._analysis_count(pid), before + 1)

    def test_request_without_origin_is_untouched(self):
        """Non-browser callers (Stripe's webhook, server-side fetches) send no
        Origin. They must reach the handler, not the guard."""

        pid = self._signed_in_project()

        allowed = self.client.post(f"/projects/{pid}/intake/analyze")

        self.assertEqual(allowed.status_code, 201)

    def test_reads_are_not_blocked_by_origin(self):
        """GET is left to CORS: the foreign page can send it but cannot read
        the reply, and blocking it here would break nothing but add risk."""

        pid = self._signed_in_project()

        self.assertEqual(self.client.get(f"/projects/{pid}", headers={"Origin": EVIL}).status_code, 200)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
