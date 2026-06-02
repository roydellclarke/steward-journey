"""Main Orchestrator controller."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import time

from harness.agents.evaluator_agent import EvaluatorAgent
from harness.agents.generator_agent import GeneratorAgent
from harness.agents.planner_agent import PlannerAgent
from harness.autonomy_tracker import AutonomyTracker
from harness.config import HarnessConfig
from harness.cost_tracker import CostTracker
from harness.divergence import DivergenceScorer
from harness.loop_controller import LoopController
from harness.observability import EventLogger
from harness.schemas.loop_state import LoopState
from harness.tools.file_tools import FileTools
from harness.workspace import Workspace


class Orchestrator:
    def __init__(self, config: HarnessConfig) -> None:
        self.config = config
        self.workspace = Workspace(config)
        self.files = FileTools(config.workspace_root)
        self.cost = CostTracker(config.workspace_root)
        self.autonomy = AutonomyTracker(config.workspace_root)
        self.divergence = DivergenceScorer(config.workspace_root)
        self.events = EventLogger(config.workspace_root)
        self.controller = LoopController(config)
        self.planner = PlannerAgent(config, self.files)
        self.generator = GeneratorAgent(config, self.files)
        self.evaluator = EvaluatorAgent(config, self.files)

    def init_workspace(self) -> None:
        self.workspace.initialize()
        self._log_event(self._load_state_if_exists(), "workspace_initialized", details={"workspace": str(self.config.workspace_root)})

    def run(self, goals_path: Path) -> str:
        self.init_workspace()
        self.workspace.reset_run_state()
        self.workspace.save_goals(goals_path)
        self.autonomy.start()
        state = self._load_state()
        self._log_event(state, "run_started", details={"goals_path": str(goals_path)})

        self.planner.create_sprint_plan()
        self._log_agent_cost("planner", self.config.planner.model)
        self._log_event(state, "planner_completed", agent="planner")

        contract_ready = self._contract_handshake(state)
        if not contract_ready:
            return self._abort(state, "contract handshake failed")

        while True:
            stop = self.controller.stop_reason(state)
            if stop.should_stop:
                return self._abort(state, stop.reason)

            state.phase = "BUILD"
            state.total_iterations += 1
            state.sprint_iterations += 1
            self._save_state(state)
            self._log_event(state, "build_started", agent="generator", iteration=state.total_iterations)

            self.generator.build_or_repair(state.total_iterations)
            self._log_agent_cost("generator", self.config.generator.model)
            self._log_event(state, "build_completed", agent="generator", iteration=state.total_iterations)

            state.phase = "EVALUATE"
            self._log_event(state, "evaluation_started", agent="evaluator", iteration=state.total_iterations)
            server = self._start_app_server()
            try:
                verdict = self.evaluator.evaluate(state.total_iterations)
            finally:
                if server.poll() is None:
                    server.terminate()
                    try:
                        server.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        server.kill()
            self.cost.log_invocation(agent="evaluator", model=self.config.evaluator.model)
            report = self.files.read_file("feedback/evaluation_report.md")
            state.divergence_score = self.divergence.score_report(report)
            state.latest_verdict = verdict
            state.design_review_passed = "Design Review: PASS" in report
            state.cumulative_cost_usd = self.cost.cumulative_cost()
            self._log_event(
                state,
                "evaluation_completed",
                agent="evaluator",
                iteration=state.total_iterations,
                details={"verdict": verdict, "design_review_passed": state.design_review_passed},
            )

            if state.total_iterations % self.config.context_reset_every_iterations == 0:
                self._write_handoff_summary(state)
                self._log_event(state, "context_handoff_written", iteration=state.total_iterations)

            if verdict == "PASS":
                state.repeated_failure_count = 0
                blocker = self._completion_blocker(state)
                if blocker:
                    state.completion_blocker = blocker
                    self._save_state(state)
                    self._log_event(state, "completion_blocked", details={"blocker": blocker})
                    continue
                state.completion_blocker = ""
                self._save_state(state)
                return self._complete(state)

            state.repeated_failure_count += 1
            self._save_state(state)
            self._log_event(state, "repair_required", details={"repeated_failure_count": state.repeated_failure_count})

    def _completion_blocker(self, state: LoopState) -> str:
        if state.sprint_iterations < self.config.min_iterations_per_sprint:
            return (
                "minimum sprint iterations not reached "
                f"({state.sprint_iterations}/{self.config.min_iterations_per_sprint})"
            )
        if self.config.require_design_review_pass and not state.design_review_passed:
            return "design review pass required"
        return ""

    def resume(self) -> str:
        goals = self.config.workspace_root / "goals" / "user_goals.md"
        if not goals.exists():
            raise FileNotFoundError("No saved goals found. Run with --goals first.")
        return self.run(goals)

    def status(self) -> str:
        self.init_workspace()
        return json.dumps(self._load_state().to_dict(), indent=2)

    def abort(self, reason: str = "manual abort") -> str:
        self.init_workspace()
        return self._abort(self._load_state(), reason)

    def report(self) -> str:
        completion = self.config.workspace_root / "reports" / "completion_report.md"
        abort = self.config.workspace_root / "reports" / "abort_report.md"
        if completion.exists():
            return completion.read_text(encoding="utf-8")
        if abort.exists():
            return abort.read_text(encoding="utf-8")
        return "No completion or abort report exists yet."

    def _contract_handshake(self, state: LoopState) -> bool:
        while state.contract_handshake_rounds < self.config.max_contract_handshake_rounds:
            state.phase = "CONTRACT_HANDSHAKE"
            state.contract_handshake_rounds += 1
            self.generator.propose_test_plan()
            self._log_agent_cost("generator", self.config.generator.model)
            self._log_event(state, "test_plan_proposed", agent="generator", details={"round": state.contract_handshake_rounds})
            accepted = self.evaluator.critique_test_plan()
            self._log_agent_cost("evaluator", self.config.evaluator.model)
            self._log_event(state, "test_plan_critiqued", agent="evaluator", details={"accepted": accepted, "round": state.contract_handshake_rounds})
            if accepted:
                self._write_current_contract()
                state.phase = "CONTRACT_READY"
                self._save_state(state)
                self._log_event(state, "contract_ready")
                return True
            self._save_state(state)
        return False

    def _write_current_contract(self) -> None:
        goals = self.files.read_file("goals/user_goals.md")
        content = f"""# Current Sprint Contract

## Sprint ID

sprint-001

## Sprint Objective

Create and validate a browser-visible landing page that reflects the user's
current goal.

## User Goal Excerpt

{goals[:1800]}

## Scope

- Generate `/workspace/src/index.html` and `/workspace/src/app.js`.
- Reflect the named product or system from the user goal.
- Include a clear hero, platform capabilities, target audience, and CTA.
- Mention deployment, Android, marketplace, or model gateway concepts when
  present in the goal.
- Validate the page through Puppeteer.

## Out of Scope

- Cloud LLM credentials.
- Backend implementation.
- Real deployment side effects.

## App Startup Command

```bash
python3 -m http.server 3000 --directory workspace/src
```

## Routes

- /

## Required User Flows

- Start the app.
- Navigate to `/`.
- Verify visible product identity and goal concepts.
- Click the landing-page CTA.
- Capture console errors.
- Capture a screenshot.

## Acceptance Criteria

### Functional Criteria

- [ ] A browser-visible app route exists at `/`.
- [ ] The page includes the product or system name from the user goal.
- [ ] The page includes the domain concepts requested by the goal.

### UX Criteria

- [ ] The page has a clear hero section.
- [ ] The page contains a clickable primary CTA.
- [ ] The page lists concrete capabilities.

### Design Criteria

- [ ] The page uses readable typography, spacing, and contrast.
- [ ] The page avoids placeholder slop and generic gradient abuse.

### Error Handling Criteria

- [ ] Console has no critical errors.
- [ ] Missing Puppeteer evidence prevents pass.

### Performance Criteria

- [ ] Initial page text is available within normal Puppeteer timeout.

## Puppeteer Validation Plan

- Navigate to the app URL.
- Read page text.
- Capture console errors.
- Capture screenshot.
- Map evidence to every criterion.

## Test Data

No external test data required.

## Failure Threshold

Fail on any missing Puppeteer evidence, missing requested product identity,
missing goal concepts, dead CTA, or critical console error.

## Done Definition

Only the Evaluator can mark this sprint passed after active Puppeteer
validation maps evidence to every required criterion.
"""
        self.files.write_file("contracts/current_sprint.md", content)
        self.files.append_file("contracts/contract_history.md", "\n\n" + content)

    def _log_agent_cost(self, agent: str, model: str) -> None:
        usage_path = self.config.workspace_root / "state" / f"{agent}_latest_usage.json"
        if not usage_path.exists():
            self.cost.log_invocation(agent=agent, model=model)
            return

        try:
            usage = json.loads(usage_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            usage = {}

        self.cost.log_invocation(
            agent=agent,
            model=model,
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            estimated_cost_usd=float(usage.get("estimated_cost_usd", 0.0)),
        )
        usage_path.unlink(missing_ok=True)

    def _start_app_server(self) -> subprocess.Popen:
        command = [
            "python3",
            "-m",
            "http.server",
            "3000",
            "--directory",
            str(self.config.workspace_root / "src"),
        ]
        server = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        return server

    def _write_handoff_summary(self, state: LoopState) -> None:
        report = self.files.read_file("feedback/evaluation_report.md") if self.files.exists("feedback/evaluation_report.md") else "No report."
        content = f"""# Handoff Summary

## Current Sprint

{state.sprint_id}

## Current Contract

/workspace/contracts/current_sprint.md

## Completed Work

See /workspace/state/build_log.md.

## Remaining Failures

{report[:1200]}

## Active Risks

- Repeated failures: {state.repeated_failure_count}
- Divergence score: {state.divergence_score}
- Cost: {state.cumulative_cost_usd}
- Completion blocker: {state.completion_blocker or "None"}

## Latest Evaluator Verdict

{state.latest_verdict}

## Next Required Action

Continue build-break loop unless a threshold stops execution.

## Files That Matter

- /workspace/contracts/current_sprint.md
- /workspace/feedback/evaluation_report.md
- /workspace/state/build_log.md
"""
        self.files.write_file("state/handoff_summary.md", content)

    def _complete(self, state: LoopState) -> str:
        state.phase = "COMPLETE"
        self._save_state(state)
        report = f"""# Completion Report

## Final Verdict

PASS

## Goals Completed

The harness completed the current sprint contract after Evaluator validation.

## Sprint Contracts Completed

- {state.sprint_id}

## Evidence

See /workspace/feedback/evaluation_report.md.

## Puppeteer Tests Performed

See the evaluation report's Puppeteer actions section.

## Screenshots

See /workspace/screenshots.

## Files Created or Modified

See /workspace/state/file_writes.log.

## Known Limitations

Provider token usage is logged through a placeholder interface until live model
usage metadata is wired.

## Cost Summary

{state.cumulative_cost_usd}

## Autonomy Duration

See /workspace/state/autonomy_log.md.

## How to Run the App

```bash
python3 -m http.server 3000 --directory workspace/src
```

## How to Run Tests

```bash
python3 -m unittest discover -s tests
```

## Recommended Next Improvements

- Wire real ADK Runner invocation.
- Add persistent browser sessions for multi-step Evaluator flows.
- Add provider-specific token accounting.
"""
        self.files.write_file("reports/completion_report.md", report)
        self.autonomy.finish(iterations=state.total_iterations, status="COMPLETE", reason="Evaluator passed contract")
        self._log_event(state, "run_completed", details={"iterations": state.total_iterations})
        return report

    def _abort(self, state: LoopState, reason: str) -> str:
        state.phase = "ABORT"
        self._save_state(state)
        report = f"""# Abort Report

## Reason for Abort

{reason}

## Final State

{state.phase}

## Iterations Completed

{state.total_iterations}

## Cost Used

{state.cumulative_cost_usd}

## Last Passing Criteria

See latest evaluation report if one exists.

## Last Failing Criteria

See /workspace/feedback/evaluation_report.md.

## Files Changed

See /workspace/state/file_writes.log.

## Recommended Next Step

Inspect the contract, build log, and evaluation report. Tighten the contract or
adjust hyperknobs before resuming.
"""
        self.files.write_file("reports/abort_report.md", report)
        self.autonomy.finish(iterations=state.total_iterations, status="ABORT", reason=reason)
        self._log_event(state, "run_aborted", details={"reason": reason, "iterations": state.total_iterations})
        return report

    def _load_state(self) -> LoopState:
        path = self.config.workspace_root / "state" / "loop_state.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        known = {field.name for field in LoopState.__dataclass_fields__.values()}
        filtered = {key: value for key, value in data.items() if key in known}
        return LoopState(**filtered)

    def _load_state_if_exists(self) -> LoopState:
        path = self.config.workspace_root / "state" / "loop_state.json"
        if not path.exists():
            return LoopState(hyperknobs=self.config.hyperknobs(), models=self.config.model_table())
        return self._load_state()

    def _save_state(self, state: LoopState) -> None:
        state.hyperknobs = self.config.hyperknobs()
        state.models = self.config.model_table()
        self.workspace.write_json("state/loop_state.json", state.to_dict())

    def _log_event(
        self,
        state: LoopState,
        event: str,
        *,
        agent: str | None = None,
        iteration: int | None = None,
        details: dict | None = None,
    ) -> None:
        self.events.log(
            run_id=state.run_id,
            phase=state.phase,
            event=event,
            agent=agent,
            iteration=state.total_iterations if iteration is None else iteration,
            details=details,
        )
