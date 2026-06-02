"""Reflective-Summary moments — the highest-leverage concierge component.

After a section (or every few answers), StewardPath echoes back the SPECIFICS the
owner actually gave and bridges warmly to the next question. This is what
produces the feeling of being heard, at near-zero cost.

A deterministic generator (no LLM, fully grounded) is always available so the
feature works offline and can never fabricate. When LLM routing is enabled, an
optional augmentation rewrites the *wording* under a strict grounding system
prompt; on any error it silently falls back to the deterministic reflection.
"""

from __future__ import annotations

from typing import Any

from app.intake import questions as qbank
from app.intake.branching import tone_flags
from app.storage.intake_state import SECTION_FIELDS, field_value, is_field


def _summ_business(state: dict[str, Any]) -> str | None:
    industry = field_value(state, "business", "industry")
    band = field_value(state, "business", "employeeBand")
    years = field_value(state, "business", "yearsOperating")
    bits = []
    if industry:
        bits.append(f"a {industry} business")
    if years:
        bits.append(f"you've run for {years} years")
    if band:
        bits.append(f"with around {band.replace('-', '–')} people")
    if not bits:
        return None
    return "So I'm hearing " + ", ".join(bits)


def _summ_operational(state: dict[str, Any]) -> str | None:
    functions = field_value(state, "operationalTransferability", "functionsDependentOnOwner") or []
    sops = field_value(state, "processDocumentation", "sopsExist")
    risk = field_value(state, "operationalTransferability", "keyPersonRisk")
    parts = []
    if functions:
        parts.append(f"a lot still runs through you — especially {_join(functions)}")
    if sops is False:
        parts.append("much of it lives in your head rather than written down")
    if risk == "high":
        parts.append("and stepping away for even a month would be hard right now")
    if not parts:
        return None
    return "It sounds like " + _join(parts)


def _summ_protected(state: dict[str, Any]) -> str | None:
    concerns = (field_value(state, "protectedInterests", "employeeConcerns") or []) + \
               (field_value(state, "emotionalReadiness", "topConcerns") or [])
    if not concerns:
        return None
    return "What comes through is how much you want to protect " + _join(list(dict.fromkeys(concerns)))


def _summ_family(state: dict[str, Any]) -> str | None:
    align = field_value(state, "familyAlignment", "alignmentLevel")
    in_biz = field_value(state, "familyAlignment", "familyInBusiness")
    if align == "aligned":
        return "It's good that your family is aligned on the future"
    if align in {"partial", "misaligned"}:
        return "I hear there's still some distance in how aligned your family is"
    if in_biz:
        return "I hear family is part of this business"
    return None


SECTION_SUMMARIZERS = {
    "business": _summ_business,
    "operationalTransferability": _summ_operational,
    "processDocumentation": _summ_operational,
    "protectedInterests": _summ_protected,
    "familyAlignment": _summ_family,
}


def _acknowledge(section_key: str, state: dict[str, Any]) -> str:
    """A brief, warm acknowledgment for emotionally weighty sections."""

    if section_key == "familyAlignment":
        return " Family makes this more personal, and there's no wrong way to feel about it."
    if section_key == "emotionalReadiness":
        if tone_flags(state).get("soften"):
            return " And to be clear — you don't need to be ready to sell. There's no rush here."
        return " This part carries real weight, and it's worth taking slowly."
    if section_key == "protectedInterests":
        return " That care is exactly the kind of thing worth protecting before any buyer conversation."
    return ""


def reflect(
    state: dict[str, Any],
    *,
    completed_section: str | None = None,
    next_question_id: str | None = None,
    settings: Any | None = None,
) -> dict[str, Any]:
    """Build a reflective-summary moment grounded in the owner's answers."""

    summarizer = SECTION_SUMMARIZERS.get(completed_section or "")
    reflection = summarizer(state) if summarizer else None
    if not reflection:
        reflection = "Thanks for sharing that"
    reflection = reflection.rstrip(".") + "."
    reflection += _acknowledge(completed_section or "", state)

    bridge = ""
    next_q = qbank.QUESTION_BY_ID.get(next_question_id or "")
    if next_q:
        bridge = f"With that in mind, it helps to look at this next: {next_q['prompt']}"
    else:
        bridge = "When you're ready, we can pull together what this all means for your readiness."

    text = f"{reflection} {bridge}".strip()
    result = {
        "reflection": reflection,
        "bridge": bridge,
        "text": text,
        "grounded": True,
        "source": "deterministic",
        "nextQuestionId": next_question_id,
    }

    if settings is not None and getattr(settings, "use_llm", False):
        improved = _augment_reflection(state, result, completed_section, next_q, settings)
        if improved:
            result.update(improved)
    return result


def _augment_reflection(
    state: dict[str, Any],
    base: dict[str, Any],
    completed_section: str | None,
    next_q: dict[str, Any] | None,
    settings: Any,
) -> dict[str, Any] | None:
    from app.services.llm_reasoning import _complete, _parse_json_object
    import json

    slice_keys = [completed_section] if completed_section else list(SECTION_FIELDS.keys())
    state_slice = {k: state.get(k) for k in slice_keys if state.get(k)}
    user = json.dumps({
        "intake_state_slice": state_slice,
        "next_question": next_q["prompt"] if next_q else None,
        "deterministic_reflection": base["text"],
    }, indent=2)
    try:
        content = _complete(
            model=getattr(settings, "kimi_model", "moonshot/kimi-k2.5"),
            temperature=getattr(settings, "kimi_temperature", 0.5),
            system=REFLECTION_SYSTEM_PROMPT,
            user=user,
            timeout=getattr(settings, "request_timeout_seconds", 120),
        )
        patch = _parse_json_object(content)
    except Exception:  # noqa: BLE001 — never surface to the owner; fall back
        return None
    text = patch.get("text") or patch.get("reflection")
    if isinstance(text, str) and text.strip():
        return {"text": text.strip(), "source": "llm_augmented"}
    return None


def _join(items: list[str]) -> str:
    items = [str(i).strip() for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


REFLECTION_SYSTEM_PROMPT = """You are the reflective voice of StewardPath. Your only
job is to make the owner feel genuinely heard and gently bridge to what comes next.
You are NOT giving legal, tax, valuation, or investment advice.
RULES: Reflect back SPECIFICS the owner actually gave, in their own framing. Ground
everything strictly in intake_state_slice; do NOT invent facts, numbers, or
implications. Treat "unknown"/"skipped" as normal, acceptable gaps — never a fault.
Briefly and warmly acknowledge emotional weight before bridging. Plain language, no
jargon, calm and unhurried. SHORT — a few sentences. Then bridge to next_question.
Return ONLY JSON: {"text": "<reflection + bridge>"}."""
