"""Evaluator agent."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from harness.agents.adk_factory import ADKAgentHandle, create_adk_agent
from harness.agents.prompts import EVALUATOR_PROMPT
from harness.config import HarnessConfig
from harness.llm_client import LlmClient, LlmResult
from harness.tools.file_tools import FileTools
from harness.tools.puppeteer_bridge import PuppeteerBridge


class EvaluatorAgent:
    name = "evaluator"

    def __init__(self, config: HarnessConfig, files: FileTools, browser: PuppeteerBridge | None = None) -> None:
        self.config = config
        self.files = files
        self.browser = browser or PuppeteerBridge()
        self.llm = LlmClient()
        self.adk_agent: ADKAgentHandle = create_adk_agent(
            name="Evaluator",
            model_config=config.evaluator,
            instruction=EVALUATOR_PROMPT,
            tools=(
                "read_file",
                "write_file",
                "list_directory",
                "puppeteer_navigate",
                "puppeteer_click",
                "puppeteer_type",
                "puppeteer_screenshot",
                "puppeteer_get_console_errors",
                "puppeteer_get_page_text",
                "puppeteer_wait_for_selector",
                "puppeteer_evaluate_dom",
            ),
            tool_objects=(
                files.read_file,
                files.write_file,
                files.list_directory,
                self.browser.navigate,
                self.browser.click,
                self.browser.type,
                self.browser.screenshot,
                self.browser.get_console_errors,
                self.browser.get_page_text,
                self.browser.wait_for_selector,
                self.browser.evaluate_dom,
            ),
        )

    def critique_test_plan(self) -> bool:
        proposal = self.files.read_file("proposals/test_plan.md")
        if self.config.use_llm:
            result = self.llm.complete(
                model_config=self.config.evaluator,
                system=EVALUATOR_PROMPT,
                user=EVALUATOR_CRITIQUE_PROMPT.format(proposal=proposal),
            )
            self.files.write_file("feedback/critique.md", result.content)
            self._write_usage("evaluator", result)
            accepted = "Accepted for Contract: YES" in result.content
            self.files.append_file("traces/evaluator_trace.md", f"\n## {datetime.now(UTC).isoformat()}\nLLM critiqued test plan: {'YES' if accepted else 'NO'}.\n")
            return accepted

        weak = "Puppeteer" not in proposal or "Acceptance Criteria" not in proposal
        accepted = not weak
        verdict = "YES" if accepted else "NO"
        content = f"""# Evaluator Critique

## Verdict

Accepted for Contract: {verdict}

## Weak Criteria

{"None blocking." if accepted else "The test plan does not provide enough active browser validation detail."}

## Missing Edge Cases

- App startup failure.
- No Puppeteer evidence.
- Repeated same failure.
- Path traversal attempts.

## Scope Problems

The first sprint must stay focused on harness viability and role boundaries.

## Required Changes

{"No changes required before contract creation." if accepted else "Add granular criteria and explicit Puppeteer actions."}

## Minimum Granular Acceptance Criteria

- Workspace directories are created.
- Generator cannot issue pass verdicts.
- Evaluator has exclusive Puppeteer capability.
- Pass requires browser evidence and criterion mapping.
- Thresholds can abort the loop.
"""
        self.files.write_file("feedback/critique.md", content)
        self.files.append_file("traces/evaluator_trace.md", f"\n## {datetime.now(UTC).isoformat()}\nCritiqued test plan: {verdict}.\n")
        return accepted

    def evaluate(self, iteration: int) -> str:
        contract = self.files.read_file("contracts/current_sprint.md")
        goals = self.files.read_file("goals/user_goals.md")
        desktop_report_path = Path("screenshots") / f"iteration-{iteration}-desktop.png"
        mobile_report_path = Path("screenshots") / f"iteration-{iteration}-mobile.png"
        audit = self.browser.audit(
            self.config.app_base_url,
            str(self.files.workspace_root / desktop_report_path),
            "#primary-action",
            viewports=[
                {"name": "desktop", "width": 1366, "height": 900},
                {"name": "mobile", "width": 390, "height": 844},
            ],
            screenshot_paths={
                "desktop": str(self.files.workspace_root / desktop_report_path),
                "mobile": str(self.files.workspace_root / mobile_report_path),
            },
        )

        puppeteer_ok = bool(audit.get("ok")) or not self.config.require_puppeteer_for_pass
        viewport_results = audit.get("results", []) or []
        desktop = _viewport_result(viewport_results, "desktop")
        mobile = _viewport_result(viewport_results, "mobile")
        text = str(desktop.get("text", audit.get("text", "")))
        clicked_text = str(desktop.get("clickedText", audit.get("clickedText", "")))
        brand = _expected_brand(goals)
        lowered_goals = goals.lower()
        lowered_text = text.lower()
        product_identity_ok = brand.lower() in text.lower()
        deployment_requested = any(term in lowered_goals for term in ["deploy", "deployment", "docker", "kubernetes", "gateway"])
        android_requested = "android" in lowered_goals or "mobile app" in lowered_goals
        marketplace_requested = any(term in lowered_goals for term in ["advertise", "sell", "business", "retired", "retirement"])
        deployment_ok = (not deployment_requested) or ("deploy" in lowered_text or "deployment" in lowered_text)
        android_ok = (not android_requested) or ("android" in lowered_text or "mobile" in lowered_text or "app" in lowered_text)
        marketplace_ok = (not marketplace_requested) or ("business" in lowered_text and ("sell" in lowered_text or "buyer" in lowered_text or "retirement" in lowered_text))
        model_gateway_requested = "model gateway" in lowered_goals or "model provider" in lowered_goals or "providers" in lowered_goals
        model_gateway_ok = (not model_gateway_requested) or ("model gateway" in lowered_text or "provider" in lowered_text or "fallback" in lowered_text)
        cta_ok = any(phrase in clicked_text for phrase in ["Preview generated", "Deployment preview generated", "Match preview generated"])
        console_clean = not audit.get("errors")
        desktop_metrics = desktop.get("metrics", {}) or {}
        mobile_metrics = mobile.get("metrics", {}) or {}
        desktop_layout_ok = bool(desktop) and not desktop_metrics.get("hasHorizontalOverflow", True)
        mobile_layout_ok = bool(mobile) and not mobile_metrics.get("hasHorizontalOverflow", True)
        feature_depth_ok = int(desktop_metrics.get("featureCount", 0) or 0) >= 3
        design_score = _score_design(
            product_identity_ok=product_identity_ok,
            deployment_ok=deployment_ok,
            android_ok=android_ok,
            marketplace_ok=marketplace_ok,
            model_gateway_ok=model_gateway_ok,
            cta_ok=cta_ok,
            desktop_layout_ok=desktop_layout_ok,
            mobile_layout_ok=mobile_layout_ok,
            feature_depth_ok=feature_depth_ok,
        )
        craft_score = _score_craft(desktop_metrics, mobile_metrics)
        originality_score = _score_originality(text)
        functionality_score = _score_functionality(puppeteer_ok, cta_ok, console_clean)
        design_review_passed = min(design_score, craft_score, originality_score, functionality_score) >= 4
        screenshot_ok = bool(desktop.get("screenshotPath")) and bool(mobile.get("screenshotPath")) or not self.config.require_puppeteer_for_pass

        passed = (
            puppeteer_ok
            and product_identity_ok
            and deployment_ok
            and android_ok
            and marketplace_ok
            and model_gateway_ok
            and cta_ok
            and console_clean
            and screenshot_ok
            and desktop_layout_ok
            and mobile_layout_ok
            and feature_depth_ok
            and design_review_passed
        )
        verdict = "PASS" if passed else "FAIL"
        evidence = text[:500] if audit.get("ok") else audit.get("error", "missing evidence")
        content = f"""# Evaluation Report

## Iteration

{iteration}

## Verdict

{verdict}

## Contract Criteria Results

| Criterion | Result | Evidence | Notes |
|---|---|---|---|
| Workspace and app route can be actively inspected | {"PASS" if puppeteer_ok else "FAIL"} | {evidence} | Puppeteer get_page_text result |
| Page exposes requested product identity | {"PASS" if product_identity_ok else "FAIL"} | Expected `{brand}` | Required visible proof |
| Page communicates deployment value when requested | {"PASS" if deployment_ok else "FAIL"} | deploy/deployment language | Required only for deployment goals |
| Page communicates Android/mobile app value when requested | {"PASS" if android_ok else "FAIL"} | android/mobile/app language | Required only for mobile goals |
| Page communicates marketplace/business succession value when requested | {"PASS" if marketplace_ok else "FAIL"} | business sell/buyer/retirement language | Required only for succession goals |
| Page communicates model gateway/provider value | {"PASS" if model_gateway_ok else "FAIL"} | model gateway/provider/fallback language | Required when goal asks for model gateway |
| Primary CTA responds to click | {"PASS" if cta_ok else "FAIL"} | Preview generated | Puppeteer clicked #primary-action |
| Desktop layout has no horizontal overflow | {"PASS" if desktop_layout_ok else "FAIL"} | {desktop_metrics} | 1366px viewport |
| Mobile layout has no horizontal overflow | {"PASS" if mobile_layout_ok else "FAIL"} | {mobile_metrics} | 390px viewport |
| Capabilities have enough concrete depth | {"PASS" if feature_depth_ok else "FAIL"} | feature count {desktop_metrics.get("featureCount", 0)} | At least 3 feature cards |
| Console has no critical errors | {"PASS" if console_clean else "FAIL"} | {audit.get("errors", [])} | Browser console inspection |
| Desktop and mobile screenshots captured | {"PASS" if screenshot_ok else "FAIL"} | {desktop_report_path}, {mobile_report_path} | Visual evidence |

## Design Review

Design Review: {"PASS" if design_review_passed else "FAIL"}

| Dimension | Score | Notes |
|---|---:|---|
| Design | {design_score}/5 | Product identity, hierarchy, responsiveness, and goal fit |
| Originality | {originality_score}/5 | Penalizes generic AI-page phrasing |
| Craft | {craft_score}/5 | Layout stability and section structure |
| Functionality | {functionality_score}/5 | Browser launch, CTA behavior, console health |

## Puppeteer Actions Performed

- audit `{self.config.app_base_url}`
- click `#primary-action`
- screenshot `{desktop_report_path}`
- screenshot `{mobile_report_path}`

## Console Errors

{audit.get("errors", [])}

## Screenshots Captured

- {desktop_report_path}
- {mobile_report_path}

## Bugs Found

{"None blocking." if passed else "Active browser evidence was incomplete or required goal-specific text was missing."}

## Reproduction Steps

1. Start the app with the contract startup command.
2. Navigate to `{self.config.app_base_url}`.
3. Capture page text, console errors, and screenshot.

## Required Fixes

{"None." if passed else "Ensure the app starts, renders the requested product identity and goal concepts, and has no critical console errors."}

## Severity

{"LOW" if passed else "HIGH"}

## Recommendation

{"CONTINUE" if passed else "CONTINUE"}

## Contract Excerpt

{contract[:1500]}
"""
        self.files.write_file("feedback/evaluation_report.md", content)
        self.files.append_file("traces/evaluator_trace.md", f"\n## {datetime.now(UTC).isoformat()}\nEvaluated iteration {iteration}: {verdict}.\n")
        return verdict

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


EVALUATOR_CRITIQUE_PROMPT = """Read the Generator's proposed test plan.

Return Markdown only with this exact structure:

# Evaluator Critique

## Verdict

Accepted for Contract: YES/NO

## Weak Criteria
## Missing Edge Cases
## Scope Problems
## Required Changes
## Minimum Granular Acceptance Criteria

Rules:
- Be harsh.
- Reject vague, non-computable, or non-Puppeteer-testable plans.
- Do not helpfully rewrite the whole app.
- Accept only if the plan can become a granular current sprint contract.

Proposed test plan:
{proposal}
"""


def _expected_brand(goals: str) -> str:
    import re

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


def _viewport_result(results: list[dict], name: str) -> dict:
    for result in results:
        if result.get("name") == name:
            return result
    return {}


def _score_design(
    *,
    product_identity_ok: bool,
    deployment_ok: bool,
    android_ok: bool,
    marketplace_ok: bool,
    model_gateway_ok: bool,
    cta_ok: bool,
    desktop_layout_ok: bool,
    mobile_layout_ok: bool,
    feature_depth_ok: bool,
) -> int:
    checks = [
        product_identity_ok,
        deployment_ok,
        android_ok,
        marketplace_ok,
        model_gateway_ok,
        cta_ok,
        desktop_layout_ok,
        mobile_layout_ok,
        feature_depth_ok,
    ]
    return min(5, max(1, round(sum(checks) / len(checks) * 5)))


def _score_craft(desktop_metrics: dict, mobile_metrics: dict) -> int:
    checks = [
        int(desktop_metrics.get("buttonCount", 0) or 0) >= 2,
        int(desktop_metrics.get("featureCount", 0) or 0) >= 3,
        int(desktop_metrics.get("sectionCount", 0) or 0) >= 2,
        not desktop_metrics.get("hasHorizontalOverflow", True),
        not mobile_metrics.get("hasHorizontalOverflow", True),
    ]
    return min(5, max(1, round(sum(checks) / len(checks) * 5)))


def _score_originality(text: str) -> int:
    generic_phrases = [
        "supercharge your workflow",
        "unlock your potential",
        "revolutionize",
        "seamless experience",
        "next generation platform",
    ]
    lowered = text.lower()
    penalty = sum(1 for phrase in generic_phrases if phrase in lowered)
    return max(1, 5 - penalty)


def _score_functionality(puppeteer_ok: bool, cta_ok: bool, console_clean: bool) -> int:
    checks = [puppeteer_ok, cta_ok, console_clean]
    return min(5, max(1, round(sum(checks) / len(checks) * 5)))
