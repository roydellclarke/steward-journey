"""Optional Kimi + DeepSeek augmentation for the standalone backend."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
import re
from typing import Any
from urllib import request
from urllib.error import HTTPError

from app.core.config import Settings
from app.services.reasoning import OwnerProfile, analyze_owner_profile


def analyze_owner_profile_with_optional_llm(profile: OwnerProfile, settings: Settings) -> dict[str, Any]:
    base = analyze_owner_profile(profile)
    if not settings.use_llm:
        base["analysis_source"] = "deterministic"
        base["llm_status"] = "disabled"
        return base

    errors: list[str] = []
    kimi_patch: dict[str, Any] = {}
    deepseek_patch: dict[str, Any] = {}

    def call_kimi() -> dict[str, Any]:
        content = _complete(
            model=settings.kimi_model,
            temperature=settings.kimi_temperature,
            system=KIMI_SYSTEM_PROMPT,
            user=_analysis_prompt(profile, base),
            timeout=settings.request_timeout_seconds,
        )
        return _parse_json_object(content)

    def call_deepseek() -> dict[str, Any]:
        content = _complete(
            model=settings.deepseek_model,
            temperature=settings.deepseek_temperature,
            system=DEEPSEEK_SYSTEM_PROMPT,
            user=_analysis_prompt(profile, base),
            timeout=settings.request_timeout_seconds,
        )
        return _parse_json_object(content)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {"Kimi": executor.submit(call_kimi), "DeepSeek": executor.submit(call_deepseek)}
        for provider, future in futures.items():
            try:
                if provider == "Kimi":
                    kimi_patch = future.result()
                else:
                    deepseek_patch = future.result()
            except Exception as exc:
                errors.append(f"{provider} unavailable: {type(exc).__name__}: {exc}")

    enriched = _merge_enrichment(base, kimi_patch, deepseek_patch)
    if not errors:
        enriched["analysis_source"] = "llm_augmented"
        enriched["llm_status"] = "ok"
    elif kimi_patch or deepseek_patch:
        enriched["analysis_source"] = "llm_partial"
        enriched["llm_status"] = "partial"
    else:
        enriched["analysis_source"] = "deterministic_with_llm_errors"
        enriched["llm_status"] = "fallback"
    enriched["llm_models"] = {"kimi": settings.kimi_model, "deepseek": settings.deepseek_model}
    enriched["llm_errors"] = errors
    return enriched


def _complete(*, model: str, temperature: float, system: str, user: str, timeout: int) -> str:
    provider, model_name = model.split("/", 1) if "/" in model else ("", model)
    endpoint, api_key = _provider_settings(provider.lower())
    if not endpoint or not api_key:
        raise RuntimeError(f"No API key configured for model `{model}`.")
    payload = {
        "model": model_name,
        "temperature": temperature,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{provider} API request failed with HTTP {exc.code}: {detail}") from exc
    return data["choices"][0]["message"]["content"] or ""


def _provider_settings(provider: str) -> tuple[str, str]:
    if provider == "deepseek":
        return "https://api.deepseek.com/chat/completions", os.getenv("DEEPSEEK_API_KEY", "")
    if provider in {"moonshot", "kimi"}:
        return "https://api.moonshot.ai/v1/chat/completions", os.getenv("MOONSHOT_API_KEY", "")
    return "", ""


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
    """Overlay LLM output onto the deterministic base.

    Product law: the LLM may refine wording only, never invent or change a
    computed figure. So this whitelists narrative/text fields and never copies
    numeric keys (readiness `dimensions`/`overall`, Buffett `scores`) from the
    model. The deterministic scores always win.
    """

    output = json.loads(json.dumps(base))

    # Kimi: owner-facing narrative text.
    if isinstance(kimi.get("narratives"), dict):
        output.setdefault("narratives", {}).update(
            {k: v for k, v in kimi["narratives"].items() if isinstance(v, str)}
        )
    if isinstance(kimi.get("jtbd"), dict):
        output.setdefault("jtbd", {}).update(kimi["jtbd"])
    if kimi.get("owner_questions"):
        output["owner_questions"] = kimi["owner_questions"]

    # DeepSeek: refine wording only. Protect every deterministic score.
    ds_readiness = deepseek.get("readiness")
    if isinstance(ds_readiness, dict) and isinstance(ds_readiness.get("interpretation"), str):
        # Only the interpretation sentence may be reworded; dimensions and
        # overall stay exactly as computed.
        output.setdefault("readiness", {})["interpretation"] = ds_readiness["interpretation"]
    ds_quality = deepseek.get("buffett_quality")
    if isinstance(ds_quality, dict):
        quality = output.setdefault("buffett_quality", {})
        if isinstance(ds_quality.get("summary"), str):
            quality["summary"] = ds_quality["summary"]
        if isinstance(ds_quality.get("questions_to_answer"), list):
            quality["questions_to_answer"] = ds_quality["questions_to_answer"]
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
