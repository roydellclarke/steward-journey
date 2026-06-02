"""Generator agent."""

from __future__ import annotations

from datetime import UTC, datetime
import html
import re

from harness.agents.adk_factory import ADKAgentHandle, create_adk_agent
from harness.agents.file_patch import extract_generated_files
from harness.agents.prompts import GENERATOR_PROMPT
from harness.config import HarnessConfig
from harness.llm_client import LlmClient, LlmResult
from harness.tools.file_tools import FileTools


class GeneratorAgent:
    name = "generator"

    def __init__(self, config: HarnessConfig, files: FileTools) -> None:
        self.config = config
        self.files = files
        self.llm = LlmClient()
        self.adk_agent: ADKAgentHandle = create_adk_agent(
            name="Generator",
            model_config=config.generator,
            instruction=GENERATOR_PROMPT,
            tools=("read_file", "write_file", "list_directory"),
            tool_objects=(files.read_file, files.write_file, files.list_directory),
        )

    def propose_test_plan(self) -> None:
        sprint = self.files.read_file("specs/sprint_plan.md")
        if self.config.use_llm:
            result = self.llm.complete(
                model_config=self.config.generator,
                system=GENERATOR_PROMPT,
                user=GENERATOR_TEST_PLAN_PROMPT.format(sprint=sprint),
            )
            self.files.write_file("proposals/test_plan.md", result.content)
            self.files.write_file("proposals/implementation_plan.md", IMPLEMENTATION_PLAN)
            self._write_usage("generator", result)
            self.files.append_file("traces/generator_trace.md", f"\n## {datetime.now(UTC).isoformat()}\nProposed LLM test plan.\n")
            return

        content = f"""# Proposed Test Plan

## Feature Under Test

Long-running adversarial agent harness.

## Proposed User Flows

- Initialize a workspace.
- Run the contract handshake.
- Generate or repair code from a current sprint contract.
- Evaluate with Puppeteer evidence.
- Stop with completion or abort report.

## Proposed Edge Cases

- Missing goals file.
- Weak test plan rejected by Evaluator.
- App startup command missing.
- Evaluator reports repeated same failure.
- Cost or iteration threshold exceeded.

## Proposed Failure Modes

- Generator attempts to self-approve.
- Evaluator pass has no Puppeteer actions.
- Path traversal attempts escape workspace.
- Contract criteria are vague or untestable.

## Proposed Acceptance Criteria

- Workspace directories exist before loop execution.
- Planner, Generator, and Evaluator are distinct logical roles.
- Generator cannot write pass verdicts.
- Evaluator alone can write pass/fail reports.
- Puppeteer evidence is required for pass.
- Loop aborts when configured thresholds are exceeded.

## Required Test Data

- A Markdown goals file.
- A valid current sprint contract.

## App Startup Command

```bash
python3 -m http.server 3000 --directory workspace/src
```

## Routes to Test

- /

## Known Uncertainties

- External LLM credentials may not be configured during local tests.

## Sprint Plan Read

{sprint[:2000]}
"""
        self.files.write_file("proposals/test_plan.md", content)
        self.files.write_file("proposals/implementation_plan.md", IMPLEMENTATION_PLAN)
        self.files.append_file("traces/generator_trace.md", f"\n## {datetime.now(UTC).isoformat()}\nProposed test plan.\n")

    def build_or_repair(self, iteration: int) -> None:
        contract = self.files.read_file("contracts/current_sprint.md")
        feedback = self.files.read_file("feedback/evaluation_report.md") if self.files.exists("feedback/evaluation_report.md") else ""
        goals = self.files.read_file("goals/user_goals.md")
        design_brief = self.files.read_file("specs/design_brief.md") if self.files.exists("specs/design_brief.md") else ""
        if self.config.use_llm:
            result = self.llm.complete(
                model_config=self.config.generator,
                system=GENERATOR_PROMPT,
                user=GENERATOR_BUILD_PROMPT.format(
                    iteration=iteration,
                    contract=contract,
                    feedback=feedback.strip() or "No prior Evaluator feedback.",
                ),
            )
            self.files.write_file("state/generator_build_response.md", result.content)
            self._write_usage("generator", result)
            generated_files = extract_generated_files(result.content)
            if generated_files:
                for generated_file in generated_files:
                    self.files.write_file(generated_file.path, generated_file.content)
                files_changed = "\n".join(f"- /workspace/{generated_file.path}" for generated_file in generated_files)
                self._write_build_log(
                    iteration=iteration,
                    contract=contract,
                    feedback=feedback,
                    design_brief=design_brief,
                    files_changed=files_changed,
                    summary="Applied safe file blocks from the live Generator model response.",
                )
                self.files.append_file("traces/generator_trace.md", f"\n## {datetime.now(UTC).isoformat()}\nApplied LLM file blocks for iteration {iteration}.\n")
                return

        app = render_landing_page(goals=goals, iteration=iteration)
        self.files.write_file("src/index.html", app)
        self.files.write_file("src/app.js", render_landing_page_js())
        self._write_build_log(
            iteration=iteration,
            contract=contract,
            feedback=feedback,
            design_brief=design_brief,
            files_changed="- /workspace/src/index.html\n- /workspace/src/app.js",
            summary="Built or repaired the browser landing page requested in the user goals.",
        )
        self.files.append_file("traces/generator_trace.md", f"\n## {datetime.now(UTC).isoformat()}\nBuilt iteration {iteration}.\n")

    def _write_build_log(
        self,
        *,
        iteration: int,
        contract: str,
        feedback: str,
        design_brief: str,
        files_changed: str,
        summary: str,
    ) -> None:
        log = f"""# Build Log

## Iteration

{iteration}

## Files Changed

{files_changed}

## Summary of Changes

{summary} The Generator is not claiming completion.

## Evaluator Feedback Addressed

{feedback.strip() or "No prior Evaluator feedback."}

## Known Issues

- Deterministic no-cloud mode uses a goal-aware landing page generator. Live LLM
  mode should eventually replace this with full code-writing patches.

## Startup Instructions

```bash
python3 -m http.server 3000 --directory workspace/src
```

## Notes for Evaluator

Use Puppeteer to navigate to `/`, inspect text, click the call-to-action
buttons, and check console errors. Contract excerpt:

{contract[:2000]}

## Design Brief Used

{design_brief[:1600] or "No design brief found."}
"""
        self.files.write_file("state/build_log.md", log)

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


IMPLEMENTATION_PLAN = """# Implementation Plan

## Approach

Keep the first sprint small and verifiable: create a browser-visible landing
page in `/workspace/src` from the user's goal that the Evaluator can actively
validate.

## Boundaries

The Generator will not mark pass/fail status and will not bypass Evaluator
feedback.
"""


def render_landing_page(*, goals: str, iteration: int) -> str:
    brief = summarize_goal(goals)
    brand = extract_brand(goals)
    features = extract_feature_points(goals)
    audience = extract_audience(goals)
    concept = infer_goal_concept(goals)
    escaped_brand = html.escape(brand)
    escaped_brief = html.escape(brief)
    feature_cards = "\n".join(
        f"""          <article class="feature">
            <span>{index:02d}</span>
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(body)}</p>
          </article>"""
        for index, (title, body) in enumerate(features, start=1)
    )
    audience_items = "\n".join(f"<li>{html.escape(item)}</li>" for item in audience)
    nav_items = "\n".join(f"<span>{html.escape(item)}</span>" for item in concept["nav"].split("|"))
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="data:,">
    <title>{escaped_brand} Landing Page</title>
    <style>
      :root {{
        --ink: #14202e;
        --muted: #5c6978;
        --line: #d8dee6;
        --panel: #ffffff;
        --bg: #f4f7f9;
        --green: #116149;
        --blue: #204b8f;
        --amber: #a06416;
      }}
      * {{
        box-sizing: border-box;
      }}
      body {{
        margin: 0;
        font-family: Arial, sans-serif;
        background: var(--bg);
        color: var(--ink);
      }}
      header, section, footer {{
        width: min(1180px, calc(100vw - 32px));
        margin: 0 auto;
      }}
      nav {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 22px 0;
      }}
      .brand {{
        font-weight: 900;
        font-size: 20px;
      }}
      .navLinks {{
        display: flex;
        gap: 18px;
        color: var(--muted);
        font-size: 14px;
      }}
      .hero {{
        display: grid;
        grid-template-columns: minmax(0, 1.08fr) minmax(320px, .92fr);
        gap: 34px;
        align-items: center;
        padding: 44px 0 34px;
      }}
      .eyebrow {{
        color: var(--green);
        font-weight: 900;
        text-transform: uppercase;
        font-size: 13px;
        margin: 0 0 12px;
      }}
      h1 {{
        font-size: clamp(40px, 6vw, 72px);
        line-height: .98;
        margin: 0 0 20px;
      }}
      .hero p {{
        color: var(--muted);
        font-size: 19px;
        line-height: 1.55;
        max-width: 680px;
      }}
      .actions {{
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 28px;
      }}
      button, .button {{
        border: 1px solid var(--line);
        border-radius: 8px;
        min-height: 44px;
        padding: 11px 16px;
        font-weight: 800;
        cursor: pointer;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        color: var(--ink);
        background: #fff;
      }}
      .primary {{
        background: var(--green);
        border-color: var(--green);
        color: white;
      }}
      .productPanel {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 6px;
        padding: 18px;
        box-shadow: 0 18px 50px rgba(20, 32, 46, .08);
      }}
      .terminal {{
        background: #101820;
        color: #e7edf3;
        border-radius: 6px;
        padding: 16px;
        font-family: Menlo, Consolas, monospace;
        font-size: 13px;
        line-height: 1.55;
        overflow: hidden;
      }}
      .terminal strong {{
        color: #7dd3b0;
      }}
      .sectionTitle {{
        margin: 42px 0 18px;
        font-size: 30px;
      }}
      .features {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
      }}
      .feature {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 6px;
        padding: 18px;
        min-height: 190px;
      }}
      .feature span {{
        color: var(--amber);
        font-weight: 900;
        font-size: 13px;
      }}
      .feature h3 {{
        margin: 12px 0 8px;
      }}
      .feature p, .audience p, footer {{
        color: var(--muted);
        line-height: 1.5;
      }}
      .audience {{
        display: grid;
        grid-template-columns: minmax(0, .8fr) minmax(280px, .45fr);
        gap: 24px;
        align-items: start;
        background: #ffffff;
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 24px;
        margin-top: 20px;
      }}
      ul {{
        margin: 0;
        padding-left: 18px;
        color: var(--ink);
        line-height: 1.7;
      }}
      footer {{
        padding: 36px 0;
      }}
      @media (max-width: 850px) {{
        .hero, .audience, .features {{
          grid-template-columns: 1fr;
        }}
        .navLinks {{
          display: none;
        }}
      }}
    </style>
  </head>
  <body>
    <header>
      <nav>
        <div class="brand">{escaped_brand}</div>
        <div class="navLinks">
          {nav_items}
        </div>
      </nav>
      <div class="hero">
        <div>
          <p class="eyebrow">{html.escape(concept["eyebrow"])}</p>
          <h1>{escaped_brand}</h1>
          <p>{escaped_brief}</p>
          <div class="actions">
            <button id="primary-action" class="primary" type="button">{html.escape(concept["primary_cta"])}</button>
            <button id="secondary-action" type="button">{html.escape(concept["secondary_cta"])}</button>
          </div>
          <p id="result" aria-live="polite">{html.escape(concept["ready_state"])}</p>
        </div>
        <aside class="productPanel" aria-label="{html.escape(concept["artifact_label"])}">
          <div class="terminal">
            {render_artifact_lines(concept)}
          </div>
        </aside>
      </div>
    </header>

    <section>
      <h2 class="sectionTitle">Platform capabilities</h2>
      <div class="features">
{feature_cards}
      </div>
    </section>

    <section class="audience">
      <div>
        <h2>{html.escape(concept["audience_heading"])}</h2>
        <p>{html.escape(concept["audience_copy"])}</p>
      </div>
      <ul>
        {audience_items}
      </ul>
    </section>

    <footer>
      Generated from user goals in deterministic no-cloud mode. Iteration {iteration}.
    </footer>
    <script src="./app.js"></script>
  </body>
</html>
"""

def render_landing_page_js() -> str:
    return """const primary = document.querySelector("#primary-action");
const secondary = document.querySelector("#secondary-action");
const result = document.querySelector("#result");

primary.addEventListener("click", () => {
  result.textContent = "Preview generated. Next step is ready.";
});

secondary.addEventListener("click", () => {
  result.textContent = "Secondary workflow opened. Review details are ready.";
});
"""


def extract_brand(goals: str) -> str:
    quoted = re.search(r'System:\s*"([^"]+?)\s+is\b', goals, re.IGNORECASE | re.DOTALL)
    if quoted:
        return quoted.group(1).strip()
    named = re.search(r"for\s+([A-Z][A-Za-z0-9 ]{2,40}?)(?:\s+Platform|\s+system|\s+that|\.)", goals)
    if named:
        return named.group(1).strip()
    lowered = goals.lower()
    if "boomer" in lowered and "business" in lowered:
        return "Legacy Market"
    if "android" in lowered:
        return "Android Launch App"
    return "AI Launch Platform"


def summarize_goal(goals: str) -> str:
    normalized = " ".join(goals.split())
    match = re.search(r"is\s+(.*?)(?:Its core idea|Core Philosophy|Main Capabilities|$)", normalized, re.IGNORECASE)
    if match:
        summary = match.group(1).strip()
    else:
        summary = normalized[:360]
    summary = summary[:360].rsplit(" ", 1)[0]
    return summary or "A focused landing page for launching AI applications through a model-aware deployment gateway."


def extract_feature_points(goals: str) -> list[tuple[str, str]]:
    text = goals.lower()
    if "boomer" in text and "business" in text:
        return [
            ("Retirement-ready listings", "Owners can describe the business, asking terms, location, history, and handoff needs."),
            ("Buyer matching", "Qualified buyers can discover businesses by category, region, price range, and owner timeline."),
            ("Succession story pages", "Each listing captures why the business matters and what kind of buyer should carry it forward."),
            ("Guided seller workflow", "Simple prompts help non-technical owners publish without learning a complicated marketplace tool."),
            ("Trust and privacy controls", "Owners can choose what is public, what requires buyer interest, and when to reveal sensitive details."),
            ("Mobile-first Android flow", "The core experience is shaped for phone use, quick editing, and easy inquiry handling."),
        ]
    if "android" in text:
        return [
            ("Mobile onboarding", "Guide users from first open to the key action with plain language and minimal steps."),
            ("Profile-driven experience", "Capture the details the app needs to personalize recommendations and workflows."),
            ("Action dashboard", "Show the next best action, status, and recent activity in a compact mobile layout."),
            ("Notifications and reminders", "Keep users aware of important updates without overwhelming them."),
            ("Secure account state", "Design around privacy, recovery, and clear control of user information."),
            ("Responsive prototype", "Represent the Android product as a browser-testable mobile-first prototype."),
        ]
    candidates = [
        ("Domain-driven launches", "Turn a domain and Docker image into a routed, observable, running application."),
        ("Model gateway awareness", "Track providers, capabilities, API keys, fallbacks, budgets, and routing metadata."),
        ("Preview, diff, validate, apply", "Use a safe deployment workflow before changing live infrastructure."),
        ("Registry-driven state", "Keep apps, providers, capabilities, tools, data, memory, cost, and evals inspectable."),
        ("Operator control panel", "Give non-terminal users status cards, health checks, history, snapshots, and rollback."),
        ("Recovery-first operations", "Make deployments versioned, observable, reversible, and disaster-recovery friendly."),
    ]
    if "caddy" in text:
        candidates[0] = ("Caddy routing and HTTPS", "Generate public routes, HTTPS, redirects, and preserved custom blocks.")
    if "docker compose" in text:
        candidates[2] = ("Docker Compose runtime", "Run apps with familiar services, ports, health checks, env files, and logs.")
    return candidates[:6]


def extract_audience(goals: str) -> list[str]:
    text = goals.lower()
    if "boomer" in text and "business" in text:
        return ["retiring business owners", "qualified local buyers", "family-run companies", "business brokers", "community lenders"]
    items = ["AI engineers", "founders", "small platform teams", "domain experts"]
    if "operators" in text:
        items.append("operators")
    if "small teams" in text:
        items.append("small AI teams")
    return list(dict.fromkeys(items))[:5]


def infer_goal_concept(goals: str) -> dict[str, str]:
    lowered = goals.lower()
    if "boomer" in lowered and "business" in lowered:
        return {
            "eyebrow": "Business succession marketplace for retiring owners",
            "primary_cta": "Preview seller listing",
            "secondary_cta": "Browse buyer matches",
            "ready_state": "Ready to help an owner list a business for sale or handoff.",
            "artifact_label": "Android marketplace preview",
            "nav": "List|Match|Inquire|Handoff",
            "audience_heading": "Built for owners ready to pass the torch",
            "audience_copy": "Legacy Market helps retiring owners present the value, story, and handoff needs of a real local business so qualified buyers can discover it with context and confidence.",
            "artifact_lines": "\n".join(
                [
                    "app: Legacy Market Android",
                    "seller: retiring owner",
                    "listing: business profile + handoff terms",
                    "buyers: qualified local operators",
                    "workflow: draft -> verify -> publish -> inquiries",
                    "status: mobile listing preview ready",
                ]
            ),
        }
    if "android" in lowered:
        return {
            "eyebrow": "Mobile-first Android app concept",
            "primary_cta": "Preview app flow",
            "secondary_cta": "Review user journey",
            "ready_state": "Ready to preview the Android app workflow.",
            "artifact_label": "Android app preview",
            "nav": "Onboard|Profile|Action|Follow-up",
            "audience_heading": "Built for mobile users who need a focused workflow",
            "audience_copy": "This Android concept keeps the core user journey clear: quick onboarding, useful profile context, a focused action dashboard, and simple follow-up states.",
            "artifact_lines": "\n".join(
                [
                    "platform: Android",
                    "screen: onboarding + dashboard",
                    "state: prototype ready",
                    "workflow: open -> profile -> action -> follow-up",
                    "status: mobile preview ready",
                ]
            ),
        }
    return {
        "eyebrow": "AI deployment without Kubernetes drag",
        "primary_cta": "Preview deployment",
        "secondary_cta": "View model gateway",
        "ready_state": "Ready to launch app through the model gateway.",
        "artifact_label": "Deployment preview",
        "nav": "Deploy|Observe|Validate|Recover",
        "audience_heading": "Built for small AI teams that need control",
        "audience_copy": "AI Launch Platform keeps deployment state visible through registries, CLI commands, and a responsive control panel. It is designed for teams that want practical platform engineering without inheriting a heavy orchestration stack.",
        "artifact_lines": "\n".join(
            [
                "$ yezamo preview claritypro",
                "domain: claritypro.yezamo.com",
                "image: ghcr.io/team/app:v1.0.2",
                "gateway: DeepSeek + Kimi + OpenAI fallback",
                "workflow: preview -> diff -> validate -> apply",
                "status: recoverable deployment plan ready",
            ]
        ),
    }


def render_artifact_lines(concept: dict[str, str]) -> str:
    lines = []
    for index, line in enumerate(concept["artifact_lines"].splitlines()):
        escaped = html.escape(line)
        if index == 0:
            lines.append(f"<div><strong>$</strong> {escaped}</div>")
        else:
            lines.append(f"<div>{escaped}</div>")
    return "\n            ".join(lines)

GENERATOR_TEST_PLAN_PROMPT = """Read the sprint plan and write `/proposals/test_plan.md`.

Return Markdown only with this exact structure:

# Proposed Test Plan

## Feature Under Test
## Proposed User Flows
## Proposed Edge Cases
## Proposed Failure Modes
## Proposed Acceptance Criteria
## Required Test Data
## App Startup Command
## Routes to Test
## Known Uncertainties

Rules:
- You are the Generator, not the Evaluator.
- Do not say the work is done.
- Make the plan granular enough for a harsh Evaluator to accept or reject.
- Include Puppeteer-testable user flows.

Sprint plan:
{sprint}
"""

GENERATOR_BUILD_PROMPT = """You are building or repairing iteration {iteration}.

Read the current sprint contract and Evaluator feedback. Return concise
implementation notes and, when you are ready to write files, include safe file
blocks using this exact format:

```file src/index.html
<!doctype html>
...
```

```file src/app.js
...
```

Rules:
- Do not approve your own work.
- Do not mark criteria passed.
- Address the Evaluator feedback directly.
- Only write files under `src/`.
- Do not include secrets or API keys.
- The output must be a complete browser-runnable page when file blocks are used.

Current contract:
{contract}

Evaluator feedback:
{feedback}
"""
