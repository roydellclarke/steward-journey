"""Connector registry that stores references to secrets, not raw secrets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Connector:
    connector_id: str = field(default_factory=lambda: uuid4().hex)
    provider: str = "meta_pages"
    name: str = "Meta Pages"
    status: str = "inactive"
    token_env_var: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["secret_storage"] = "env_reference_only"
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Connector":
        return cls(
            connector_id=str(data.get("connector_id") or uuid4().hex),
            provider=str(data.get("provider") or "meta_pages"),
            name=str(data.get("name") or "Meta Pages"),
            status=str(data.get("status") or "inactive"),
            token_env_var=str(data.get("token_env_var") or ""),
            config=dict(data.get("config") or {}),
            created_at=str(data.get("created_at") or _now()),
            updated_at=str(data.get("updated_at") or _now()),
        )


class ConnectorVault:
    """Workspace-local connector metadata store.

    The vault intentionally stores an environment variable name such as
    `META_PAGE_ACCESS_TOKEN`, not the token value. This keeps `.env` and shell
    secret handling as the only credential source.
    """

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        self.path = workspace_root / "state" / "connectors.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def upsert_meta_pages(self, *, name: str, page_id: str, token_env_var: str = "META_PAGE_ACCESS_TOKEN") -> Connector:
        if not token_env_var or any(marker in token_env_var.lower() for marker in ["sk-", "token="]):
            raise ValueError("Pass an environment variable name, not a raw access token.")
        connector = Connector(
            provider="meta_pages",
            name=name,
            status="active",
            token_env_var=token_env_var,
            config={"page_id": page_id, "requires_approval": True, "dry_run_default": True},
        )
        connectors = [item for item in self.list_connectors() if item.provider != "meta_pages" or item.name != name]
        connectors.append(connector)
        self._write(connectors)
        return connector

    def list_connectors(self) -> list[Connector]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raw = []
        return [Connector.from_dict(item) for item in raw]

    def get_connector(self, connector_id: str) -> Connector:
        for connector in self.list_connectors():
            if connector.connector_id == connector_id:
                return connector
        raise KeyError(f"Unknown connector: {connector_id}")

    def _write(self, connectors: list[Connector]) -> None:
        self.path.write_text(json.dumps([connector.to_dict() for connector in connectors], indent=2), encoding="utf-8")

