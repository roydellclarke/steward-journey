"""Local reasoning engine for the StewardPath MVP.

This is deliberately deterministic so the MVP can run without cloud LLM keys.
The later LLM-backed layer should preserve this JSON shape and improve the
interviewing/narrative quality.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import exp
from typing import Any


@dataclass(frozen=True)
class OwnerProfile:
    business_name: str
    industry: str
    years_operating: int
    employees: int
    revenue_range: str
    profit_margin: str
    owner_dependency: str
    timeline: str
    owner_goal: str
    fears: str
    non_negotiables: str
    family_context: str
    next_owner_traits: str


def analyze_owner_profile(profile: OwnerProfile) -> dict[str, Any]:
    readiness = readiness_score(profile)
    return {
        "profile": asdict(profile),
        "positioning": {
            "product_name": "StewardPath",
            "promise": "Before you sell, decide what must be protected.",
            "primary_job": "Move from quiet worry about what could be lost to a clear transfer plan you can explain.",
        },
        "jtbd": jtbd_map(profile),
        "growth_discovery": growth_discovery(profile),
        "buffett_quality": buffett_quality(profile),
        "readiness": readiness,
        "buyer_paths": buyer_paths(profile),
        "roadmap": roadmap(profile, readiness),
        "narratives": narratives(profile),
        "disclaimers": [
            "Educational decision support only.",
            "Not legal, tax, investment, or valuation advice.",
            "Not a formal valuation.",
            "Consult qualified advisors before making transfer decisions.",
        ],
    }


def jtbd_map(profile: OwnerProfile) -> dict[str, Any]:
    fear_text = profile.fears or "You may worry that employees, family, or longtime customers could be let down."
    return {
        "struggling_moment": f"You may be ready to step back from {profile.business_name or 'the business'}, but you do not want buyers, brokers, or timing pressure to decide what your life's work becomes.",
        "first_thought": _first_thought(profile),
        "push_forces": [
            f"Your timeline is {profile.timeline or 'getting harder to ignore'}.",
            "You may not want to remain the emergency backup for every hard decision.",
            "Your family, advisors, or employees may need clarity before uncertainty becomes risk.",
        ],
        "pull_forces": [
            "You can protect jobs, customer trust, and the company name before a buyer changes the story.",
            "You can make the business easier for a good successor to preserve.",
            "You can step back without feeling like you abandoned the people who helped you build it.",
        ],
        "anxiety_forces": [
            fear_text,
            "You may worry the wrong buyer will strip the business, change the culture, or disappoint employees.",
            "You may worry people will judge the transition as abandonment instead of stewardship.",
        ],
        "habit_forces": [
            "It is easy to keep personally rescuing problems because that has always worked.",
            "It is easier to postpone the conversation than risk hearing the wrong answer.",
            "Advisor conversations can feel scattered until you have one clear story.",
        ],
        "functional_jobs": [
            "See what must be fixed before you talk seriously with buyers.",
            "Compare transfer paths without being pushed toward one answer too soon.",
            "Prepare clear materials for your advisors, family, and eventual successor.",
            "Reduce the places where the business still depends too much on you.",
        ],
        "emotional_jobs": [
            "Feel that decades of work will not be casually undone.",
            "Replace dread with a plan you can explain.",
            "Make your next chapter feel like continuity, not disappearance.",
        ],
        "social_jobs": [
            "Show employees you are trying to protect them, not surprise them.",
            "Give your family a clearer picture of what matters beyond price.",
            "Protect your reputation in the community after you step back.",
        ],
        "hiring_criteria": [
            "Feels private and advisor-grade.",
            "Speaks the owner's language, not broker jargon.",
            "Produces useful artifacts quickly.",
        ],
        "firing_criteria": [
            "Feels like a lead-gen funnel.",
            "Pushes a sale before understanding legacy concerns.",
            "Pretends to provide valuation/legal/tax advice.",
        ],
    }


def growth_discovery(profile: OwnerProfile) -> dict[str, Any]:
    return {
        "north_star_metric": "You have a written plan for what must be protected.",
        "activation_event": "You complete the intake, review your readiness report, and save at least one non-negotiable successor criterion.",
        "journey": {
            "struggle": [
                "You feel fatigue, health pressure, family pressure, or uncertainty after something exposes how much the business still relies on you.",
                "You start thinking: this business may need to outlive your daily involvement.",
            ],
            "search": [
                "You ask a CPA, attorney, broker, spouse, peer owner, or Google what to do next.",
                "You compare broker, advisor, family transfer, employee sale, outside buyer, and doing nothing.",
            ],
            "selection": [
                "You need proof this is private, non-pushy, and respectful.",
                "You need to feel: this understands what could be lost, not just what the company might sell for.",
            ],
        },
        "locksmith_moments": [
            "A key employee leaves or hints they may leave.",
            "Your children make it clear they do not want to run the business.",
            "A buyer approaches before you are prepared.",
            "Your CPA or attorney asks what happens if you cannot work for 90 days.",
            "A peer owner sells and regrets what happened to the company.",
        ],
        "key_drivers": [
            "You can name what must be protected.",
            "You know where the business depends too much on you.",
            "You have a report you can share with advisors.",
            "You have at least one realistic successor path.",
            "You return to update the plan instead of avoiding it.",
        ],
        "rate_limiting_step_hypothesis": "The hardest part may not be finding a buyer. It may be admitting what could be lost if you wait too long.",
        "growth_levers": [
            {
                "idea": "Readiness check before a sale conversation",
                "key_driver": "You can name what must be protected.",
                "impact": 5,
                "effort": 2,
                "risky_assumption": "You are more likely to act when the report speaks to protection, not just valuation.",
            },
            {
                "idea": "Advisor briefing memo",
                "key_driver": "You have a report you can share with advisors.",
                "impact": 4,
                "effort": 3,
                "risky_assumption": "Your advisors can help more when your concerns are organized before the meeting.",
            },
            {
                "idea": "Successor-fit comparison",
                "key_driver": "You have at least one realistic successor path.",
                "impact": 4,
                "effort": 2,
                "risky_assumption": "You will make better progress when buyer fit is visible, not just price.",
            },
        ],
        "minimum_viable_tests": [
            {
                "name": "Legacy language landing page test",
                "risk": "Owners may not prefer legacy framing.",
                "prediction": "Legacy-transfer headline beats business-sale headline on report-start rate.",
            },
            {
                "name": "Concierge readiness report",
                "risk": "Owners may not provide enough sensitive detail.",
                "prediction": "At least 5 of 10 interviewed owners say they would share the report with an advisor.",
            },
        ],
    }


def buffett_quality(profile: OwnerProfile) -> dict[str, Any]:
    dependency = _dependency_score(profile.owner_dependency)
    years_score = 5 if profile.years_operating >= 20 else 4 if profile.years_operating >= 10 else 3
    employees_score = 4 if profile.employees >= 5 else 2
    moat_score = round((years_score + employees_score + dependency) / 3, 1)
    return {
        "summary": "This is not a valuation. It shows where a careful buyer may see strength, risk, or dependency before those issues cost you leverage.",
        "scores": {
            "understandable_business": years_score,
            "founder_independence": dependency,
            "management_depth": employees_score,
            "durable_customer_value": moat_score,
            "stewardship_fit": 4,
        },
        "questions_to_answer": [
            "What would earnings look like if you stepped away for 90 days?",
            "Which customers buy because of the company, not only because of you?",
            "Where does the business have pricing power or repeat demand?",
            "What debt, reinvestment, or customer concentration risks would worry a patient buyer?",
        ],
    }


def readiness_score(profile: OwnerProfile) -> dict[str, Any]:
    founder = _dependency_score(profile.owner_dependency)
    docs = 3 if profile.non_negotiables else 2
    family = 4 if profile.family_context else 2
    emotional = 4 if profile.fears and profile.next_owner_traits else 2
    financial = 3 if profile.revenue_range and profile.profit_margin else 1
    dimensions = {
        "financial_clarity": financial,
        "operational_transferability": founder,
        "process_documentation": docs,
        "family_alignment": family,
        "owner_emotional_readiness": emotional,
    }
    total = _unified_readiness_score(dimensions)
    return {
        "overall": total,
        "dimensions": dimensions,
        "interpretation": _readiness_label(total),
    }


def _unified_readiness_score(dimensions: dict[str, int | float]) -> int:
    scores = [max(0.0, min(5.0, float(score))) for score in dimensions.values()]
    if not scores:
        return 0
    weights = [exp(5.0 - score) for score in scores]
    total_weight = sum(weights)
    weighted_score = sum(score * weight for score, weight in zip(scores, weights)) / total_weight
    return round((weighted_score / 5.0) * 100)


def buyer_paths(profile: OwnerProfile) -> list[dict[str, Any]]:
    paths = [
        ("Family transfer", 5, 3, 4, "Best when family desire and capability are real, not assumed."),
        ("Employee ownership", 5, 3, 4, "Strong continuity path if leadership bench and financing can work."),
        ("Management buyout", 4, 4, 4, "Often preserves culture when managers can operate without founder rescue."),
        ("Independent entrepreneur buyer", 4, 4, 3, "Can fit legacy goals if buyer values stewardship and local trust."),
        ("Strategic buyer", 3, 5, 2, "May pay well but can create employee and culture-change risk."),
        ("Private equity buyer", 2, 5, 2, "Can be financially attractive but needs careful fit screening."),
    ]
    return [
        {
            "path": name,
            "legacy_preservation": legacy,
            "financial_potential": proceeds,
            "emotional_fit": fit,
            "notes": notes,
        }
        for name, legacy, proceeds, fit, notes in paths
    ]


def roadmap(profile: OwnerProfile, readiness: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"phase": "1. Name the legacy job", "action": "Write the owner goal, fears, non-negotiables, and successor traits in plain language."},
        {"phase": "2. Reduce founder dependency", "action": "Document decisions, customer relationships, operating rhythms, and emergency procedures."},
        {"phase": "3. Prepare advisor evidence", "action": "Gather financial clarity, customer concentration, management bench, and process documentation."},
        {"phase": "4. Compare transfer paths", "action": "Screen family, employees, managers, local buyers, strategic buyers, and financial buyers against legacy criteria."},
        {"phase": "5. Communicate carefully", "action": "Prepare separate family, employee, advisor, and buyer narratives."},
        {"phase": "6. Decide next step", "action": f"Current readiness is {readiness['overall']}/100: focus on the lowest readiness dimension first."},
    ]


def narratives(profile: OwnerProfile) -> dict[str, str]:
    business = profile.business_name or "this business"
    steward = profile.next_owner_traits or "someone who protects employees, customers, and community trust"
    return {
        "legacy_statement": f"{business} is more than an asset. It is a promise to customers, employees, family, and the community that the work will continue with care.",
        "buyer_criteria_memo": f"The right next owner should be {steward}. Price matters, but fit, continuity, and employee trust are non-negotiable.",
        "family_conversation_guide": "Start with what must be preserved, what the owner wants life to look like next, and which decisions need professional advice.",
        "advisor_brief": f"The owner is exploring a legacy transfer on a {profile.timeline or 'thoughtful'} timeline and wants options that protect continuity as well as financial outcome.",
    }


def _dependency_score(value: str) -> int:
    normalized = value.lower()
    if "low" in normalized or "team" in normalized:
        return 5
    if "medium" in normalized or "some" in normalized:
        return 3
    if "high" in normalized or "everything" in normalized or "me" in normalized:
        return 1
    return 2


def _readiness_label(score: int) -> str:
    if score >= 75:
        return "Transfer story is becoming credible; focus on buyer fit and advisor review."
    if score >= 50:
        return "Promising but not yet steward-ready; reduce founder dependency and clarify stakeholder alignment."
    return "Early readiness; start with documentation, emotional goals, and advisor conversations."


def _first_thought(profile: OwnerProfile) -> str:
    if profile.owner_goal:
        return f"I need to figure out how to {profile.owner_goal.lower()} without damaging what I built."
    return "I cannot keep carrying this forever, but I do not know what a good transition looks like."
