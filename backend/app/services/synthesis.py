"""Grounded synthesis layer for the concierge upgrade.

Implements the three brief synthesis prompts as deterministic, fabrication-free
generators with OPTIONAL Kimi/DeepSeek augmentation that may only improve the
*wording* of narrative text, never invent facts, figures, or scores:

  1. Score Rationale  (delegated to ``scoring.score_intake`` for the numbers;
     this module adds the owner-facing narrative summary)
  2. Buyer-Fit Comparison  (excludes/​down-weights unacceptable paths)
  3. Successor-Fit Brief

Everything is grounded strictly in the ``IntakeState``. Where the owner hasn't
supplied something, the text says so plainly rather than guessing.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from app.services.scoring import DRIVER_LABELS, score_intake
from app.storage.intake_state import field_value


# Base path characteristics (legacy, financial, emotional on a 1–5 scale) and the
# main trade-off to name. Mirrors the legacy engine so the report stays familiar.
PATH_BASE: dict[str, dict[str, Any]] = {
    "family_transfer": {"label": "Family transfer", "legacy": 5, "financial": 3, "emotional": 4,
                        "tradeoff": "Best when family desire and capability are both real, not assumed."},
    "employee_ownership": {"label": "Employee ownership", "legacy": 5, "financial": 3, "emotional": 4,
                           "tradeoff": "Strong continuity, but depends on a leadership bench and workable financing."},
    "management_buyout": {"label": "Management buyout", "legacy": 4, "financial": 4, "emotional": 4,
                          "tradeoff": "Often preserves culture if managers can operate without you rescuing them."},
    "independent_buyer": {"label": "Independent buyer", "legacy": 4, "financial": 4, "emotional": 3,
                          "tradeoff": "Can fit legacy goals when the buyer genuinely values stewardship and local trust."},
    "strategic_buyer": {"label": "Strategic buyer", "legacy": 3, "financial": 5, "emotional": 2,
                        "tradeoff": "May pay the most, but carries the highest risk to staff and culture."},
    "private_equity": {"label": "Private equity", "legacy": 2, "financial": 5, "emotional": 2,
                       "tradeoff": "Can be financially attractive but needs careful fit screening to protect what you built."},
}

PATH_ORDER = list(PATH_BASE.keys())


def _list(state: dict[str, Any], section: str, field: str) -> list[str]:
    value = field_value(state, section, field)
    return value if isinstance(value, list) else ([value] if value else [])


def buyer_fit(state: dict[str, Any]) -> dict[str, Any]:
    """Per-path fit tied to the owner's STATED priorities; excludes unacceptable."""

    acceptable = set(_list(state, "successorPreferences", "acceptablePaths"))
    unacceptable = set(_list(state, "successorPreferences", "unacceptablePaths"))
    traits = _list(state, "successorPreferences", "idealBuyerTraits")
    protected_emp = _list(state, "protectedInterests", "employeeConcerns")
    protected_cust = _list(state, "protectedInterests", "customerContinuityConcerns")
    non_neg = _list(state, "nonNegotiables", "nonNegotiables")
    cares_team = bool(protected_emp or any("team" in n.lower() or "job" in n.lower() for n in non_neg))

    paths_out: list[dict[str, Any]] = []
    excluded_out: list[dict[str, Any]] = []

    for key in PATH_ORDER:
        base = PATH_BASE[key]
        if key in unacceptable:
            excluded_out.append({
                "path": base["label"],
                "reason": "You marked this as off the table, so it's excluded from your comparison.",
            })
            continue

        legacy = base["legacy"]
        emotional = base["emotional"]
        # Priority-aware nudges, grounded in what the owner actually said.
        priority_notes: list[str] = []
        if cares_team and key in {"strategic_buyer", "private_equity"}:
            priority_notes.append("you've said protecting your team matters, which this path puts most at risk")
        if cares_team and key in {"employee_ownership", "management_buyout"}:
            priority_notes.append("it tends to keep your team and culture intact, which you've prioritized")
        if "local credibility" in traits and key in {"independent_buyer", "management_buyout", "employee_ownership"}:
            priority_notes.append("it can preserve the local credibility you value")
        if key in acceptable:
            priority_notes.append("you've already named this as acceptable")

        summary = _path_summary(base, priority_notes)
        paths_out.append({
            "path": base["label"],
            "key": key,
            "legacyPreservation": legacy,
            "financialPotential": base["financial"],
            "emotionalFit": emotional,
            "preferred": key in acceptable,
            "summary": summary,
            "tradeoff": base["tradeoff"],
        })

    # Preferred/acceptable paths first, then by legacy preservation.
    paths_out.sort(key=lambda p: (not p["preferred"], -p["legacyPreservation"]))
    return {"paths": paths_out, "excluded": excluded_out}


def _path_summary(base: dict[str, Any], priority_notes: list[str]) -> str:
    head = {
        5: "Strong fit for continuity and legacy.",
        4: "A solid, balanced option.",
        3: "A conditional fit worth weighing carefully.",
        2: "A financially-driven option that needs careful screening.",
    }.get(base["legacy"], "An option to weigh.")
    if priority_notes:
        return head + " Against your priorities, " + _join(priority_notes) + ". Consider it as one option to weigh, not a recommendation."
    return head + " Consider it as one option to weigh, not a recommendation."


def successor_fit_brief(state: dict[str, Any]) -> str:
    """A short, advisor-shareable brief drawn only from the owner's stated wishes."""

    traits = _list(state, "successorPreferences", "idealBuyerTraits")
    dealbreakers = _list(state, "successorPreferences", "dealbreakers")
    non_neg = _list(state, "nonNegotiables", "nonNegotiables")
    protected_emp = _list(state, "protectedInterests", "employeeConcerns")
    protected_cust = _list(state, "protectedInterests", "customerContinuityConcerns")

    sentences: list[str] = []
    if traits:
        sentences.append(f"The right next owner would be {_join(traits)}.")
    else:
        sentences.append("The right next owner hasn't been described in detail yet, that's worth defining before buyer conversations.")
    if protected_emp or protected_cust:
        protect = _join(list(dict.fromkeys(protected_emp + protected_cust)))
        sentences.append(f"Above price, this transition must protect {protect}.")
    if non_neg:
        sentences.append(f"What must not be lost: {_join(non_neg)}.")
    if dealbreakers:
        sentences.append(f"Automatic dealbreakers: {_join(dealbreakers)}.")
    sentences.append("Price matters, but fit, continuity, and trust are the test a good buyer has to pass.")
    return " ".join(sentences)


def narrative_outputs(state: dict[str, Any], scored: dict[str, Any]) -> dict[str, str]:
    """Owner-facing copyable artifacts, grounded in inputs. No fabrication."""

    industry = field_value(state, "business", "industry")
    years = field_value(state, "business", "yearsOperating")
    business_ref = f"This {industry} business" if industry else "This business"
    if years:
        business_ref += f", built over {years} years,"
    non_neg = _list(state, "nonNegotiables", "nonNegotiables")
    protect = _join(non_neg) if non_neg else "the people, standards, and trust behind it"
    overall = scored.get("overall", 0)
    top_gaps = [g["gap"] for g in scored.get("topGaps", [])]
    gap_text = _join(top_gaps) if top_gaps else "a few areas worth tightening"

    # Advisor brief stays in one voice: third person about the owner throughout.
    advisor = (
        f"{business_ref} is preparing for a thoughtful transition. "
        f"Current readiness is {overall} out of 100. Above all, the owner wants to protect {protect}. "
        f"Before any buyer conversation, the priorities are: {gap_text}. "
        f"This is preparation support: not a valuation, and not legal, tax, or investment advice."
    )
    family = (
        "This isn't only a decision about whether to sell. It's a decision about what must not be lost, "
        f"{protect}. The next step is to prepare carefully, together, before timing or a buyer defines the terms."
    )
    return {
        "advisorSummary": advisor,
        "familyConversationGuide": family,
        "successorFitBrief": successor_fit_brief(state),
    }


def synthesize(state: dict[str, Any], settings: Any | None = None) -> dict[str, Any]:
    """Full grounded synthesis bundle from an IntakeState."""

    scored = score_intake(state)
    base = {
        "analysis_source": "intake_deterministic",
        "llm_status": "disabled",
        "readiness": {
            "overall": scored["overall"],
            "dimensions": scored["dimensions"],
            "interpretation": scored["interpretation"],
        },
        "scoreRationale": scored["scoreRationale"],
        "driverLabels": DRIVER_LABELS,
        "flaggedGaps": scored["flaggedGaps"],
        "topGaps": scored["topGaps"],
        "buyerFit": buyer_fit(state),
        "narratives": narrative_outputs(state, scored),
        "completionPct": scored["completionPct"],
        "disclaimers": [
            "Educational preparation support only.",
            "Not legal, tax, investment, or valuation advice.",
            "Not a formal valuation.",
            "Grounded only in what you've shared; nothing here is fabricated.",
        ],
    }

    if settings is None or not getattr(settings, "use_llm", False):
        return base

    enriched = _augment_with_llm(state, base, settings)
    return enriched


def _augment_with_llm(state: dict[str, Any], base: dict[str, Any], settings: Any) -> dict[str, Any]:
    """Optionally improve ONLY narrative wording via Kimi/DeepSeek. Scores and
    facts from ``base`` are authoritative and never overwritten."""

    # Imported lazily so deterministic mode never requires network code paths.
    from app.services.llm_reasoning import _complete, _parse_json_object

    import json

    prompt = json.dumps({
        "instruction": "Improve the WORDING of the narratives only. Ground strictly in intake_state. Do not invent facts, numbers, names, or implications. Keep it plain, warm, and short.",
        "intake_state": state,
        "current_narratives": base["narratives"],
    }, indent=2)

    errors: list[str] = []
    patch: dict[str, Any] = {}

    def call() -> dict[str, Any]:
        content = _complete(
            model=getattr(settings, "kimi_model", "moonshot/kimi-k2.5"),
            temperature=getattr(settings, "kimi_temperature", 0.4),
            system=NARRATIVE_SYSTEM_PROMPT,
            user=prompt,
            timeout=getattr(settings, "request_timeout_seconds", 120),
        )
        return _parse_json_object(content)

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            patch = executor.submit(call).result()
    except Exception as exc:  # noqa: BLE001 - record, never raise to the owner
        errors.append(f"{type(exc).__name__}: {exc}")

    enriched = json.loads(json.dumps(base))
    if isinstance(patch.get("narratives"), dict):
        for key in ("advisorSummary", "familyConversationGuide", "successorFitBrief"):
            if isinstance(patch["narratives"].get(key), str) and patch["narratives"][key].strip():
                enriched["narratives"][key] = patch["narratives"][key].strip()
        enriched["analysis_source"] = "intake_llm_augmented"
        enriched["llm_status"] = "ok"
    if errors:
        enriched["analysis_source"] = "intake_deterministic_with_llm_errors"
        enriched["llm_status"] = "fallback"
        enriched["llm_errors"] = errors
    return enriched


def _join(items: list[str]) -> str:
    items = [str(i).strip() for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


NARRATIVE_SYSTEM_PROMPT = """You are StewardPath's owner-facing narrative editor.
Return ONLY valid JSON of shape {"narratives": {"advisorSummary": "...",
"familyConversationGuide": "...", "successorFitBrief": "..."}}.
Improve clarity and warmth ONLY. Ground every word strictly in the provided
intake_state and current_narratives. Never invent facts, numbers, names, or
implications. Do not give legal, tax, valuation, or investment advice. Write
directly to the owner in plain language. Keep each field short."""
