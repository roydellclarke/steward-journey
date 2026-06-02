"""A2A interoperability constraints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from uuid import uuid4


ALLOWED_MESSAGE_TYPES = {
    "sprint_spec",
    "test_plan",
    "critique",
    "build_log",
    "evaluation_report",
    "handoff_summary",
}


@dataclass(frozen=True)
class A2AMessage:
    message_id: str
    sender: str
    recipient: str
    message_type: str
    artifact_path: str
    created_at: str


class A2APolicy:
    def __init__(self, workspace_root: Path) -> None:
        self.path = workspace_root / "state" / "a2a_messages.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record_message(self, *, sender: str, recipient: str, message_type: str, artifact_path: str) -> A2AMessage:
        if message_type not in ALLOWED_MESSAGE_TYPES:
            raise ValueError(f"unsupported A2A message type: {message_type}")
        if not artifact_path or artifact_path.startswith("../") or "/../" in artifact_path:
            raise ValueError("A2A messages must reference workspace artifact paths")
        message = A2AMessage(
            message_id=uuid4().hex,
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            artifact_path=artifact_path,
            created_at=datetime.now(UTC).isoformat(),
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(message.__dict__, sort_keys=True) + "\n")
        return message
