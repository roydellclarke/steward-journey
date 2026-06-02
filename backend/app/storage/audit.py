"""Append-only audit log of access / sharing / deletion events.

Backs the Security & Confidentiality requirement: any access or sharing event is
recorded. The log stores event metadata only — never the sensitive payload — so
it is safe to retain even after a hard delete.
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(UTC).isoformat()


class AuditLog:
    def __init__(self, root: Path) -> None:
        self.path = root / "audit" / "events.jsonl"

    def record(
        self,
        action: str,
        *,
        project_id: str | None = None,
        actor: str = "owner",
        detail: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record an event. ``detail`` must contain only non-sensitive metadata."""

        entry = {
            "id": str(uuid4()),
            "at": _now(),
            "action": action,            # e.g. project_created, intake_saved, exported, deleted, sharing_changed
            "projectId": project_id,
            "actor": actor,
            "detail": detail or {},
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
        return entry

    def events(self, project_id: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if project_id:
            rows = [row for row in rows if row.get("projectId") == project_id]
        rows.sort(key=lambda row: row["at"], reverse=True)
        return rows[:limit]
