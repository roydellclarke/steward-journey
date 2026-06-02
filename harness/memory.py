"""Safe semantic-memory indexing interface.

This is intentionally dependency-light. It creates a redacted manifest of files
that are safe to index. A future Zvec adapter can consume this manifest and
store embeddings without changing the privacy boundary.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path

from harness.privacy import is_sensitive_path, redact_text
from harness.security_policy import SecurityPolicy


INDEXABLE_SUFFIXES = {".md", ".json", ".html", ".js", ".txt"}


@dataclass(frozen=True)
class MemoryDocument:
    path: str
    trust_label: str
    chars: int
    indexed_at: str
    preview: str


class MemoryIndex:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        self.manifest_path = workspace_root / "state" / "memory_manifest.json"
        self.policy = SecurityPolicy(workspace_root)

    def build_manifest(self) -> list[MemoryDocument]:
        documents: list[MemoryDocument] = []
        for path in sorted(self.workspace_root.rglob("*")):
            if not path.is_file() or path.suffix not in INDEXABLE_SUFFIXES:
                continue
            relative = str(path.relative_to(self.workspace_root))
            if is_sensitive_path(path, self.workspace_root):
                continue
            if not self.policy.can_send_to_llm(relative).allowed:
                continue
            text = redact_text(path.read_text(encoding="utf-8", errors="replace"))
            record = self.policy.trust.get(relative)
            documents.append(
                MemoryDocument(
                    path=relative,
                    trust_label=record.label if record else "unknown",
                    chars=len(text),
                    indexed_at=datetime.now(UTC).isoformat(),
                    preview=text[:500],
                )
            )
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps([asdict(doc) for doc in documents], indent=2), encoding="utf-8")
        return documents
