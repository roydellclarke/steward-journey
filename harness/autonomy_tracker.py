"""Autonomy-duration logging."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


class AutonomyTracker:
    def __init__(self, workspace_root: Path) -> None:
        self.path = workspace_root / "state" / "autonomy_log.md"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def start(self) -> None:
        if not self.path.exists():
            self.path.write_text(f"# Autonomy Log\n\n## Start Time\n\n{datetime.now(UTC).isoformat()}\n", encoding="utf-8")

    def finish(self, *, iterations: int, status: str, reason: str) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                f"\n## End Time\n\n{datetime.now(UTC).isoformat()}\n"
                f"\n## Iterations Completed\n\n{iterations}\n"
                f"\n## Sprint Status\n\n{status}\n"
                f"\n## Completion / Abort Reason\n\n{reason}\n"
            )
