import os
import unittest
from unittest.mock import patch

from mvp.stewardpath.backend.llm_reasoning import analyze_owner_profile_with_optional_llm
from tests.test_stewardpath_reasoning import StewardPathReasoningTests


class StewardPathLlmReasoningTests(unittest.TestCase):
    def test_llm_disabled_returns_deterministic_source(self) -> None:
        profile = StewardPathReasoningTests().profile()
        with patch.dict(os.environ, {"STEWARDPATH_USE_LLM": "false"}, clear=False):
            analysis = analyze_owner_profile_with_optional_llm(profile)
        self.assertEqual(analysis["analysis_source"], "deterministic")
        self.assertEqual(analysis["llm_status"], "disabled")

    def test_llm_enabled_falls_back_when_keys_missing(self) -> None:
        profile = StewardPathReasoningTests().profile()
        with patch.dict(
            os.environ,
            {
                "STEWARDPATH_USE_LLM": "true",
                "DEEPSEEK_API_KEY": "",
                "MOONSHOT_API_KEY": "",
            },
            clear=False,
        ):
            analysis = analyze_owner_profile_with_optional_llm(profile)
        self.assertEqual(analysis["analysis_source"], "deterministic_with_llm_errors")
        self.assertEqual(analysis["llm_status"], "fallback")
        self.assertTrue(analysis["llm_errors"])

    def test_partial_llm_status_when_one_provider_succeeds(self) -> None:
        profile = StewardPathReasoningTests().profile()

        def fake_complete(*, model_config, system, user):
            class Result:
                content = "{}"
            if "moonshot" in model_config.model:
                raise RuntimeError("kimi failed")
            Result.content = '{"risks":["founder dependency"],"next_best_questions":["Who owns customer relationships?"]}'
            return Result()

        with patch.dict(os.environ, {"STEWARDPATH_USE_LLM": "true"}, clear=False):
            with patch("mvp.stewardpath.backend.llm_reasoning.LlmClient.complete", side_effect=fake_complete):
                analysis = analyze_owner_profile_with_optional_llm(profile)

        self.assertEqual(analysis["analysis_source"], "llm_partial")
        self.assertEqual(analysis["llm_status"], "partial")
        self.assertIn("founder dependency", analysis["advisor_risks"])


if __name__ == "__main__":
    unittest.main()
