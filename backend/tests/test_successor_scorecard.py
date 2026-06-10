"""Tests for the successor-fit scorecard: fit scoring, and ranking by fit
rather than by the size of the offer.

Unit tests need no web stack. API tests skip without FastAPI.

Run:  python -m unittest discover -s backend/tests
"""

from __future__ import annotations

import importlib
import os
import tempfile
import unittest

from app.services.successor_scorecard import CRITERIA, build_scorecard, score_candidate


try:
    from fastapi.testclient import TestClient  # noqa: F401
    import slowapi  # noqa: F401
    import itsdangerous  # noqa: F401
    HAS_STACK = True
except Exception:  # pragma: no cover
    HAS_STACK = False


def _ratings(v):
    return {c["key"]: v for c in CRITERIA}


class ScorecardUnitTestCase(unittest.TestCase):
    def test_fit_score_from_ratings(self):
        top = score_candidate({"name": "A", "ratings": _ratings(5)})
        mid = score_candidate({"name": "B", "ratings": _ratings(3)})
        self.assertEqual(top["fitScore"], 100)
        self.assertEqual(mid["fitScore"], 60)

    def test_dealbreaker_rules_out(self):
        c = score_candidate({"name": "X", "ratings": _ratings(5), "dealbreaker": True})
        self.assertTrue(c["ruledOut"])

    def test_ranks_by_fit_not_offer(self):
        # High fit, weak offer should beat low fit, strong offer.
        good_fit = {"name": "Family Maria", "ratings": _ratings(5), "offerStrength": 1}
        big_offer = {"name": "PE Buyer", "ratings": _ratings(2), "offerStrength": 5}
        card = build_scorecard([big_offer, good_fit])
        self.assertEqual(card["candidates"][0]["name"], "Family Maria")
        self.assertEqual(card["candidates"][0]["rank"], 1)
        self.assertEqual(card["summary"]["topName"], "Family Maria")

    def test_ruled_out_sinks_below_kept(self):
        kept = {"name": "Tom", "ratings": _ratings(3)}
        ruled = {"name": "Rival", "ratings": _ratings(5), "dealbreaker": True}
        card = build_scorecard([ruled, kept])
        self.assertEqual(card["candidates"][0]["name"], "Tom")
        self.assertTrue(card["candidates"][-1]["ruledOut"])

    def test_ratings_clamped(self):
        c = score_candidate({"name": "Z", "ratings": _ratings(99), "offerStrength": -4})
        self.assertEqual(c["fitScore"], 100)  # clamps to 5
        self.assertEqual(c["offerStrength"], 1)  # clamps to 1


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
class ScorecardApiTestCase(unittest.TestCase):
    def setUp(self):
        self.main = _reload_app()
        self.client = TestClient(self.main.app)
        self.pid = self.client.post("/projects", json={"name": "S", "profile": {}}).json()["project"]["id"]

    def test_put_then_get_ranks_by_fit(self):
        payload = {"candidates": [
            {"name": "PE Buyer", "ratings": _ratings(2), "offerStrength": 5},
            {"name": "Family Maria", "ratings": _ratings(5), "offerStrength": 1},
        ]}
        put = self.client.put(f"/projects/{self.pid}/successors", json=payload).json()
        self.assertEqual(put["candidates"][0]["name"], "Family Maria")
        # ids are assigned on save and persist across a GET.
        self.assertTrue(all(c["id"] for c in put["candidates"]))
        got = self.client.get(f"/projects/{self.pid}/successors").json()
        self.assertEqual(got["candidates"][0]["name"], "Family Maria")
        self.assertEqual(got["summary"]["count"], 2)

    def test_empty_scorecard(self):
        got = self.client.get(f"/projects/{self.pid}/successors").json()
        self.assertEqual(got["summary"]["count"], 0)
        self.assertEqual(len(got["criteria"]), len(CRITERIA))


if __name__ == "__main__":
    unittest.main()
