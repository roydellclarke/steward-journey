"""Structured run events for production debugging."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from harness.privacy import redact_text


SECRET_MARKERS = ("API_KEY", "TOKEN", "SECRET", "PASSWORD", "BEARER", "AUTH")


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if _looks_secret(key) else redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str) and value.startswith(("sk-", "sk_")):
        return "[REDACTED]"
    if isinstance(value, str):
        return redact_text(value)
    return value


def _looks_secret(key: str) -> bool:
    upper = key.upper()
    return any(marker in upper for marker in SECRET_MARKERS)


class EventLogger:
    def __init__(self, workspace_root: Path) -> None:
        self.path = workspace_root / "state" / "events.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        *,
        run_id: str,
        phase: str,
        event: str,
        agent: str | None = None,
        iteration: int = 0,
        details: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "run_id": run_id,
            "phase": phase,
            "event": event,
            "agent": agent,
            "iteration": iteration,
            "details": redact(details or {}),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
