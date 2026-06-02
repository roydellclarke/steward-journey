"""Curated question bank for StewardPath's guided, progressive-disclosure intake.

This is the constrained schema the deterministic branching layer renders today,
and the bounded set the (Phase 2) LLM clarifier layer is allowed to select or
rephrase from. Questions are NEVER free-generated outside this bank.

Each question maps to exactly one ``IntakeState`` field (``section`` + ``field``).
Plain language, no jargon. Sensitive questions carry a just-in-time reassurance
line and a "why we ask" expander. Everything is skippable; "I don't know" is a
first-class answer that records an ``unknown`` status (a readiness gap, not an
error).
"""

from __future__ import annotations

from typing import Any


# Just-in-time, plain-language reassurance shown before/at sensitive sections.
# Surfaces Security & Confidentiality Requirement #1 inside the flow.
SECTION_REASSURANCE: dict[str, str] = {
    "financialClarity": (
        "This stays private. We only ask for ranges and yes/no clarity — never "
        "exact figures — and you decide later what, if anything, to share, and "
        "with whom."
    ),
    "familyAlignment": (
        "This is sensitive, and it stays private. Nothing here is shared with "
        "family, employees, or anyone else unless you choose to."
    ),
    "emotionalReadiness": (
        "There are no wrong answers here. You do not need to be ready to sell. "
        "This just helps the plan move at your pace."
    ),
    "protectedInterests": (
        "What you want to protect matters as much as any number. This stays "
        "private and helps shape who a good next owner would be."
    ),
}

# Sections that MUST show a security/confidentiality reassurance before their
# first question (Branching Ruleset: confidentiality gating).
SECURITY_GATED_SECTIONS = {"financialClarity", "familyAlignment"}


def _q(
    qid: str,
    section: str,
    field: str,
    prompt: str,
    kind: str,
    *,
    options: list[dict[str, str]] | None = None,
    placeholder: str = "",
    why: str = "",
    sensitive: bool = False,
    allow_unknown: bool = True,
    allow_skip: bool = True,
    help_text: str = "",
) -> dict[str, Any]:
    return {
        "id": qid,
        "section": section,
        "field": field,
        "prompt": prompt,
        "kind": kind,  # text | longtext | boolean | single | multi | scale | band
        "options": options or [],
        "placeholder": placeholder,
        "why": why,
        "sensitive": sensitive,
        "allowUnknown": allow_unknown,
        "allowSkip": allow_skip,
        "helpText": help_text,
    }


def _opts(*pairs: tuple[str, str]) -> list[dict[str, str]]:
    return [{"value": value, "label": label} for value, label in pairs]


SECTIONS: list[dict[str, Any]] = [
    {
        "key": "business",
        "title": "Your business",
        "intro": "Let's start with the basics — nothing sensitive yet.",
        "questions": [
            _q("biz_category", "business", "category",
               "How would you describe your business?", "single",
               options=_opts(
                   ("founder-led business", "Founder-led business"),
                   ("family", "Family business"),
                   ("specialty manufacturing", "Specialty manufacturing"),
                   ("trade", "Trade / contractor"),
                   ("professional services", "Professional services"),
                   ("distribution", "Distribution / wholesale"),
                   ("niche B2B", "Niche B2B"),
               ),
               why="It helps us tailor the questions to how your business actually runs."),
            _q("biz_industry", "business", "industry",
               "What industry are you in?", "text",
               placeholder="e.g. specialty manufacturing"),
            _q("biz_region", "business", "region",
               "What region are you in?", "text",
               placeholder="e.g. Midwest US — region only, not your address",
               why="We only ask for region, never a street address, so nothing identifies you."),
            _q("biz_years", "business", "yearsOperating",
               "Roughly how many years has the business been operating?", "text",
               placeholder="e.g. 34"),
            _q("biz_employees", "business", "employeeBand",
               "About how many people work in the business?", "band",
               options=_opts(("1-9", "1–9"), ("10-25", "10–25"), ("26-50", "26–50"),
                             ("51-100", "51–100"), ("100+", "100+"))),
            _q("biz_revenue", "business", "revenueBand",
               "Which range best fits your annual revenue?", "band",
               options=_opts(("<250k", "Under $250k"), ("250k-1m", "$250k–$1M"),
                             ("1m-5m", "$1M–$5M"), ("5m-20m", "$5M–$20M"), ("20m+", "$20M+")),
               sensitive=True,
               why="A range is enough to gauge readiness. We never ask for exact figures."),
            _q("biz_concentration", "business", "customerConcentration",
               "How concentrated is your customer base?", "single",
               options=_opts(("diversified", "Diversified — many customers"),
                             ("moderate", "Moderate — a few important ones"),
                             ("high_few_clients", "High — a few clients are most of the business")),
               why="Customer concentration is one of the first things a careful buyer looks at."),
        ],
    },
    {
        "key": "owner",
        "title": "You and your role",
        "intro": "A little about your place in the business.",
        "questions": [
            _q("own_founder", "owner", "isFounder",
               "Did you found or build this business?", "boolean"),
            _q("own_role", "owner", "role",
               "What is your role day to day?", "text", placeholder="e.g. owner / operator"),
            _q("own_age", "owner", "ageBand",
               "Which age range are you in? (optional)", "single",
               options=_opts(("under_50", "Under 50"), ("50-59", "50–59"),
                             ("60-69", "60–69"), ("70+", "70+"), ("prefer_not", "Prefer not to say")),
               sensitive=True, allow_skip=True,
               why="This is optional. It only helps us understand timing pressure, never to identify you."),
            _q("own_identity", "owner", "identityTiedToBusiness",
               "How tied is your personal identity to the business?", "scale",
               help_text="1 = not much · 5 = it's a big part of who I am",
               why="Letting go is easier to plan for when we name how much of you is in it."),
        ],
    },
    {
        "key": "operationalTransferability",
        "title": "How much runs through you",
        "intro": "This is where many owners discover the real work of a handoff.",
        "questions": [
            _q("op_functions", "operationalTransferability", "functionsDependentOnOwner",
               "Which parts of the day-to-day depend specifically on you?", "multi",
               options=_opts(("sales", "Sales"), ("key relationships", "Key customer relationships"),
                             ("operations", "Operations / production"), ("finance", "Finance / money"),
                             ("hiring", "Hiring & people"), ("vendor relationships", "Vendor relationships"),
                             ("daily oversight", "Daily oversight / firefighting")),
               why="Where the business leans on you personally is the clearest signal of how transferable it is."),
            _q("op_keyperson", "operationalTransferability", "keyPersonRisk",
               "If you were out for a month, how at-risk would things be?", "single",
               options=_opts(("low", "Low — the team would manage"),
                             ("medium", "Medium — some things would slip"),
                             ("high", "High — a lot depends on me"))),
            _q("op_mgmt", "operationalTransferability", "managementDepth",
               "How deep is your management bench?", "single",
               options=_opts(("none", "None — it's mostly me"),
                             ("thin", "Thin — one or two key people"),
                             ("solid", "Solid — capable leaders in place"))),
            _q("op_systems", "operationalTransferability", "systemsDocumented",
               "Are your core systems and tools documented?", "boolean"),
        ],
    },
    {
        "key": "processDocumentation",
        "title": "What's written down",
        "intro": "Knowledge that lives only in your head is the hardest thing to transfer.",
        "questions": [
            _q("proc_sops", "processDocumentation", "sopsExist",
               "Are there written, step-by-step instructions for how the main work gets done?", "boolean"),
            _q("proc_areas", "processDocumentation", "documentedAreas",
               "Which areas are documented? (add any that apply)", "multi",
               options=_opts(("operations", "Operations"), ("sales", "Sales"),
                             ("finance", "Finance"), ("customer handoff", "Customer handoff"),
                             ("hr", "HR / onboarding"), ("safety", "Safety / compliance"))),
            _q("proc_tribal", "processDocumentation", "tribalKnowledgeRisk",
               "How much of the business runs on knowledge that isn't written down?", "single",
               options=_opts(("low", "Low — most is documented"),
                             ("medium", "Medium — some gaps"),
                             ("high", "High — a lot is in people's heads"))),
        ],
    },
    {
        "key": "financialClarity",
        "title": "Financial clarity",
        "intro": "Ranges and yes/no only — never exact numbers.",
        "questions": [
            _q("fin_books", "financialClarity", "booksUpToDate",
               "Are your books current and up to date?", "boolean", sensitive=True,
               why="A buyer's first question is whether the numbers can be trusted — not what they are."),
            _q("fin_documented", "financialClarity", "financialsDocumented",
               "Do you have documented financial statements (P&L, balance sheet)?", "boolean",
               sensitive=True),
            _q("fin_trend", "financialClarity", "revenueTrend",
               "Over the last few years, revenue has been…", "single",
               options=_opts(("declining", "Declining"), ("flat", "Flat"), ("growing", "Growing")),
               sensitive=True),
            _q("fin_profit", "financialClarity", "profitabilityClear",
               "Is your profitability clear and consistent?", "boolean", sensitive=True),
            _q("fin_ownercomp", "financialClarity", "ownerCompNormalized",
               "Are personal expenses and owner pay cleanly separated from the business?",
               "boolean", sensitive=True,
               why="Mixing personal and business spending is common and fixable — sorting it out early keeps you in a stronger spot when you talk to a buyer."),
        ],
    },
    {
        "key": "successorPreferences",
        "title": "Who could take it on",
        "intro": "There are no wrong answers — this is about your preferences.",
        "questions": [
            _q("suc_acceptable", "successorPreferences", "acceptablePaths",
               "Which kinds of transition feel acceptable to you?", "multi",
               options=_opts(
                   ("family_transfer", "Family transfer"),
                   ("employee_ownership", "Employee ownership"),
                   ("management_buyout", "Management buyout"),
                   ("independent_buyer", "Independent buyer / entrepreneur"),
                   ("strategic_buyer", "Strategic buyer / competitor"),
                   ("private_equity", "Private equity"),
               )),
            _q("suc_unacceptable", "successorPreferences", "unacceptablePaths",
               "Are any of these off the table for you?", "multi",
               options=_opts(
                   ("family_transfer", "Family transfer"),
                   ("employee_ownership", "Employee ownership"),
                   ("management_buyout", "Management buyout"),
                   ("independent_buyer", "Independent buyer / entrepreneur"),
                   ("strategic_buyer", "Strategic buyer / competitor"),
                   ("private_equity", "Private equity"),
               ),
               why="Telling us what you'd refuse is just as useful as what you'd accept — we'll respect it."),
            _q("suc_traits", "successorPreferences", "idealBuyerTraits",
               "What traits would the right next owner have?", "multi",
               options=_opts(("patient operator", "Patient operator"),
                             ("local credibility", "Local credibility"),
                             ("industry experience", "Industry experience"),
                             ("keeps the team", "Will keep the team"),
                             ("protects the name", "Protects the company name"),
                             ("financial strength", "Financial strength"))),
            _q("suc_dealbreakers", "successorPreferences", "dealbreakers",
               "What would make a buyer an automatic no?", "multi",
               options=_opts(("layoffs", "Plans layoffs"), ("relocation", "Would relocate the business"),
                             ("strips assets", "Strips the business for parts"),
                             ("erases the name", "Erases the company name"),
                             ("ignores culture", "Ignores the culture"))),
        ],
    },
    {
        "key": "protectedInterests",
        "title": "What must be protected",
        "intro": "The heart of stewardship — what you will not let be lost.",
        "questions": [
            _q("prot_employees", "protectedInterests", "employeeConcerns",
               "What do you most want protected for your employees?", "multi",
               options=_opts(("jobs kept", "Their jobs"), ("culture", "The culture"),
                             ("pay & benefits", "Pay & benefits"),
                             ("growth", "Their chance to grow"),
                             ("loyalty rewarded", "Loyalty rewarded"))),
            _q("prot_customers", "protectedInterests", "customerContinuityConcerns",
               "What matters most for your customers after you step back?", "multi",
               options=_opts(("service standards", "Service standards"),
                             ("continuity", "Continuity / no disruption"),
                             ("relationships", "Their relationships"),
                             ("the name", "The company name"),
                             ("local presence", "Local presence"))),
            _q("prot_nonneg", "nonNegotiables", "nonNegotiables",
               "If nothing else, what must NOT be lost in a transition?", "multi",
               options=_opts(("the team", "The team"), ("the name", "The company name"),
                             ("service quality", "Service quality"),
                             ("community role", "Community role"),
                             ("customer trust", "Customer trust"))),
        ],
    },
    {
        "key": "familyAlignment",
        "title": "Family alignment",
        "intro": "Only if relevant — and only as much as you want to share.",
        "questions": [
            _q("fam_inbiz", "familyAlignment", "familyInBusiness",
               "Is any family member involved in the business?", "boolean", sensitive=True),
            _q("fam_expect", "familyAlignment", "expectationsKnown",
               "Do you know what your family expects to happen?", "boolean", sensitive=True),
            _q("fam_align", "familyAlignment", "alignmentLevel",
               "How aligned is your family on the future?", "single",
               options=_opts(("unknown", "Not sure"), ("misaligned", "Not aligned"),
                             ("partial", "Partly aligned"), ("aligned", "Fully aligned")),
               sensitive=True),
            _q("fam_conflict", "familyAlignment", "conflictRisk",
               "Is there risk of family conflict over this?", "single",
               options=_opts(("low", "Low"), ("medium", "Medium"), ("high", "High")),
               sensitive=True,
               why="Naming this privately now is far easier than discovering it mid-transition."),
        ],
    },
    {
        "key": "emotionalReadiness",
        "title": "Where you are with letting go",
        "intro": "This part is just between us. Move at your pace.",
        "questions": [
            _q("emo_motivation", "emotionalReadiness", "primaryMotivation",
               "What's driving you to think about this now?", "longtext",
               placeholder="In your own words…"),
            _q("emo_urgency", "emotionalReadiness", "urgencyDrivers",
               "What's adding urgency, if anything?", "multi",
               options=_opts(("health", "Health"), ("age", "Age"), ("fatigue", "Fatigue / burnout"),
                             ("timing", "Market timing"), ("family", "Family reasons"),
                             ("none", "No real urgency")),
               sensitive=True,
               why="If health or fatigue is part of it, we'll make sure you're not left to software alone."),
            _q("emo_letgo", "emotionalReadiness", "readinessToLetGo",
               "How ready do you feel to step back?", "scale",
               help_text="1 = not ready at all · 5 = ready when the time is right",
               sensitive=True),
            _q("emo_concerns", "emotionalReadiness", "topConcerns",
               "What worries you most about a transition?", "longtext",
               placeholder="The things that keep this on your mind…", sensitive=True),
        ],
    },
]


SECTION_BY_KEY = {section["key"]: section for section in SECTIONS}
QUESTION_BY_ID = {q["id"]: q for section in SECTIONS for q in section["questions"]}


def all_sections() -> list[dict[str, Any]]:
    return SECTIONS


def section_questions(section_key: str) -> list[dict[str, Any]]:
    section = SECTION_BY_KEY.get(section_key)
    return list(section["questions"]) if section else []
