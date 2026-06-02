"""Tests for the StewardPath concierge-experience upgrade.

Pure-logic tests run anywhere (no FastAPI required). The API tests are skipped
automatically when FastAPI/Starlette is not installed, so this suite stays green
in the offline harness environment while still being runnable in the service env.

Run:  python -m unittest discover -s backend/tests
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.intake import branching
from app.intake.handoff import build_handoff
from app.intake.reflection import reflect
from app.services.scoring import score_intake
from app.services.synthesis import buyer_fit, successor_fit_brief, synthesize
from app.storage.intake_state import (
    INTAKE_SCHEMA_VERSION,
    field_value,
    merge_intake_patch,
    migrate_profile_to_intake_state,
    open_gaps,
)
from app.storage.projects import ProjectStore


SAMPLE_V3 = {
    "meta": {"ownerRecordId": "rec-1", "schemaVersion": 3, "createdAt": "2026-01-01T00:00:00Z",
             "updatedAt": "2026-01-01T00:00:00Z", "completionPct": 50, "lastSection": "business", "snapshots": []},
    "business": {"industry": {"value": "specialty manufacturing", "status": "answered", "confidence": "medium", "updatedAt": "x", "note": ""},
                 "revenueBand": {"value": "5m-20m", "status": "answered", "confidence": "medium", "updatedAt": "x", "note": ""}},
    "operationalTransferability": {"keyPersonRisk": {"value": "high", "status": "answered", "confidence": "medium", "updatedAt": "x", "note": ""}},
    "nonNegotiables": {"value": ["keep the local team"], "status": "answered", "confidence": "medium", "updatedAt": "x", "note": ""},
    "disclosureControls": {"defaultVisibility": "private", "sectionOverrides": {}, "fieldOverrides": {}},
}


class TestSchemaMigration(unittest.TestCase):
    def test_v3_to_v4_is_lossless(self):
        mig = migrate_profile_to_intake_state(None, SAMPLE_V3)
        self.assertEqual(mig["meta"]["schemaVersion"], INTAKE_SCHEMA_VERSION)
        self.assertEqual(mig["meta"]["ownerRecordId"], "rec-1")
        self.assertEqual(field_value(mig, "business", "industry"), "specialty manufacturing")
        self.assertEqual(field_value(mig, "operationalTransferability", "keyPersonRisk"), "high")
        self.assertEqual(field_value(mig, "nonNegotiables", "nonNegotiables"), ["keep the local team"])

    def test_migration_is_idempotent(self):
        once = migrate_profile_to_intake_state(None, SAMPLE_V3)
        twice = migrate_profile_to_intake_state(None, once)
        self.assertEqual(field_value(twice, "business", "industry"), "specialty manufacturing")
        self.assertEqual(twice["meta"]["ownerRecordId"], once["meta"]["ownerRecordId"])

    def test_default_visibility_is_private(self):
        state = migrate_profile_to_intake_state({}, None)
        self.assertEqual(state["disclosureControls"]["defaultVisibility"], "private")

    def test_patch_preserves_other_answers(self):
        base = migrate_profile_to_intake_state(None, SAMPLE_V3)
        patched = merge_intake_patch(base, {"emotionalReadiness": {"readinessToLetGo": {"value": 4, "status": "answered"}}})
        self.assertEqual(field_value(patched, "emotionalReadiness", "readinessToLetGo"), 4)
        self.assertEqual(field_value(patched, "business", "industry"), "specialty manufacturing")

    def test_unknown_is_a_signal_not_error(self):
        state = migrate_profile_to_intake_state({}, None)
        self.assertIn("emotionalReadiness.readinessToLetGo", open_gaps(state))


class TestBranching(unittest.TestCase):
    def test_security_gated_sections(self):
        plan = branching.build_intake_plan(migrate_profile_to_intake_state({}, None))
        self.assertEqual(set(plan["securityGatedSections"]), {"financialClarity", "familyAlignment"})
        fin = next(s for s in plan["sections"] if s["key"] == "financialClarity")
        self.assertTrue(fin["securityGate"] and fin["reassurance"])

    def test_family_collapse_keeps_expectations(self):
        state = merge_intake_patch(
            migrate_profile_to_intake_state({}, None),
            {"familyAlignment": {"familyInBusiness": {"value": False, "status": "answered"}}},
        )
        fam = next(s for s in branching.build_intake_plan(state)["sections"] if s["key"] == "familyAlignment")
        fields = [q["field"] for q in fam["questions"]]
        self.assertEqual(fields, ["familyInBusiness", "expectationsKnown"])

    def test_not_ready_softens_and_no_timing_pressure(self):
        state = merge_intake_patch(
            migrate_profile_to_intake_state({}, None),
            {"emotionalReadiness": {"readinessToLetGo": {"value": 1, "status": "answered"}}},
        )
        flags = branching.build_intake_plan(state)["toneFlags"]
        self.assertTrue(flags["soften"] and flags["noTimingPressure"])

    def test_health_urgency_routes_to_human(self):
        state = merge_intake_patch(
            migrate_profile_to_intake_state({}, None),
            {"emotionalReadiness": {"urgencyDrivers": {"value": ["health"], "status": "answered"}}},
        )
        self.assertEqual(branching.build_intake_plan(state, 40)["routing"]["mode"], "human_touchpoint")

    def test_high_readiness_warm_handoff(self):
        plan = branching.build_intake_plan(migrate_profile_to_intake_state({}, None), 82)
        self.assertEqual(plan["routing"]["mode"], "warm_handoff")

    def test_unanswered_never_blocks_completion_of_plan(self):
        # An empty state still yields a full, valid plan with a next question.
        plan = branching.build_intake_plan(migrate_profile_to_intake_state({}, None))
        self.assertFalse(plan["done"])
        self.assertIsNotNone(plan["nextQuestionId"])


class TestScoringAndGrounding(unittest.TestCase):
    def setUp(self):
        self.state = migrate_profile_to_intake_state(None, SAMPLE_V3)

    def test_score_shape_and_bounds(self):
        scored = score_intake(self.state)
        self.assertTrue(0 <= scored["overall"] <= 100)
        self.assertEqual(set(scored["dimensions"]),
                         {"financial_clarity", "operational_transferability", "process_documentation",
                          "family_alignment", "owner_emotional_readiness"})
        self.assertEqual(set(scored["scoreRationale"]), set(scored["dimensions"]))

    def test_rationale_is_grounded_in_inputs(self):
        scored = score_intake(self.state)
        # keyPersonRisk == high was an input; rationale must reflect dependency.
        self.assertIn("depends on you", scored["scoreRationale"]["operational_transferability"].lower())

    def test_buyer_fit_excludes_unacceptable(self):
        state = merge_intake_patch(self.state, {"successorPreferences": {
            "unacceptablePaths": {"value": ["private_equity"], "status": "answered"}}})
        bf = buyer_fit(state)
        labels = [p["path"] for p in bf["paths"]]
        self.assertIn("Private equity", [e["path"] for e in bf["excluded"]])
        self.assertNotIn("Private equity", labels)

    def test_no_fabricated_dollar_figures(self):
        bundle = synthesize(self.state)  # deterministic
        for text in bundle["narratives"].values():
            self.assertNotIn("$", text)  # we report bands & scores, never invented dollars

    def test_empty_state_admits_gaps_rather_than_inventing(self):
        empty = migrate_profile_to_intake_state({}, None)
        brief = successor_fit_brief(empty)
        self.assertIn("hasn't been described", brief.lower())

    def test_synthesis_is_deterministic_without_settings(self):
        bundle = synthesize(self.state)
        self.assertEqual(bundle["analysis_source"], "intake_deterministic")
        self.assertEqual(bundle["llm_status"], "disabled")
        self.assertGreaterEqual(len(bundle["disclaimers"]), 3)


class TestReflection(unittest.TestCase):
    def test_reflection_is_grounded_and_specific(self):
        state = migrate_profile_to_intake_state(None, SAMPLE_V3)
        r = reflect(state, completed_section="business", next_question_id="biz_region")
        self.assertTrue(r["grounded"])
        self.assertEqual(r["source"], "deterministic")
        self.assertIn("specialty manufacturing", r["text"])


class TestHandoff(unittest.TestCase):
    def test_handoff_package_complete(self):
        state = migrate_profile_to_intake_state(None, SAMPLE_V3)
        h = build_handoff(state)
        self.assertEqual(len(h["readiness"]["drivers"]), 5)
        self.assertEqual(h["disclosure"]["defaultVisibility"], "private")
        self.assertTrue(h["talkingPoints"])
        self.assertTrue(h["highestImpactNextSteps"])


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.store = ProjectStore(Path(tempfile.mkdtemp()))

    def test_create_seeds_intake_and_persists(self):
        proj = self.store.create_project(name="X", profile={"industry": "trades", "employees": 12})
        self.assertEqual(proj["intakeState"]["meta"]["schemaVersion"], INTAKE_SCHEMA_VERSION)
        again = self.store.get_project(proj["id"])
        self.assertIsNotNone(again["intakeState"])

    def test_snapshot_on_analysis(self):
        proj = self.store.create_project(name="X", profile={})
        self.store.append_analysis(proj["id"], profile_snapshot={}, analysis={"readiness": {"overall": 61}})
        self.assertEqual(self.store.snapshots(proj["id"])[0]["readinessScore"], 61)

    def test_export_then_hard_delete(self):
        proj = self.store.create_project(name="X", profile={})
        export = self.store.export_project(proj["id"])
        self.assertIsNotNone(export["intakeState"])
        self.assertTrue(self.store.delete_project(proj["id"]))
        self.assertIsNone(self.store.get_project(proj["id"]))
        # audit retains the deletion event (metadata only)
        self.assertTrue(any(e["action"] == "deleted" for e in self.store.audit.events(proj["id"])))

    def test_legacy_signatures_still_work(self):
        proj = self.store.create_project(name="L", profile={"business_name": "Legacy"})
        entry = self.store.append_analysis(proj["id"], profile_snapshot={}, analysis={"readiness": {"overall": 50}})
        self.assertIsNotNone(entry)


try:
    from fastapi.testclient import TestClient  # noqa: F401
    HAS_FASTAPI = True
except Exception:  # pragma: no cover
    HAS_FASTAPI = False


@unittest.skipUnless(HAS_FASTAPI, "FastAPI not installed in this environment")
class TestApi(unittest.TestCase):
    def setUp(self):
        import os
        os.environ["STEWARDPATH_DATA_ROOT"] = tempfile.mkdtemp()
        from fastapi.testclient import TestClient
        # Re-import app fresh so it binds to the temp data root.
        import importlib
        import app.main as main_module
        importlib.reload(main_module)
        self.client = TestClient(main_module.app)

    def test_health_and_existing_analyze(self):
        self.assertTrue(self.client.get("/health").json()["ok"])
        r = self.client.post("/analyze", json={"profile": {"business_name": "H", "industry": "mfg"}})
        self.assertEqual(r.status_code, 200)
        self.assertIn("readiness", r.json()["analysis"])

    def test_full_intake_lifecycle(self):
        c = self.client
        self.assertEqual(len(c.get("/intake/questions").json()["sections"]), 9)
        pid = c.post("/projects", json={"name": "H", "profile": {"industry": "mfg"}}).json()["project"]["id"]
        self.assertEqual(c.get(f"/projects/{pid}/intake").status_code, 200)
        put = c.put(f"/projects/{pid}/intake", json={"intakeState": {"emotionalReadiness": {"readinessToLetGo": {"value": 4, "status": "answered"}}}})
        self.assertEqual(put.status_code, 200)
        self.assertEqual(c.post(f"/projects/{pid}/intake/analyze").status_code, 201)
        self.assertEqual(len(c.get(f"/projects/{pid}/handoff").json()["handoff"]["readiness"]["drivers"]), 5)
        self.assertTrue(c.get(f"/projects/{pid}/export").json()["intakeState"])
        self.assertEqual(c.delete(f"/projects/{pid}").status_code, 200)
        self.assertEqual(c.get(f"/projects/{pid}").status_code, 404)


if __name__ == "__main__":
    unittest.main()
