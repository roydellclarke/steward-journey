"""Safe file-system tools used for inter-agent transport."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from harness.trust import GENERATED, TrustStore


@dataclass(frozen=True)
class FileTools:
    workspace_root: Path

    def _resolve(self, path: str | Path) -> Path:
        raw = Path(path)
        root = self.workspace_root.resolve()
        candidate = raw if raw.is_absolute() else root / raw
        resolved = candidate.resolve()
        if root != resolved and root not in resolved.parents:
            raise ValueError(f"path escapes workspace: {path}")
        return resolved

    def read_file(self, path: str | Path) -> str:
        return self._resolve(path).read_text(encoding="utf-8")

    def write_file(self, path: str | Path, content: str) -> str:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self._log_write(target, "write")
        self._label_write(target, "write")
        return str(target)

    def append_file(self, path: str | Path, content: str) -> str:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(content)
        self._log_write(target, "append")
        self._label_write(target, "append")
        return str(target)

    def list_directory(self, path: str | Path = ".") -> list[str]:
        target = self._resolve(path)
        return sorted(item.name for item in target.iterdir())

    def exists(self, path: str | Path) -> bool:
        return self._resolve(path).exists()

    def _log_write(self, target: Path, action: str) -> None:
        root = self.workspace_root.resolve()
        log_path = root / "state" / "file_writes.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).isoformat()
        rel = target.relative_to(root)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{timestamp} {action} {rel}\n")

    def _label_write(self, target: Path, action: str) -> None:
        root = self.workspace_root.resolve()
        try:
            rel = str(target.relative_to(root))
        except ValueError:
            return
        if rel.startswith("state/trust_labels.json"):
            return
        TrustStore(root).label(rel, GENERATED, source="file_tools", notes=action)
