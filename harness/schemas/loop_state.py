"""Loop state persisted by the orchestrator."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass
class LoopState:
    phase: str = "INIT"
    run_id: str = field(default_factory=lambda: uuid4().hex)
    sprint_id: str = "sprint-001"
    total_iterations: int = 0
    sprint_iterations: int = 0
    contract_handshake_rounds: int = 0
    repeated_failure_count: int = 0
    cumulative_cost_usd: float = 0.0
    divergence_score: float = 0.0
    latest_verdict: str = "NONE"
    latest_recommendation: str = "CONTINUE"
    design_review_passed: bool = False
    completion_blocker: str = ""
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    hyperknobs: dict[str, Any] = field(default_factory=dict)
    models: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        self.updated_at = datetime.now(UTC).isoformat()
        return asdict(self)
