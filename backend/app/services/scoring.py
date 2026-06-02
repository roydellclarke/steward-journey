"""Readiness scoring directly from the structured ``IntakeState``.

Produces the five readiness drivers (0–5), a unified 0–100 score using the same
weakest-link-weighted formula as the legacy profile-based engine, a plain-language
RATIONALE for every driver grounded strictly in the owner's actual answers
(Requirement #5: score explainability), and ``flaggedGaps`` + top next steps.

``unknown``/``skipped`` fields are treated as gaps that hold a driver back — never
as errors, and never silently inflated. Pure Python; no LLM, no fabrication.
"""

from __future__ import annotations

from typing import Any

from app.intake.branching import flagged_gaps
from app.services.reasoning import _unified_readiness_score
from app.storage.intake_state import field_status, field_value


DRIVERS = [
    "financial_clarity",
    "operational_transferability",
    "process_documentation",
    "family_alignment",
    "owner_emotional_readiness",
]

DRIVER_LABELS = {
    "financial_clarity": "Financial clarity",
    "operational_transferability": "Operational transferability",
    "process_documentation": "Process documentation",
    "family_alignment": "Family alignment",
    "owner_emotional_readiness": "Owner emotional readiness",
}


def _clamp(score: float) -> float:
    return max(0.0, min(5.0, score))


def _financial(state: dict[str, Any]) -> tuple[float, str, list[str]]:
    score = 2.0
    notes: list[str] = []
    gaps: list[str] = []
    books = field_value(state, "financialClarity", "booksUpToDate")
    documented = field_value(state, "financialClarity", "financialsDocumented")
    profit = field_value(state, "financialClarity", "profitabilityClear")
    comp = field_value(state, "financialClarity", "ownerCompNormalized")
    trend = field_value(state, "financialClarity", "revenueTrend")

    if books is True:
        score += 1.0
        notes.append("your books are current")
    elif books is False:
        score -= 0.5
        gaps.append("books aren't up to date")
    if documented is True:
        score += 1.0
        notes.append("you have documented financial statements")
    elif documented is False:
        gaps.append("financial statements aren't documented")
    if profit is True:
        score += 0.5
        notes.append("profitability is clear")
    elif profit is False:
        gaps.append("profitability isn't clearly established")
    if comp is True:
        score += 0.5
        notes.append("owner pay is cleanly separated")
    elif comp is False:
        gaps.append("personal and business spending are still mixed")
    if trend == "growing":
        score += 0.5
        notes.append("revenue is growing")
    elif trend == "declining":
        score -= 0.5
        gaps.append("revenue has been declining")

    rationale = _compose_rationale("Financial clarity", notes, gaps, state,
                                   ("financialClarity", "booksUpToDate"))
    return _clamp(score), rationale, gaps


def _operational(state: dict[str, Any]) -> tuple[float, str, list[str]]:
    score = 3.0
    notes: list[str] = []
    gaps: list[str] = []
    key_risk = field_value(state, "operationalTransferability", "keyPersonRisk")
    mgmt = field_value(state, "operationalTransferability", "managementDepth")
    systems = field_value(state, "operationalTransferability", "systemsDocumented")
    functions = field_value(state, "operationalTransferability", "functionsDependentOnOwner") or []

    if key_risk == "low":
        score += 1.5
        notes.append("the team could carry on without you")
    elif key_risk == "high":
        score -= 1.5
        gaps.append("a lot still depends on you personally")
    if mgmt == "solid":
        score += 1.0
        notes.append("you have a capable management bench")
    elif mgmt == "thin":
        score -= 0.5
        gaps.append("your management bench is thin")
    elif mgmt == "none":
        score -= 1.5
        gaps.append("there's little management depth below you")
    if systems is True:
        score += 0.5
        notes.append("core systems are documented")
    elif systems is False:
        gaps.append("core systems aren't documented")
    if len(functions) >= 4:
        score -= 1.0
        gaps.append(f"{len(functions)} core functions run through you")
    elif functions:
        notes.append(f"you named {len(functions)} function(s) that lean on you")

    rationale = _compose_rationale("Operational transferability", notes, gaps, state,
                                   ("operationalTransferability", "keyPersonRisk"))
    return _clamp(score), rationale, gaps


def _process(state: dict[str, Any]) -> tuple[float, str, list[str]]:
    score = 2.5
    notes: list[str] = []
    gaps: list[str] = []
    sops = field_value(state, "processDocumentation", "sopsExist")
    tribal = field_value(state, "processDocumentation", "tribalKnowledgeRisk")
    areas = field_value(state, "processDocumentation", "documentedAreas") or []

    if sops is True:
        score += 1.0
        notes.append("written procedures exist")
    elif sops is False:
        score -= 1.0
        gaps.append("there are no written procedures yet")
    if tribal == "low":
        score += 1.0
        notes.append("little of the business lives only in people's heads")
    elif tribal == "high":
        score -= 1.0
        gaps.append("a lot of the business runs on undocumented knowledge")
    if len(areas) >= 3:
        score += 0.5
        notes.append(f"{len(areas)} areas are documented")
    elif not areas:
        gaps.append("no specific areas are documented yet")

    rationale = _compose_rationale("Process documentation", notes, gaps, state,
                                   ("processDocumentation", "sopsExist"))
    return _clamp(score), rationale, gaps


def _family(state: dict[str, Any]) -> tuple[float, str, list[str]]:
    score = 3.0
    notes: list[str] = []
    gaps: list[str] = []
    align = field_value(state, "familyAlignment", "alignmentLevel")
    expectations = field_value(state, "familyAlignment", "expectationsKnown")
    conflict = field_value(state, "familyAlignment", "conflictRisk")

    if align == "aligned":
        score += 1.5
        notes.append("your family is aligned on the future")
    elif align == "partial":
        score += 0.25
        notes.append("your family is partly aligned")
    elif align == "misaligned":
        score -= 1.5
        gaps.append("your family isn't aligned yet")
    if expectations is True:
        score += 0.5
        notes.append("you know what your family expects")
    elif expectations is False:
        gaps.append("family expectations aren't clear")
    if conflict == "low":
        score += 0.5
    elif conflict == "high":
        score -= 1.0
        gaps.append("there's real risk of family conflict")

    rationale = _compose_rationale("Family alignment", notes, gaps, state,
                                   ("familyAlignment", "alignmentLevel"))
    return _clamp(score), rationale, gaps


def _emotional(state: dict[str, Any]) -> tuple[float, str, list[str]]:
    score = 2.5
    notes: list[str] = []
    gaps: list[str] = []
    let_go = field_value(state, "emotionalReadiness", "readinessToLetGo")
    identity = field_value(state, "owner", "identityTiedToBusiness")
    motivation = field_value(state, "emotionalReadiness", "primaryMotivation")
    concerns = field_value(state, "emotionalReadiness", "topConcerns")

    if isinstance(let_go, (int, float)):
        score += (let_go - 3) * 0.6
        if let_go >= 4:
            notes.append("you feel close to ready to step back")
        elif let_go <= 2:
            gaps.append("stepping back still feels hard")
    if isinstance(identity, (int, float)) and identity >= 4:
        score -= 0.5
        gaps.append("much of your identity is tied to the business")
    if motivation:
        score += 0.5
        notes.append("you've named what's driving this")
    else:
        gaps.append("the motivation behind a transition isn't named yet")
    if concerns:
        score += 0.25
        notes.append("you've named your main concerns")

    rationale = _compose_rationale("Owner emotional readiness", notes, gaps, state,
                                   ("emotionalReadiness", "readinessToLetGo"))
    return _clamp(score), rationale, gaps


def _compose_rationale(
    label: str,
    notes: list[str],
    gaps: list[str],
    state: dict[str, Any],
    primary: tuple[str, str],
) -> str:
    """Grounded, hedged 1–2 sentence 'why' for a driver. No fabrication."""

    status = field_status(state, *primary)
    if status in {"unknown", "skipped"} and not notes and not gaps:
        return (
            f"{label} hasn't been established yet — you haven't answered these "
            f"questions. That's a normal gap to come back to, not a problem."
        )
    parts: list[str] = []
    if notes:
        parts.append("This scored higher because " + _join(notes) + ".")
    if gaps:
        parts.append(
            ("It's held back because " if notes else "This is an early area because ")
            + _join(gaps) + "."
        )
    if not parts:
        parts.append(f"{label} is at a middle baseline; more detail would sharpen it.")
    return " ".join(parts)


def _join(items: list[str]) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _next_step_for(gap: str) -> str:
    mapping = {
        "books aren't up to date": "Ask your bookkeeper or CPA to bring the books current.",
        "financial statements aren't documented": "Have current P&L and balance sheet prepared — ranges are fine to start.",
        "profitability isn't clearly established": "Clarify a normalized profit picture with your accountant.",
        "personal and business spending are still mixed": "Separate owner pay and personal expenses from the business.",
        "revenue has been declining": "Prepare a short, honest explanation of the trend before any buyer asks.",
        "a lot still depends on you personally": "Pick one function to start delegating or documenting this quarter.",
        "your management bench is thin": "Identify one person to develop into a second-in-command.",
        "there's little management depth below you": "Name who could run things for a month, and start preparing them.",
        "core systems aren't documented": "Write down the one process only you know how to run.",
        "there are no written procedures yet": "Start with a simple SOP for your most critical task.",
        "a lot of the business runs on undocumented knowledge": "Capture the customer-handoff steps that live in your head.",
        "no specific areas are documented yet": "Document one area — operations or customer handoff is a good start.",
        "your family isn't aligned yet": "Have a low-stakes first conversation about what matters, not timing.",
        "family expectations aren't clear": "Ask family members what they each expect — separately, without pressure.",
        "there's real risk of family conflict": "Consider a neutral facilitator before decisions, not after.",
        "stepping back still feels hard": "You don't need to be ready to sell — just to prepare. Move at your pace.",
        "much of your identity is tied to the business": "Picture what a good next chapter looks like for you, beyond the business.",
        "the motivation behind a transition isn't named yet": "Write one sentence on why you're thinking about this now.",
    }
    return mapping.get(gap, "Revisit this when you're ready — it's a normal gap, not a problem.")


def score_intake(state: dict[str, Any]) -> dict[str, Any]:
    """Compute readiness from an IntakeState. Returns derived-shaped output."""

    financial, fin_r, fin_g = _financial(state)
    operational, op_r, op_g = _operational(state)
    process, proc_r, proc_g = _process(state)
    family, fam_r, fam_g = _family(state)
    emotional, emo_r, emo_g = _emotional(state)

    driver_scores = {
        "financial_clarity": round(financial, 1),
        "operational_transferability": round(operational, 1),
        "process_documentation": round(process, 1),
        "family_alignment": round(family, 1),
        "owner_emotional_readiness": round(emotional, 1),
    }
    overall = _unified_readiness_score(driver_scores)

    score_rationale = {
        "financial_clarity": fin_r,
        "operational_transferability": op_r,
        "process_documentation": proc_r,
        "family_alignment": fam_r,
        "owner_emotional_readiness": emo_r,
    }

    gaps = flagged_gaps(state)
    # Top 3 gaps + single most useful next step each (grounded).
    driver_gaps = fin_g + op_g + proc_g + fam_g + emo_g
    top_gaps = []
    for gap in driver_gaps:
        if gap not in [g["gap"] for g in top_gaps]:
            top_gaps.append({"gap": gap, "nextStep": _next_step_for(gap)})
        if len(top_gaps) >= 3:
            break

    return {
        "overall": overall,
        "dimensions": driver_scores,           # keys match the existing report UI
        "driverScores": driver_scores,
        "scoreRationale": score_rationale,     # REQUIRED explainability
        "flaggedGaps": gaps,
        "topGaps": top_gaps,
        "interpretation": _interpretation(overall),
        "completionPct": state.get("meta", {}).get("completionPct", 0),
    }


def _interpretation(score: int) -> str:
    if score >= 75:
        return "Your transfer story is becoming credible; focus on buyer fit and advisor review."
    if score >= 50:
        return "Promising but not yet steward-ready; reduce founder dependency and clarify alignment."
    return "Early readiness; start with documentation, emotional goals, and advisor conversations."
