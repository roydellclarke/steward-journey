"""Bounded loop-state decisions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from harness.config import HarnessConfig
from harness.schemas.loop_state import LoopState


@dataclass(frozen=True)
class StopDecision:
    should_stop: bool
    reason: str = ""


class LoopController:
    def __init__(self, config: HarnessConfig) -> None:
        self.config = config

    def stop_reason(self, state: LoopState) -> StopDecision:
        if state.total_iterations >= self.config.max_total_iterations:
            return StopDecision(True, "maximum total iterations reached")
        if state.sprint_iterations >= self.config.max_iterations_per_sprint:
            return StopDecision(True, "maximum sprint iterations reached")
        if state.contract_handshake_rounds >= self.config.max_contract_handshake_rounds:
            return StopDecision(True, "contract handshake limit reached")
        if state.cumulative_cost_usd >= self.config.max_cost_usd:
            return StopDecision(True, "maximum cost reached")
        if state.repeated_failure_count >= self.config.max_repeated_failure_count:
            return StopDecision(True, "repeated failure threshold reached")
        if state.divergence_score >= self.config.divergence_score_threshold:
            return StopDecision(True, "evaluator divergence threshold reached")
        started = datetime.fromisoformat(state.started_at)
        elapsed_minutes = (datetime.now(UTC) - started).total_seconds() / 60
        if elapsed_minutes >= self.config.max_wall_clock_minutes:
            return StopDecision(True, "maximum wall-clock time reached")
        return StopDecision(False)
