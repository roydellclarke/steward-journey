"""Optional LLM augmentation for StewardPath analysis."""

from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from harness.config import ModelConfig
from harness.env_loader import load_env_file
from harness.llm_client import LlmClient
from mvp.stewardpath.backend.reasoning import OwnerProfile, analyze_owner_profile


def analyze_owner_profile_with_optional_llm(profile: OwnerProfile) -> dict[str, Any]:
    """Return local analysis, optionally enriched by Kimi and DeepSeek.

    Kimi is used for owner-facing language and narrative nuance. DeepSeek is
    used for reasoning review, missing-risk detection, and score adjustment
    suggestions. If either provider is unavailable, the deterministic analysis
    remains the usable fallback and the response explains what happened.
    """

    base = analyze_owner_profile(profile)
    load_env_file()
    if not _llm_enabled():
        base["analysis_source"] = "deterministic"
        base["llm_status"] = "disabled"
        return base

    client = LlmClient()
    kimi_model = os.getenv("STEWARDPATH_KIMI_MODEL", os.getenv("GENERATOR_MODEL", "moonshot/kimi-k2.5"))
    deepseek_model = os.getenv("STEWARDPATH_DEEPSEEK_MODEL", os.getenv("EVALUATOR_MODEL", "deepseek/deepseek-reasoner"))

    errors: list[str] = []
    kimi_patch: dict[str, Any] = {}
    deepseek_patch: dict[str, Any] = {}

    def call_kimi() -> dict[str, Any]:
        kimi = client.complete(
            model_config=ModelConfig("stewardpath_kimi", kimi_model, float(os.getenv("STEWARDPATH_KIMI_TEMPERATURE", "1"))),
            system=KIMI_SYSTEM_PROMPT,
            user=_analysis_prompt(profile, base),
        )
        return _parse_json_object(kimi.content)

    def call_deepseek() -> dict[str, Any]:
        deepseek = client.complete(
            model_config=ModelConfig("stewardpath_deepseek", deepseek_model, float(os.getenv("STEWARDPATH_DEEPSEEK_TEMPERATURE", "0.15"))),
            system=DEEPSEEK_SYSTEM_PROMPT,
            user=_analysis_prompt(profile, base),
        )
        return _parse_json_object(deepseek.content)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            "Kimi": executor.submit(call_kimi),
            "DeepSeek": executor.submit(call_deepseek),
        }
        for provider, future in futures.items():
            try:
                if provider == "Kimi":
                    kimi_patch = future.result()
                else:
                    deepseek_patch = future.result()
            except Exception as exc:  # Keep product usable if keys/provider fail.
                errors.append(f"{provider} unavailable: {type(exc).__name__}: {exc}")

    enriched = _merge_enrichment(base, kimi_patch, deepseek_patch)
    any_llm_succeeded = bool(kimi_patch or deepseek_patch)
    if not errors:
        enriched["analysis_source"] = "llm_augmented"
        enriched["llm_status"] = "ok"
    elif any_llm_succeeded:
        enriched["analysis_source"] = "llm_partial"
        enriched["llm_status"] = "partial"
    else:
        enriched["analysis_source"] = "deterministic_with_llm_errors"
        enriched["llm_status"] = "fallback"
    enriched["llm_models"] = {"kimi": kimi_model, "deepseek": deepseek_model}
    enriched["llm_errors"] = errors
    return enriched


def _llm_enabled() -> bool:
    raw = os.getenv("STEWARDPATH_USE_LLM", os.getenv("HARNESS_USE_LLM", "false"))
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _analysis_prompt(profile: OwnerProfile, base: dict[str, Any]) -> str:
    return json.dumps({"profile": profile.__dict__, "base_analysis": base}, indent=2)


def _parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if not match:
        raise ValueError("LLM response did not contain a JSON object.")
    return json.loads(match.group(0))


def _merge_enrichment(base: dict[str, Any], kimi: dict[str, Any], deepseek: dict[str, Any]) -> dict[str, Any]:
    output = json.loads(json.dumps(base))
    if kimi.get("narratives"):
        output["narratives"].update(kimi["narratives"])
    if kimi.get("jtbd"):
        output["jtbd"].update(kimi["jtbd"])
    if kimi.get("owner_questions"):
        output["owner_questions"] = kimi["owner_questions"]
    if deepseek.get("readiness"):
        output["readiness"].update(deepseek["readiness"])
    if deepseek.get("buffett_quality"):
        output["buffett_quality"].update(deepseek["buffett_quality"])
    if deepseek.get("risks"):
        output["advisor_risks"] = deepseek["risks"]
    if deepseek.get("next_best_questions"):
        output["next_best_questions"] = deepseek["next_best_questions"]
    return output


KIMI_SYSTEM_PROMPT = """You are StewardPath's owner-facing narrative specialist.
Return ONLY valid JSON. Do not provide legal, tax, investment, or valuation advice.
Write directly to the business owner using "you" and "your."
Use plain, loss-aware language: what could be lost, what must be protected,
what delay may cost, and what progress becomes possible.
Do not mention internal frameworks, Jobs to Be Done, pushes, pulls, habits,
anxieties, Buffett, design thinking, books, PDFs, or source materials.

JSON shape:
{
  "jtbd": {
    "struggling_moment": "...",
    "first_thought": "...",
    "emotional_jobs": ["..."],
    "social_jobs": ["..."]
  },
  "narratives": {
    "legacy_statement": "...",
    "buyer_criteria_memo": "...",
    "family_conversation_guide": "...",
    "advisor_brief": "..."
  },
  "owner_questions": ["..."]
}
"""


DEEPSEEK_SYSTEM_PROMPT = """You are StewardPath's adversarial reasoning reviewer.
Review the local analysis for weak assumptions, missing risks, and readiness scoring.
Return ONLY valid JSON. Do not provide legal, tax, investment, or valuation advice.
Write directly to the business owner using "you" and "your."
Use plain, loss-aware language: what could be lost, what must be protected,
what delay may cost, and what progress becomes possible.
Do not mention internal frameworks, Jobs to Be Done, pushes, pulls, habits,
anxieties, Buffett, design thinking, books, PDFs, or source materials.

JSON shape:
{
  "readiness": {
    "interpretation": "...",
    "dimensions": {
      "financial_clarity": 0,
      "operational_transferability": 0,
      "process_documentation": 0,
      "family_alignment": 0,
      "owner_emotional_readiness": 0
    }
  },
  "buffett_quality": {
    "summary": "...",
    "questions_to_answer": ["..."]
  },
  "risks": ["..."],
  "next_best_questions": ["..."]
}
"""
