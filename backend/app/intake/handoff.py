"""Human-touchpoint handoff package generator.

When an owner books the human readiness review, this produces the single
fully-prepped package the human receives, per the brief's Handoff Spec, so the
human's prep time stays small and fixed while perceived attention stays high.

Pure Python; grounded entirely in the owner's stored data. It respects
disclosure settings by reporting them, and never fabricates.
"""

from __future__ import annotations

from typing import Any

from app.intake.branching import routing, tone_flags
from app.services.scoring import DRIVER_LABELS, score_intake
from app.services.synthesis import successor_fit_brief
from app.storage.intake_state import field_value


def _list(state: dict[str, Any], section: str, field: str) -> list[str]:
    value = field_value(state, section, field)
    return value if isinstance(value, list) else ([value] if value else [])


def build_handoff(state: dict[str, Any]) -> dict[str, Any]:
    scored = score_intake(state)
    overall = scored["overall"]

    drivers = [
        {
            "key": key,
            "label": DRIVER_LABELS[key],
            "score": scored["dimensions"][key],
            "rationale": scored["scoreRationale"][key],
        }
        for key in scored["dimensions"]
    ]

    concerns = _list(state, "emotionalReadiness", "topConcerns")
    urgency = _list(state, "emotionalReadiness", "urgencyDrivers")
    motivation = field_value(state, "emotionalReadiness", "primaryMotivation")
    non_neg = _list(state, "nonNegotiables", "nonNegotiables")

    talking_points = _talking_points(state, scored)

    return {
        "generatedFor": "human_readiness_review",
        # 1. score + per-driver scores and rationale
        "readiness": {"overall": overall, "interpretation": scored["interpretation"], "drivers": drivers},
        # 2. top 3 gaps + non-negotiables
        "topGaps": scored["topGaps"],
        "nonNegotiables": non_neg,
        # 3. concerns + emotional drivers — lead with empathy
        "ownerContext": {
            "primaryMotivation": motivation,
            "topConcerns": concerns,
            "urgencyDrivers": urgency,
            "toneGuidance": _tone_guidance(state),
        },
        # 4. disclosure settings (what the owner has / hasn't agreed to share)
        "disclosure": _disclosure_summary(state),
        # 5. suggested talking points + 2-3 highest-impact next steps
        "talkingPoints": talking_points,
        "highestImpactNextSteps": [g["nextStep"] for g in scored["topGaps"][:3]],
        "successorFitBrief": successor_fit_brief(state),
        "routing": routing(state, overall),
        "completionPct": scored["completionPct"],
        "disclaimer": "Preparation context only. Not legal, tax, valuation, or investment advice. Grounded solely in the owner's inputs.",
    }


def _tone_guidance(state: dict[str, Any]) -> str:
    flags = tone_flags(state)
    if flags.get("extraCare"):
        return "Lead with care — the owner cited health/urgency. Listen first; do not push timing."
    if flags.get("soften"):
        return "The owner isn't ready to let go. Reassure that preparation is not the same as selling."
    return "Warm and unhurried. Reflect back their priorities before discussing mechanics."


def _disclosure_summary(state: dict[str, Any]) -> dict[str, Any]:
    controls = state.get("disclosureControls", {}) or {}
    return {
        "defaultVisibility": controls.get("defaultVisibility", "private"),
        "sectionOverrides": controls.get("sectionOverrides", {}),
        "fieldOverrides": controls.get("fieldOverrides", {}),
        "note": "Only data the owner has explicitly marked shareable may be discussed beyond this review.",
    }


def _talking_points(state: dict[str, Any], scored: dict[str, Any]) -> list[str]:
    points: list[str] = []
    non_neg = _list(state, "nonNegotiables", "nonNegotiables")
    if non_neg:
        points.append(f"Open by acknowledging what must be protected: {', '.join(non_neg)}.")
    if scored["topGaps"]:
        points.append(f"Focus the review on the biggest gap first: {scored['topGaps'][0]['gap']}.")
    if field_value(state, "operationalTransferability", "keyPersonRisk") == "high":
        points.append("Discuss reducing owner-dependency as the highest-leverage preparation.")
    concerns = _list(state, "emotionalReadiness", "topConcerns")
    if concerns:
        points.append(f"Address the owner's stated worry: {concerns[0]}.")
    points.append("Reaffirm this is preparation, and route any legal/tax/valuation questions to qualified advisors.")
    return points
