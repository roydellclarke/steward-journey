"""API tests for passwordless email auth (the two intake gates).

Skipped automatically when FastAPI is not installed, matching the existing
suite. Each test reloads ``app.main`` against a fresh temp data root and a
recording email sender, so no real mail is sent. Cookies are not marked Secure
in tests so the TestClient cookie jar carries the session across calls.

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


_CODE_RE = re.compile(r"Your code: (\d{6})")
_TOKEN_RE = re.compile(r"confirm\?token=(\S+)")


def _reload_app(ttl_minutes: str = "10"):
    root = tempfile.mkdtemp()
    os.environ["STEWARDPATH_DATA_ROOT"] = root
    os.environ["STEWARDPATH_AUTH_DB_PATH"] = os.path.join(root, "auth", "auth.db")
    os.environ["STEWARDPATH_SECRET_KEY"] = "test-secret-key"
    os.environ["STEWARDPATH_COOKIE_SECURE"] = "false"
    os.environ["STEWARDPATH_FRONTEND_ORIGIN"] = "http://localhost:3000"
    os.environ["STEWARDPATH_OTP_TTL_MINUTES"] = ttl_minutes
    import app.main as main_module
    importlib.reload(main_module)
    return main_module


@unittest.skipUnless(HAS_STACK, "FastAPI/slowapi/itsdangerous not installed in this environment")
class AuthApiTestCase(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        self.main = _reload_app()
        self.client = TestClient(self.main.app)
        self.sender = self.main.email_sender  # RecordingEmailSender (no Postmark token)

    # --------------------------------------------------------------- helpers
    def _make_project(self) -> str:
        return self.client.post("/projects", json={"name": "H", "profile": {"industry": "mfg"}}).json()["project"]["id"]

    def _last_email(self):
        return self.sender.sent[-1]

    def _code_from_email(self) -> str:
        return _CODE_RE.search(self._last_email().text_body).group(1)

    def _token_from_email(self) -> str:
        return _TOKEN_RE.search(self._last_email().text_body).group(1)

    def _request(self, email="owner@example.com", project_id=None, gate="save"):
        return self.client.post("/auth/request", json={"email": email, "projectId": project_id, "gate": gate})


class TestRequestVerifyResume(AuthApiTestCase):
    def test_request_then_verify_resumes_with_intake_state(self):
        pid = self._make_project()
        self.client.put(
            f"/projects/{pid}/intake",
            json={"intakeState": {"emotionalReadiness": {"readinessToLetGo": {"value": 4, "status": "answered"}}}},
        )

        self.assertEqual(self._request(project_id=pid, gate="save").status_code, 200)
        verify = self.client.post("/auth/verify", json={"email": "owner@example.com", "code": self._code_from_email()})
        self.assertEqual(verify.status_code, 200)
        body = verify.json()
        self.assertTrue(body["authenticated"])
        self.assertEqual(body["projectId"], pid)

        # Session cookie now carries identity; /auth/me sees the claimed project.
        me = self.client.get("/auth/me").json()
        self.assertTrue(me["authenticated"])
        self.assertEqual(me["email"], "owner@example.com")
        self.assertIn(pid, me["projects"])

        # The intake the owner filled in anonymously is intact and resumable.
        state = self.client.get(f"/projects/{pid}/intake").json()["intakeState"]
        self.assertEqual(state["emotionalReadiness"]["readinessToLetGo"]["value"], 4)

    def test_anonymous_intake_persists_to_owner_on_first_auth(self):
        pid = self._make_project()
        self._request(email="new@owner.com", project_id=pid)
        self.client.post("/auth/verify", json={"email": "new@owner.com", "code": self._code_from_email()})
        owner_id = self.main.auth_store.owner_for_project(pid)
        self.assertIsNotNone(owner_id)
        self.assertEqual(self.main.auth_store.owner_email(owner_id), "new@owner.com")

    def test_other_owner_cannot_claim_an_owned_project(self):
        from fastapi.testclient import TestClient
        pid = self._make_project()
        # Owner A claims the project.
        self._request(email="a@x.com", project_id=pid)
        self.client.post("/auth/verify", json={"email": "a@x.com", "code": self._code_from_email()})
        owner_a = self.main.auth_store.owner_for_project(pid)

        # Owner B, a different browser, tries to claim the same project id.
        other = TestClient(self.main.app)
        other.post("/auth/request", json={"email": "b@x.com", "projectId": pid, "gate": "save"})
        code_b = _CODE_RE.search(self.sender.sent[-1].text_body).group(1)
        res = other.post("/auth/verify", json={"email": "b@x.com", "code": code_b})
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.json()["projectId"])  # B is signed in but claims nothing
        self.assertEqual(self.main.auth_store.owner_for_project(pid), owner_a)  # still A


class TestProjectAccessControl(AuthApiTestCase):
    def _sign_in(self, client, email, project_id=None):
        client.post("/auth/request", json={"email": email, "projectId": project_id, "gate": "save"})
        code = _CODE_RE.search(self.sender.sent[-1].text_body).group(1)
        client.post("/auth/verify", json={"email": email, "code": code})

    def test_unclaimed_project_stays_open_for_the_anonymous_flow(self):
        pid = self._make_project()
        # No session yet: the anonymous holder can read and write while unclaimed.
        self.assertEqual(self.client.get(f"/projects/{pid}/intake").status_code, 200)
        self.assertEqual(self.client.put(f"/projects/{pid}/intake", json={"intakeState": {}}).status_code, 200)

    def test_claimed_project_requires_the_owning_session(self):
        from fastapi.testclient import TestClient
        pid = self._make_project()
        self._sign_in(self.client, "owner@example.com", project_id=pid)

        # The owning session (cookie in this client's jar) still has access.
        self.assertEqual(self.client.get(f"/projects/{pid}/intake").status_code, 200)

        # A stranger with no session is refused, and the 404 hides existence.
        anon = TestClient(self.main.app)
        self.assertEqual(anon.get(f"/projects/{pid}/intake").status_code, 404)
        self.assertEqual(anon.get(f"/projects/{pid}/export").status_code, 404)
        self.assertEqual(anon.delete(f"/projects/{pid}").status_code, 404)

        # A different signed-in owner is refused too.
        other = TestClient(self.main.app)
        self._sign_in(other, "intruder@example.com")
        self.assertEqual(other.get(f"/projects/{pid}/intake").status_code, 404)

    def test_list_projects_is_owner_scoped(self):
        from fastapi.testclient import TestClient
        pid = self._make_project()
        self._sign_in(self.client, "owner@example.com", project_id=pid)
        mine = [p["id"] for p in self.client.get("/projects").json()["projects"]]
        self.assertEqual(mine, [pid])
        # Anonymous callers see nothing, not the full list.
        self.assertEqual(TestClient(self.main.app).get("/projects").json()["projects"], [])

    def test_analyze_cannot_write_to_a_claimed_project_without_session(self):
        from fastapi.testclient import TestClient
        pid = self._make_project()
        self._sign_in(self.client, "owner@example.com", project_id=pid)
        # The /analyze write path must honor ownership too, not just /projects/*.
        anon = TestClient(self.main.app)
        r = anon.post("/analyze", json={"profile": {"industry": "mfg"}, "project_id": pid})
        self.assertEqual(r.status_code, 404)

    def test_leads_list_requires_admin_token(self):
        # No token configured in tests, so the ops endpoint is unreachable.
        self.assertEqual(self.client.get("/leads").status_code, 404)
        self.assertEqual(self.client.get("/leads", headers={"X-Admin-Token": "guess"}).status_code, 404)
        # POST /leads stays public for marketing capture.
        self.assertEqual(self.client.post("/leads", json={"email": "x@y.com"}).status_code, 201)


class TestCodeFailures(AuthApiTestCase):
    def test_wrong_code_rejected(self):
        self._request()
        r = self.client.post("/auth/verify", json={"email": "owner@example.com", "code": "000000"})
        self.assertEqual(r.status_code, 400)

    def test_reused_code_rejected(self):
        self._request()
        code = self._code_from_email()
        first = self.client.post("/auth/verify", json={"email": "owner@example.com", "code": code})
        self.assertEqual(first.status_code, 200)
        second = self.client.post("/auth/verify", json={"email": "owner@example.com", "code": code})
        self.assertEqual(second.status_code, 400)

    def test_per_email_verify_lockout_across_challenges(self):
        email = "grind@x.com"
        # Two challenges, each ground to its 5-attempt cap = 10 attempts total.
        for _ in range(2):
            self._request(email=email)
            for _ in range(5):
                self.client.post("/auth/verify", json={"email": email, "code": "000000"})
        # A fresh, correct code is now refused: the per-email ceiling is hit and
        # cannot be reset by requesting again.
        self._request(email=email)
        good = self._code_from_email()
        self.assertEqual(self.client.post("/auth/verify", json={"email": email, "code": good}).status_code, 400)

    def test_expired_code_rejected(self):
        # Reload with a zero-minute TTL so the freshly minted code is already expired.
        self.main = _reload_app(ttl_minutes="0")
        from fastapi.testclient import TestClient
        self.client = TestClient(self.main.app)
        self.sender = self.main.email_sender
        self._request()
        r = self.client.post("/auth/verify", json={"email": "owner@example.com", "code": self._code_from_email()})
        self.assertEqual(r.status_code, 400)


class TestMagicLink(AuthApiTestCase):
    def test_get_confirm_does_not_consume_token(self):
        pid = self._make_project()
        self._request(project_id=pid, gate="report")
        token = self._token_from_email()

        peek = self.client.get("/auth/confirm", params={"token": token})
        self.assertEqual(peek.status_code, 200)
        self.assertEqual(peek.json()["gate"], "report")

        # The explicit POST still works, proving the GET peek did not burn it.
        confirm = self.client.post("/auth/confirm", json={"token": token})
        self.assertEqual(confirm.status_code, 200)
        self.assertEqual(confirm.json()["projectId"], pid)

    def test_reused_link_rejected(self):
        self._request()
        token = self._token_from_email()
        self.assertEqual(self.client.post("/auth/confirm", json={"token": token}).status_code, 200)
        self.assertEqual(self.client.post("/auth/confirm", json={"token": token}).status_code, 400)

    def test_tampered_link_rejected(self):
        self._request()
        token = self._token_from_email()
        self.assertEqual(self.client.post("/auth/confirm", json={"token": token + "x"}).status_code, 400)


class TestRateLimitAndPrivacy(AuthApiTestCase):
    def test_per_ip_rate_limit_triggers(self):
        statuses = [self._request().status_code for _ in range(20)]
        self.assertIn(429, statuses)

    def test_uniform_response_does_not_reveal_existence(self):
        # An existing owner and a brand-new email get the identical answer.
        self._request(email="known@example.com")
        self.client.post("/auth/verify", json={"email": "known@example.com", "code": self._code_from_email()})
        known = self._request(email="known@example.com")
        unknown = self._request(email="stranger@example.com")
        self.assertEqual(known.status_code, unknown.status_code)
        self.assertEqual(known.json(), unknown.json())

    def test_logout_clears_session(self):
        self._request()
        self.client.post("/auth/verify", json={"email": "owner@example.com", "code": self._code_from_email()})
        self.assertTrue(self.client.get("/auth/me").json()["authenticated"])
        self.client.post("/auth/logout")
        self.assertFalse(self.client.get("/auth/me").json()["authenticated"])


if __name__ == "__main__":
    unittest.main()
