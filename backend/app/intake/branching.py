"""Deterministic Branching Ruleset — the 80/20 of the "listening" feeling.

Given an ``IntakeState``, this builds the adaptive intake plan the frontend
renders: which sections/questions are visible, where confidentiality
reassurance must appear, where a reflective-summary moment is due, derived hints
(e.g. tribal-knowledge risk), flagged gaps, tone adjustments, and end-of-flow
routing toward the human touchpoint or a warm advisor handoff.

Rules reference ``IntakeState`` fields. ``unknown``/``skipped`` are signals,
never blockers. No LLM is used here; this is pure, predictable logic.
"""

from __future__ import annotations

from typing import Any

from app.intake import questions as qbank
from app.storage.intake_state import (
    SECTION_ORDER,
    field_status,
    field_value,
    is_field,
    open_gaps,
)


# readiness (0-100) at/under which we proactively offer the human touchpoint.
HUMAN_TOUCHPOINT_THRESHOLD = 55
# readiness at/over which the owner is "prepared enough" to warm-hand-off.
WARM_HANDOFF_THRESHOLD = 75


def _section_complete(state: dict[str, Any], section_key: str) -> bool:
    """A section is 'addressed' when every visible field has a decision
    (answered/estimated/skipped). ``unknown`` leaves it open."""

    for question in _visible_questions(state, section_key):
        status = _status_for(state, question)
        if status not in {"answered", "estimated", "skipped", "pending_document"}:
            return False
    return True


def _status_for(state: dict[str, Any], question: dict[str, Any]) -> str:
    return field_status(state, question["section"], question["field"])


def _value_for(state: dict[str, Any], question: dict[str, Any]) -> Any:
    return field_value(state, question["section"], question["field"])


def _visible_questions(state: dict[str, Any], section_key: str) -> list[dict[str, Any]]:
    """Apply collapse/expand rules to a section's question list."""

    base = qbank.section_questions(section_key)
    if section_key == "familyAlignment":
        family_in_biz = field_value(state, "familyAlignment", "familyInBusiness")
        category = field_value(state, "business", "category")
        family_relevant = bool(family_in_biz) or category == "family"
        if family_in_biz is False and not family_relevant:
            # Collapse family-successor drill-down, but ALWAYS keep
            # expectationsKnown — family may hold expectations regardless.
            return [q for q in base if q["field"] in {"familyInBusiness", "expectationsKnown"}]
    return base


def _clarifiers(state: dict[str, Any]) -> list[dict[str, str]]:
    """Deterministic, bounded follow-up nudges (the long tail handled by rules).

    These are surfaced as gentle prompts, not new schema fields.
    """

    out: list[dict[str, str]] = []

    if field_value(state, "successorPreferences", "acceptablePaths") and \
            "employee_ownership" in (field_value(state, "successorPreferences", "acceptablePaths") or []):
        out.append({
            "id": "clar_employee_finance",
            "prompt": "Could your employees realistically finance a purchase, or would that need outside help?",
        })

    if field_value(state, "operationalTransferability", "managementDepth") == "none":
        out.append({
            "id": "clar_who_runs",
            "prompt": "If you were out for a month, who would actually run the business day to day?",
        })

    functions = field_value(state, "operationalTransferability", "functionsDependentOnOwner") or []
    if "sales" in functions or "key relationships" in functions:
        out.append({
            "id": "clar_relationship_transfer",
            "prompt": "Could those relationships transfer to someone else over time, or do they really only work with you?",
        })

    if field_status(state, "financialClarity", "booksUpToDate") == "answered" and \
            field_value(state, "financialClarity", "booksUpToDate") is False:
        out.append({
            "id": "clar_bookkeeper",
            "prompt": "Is a bookkeeper or CPA involved today? (No exact numbers needed.)",
        })
    if field_value(state, "financialClarity", "financialsDocumented") is False:
        out.append({
            "id": "clar_financials_help",
            "prompt": "Would a little help getting statements in order feel useful before any buyer conversation?",
        })

    if field_value(state, "familyAlignment", "familyInBusiness") and \
            field_value(state, "business", "category") == "family":
        out.append({
            "id": "clar_family_successor",
            "prompt": "Is a family member a realistic successor candidate, or more of an owner than an operator?",
        })

    return out


def derived_hints(state: dict[str, Any]) -> dict[str, Any]:
    """Non-destructive hints the scoring/roadmap layers can lean on.

    These do not mutate owner answers; they record inferences the rules make.
    """

    hints: dict[str, Any] = {}

    if field_value(state, "processDocumentation", "sopsExist") is False:
        hints["tribalKnowledgeRisk"] = "high"
        hints["surfaceFunctionsDependentOnOwner"] = True

    if field_value(state, "operationalTransferability", "managementDepth") == "none":
        hints["keyPersonRisk"] = "high"

    revenue = field_value(state, "business", "revenueBand")
    if revenue in {"5m-20m", "20m+"} and \
            field_value(state, "financialClarity", "financialsDocumented") is False:
        hints["financialDocsHighPriority"] = True

    return hints


def tone_flags(state: dict[str, Any]) -> dict[str, Any]:
    """Emotional-pacing adjustments for the reflection/UX layer."""

    flags: dict[str, Any] = {"soften": False, "noTimingPressure": False, "extraCare": False}

    let_go = field_value(state, "emotionalReadiness", "readinessToLetGo")
    if isinstance(let_go, (int, float)) and let_go <= 2:
        flags["soften"] = True
        flags["noTimingPressure"] = True
        flags["message"] = "You don't need to be ready to sell. There's no rush here."

    urgency = field_value(state, "emotionalReadiness", "urgencyDrivers") or []
    if "health" in urgency:
        flags["extraCare"] = True
        flags["surfaceHumanEarly"] = True

    return flags


def flagged_gaps(state: dict[str, Any]) -> list[str]:
    """Human-readable readiness gaps from unanswered fields + known weak spots."""

    labels = {
        "financialClarity.booksUpToDate": "Books are not yet up to date",
        "financialClarity.financialsDocumented": "Financial statements aren't documented",
        "financialClarity.profitabilityClear": "Profitability isn't clearly established",
        "processDocumentation.sopsExist": "Core procedures aren't written down",
        "operationalTransferability.managementDepth": "Management bench is thin or untested",
        "operationalTransferability.functionsDependentOnOwner": "Key functions still depend on you",
        "familyAlignment.alignmentLevel": "Family alignment is unclear",
        "successorPreferences.acceptablePaths": "Acceptable successor paths aren't decided",
        "emotionalReadiness.readinessToLetGo": "Readiness to step back isn't established",
    }
    gaps: list[str] = []

    # Explicit weak answers are gaps even when "answered".
    if field_value(state, "processDocumentation", "sopsExist") is False:
        gaps.append("Core procedures aren't written down")
    if field_value(state, "operationalTransferability", "managementDepth") == "none":
        gaps.append("Management bench is thin or untested")
    if field_value(state, "operationalTransferability", "keyPersonRisk") == "high":
        gaps.append("The business carries high key-person risk on you")
    if field_value(state, "financialClarity", "booksUpToDate") is False:
        gaps.append("Books are not yet up to date")

    # Open (unanswered) fields that matter become gaps too.
    for path in open_gaps(state):
        if path in labels and labels[path] not in gaps:
            gaps.append(labels[path])

    # De-dupe, keep order.
    seen: set[str] = set()
    ordered = []
    for gap in gaps:
        if gap not in seen:
            seen.add(gap)
            ordered.append(gap)
    return ordered


def routing(state: dict[str, Any], readiness_score: int | None) -> dict[str, Any]:
    """End-of-flow routing toward the human touchpoint or a warm handoff."""

    urgency = field_value(state, "emotionalReadiness", "urgencyDrivers") or []
    has_urgency = bool([u for u in urgency if u and u != "none"])
    score = readiness_score if isinstance(readiness_score, int) else None

    if tone_flags(state).get("surfaceHumanEarly"):
        return {
            "mode": "human_touchpoint",
            "reason": "health_urgency",
            "headline": "You don't have to do this alone.",
            "body": "Given what you've shared, it may help to talk with a person sooner rather than later. We can set up a private readiness review.",
            "cta": "Book a private readiness review",
        }
    if score is not None and score < HUMAN_TOUCHPOINT_THRESHOLD and has_urgency:
        return {
            "mode": "human_touchpoint",
            "reason": "low_readiness_with_urgency",
            "headline": "A guided review would help here.",
            "body": "There's meaningful preparation ahead and some time pressure. A private readiness review can turn this into a clear, paced plan.",
            "cta": "Book a private readiness review",
        }
    if score is not None and score >= WARM_HANDOFF_THRESHOLD:
        return {
            "mode": "warm_handoff",
            "reason": "prepared",
            "headline": "You're prepared enough to bring in an advisor.",
            "body": "Your readiness is strong. When you're ready, we can connect you with a vetted advisor — only with your explicit permission, and only what you choose to share.",
            "cta": "See advisor options",
        }
    return {
        "mode": "self_serve",
        "reason": "in_progress",
        "headline": "Keep going at your pace.",
        "body": "You can save and come back anytime. When you'd like a person in the loop, a private readiness review is one click away.",
        "cta": "Continue, or book a review when ready",
    }


def build_intake_plan(state: dict[str, Any], readiness_score: int | None = None) -> dict[str, Any]:
    """The adaptive plan the frontend renders, derived purely from state."""

    sections_out: list[dict[str, Any]] = []
    next_section_key: str | None = None
    next_question_id: str | None = None

    for key in SECTION_ORDER:
        section_meta = qbank.SECTION_BY_KEY[key]
        visible = _visible_questions(state, key)
        questions_out = []
        for q in visible:
            status = _status_for(state, q)
            questions_out.append({
                **q,
                "value": _value_for(state, q),
                "status": status,
            })
            if status == "unknown" and next_question_id is None:
                next_question_id = q["id"]
                next_section_key = key

        complete = _section_complete(state, key)
        sections_out.append({
            "key": key,
            "title": section_meta["title"],
            "intro": section_meta["intro"],
            "securityGate": key in qbank.SECURITY_GATED_SECTIONS,
            "reassurance": qbank.SECTION_REASSURANCE.get(key, ""),
            # A reflective-summary moment is due after each section and before
            # emotionally heavy ones (family, emotional readiness).
            "reflectAfter": True,
            "emotionallyHeavy": key in {"familyAlignment", "emotionalReadiness"},
            "complete": complete,
            "questions": questions_out,
        })

    done = next_question_id is None

    return {
        "schemaVersion": state.get("meta", {}).get("schemaVersion"),
        "completionPct": state.get("meta", {}).get("completionPct", 0),
        "lastSection": state.get("meta", {}).get("lastSection"),
        "sections": sections_out,
        "nextSectionKey": next_section_key,
        "nextQuestionId": next_question_id,
        "done": done,
        "clarifiers": _clarifiers(state),
        "hints": derived_hints(state),
        "toneFlags": tone_flags(state),
        "flaggedGaps": flagged_gaps(state),
        "routing": routing(state, readiness_score),
        "securityGatedSections": sorted(qbank.SECURITY_GATED_SECTIONS),
    }
