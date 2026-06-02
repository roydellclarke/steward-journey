"""Trust labels for workspace artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path


TRUSTED = "trusted"
USER_PROVIDED = "user_provided"
GENERATED = "generated"
EXTERNAL = "external"
QUARANTINED = "quarantined"


@dataclass(frozen=True)
class TrustRecord:
    path: str
    label: str
    source: str
    updated_at: str
    notes: str = ""


class TrustStore:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        self.path = workspace_root / "state" / "trust_labels.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}\n", encoding="utf-8")

    def label(self, relative_path: str, label: str, *, source: str, notes: str = "") -> None:
        data = self._read()
        data[relative_path] = asdict(
            TrustRecord(
                path=relative_path,
                label=label,
                source=source,
                notes=notes,
                updated_at=datetime.now(UTC).isoformat(),
            )
        )
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def get(self, relative_path: str) -> TrustRecord | None:
        record = self._read().get(relative_path)
        return TrustRecord(**record) if record else None

    def _read(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
