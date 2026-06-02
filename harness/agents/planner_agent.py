"""Planner agent."""

from __future__ import annotations

from datetime import UTC, datetime

from harness.agents.adk_factory import ADKAgentHandle, create_adk_agent
from harness.agents.prompts import PLANNER_PROMPT
from harness.config import HarnessConfig
from harness.llm_client import LlmClient, LlmResult
from harness.tools.file_tools import FileTools


class PlannerAgent:
    name = "planner"

    def __init__(self, config: HarnessConfig, files: FileTools) -> None:
        self.config = config
        self.files = files
        self.llm = LlmClient()
        self.adk_agent: ADKAgentHandle = create_adk_agent(
            name="Planner",
            model_config=config.planner,
            instruction=PLANNER_PROMPT,
            tools=("read_file", "write_file", "list_directory"),
            tool_objects=(files.read_file, files.write_file, files.list_directory),
        )

    def create_sprint_plan(self) -> None:
        goals = self.files.read_file("goals/user_goals.md")
        handoff = self._optional("state/handoff_summary.md")
        rejection = self._optional("feedback/rejection_reasons.md")
        if self.config.use_llm:
            result = self.llm.complete(
                model_config=self.config.planner,
                system=PLANNER_PROMPT,
                user=PLANNER_USER_PROMPT.format(
                    goals=goals.strip(),
                    handoff=handoff.strip() or "No prior handoff.",
                    rejection=rejection.strip() or "No prior rejections.",
                ),
            )
            self.files.write_file("specs/sprint_plan.md", result.content)
            self.files.write_file("specs/architecture_notes.md", ARCHITECTURE_NOTES)
            self.files.write_file("specs/design_brief.md", build_design_brief(goals))
            self._write_usage("planner", result)
            self.files.append_file("traces/planner_trace.md", f"\n## {datetime.now(UTC).isoformat()}\nCreated LLM sprint plan.\n")
            return

        content = f"""# Sprint Plan

Generated: {datetime.now(UTC).isoformat()}

## User Goals

{goals.strip()}

## Sprint Objective

Create a bounded first application sprint that can be negotiated into granular,
Puppeteer-testable acceptance criteria.

## User Outcome

The user can run a long-running adversarial agent harness where a Planner,
Generator, and Evaluator cycle toward a goal under explicit cost, time,
iteration, and quality constraints.

## Scope

- Initialize the required workspace container.
- Enforce three role boundaries.
- Route each role through distinct logical model configuration.
- Use Markdown and JSON files as the durable transport.
- Require Evaluator-controlled Puppeteer validation before pass.

## Out of Scope

- Hard-coded cloud credentials.
- Unbounded autonomous operation.
- Generator self-approval.

## Risks

- Weak contracts can cause noisy loops.
- Browser validation can fail if the target app does not start.
- Cost tracking may be approximate until provider token usage is wired.

## Suggested Acceptance Areas

- Workspace creation.
- Safe file tools.
- Contract handshake.
- Build-and-break cycle.
- Abort and completion thresholds.
- Puppeteer evidence for pass verdicts.

## Open Questions

- Which provider credentials should be enabled first?
- Should the generated app live in `/workspace/src` only, or in a separate repo?

## Suggested Sprint Sequence

1. Harness skeleton and file tools.
2. Agent definitions and model routing.
3. Contract handshake.
4. Build-and-break loop.
5. Puppeteer validation and reports.
6. Cost, autonomy, divergence, and context hygiene.

## Prior Handoff Context

{handoff.strip() or "No prior handoff."}

## Prior Rejections

{rejection.strip() or "No prior rejections."}
"""
        self.files.write_file("specs/sprint_plan.md", content)
        self.files.write_file("specs/architecture_notes.md", ARCHITECTURE_NOTES)
        self.files.write_file("specs/design_brief.md", build_design_brief(goals))
        self.files.append_file("traces/planner_trace.md", f"\n## {datetime.now(UTC).isoformat()}\nCreated sprint plan.\n")

    def _optional(self, path: str) -> str:
        return self.files.read_file(path) if self.files.exists(path) else ""

    def _write_usage(self, agent: str, result: LlmResult) -> None:
        self.files.write_file(
            f"state/{agent}_latest_usage.json",
            (
                "{\n"
                f'  "input_tokens": {result.input_tokens},\n'
                f'  "output_tokens": {result.output_tokens},\n'
                f'  "estimated_cost_usd": {result.estimated_cost_usd}\n'
                "}\n"
            ),
        )


ARCHITECTURE_NOTES = """# Architecture Notes

The Orchestrator is the controller. The workspace is the context container.
The file tools are the transport. The Evaluator is the only active validation
sensor with browser access. Hyperknobs bound turbulence from cost, time,
iteration count, repeated failures, and divergence.
"""


def build_design_brief(goals: str) -> str:
    return f"""# Design Brief

## Source Goal

{goals.strip()[:2200]}

## Design Direction

Create a restrained, premium SaaS landing page that makes the product or system
visible in the first viewport. Use clear hierarchy, high contrast, compact
sections, concrete product mechanics, and action-oriented CTAs.

## Do

- Show the named product or system as the dominant first-viewport signal.
- Explain the operational workflow in concrete terms.
- Include a believable product/system artifact.
- Keep cards compact and purposeful.
- Make mobile and desktop layouts readable.

## Avoid

- Generic AI marketing copy.
- Fake analytics without product meaning.
- Purple-blue gradient overload.
- Dead buttons.
- Placeholder names or lorem ipsum.
"""

PLANNER_USER_PROMPT = """Create `/specs/sprint_plan.md` content for this harness run.

Return Markdown only, using this exact structure:

# Sprint Plan

## User Goals
## Sprint Objective
## User Outcome
## Scope
## Out of Scope
## Risks
## Suggested Acceptance Areas
## Open Questions
## Suggested Sprint Sequence

Constraints:
- Do not write application code.
- Do not approve completion.
- Keep implementation details negotiable.
- Make the next sprint testable by Generator and Evaluator.

User goals:
{goals}

Prior handoff:
{handoff}

Prior rejections:
{rejection}
"""
