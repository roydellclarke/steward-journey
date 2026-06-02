"""Cost tracking with provider-usage placeholders."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import json


class CostTracker:
    def __init__(self, workspace_root: Path) -> None:
        self.path = workspace_root / "state" / "cost_log.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def cumulative_cost(self) -> float:
        entries = json.loads(self.path.read_text(encoding="utf-8"))
        if not entries:
            return 0.0
        return float(entries[-1]["cumulative_cost_usd"])

    def log_invocation(
        self,
        *,
        agent: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
    ) -> None:
        entries = json.loads(self.path.read_text(encoding="utf-8"))
        cumulative = (float(entries[-1]["cumulative_cost_usd"]) if entries else 0.0) + estimated_cost_usd
        entries.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "agent": agent,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost_usd": estimated_cost_usd,
                "cumulative_cost_usd": cumulative,
            }
        )
        self.path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
