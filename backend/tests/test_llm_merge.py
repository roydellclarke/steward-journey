"""Tests for the optional Kimi + DeepSeek augmentation.

Product laws #3/#4: the LLM may refine wording only. It must never invent or
change a computed figure, and when a provider fails the deterministic result
must survive. No network is used; `_complete` is monkeypatched.

Run:  python -m unittest discover -s backend/tests
"""

from __future__ import annotations

import unittest
from unittest import mock

from app.services import llm_reasoning
from app.services.llm_reasoning import (
    _merge_enrichment,
    analyze_owner_profile_with_optional_llm,
)
from app.services.reasoning import OwnerProfile, analyze_owner_profile


def _profile() -> OwnerProfile:
    return OwnerProfile(
        business_name="Ridgeline HVAC",
        industry="HVAC",
        years_operating=22,
        employees=14,
        revenue_range="$2M-$5M",
        profit_margin="10-15%",
        owner_dependency="high",
        timeline="1-3 years",
        owner_goal="protect my crew and name",
        fears="wrong buyer guts the team",
        non_negotiables="keep the crew",
        family_context="kids not interested",
        next_owner_traits="operator who values people",
    )


class _Settings:
    """Minimal stand-in for Settings; only the fields the path reads."""

    use_llm = True
    kimi_model = "moonshot/kimi-k2.6"
    deepseek_model = "deepseek/deepseek-reasoner"
    kimi_temperature = 1.0
    deepseek_temperature = 0.15
    request_timeout_seconds = 30


class MergeGroundingTests(unittest.TestCase):
    def test_llm_never_overwrites_readiness_scores(self):
        base = analyze_owner_profile(_profile())
        original_dims = dict(base["readiness"]["dimensions"])
        original_overall = base["readiness"]["overall"]

        # A hostile DeepSeek patch that tries to invent every number.
        deepseek = {
            "readiness": {
                "interpretation": "A reworded, grounded sentence.",
                "dimensions": {k: 99 for k in original_dims},
            },
            "buffett_quality": {
                "summary": "Reworded summary.",
                "scores": {"understandable_business": 0},
                "questions_to_answer": ["New question?"],
            },
        }
        merged = _merge_enrichment(base, {}, deepseek)

        # Numbers are untouched; sum still holds.
        self.assertEqual(merged["readiness"]["dimensions"], original_dims)
        self.assertEqual(merged["readiness"]["overall"], original_overall)
        self.assertEqual(
            merged["buffett_quality"]["scores"], base["buffett_quality"]["scores"]
        )
        # Text was refined.
        self.assertEqual(
            merged["readiness"]["interpretation"], "A reworded, grounded sentence."
        )
        self.assertEqual(merged["buffett_quality"]["summary"], "Reworded summary.")

    def test_kimi_narratives_take_only_strings(self):
        base = analyze_owner_profile(_profile())
        kimi = {"narratives": {"legacy_statement": "Grounded.", "sneaky": {"n": 1}}}
        merged = _merge_enrichment(base, kimi, {})
        self.assertEqual(merged["narratives"]["legacy_statement"], "Grounded.")
        self.assertNotIn("sneaky", merged["narratives"])


class FallbackTests(unittest.TestCase):
    def test_provider_failure_falls_back_to_deterministic(self):
        settings = _Settings()
        base = analyze_owner_profile(_profile())

        def boom(*args, **kwargs):
            raise RuntimeError("provider down")

        with mock.patch.object(llm_reasoning, "_complete", boom):
            out = analyze_owner_profile_with_optional_llm(_profile(), settings)

        self.assertEqual(out["llm_status"], "fallback")
        self.assertEqual(out["analysis_source"], "deterministic_with_llm_errors")
        # Deterministic scores are intact.
        self.assertEqual(out["readiness"]["overall"], base["readiness"]["overall"])
        self.assertEqual(len(out["llm_errors"]), 2)

    def test_disabled_returns_deterministic(self):
        s = _Settings()
        s.use_llm = False
        out = analyze_owner_profile_with_optional_llm(_profile(), s)
        self.assertEqual(out["llm_status"], "disabled")
        self.assertEqual(out["analysis_source"], "deterministic")


if __name__ == "__main__":
    unittest.main()
