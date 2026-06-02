"""Workspace initialization and context hygiene."""

from __future__ import annotations

import json
from pathlib import Path

from harness.config import HarnessConfig
from harness.schemas.loop_state import LoopState
from harness.trust import TRUSTED, TrustStore, USER_PROVIDED
from harness.mcp_policy import DEFAULT_MCP_POLICY


WORKSPACE_DIRS = [
    "goals",
    "specs",
    "contracts",
    "src",
    "proposals",
    "feedback",
    "state",
    "rubrics",
    "traces",
    "reports",
    "screenshots",
    "quarantine",
]


class Workspace:
    def __init__(self, config: HarnessConfig) -> None:
        self.config = config
        self.root = config.workspace_root

    def initialize(self) -> None:
        for directory in WORKSPACE_DIRS:
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        self._seed_file("rubrics/design_taste.md", DESIGN_TASTE_RUBRIC)
        self._seed_file("rubrics/functionality_rubric.md", FUNCTIONALITY_RUBRIC)
        self._seed_file("rubrics/acceptance_criteria_template.md", ACCEPTANCE_TEMPLATE)
        self._seed_file("rubrics/landing_page_design.md", LANDING_PAGE_DESIGN_RUBRIC)
        self._seed_file("rubrics/saas_ui_quality.md", SAAS_UI_QUALITY_RUBRIC)
        self._seed_file("rubrics/conversion_copywriting.md", CONVERSION_COPYWRITING_RUBRIC)
        self._seed_file("state/redaction_policy.md", REDACTION_POLICY)
        self._seed_file("state/sensitive_paths.json", json.dumps(SENSITIVE_PATHS, indent=2))
        self._seed_file("state/mcp_policy.json", json.dumps(DEFAULT_MCP_POLICY, indent=2))
        self._seed_file("state/a2a_policy.md", A2A_POLICY)
        if not (self.root / "state" / "loop_state.json").exists():
            state = LoopState(
                hyperknobs=self.config.hyperknobs(),
                models=self.config.model_table(),
            )
            self.write_json("state/loop_state.json", state.to_dict())
        if not (self.root / "state" / "cost_log.json").exists():
            self.write_json("state/cost_log.json", [])
        self._seed_trust_labels()

    def reset_run_state(self) -> None:
        state = LoopState(
            hyperknobs=self.config.hyperknobs(),
            models=self.config.model_table(),
        )
        self.write_json("state/loop_state.json", state.to_dict())
        self.write_json("state/cost_log.json", [])

    def save_goals(self, goals_path: Path) -> None:
        content = goals_path.read_text(encoding="utf-8")
        self.write_text("goals/user_goals.md", content)
        TrustStore(self.root).label("goals/user_goals.md", USER_PROVIDED, source=str(goals_path), notes="raw user goal")

    def read_json(self, relative_path: str) -> dict | list:
        return json.loads((self.root / relative_path).read_text(encoding="utf-8"))

    def write_json(self, relative_path: str, payload: object) -> None:
        target = self.root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def write_text(self, relative_path: str, content: str) -> None:
        target = self.root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def append_text(self, relative_path: str, content: str) -> None:
        target = self.root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(content)

    def _seed_file(self, relative_path: str, content: str) -> None:
        target = self.root / relative_path
        if not target.exists():
            self.write_text(relative_path, content)

    def _seed_trust_labels(self) -> None:
        store = TrustStore(self.root)
        for path in [
            "rubrics/design_taste.md",
            "rubrics/functionality_rubric.md",
            "rubrics/acceptance_criteria_template.md",
            "rubrics/landing_page_design.md",
            "rubrics/saas_ui_quality.md",
            "rubrics/conversion_copywriting.md",
            "state/redaction_policy.md",
            "state/sensitive_paths.json",
            "state/mcp_policy.json",
            "state/a2a_policy.md",
        ]:
            store.label(path, TRUSTED, source="harness", notes="seeded policy/rubric")


DESIGN_TASTE_RUBRIC = """# Design Taste Rubric

## Premium Examples

Premium SaaS UI has strong spacing, clear hierarchy, restrained palette,
readable typography, meaningful empty states, polished form states, real data,
and controls that visibly work.

## AI Slop Examples

Weak AI-generated UI often has purple-blue gradient overload, vague marketing
copy, fake dashboard widgets, inconsistent spacing, unreadable contrast, dead
buttons, decorative UI with no function, placeholder names, and forms that do
not submit.

## Scoring

Design: 0-5
Originality: 0-5
Craft: 0-5
Functionality: 0-5

Any score below 4 requires a FAIL unless explicitly out of scope.
"""

FUNCTIONALITY_RUBRIC = """# Functionality Rubric

Functional work must be validated by active user flows. The Evaluator should
fail any criterion that lacks evidence, has console errors, loses state,
contains dead controls, or only works on the happy path.
"""

ACCEPTANCE_TEMPLATE = """# Acceptance Criteria Template

Each criterion must be granular, observable, and testable through Puppeteer.

- [ ] User can perform a named action from a named route.
- [ ] The UI visibly confirms the state change.
- [ ] Invalid input produces a clear error state.
- [ ] Console remains free of critical errors.
"""

LANDING_PAGE_DESIGN_RUBRIC = """# Landing Page Design Rubric

## Premium Traits

- The first viewport clearly names the product or offer.
- The hero explains who it is for and why it matters.
- The primary CTA is concrete and action-oriented.
- Capabilities are specific to the product, not generic filler.
- The page shows a believable product/system artifact.
- Layout works on mobile and desktop without text overlap.

## Failure Traits

- Generic SaaS claims that could fit any product.
- Oversized decorative gradients with little product signal.
- Fake metrics or dashboard widgets not grounded in the goal.
- CTA buttons that do not respond.
- Missing or vague target audience.
- Text that overflows or becomes unreadable on mobile.

## Pass Threshold

Design, craft, originality, and functionality should each score at least 4/5
unless explicitly out of scope.
"""

SAAS_UI_QUALITY_RUBRIC = """# SaaS UI Quality Rubric

Good operational SaaS pages are quiet, legible, and dense enough to be useful.
Prefer restrained color, clear hierarchy, visible product mechanics, compact
cards, and strong spacing. Avoid decorative card piles, fake analytics, generic
purple-blue gradients, and marketing copy that says nothing concrete.
"""

CONVERSION_COPYWRITING_RUBRIC = """# Conversion Copywriting Rubric

Copy must say what the product does, who it helps, what problem it solves, and
what action the visitor should take next. Prefer concrete verbs and product
mechanics over abstract claims such as "supercharge your workflow".
"""

REDACTION_POLICY = """# Redaction Policy

The harness treats secrets, PII, screenshots, and provider credentials as
sensitive by default.

Do not send these to live LLMs or vector memory unless a future contract
explicitly allows it:

- `.env` files
- API keys, bearer tokens, passwords, private keys
- email addresses
- phone numbers
- screenshots that may contain private data
- cost logs and provider usage metadata
- unredacted user documents

Generated reports and event logs must redact common secret and PII patterns.
"""

SENSITIVE_PATHS = {
    "never_index": [
        ".env",
        ".env.*",
        "workspace/screenshots/*",
        "workspace/state/cost_log.json",
        "*.pem",
        "*.key",
        "*secret*",
        "*token*"
    ],
    "redact_before_llm": [
        "workspace/goals/*",
        "workspace/feedback/*",
        "workspace/reports/*",
        "workspace/state/events.jsonl",
        "workspace/quarantine/*",
        "workspace/state/memory_manifest.json"
    ]
}

A2A_POLICY = """# A2A Policy

Agent-to-agent communication must not bypass the workspace.

Allowed A2A messages are structured references to durable artifacts:

- sprint_spec
- test_plan
- critique
- build_log
- evaluation_report
- handoff_summary

Free-form hidden agent chat is forbidden. External A2A systems must reference a
workspace artifact path and must not carry secrets.
"""
