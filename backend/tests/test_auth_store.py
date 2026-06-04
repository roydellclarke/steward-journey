"""Unit tests for the SQLite auth store and the email composer.

Pure logic, no network and no FastAPI. Time is injected so expiry is
deterministic. Run: python -m unittest discover -s backend/tests
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import tempfile
import unittest
from pathlib import Path

from app.services.email import RecordingEmailSender, build_auth_email, build_email_sender
from app.storage.auth_db import AuthStore


BASE = datetime(2026, 6, 4, 12, 0, 0, tzinfo=UTC)
SECRET = "test-secret-key"


class AuthStoreTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.store = AuthStore(Path(self._tmp.name) / "auth.db", SECRET)

    def _challenge(self, **overrides):
        params = dict(
            email="Owner@Example.com",
            code="123456",
            token="magic-token-abc",
            gate="save",
            project_id="proj-1",
            ttl_minutes=10,
            now=BASE,
        )
        params.update(overrides)
        return self.store.create_challenge(**params)


class TestCodeVerification(AuthStoreTestCase):
    def test_request_then_verify_succeeds(self) -> None:
        self._challenge()
        result = self.store.verify_code("owner@example.com", "123456", now=BASE + timedelta(minutes=2))
        self.assertTrue(result.ok)
        self.assertEqual(result.gate, "save")
        self.assertEqual(result.project_id, "proj-1")
        self.assertEqual(result.email, "owner@example.com")

    def test_email_match_is_case_insensitive(self) -> None:
        self._challenge(email="Owner@Example.com")
        result = self.store.verify_code("OWNER@EXAMPLE.COM", "123456", now=BASE)
        self.assertTrue(result.ok)

    def test_expired_code_rejected(self) -> None:
        self._challenge(ttl_minutes=10)
        result = self.store.verify_code("owner@example.com", "123456", now=BASE + timedelta(minutes=11))
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "expired")

    def test_reused_code_rejected(self) -> None:
        self._challenge()
        first = self.store.verify_code("owner@example.com", "123456", now=BASE)
        self.assertTrue(first.ok)
        second = self.store.verify_code("owner@example.com", "123456", now=BASE + timedelta(seconds=1))
        self.assertFalse(second.ok)
        # No open challenge remains, so the second read finds nothing.
        self.assertIn(second.reason, {"already_used", "not_found"})

    def test_wrong_code_counts_against_attempts(self) -> None:
        self._challenge(max_attempts=5)
        for _ in range(5):
            miss = self.store.verify_code("owner@example.com", "000000", now=BASE)
            self.assertEqual(miss.reason, "mismatch")
        # Sixth attempt is locked out even though the real code is correct.
        locked = self.store.verify_code("owner@example.com", "123456", now=BASE)
        self.assertFalse(locked.ok)
        self.assertEqual(locked.reason, "too_many_attempts")

    def test_unknown_email_returns_not_found(self) -> None:
        result = self.store.verify_code("nobody@example.com", "123456", now=BASE)
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "not_found")


class TestTokenConsume(AuthStoreTestCase):
    def test_magic_token_single_use(self) -> None:
        self._challenge(token="magic-token-abc")
        first = self.store.consume_token("magic-token-abc", now=BASE)
        self.assertTrue(first.ok)
        self.assertEqual(first.gate, "save")
        second = self.store.consume_token("magic-token-abc", now=BASE + timedelta(seconds=1))
        self.assertFalse(second.ok)
        self.assertEqual(second.reason, "already_used")

    def test_expired_token_rejected(self) -> None:
        self._challenge(token="magic-token-abc", ttl_minutes=10)
        result = self.store.consume_token("magic-token-abc", now=BASE + timedelta(minutes=11))
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "expired")

    def test_unknown_token_rejected(self) -> None:
        result = self.store.consume_token("not-a-real-token", now=BASE)
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "not_found")


class TestRateCounting(AuthStoreTestCase):
    def test_recent_challenge_count_windows(self) -> None:
        self._challenge(now=BASE)
        self._challenge(now=BASE + timedelta(minutes=1))
        self._challenge(now=BASE - timedelta(minutes=30))
        recent = self.store.recent_challenge_count(
            "owner@example.com", within_minutes=15, now=BASE + timedelta(minutes=2)
        )
        self.assertEqual(recent, 2)


class TestOwnersAndProjects(AuthStoreTestCase):
    def test_find_or_create_owner_is_stable(self) -> None:
        first = self.store.find_or_create_owner("owner@example.com", now=BASE)
        again = self.store.find_or_create_owner("OWNER@example.com", now=BASE)
        self.assertEqual(first, again)
        self.assertEqual(self.store.owner_email(first), "owner@example.com")

    def test_link_and_list_projects(self) -> None:
        owner = self.store.find_or_create_owner("owner@example.com", now=BASE)
        self.store.link_project(owner, "proj-1", now=BASE)
        self.store.link_project(owner, "proj-1", now=BASE)  # idempotent
        self.store.link_project(owner, "proj-2", now=BASE + timedelta(minutes=1))
        self.assertEqual(self.store.projects_for_owner(owner), ["proj-1", "proj-2"])
        self.assertEqual(self.store.owner_for_project("proj-2"), owner)


class TestSessions(AuthStoreTestCase):
    def test_session_round_trip(self) -> None:
        owner = self.store.find_or_create_owner("owner@example.com", now=BASE)
        self.store.create_session(owner, "session-token", ttl_days=30, now=BASE)
        self.assertEqual(self.store.read_session("session-token", now=BASE + timedelta(days=1)), owner)

    def test_expired_session_rejected(self) -> None:
        owner = self.store.find_or_create_owner("owner@example.com", now=BASE)
        self.store.create_session(owner, "session-token", ttl_days=30, now=BASE)
        self.assertIsNone(self.store.read_session("session-token", now=BASE + timedelta(days=31)))

    def test_logout_clears_session(self) -> None:
        owner = self.store.find_or_create_owner("owner@example.com", now=BASE)
        self.store.create_session(owner, "session-token", now=BASE)
        self.store.delete_session("session-token")
        self.assertIsNone(self.store.read_session("session-token", now=BASE))


class TestEmailComposer(unittest.TestCase):
    def test_build_auth_email_carries_code_and_link(self) -> None:
        message = build_auth_email(to="o@example.com", code="246802", link="https://x/confirm?token=t", gate="report")
        self.assertIn("246802", message.text_body)
        self.assertIn("https://x/confirm?token=t", message.text_body)
        self.assertIn("readiness report", message.text_body)
        self.assertNotIn("—", message.text_body)  # writing law: no em-dashes

    def test_factory_returns_recording_sender_without_token(self) -> None:
        sender = build_email_sender(postmark_token="", postmark_from="")
        self.assertIsInstance(sender, RecordingEmailSender)
        sender.send(build_auth_email(to="o@example.com", code="1", link="l", gate="save"))
        self.assertEqual(len(sender.sent), 1)


if __name__ == "__main__":
    unittest.main()
