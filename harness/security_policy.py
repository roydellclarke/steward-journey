"""CaMeL-lite security boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from harness.privacy import is_sensitive_path, redact_text
from harness.trust import EXTERNAL, QUARANTINED, USER_PROVIDED, TrustStore


UNTRUSTED_LABELS = {USER_PROVIDED, EXTERNAL, QUARANTINED}


@dataclass(frozen=True)
class SecurityDecision:
    allowed: bool
    reason: str


class SecurityPolicy:
    """Small policy layer inspired by dual-context prompt-injection defenses."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        self.trust = TrustStore(workspace_root)

    def can_send_to_llm(self, relative_path: str) -> SecurityDecision:
        if is_sensitive_path(self.workspace_root / relative_path, self.workspace_root):
            return SecurityDecision(False, "sensitive path")
        record = self.trust.get(relative_path)
        if record and record.label == QUARANTINED:
            return SecurityDecision(False, "quarantined content")
        return SecurityDecision(True, "allowed")

    def can_execute_tool_from_content(self, relative_path: str) -> SecurityDecision:
        record = self.trust.get(relative_path)
        if record and record.label in UNTRUSTED_LABELS:
            return SecurityDecision(False, f"untrusted content label: {record.label}")
        return SecurityDecision(True, "allowed")

    def quarantine_external_text(self, relative_path: str, content: str, *, source: str) -> str:
        safe_content = redact_text(content)
        target = self.workspace_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(safe_content, encoding="utf-8")
        self.trust.label(relative_path, QUARANTINED, source=source, notes="redacted external content")
        return str(target)
