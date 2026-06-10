"""Action plan: turn the readiness gaps into prioritized, completable steps.

This closes the loop the score alone cannot: a diagnosis becomes progress. Each
action points at one intake field, carries plain-language guidance, and is
"done" once that field reaches a good state. Completing an action updates the
field, so the deterministic readiness score genuinely moves. No fabrication, no
LLM. Steps are grounded in the owner's own answers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from app.services.scoring import DRIVER_LABELS, score_intake
from app.storage.intake_state import field_status, field_value, merge_intake_patch


@dataclass(frozen=True)
class ActionRule:
    id: str
    driver: str
    section: str
    field: str
    title: str       # imperative, owner-facing
    why: str         # why it matters, owner-facing
    guidance: str    # the concrete next step
    good: Callable[[Any], bool]
    # A value that marks the step done in one click. None means the step needs
    # the owner's own words, so we route them to the question instead.
    good_value: Any = None


def _is_true(v: Any) -> bool:
    return v is True


# Order within a driver is the order shown. Each rule mirrors a positive in the
# scoring engine, so completing it provably raises the score.
RULES: list[ActionRule] = [
    ActionRule("books-current", "financial_clarity", "financialClarity", "booksUpToDate",
               "Bring your books current",
               "Out-of-date books slow every buyer and advisor conversation.",
               "Ask your bookkeeper or CPA to bring the books current.",
               _is_true, good_value=True),
    ActionRule("financials-documented", "financial_clarity", "financialClarity", "financialsDocumented",
               "Document your financial statements",
               "Documented statements let a buyer trust the numbers.",
               "Have a current P&L and balance sheet prepared. Ranges are fine to start.",
               _is_true, good_value=True),
    ActionRule("profitability-clear", "financial_clarity", "financialClarity", "profitabilityClear",
               "Make your profitability clear",
               "A clear profit picture is the first thing a buyer checks.",
               "Clarify a normalized profit picture with your accountant.",
               _is_true, good_value=True),
    ActionRule("owner-comp-normalized", "financial_clarity", "financialClarity", "ownerCompNormalized",
               "Separate owner pay from the business",
               "Mixed personal and business spending hides the real numbers.",
               "Separate owner pay and personal expenses from the business.",
               _is_true, good_value=True),
    ActionRule("reduce-owner-dependency", "operational_transferability", "operationalTransferability", "keyPersonRisk",
               "Reduce how much depends on you",
               "If the business needs you daily, a buyer sees risk, not value.",
               "Pick one function to start delegating or documenting this quarter.",
               lambda v: v == "low", good_value="low"),
    ActionRule("build-management", "operational_transferability", "operationalTransferability", "managementDepth",
               "Build your management bench",
               "A capable second-in-command makes the business transferable.",
               "Identify one person to develop into a second-in-command.",
               lambda v: v == "solid", good_value="solid"),
    ActionRule("document-systems", "operational_transferability", "operationalTransferability", "systemsDocumented",
               "Document your core systems",
               "Documented systems survive the handoff.",
               "Write down the one process only you know how to run.",
               _is_true, good_value=True),
    ActionRule("write-sops", "process_documentation", "processDocumentation", "sopsExist",
               "Write down your key procedures",
               "Written procedures turn your knowledge into something you can hand over.",
               "Start with a simple SOP for your most critical task.",
               _is_true, good_value=True),
    ActionRule("capture-tribal", "process_documentation", "processDocumentation", "tribalKnowledgeRisk",
               "Capture knowledge that lives in people's heads",
               "Undocumented know-how walks out the door at a transition.",
               "Capture the customer-handoff steps that live in your head.",
               lambda v: v == "low", good_value="low"),
    ActionRule("align-family", "family_alignment", "familyAlignment", "alignmentLevel",
               "Get your family aligned",
               "A family that agrees on the future avoids a painful stall later.",
               "Have a low-stakes first conversation about what matters, not timing.",
               lambda v: v == "aligned", good_value="aligned"),
    ActionRule("know-expectations", "family_alignment", "familyAlignment", "expectationsKnown",
               "Learn what your family expects",
               "Clear expectations prevent surprises during the handoff.",
               "Ask family members what they each expect, separately, without pressure.",
               _is_true, good_value=True),
    ActionRule("picture-next-chapter", "owner_emotional_readiness", "emotionalReadiness", "readinessToLetGo",
               "Picture your next chapter",
               "Readiness to step back is what turns preparation into action.",
               "Picture what a good next chapter looks like for you, beyond the business.",
               lambda v: isinstance(v, (int, float)) and v >= 4, good_value=4),
    ActionRule("name-motivation", "owner_emotional_readiness", "emotionalReadiness", "primaryMotivation",
               "Name why you're doing this now",
               "Naming your motivation steadies every decision that follows.",
               "Write one sentence on why you're thinking about this now.",
               lambda v: bool(v), good_value=None),
]

_RULES_BY_ID = {r.id: r for r in RULES}


def build_action_plan(state: dict[str, Any]) -> dict[str, Any]:
    """Build the prioritized plan from the current state. Weakest driver first."""

    scored = score_intake(state)
    driver_scores = scored["driverScores"]

    actions = []
    for rule in RULES:
        value = field_value(state, rule.section, rule.field)
        done = bool(rule.good(value))
        actions.append({
            "id": rule.id,
            "driver": rule.driver,
            "driverLabel": DRIVER_LABELS.get(rule.driver, rule.driver),
            "title": rule.title,
            "why": rule.why,
            "guidance": rule.guidance,
            "section": rule.section,
            "field": rule.field,
            "status": "done" if done else "open",
            "answered": field_status(state, rule.section, rule.field) == "answered",
            # A one-click "I've done this" only where a fixed good value applies.
            "quickComplete": rule.good_value is not None,
            "_driverScore": driver_scores.get(rule.driver, 5),
        })

    # Open steps first, weakest driver first; finished steps drop to the bottom.
    order = {r.id: i for i, r in enumerate(RULES)}
    actions.sort(key=lambda a: (a["status"] == "done", a["_driverScore"], order[a["id"]]))
    for a in actions:
        a.pop("_driverScore", None)

    done = sum(1 for a in actions if a["status"] == "done")
    total = len(actions)
    return {
        "actions": actions,
        "summary": {
            "open": total - done,
            "done": done,
            "total": total,
            "completedPct": round(done / total * 100) if total else 0,
            "readiness": scored["overall"],
        },
    }


def complete_action(state: dict[str, Any], action_id: str) -> dict[str, Any] | None:
    """Mark a one-click action done by setting its field to the good value.

    Returns the updated state, or None when the action needs the owner's own
    answer (the caller should route them to the question instead).
    """

    rule = _RULES_BY_ID.get(action_id)
    if rule is None or rule.good_value is None:
        return None
    patch = {rule.section: {rule.field: {"value": rule.good_value, "status": "answered"}}}
    return merge_intake_patch(state, patch)
