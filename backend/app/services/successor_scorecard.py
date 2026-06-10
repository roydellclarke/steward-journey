"""Successor-fit scorecard: weigh real candidates against what the owner values.

This serves the promise the rest of the market ignores: the handoff goes to the
one who fits, not the one who pays the most. The owner rates each candidate (a
family member, a key employee, an outside buyer) on plain fit criteria. We rank
by fit, deterministically, and show any offer strength alongside but never as
the ranking key. A candidate the owner marks as crossing a non-negotiable is
ruled out regardless of fit. No LLM, no fabrication.
"""

from __future__ import annotations

from typing import Any


# Fixed fit criteria, in the owner's language. Offer/price is deliberately not
# one of these: it is tracked separately so it never drives the ranking.
CRITERIA = [
    {"key": "keepsPeople", "label": "Protects your employees"},
    {"key": "keepsCustomers", "label": "Keeps customers cared for"},
    {"key": "keepsName", "label": "Honors your name and reputation"},
    {"key": "readyToLead", "label": "Ready and able to lead"},
    {"key": "sharesValues", "label": "Shares your values"},
    {"key": "acceptsTerms", "label": "Willing to accept your terms"},
]
_CRITERIA_KEYS = [c["key"] for c in CRITERIA]


def _clamp_rating(value: Any) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return 3  # neutral when unrated
    return max(1, min(5, n))


def score_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Return the candidate enriched with a 0-100 fit score and ruled-out flag."""

    ratings = candidate.get("ratings") or {}
    clamped = {k: _clamp_rating(ratings.get(k)) for k in _CRITERIA_KEYS}
    mean = sum(clamped.values()) / len(_CRITERIA_KEYS)
    fit = round(mean / 5 * 100)
    ruled_out = bool(candidate.get("dealbreaker"))
    return {
        "id": candidate.get("id", ""),
        "name": candidate.get("name", "") or "Unnamed candidate",
        "kind": candidate.get("kind", "outside_buyer"),
        "ratings": clamped,
        "offerStrength": _clamp_rating(candidate.get("offerStrength")),
        "dealbreaker": ruled_out,
        "notes": candidate.get("notes", ""),
        "fitScore": fit,
        "ruledOut": ruled_out,
    }


def build_scorecard(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Rank candidates by fit (never by offer). Ruled-out candidates sink last."""

    scored = [score_candidate(c) for c in (candidates or [])]
    # Rank: kept candidates by fit (high to low), ruled-out last, name for ties.
    scored.sort(key=lambda c: (c["ruledOut"], -c["fitScore"], c["name"].lower()))
    for i, c in enumerate(scored):
        c["rank"] = i + 1

    best = next((c for c in scored if not c["ruledOut"]), None)
    return {
        "criteria": CRITERIA,
        "candidates": scored,
        "summary": {
            "count": len(scored),
            "ruledOut": sum(1 for c in scored if c["ruledOut"]),
            "topName": best["name"] if best else "",
            "topFit": best["fitScore"] if best else 0,
        },
        "note": "Ranked by fit to what you value, not by the size of the offer.",
    }
