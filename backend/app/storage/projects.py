"""File-backed StewardPath project storage.

Upgrade additions (all backward compatible — existing callers keep working):
- durable per-owner ``intakeState`` (the structured source of truth), migrated
  forward by ``schemaVersion`` on read,
- longitudinal ``meta.snapshots`` appended on each scored analysis,
- ``intakeSnapshot`` captured alongside each analysis entry,
- data-control operations: full export and hard delete,
- an append-only audit log of access/sharing/deletion events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import shutil
from typing import Any
from uuid import uuid4

from app.storage.audit import AuditLog
from app.storage.intake_state import (
    append_snapshot,
    merge_intake_patch,
    migrate_profile_to_intake_state,
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _assert_project_id(project_id: str) -> None:
    if not re.match(r"^[a-zA-Z0-9_-]+$", project_id or ""):
        raise ValueError("Invalid project id.")


def _read_json(path: Path, fallback: Any = None) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


@dataclass
class ProjectStore:
    root: Path
    audit: AuditLog = field(init=False)

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.audit = AuditLog(self.root)

    def project_dir(self, project_id: str) -> Path:
        _assert_project_id(project_id)
        return self.root / "projects" / project_id

    # ------------------------------------------------------------------ intake
    def read_intake_state(self, project_id: str) -> dict[str, Any] | None:
        existing = _read_json(self.project_dir(project_id) / "intake_state.json")
        if existing is None:
            return None
        # Always migrate forward on read so older schemaVersions stay valid.
        return migrate_profile_to_intake_state(None, existing)

    def save_intake_state(self, project_id: str, state: dict[str, Any]) -> dict[str, Any] | None:
        if not self.get_project(project_id):
            return None
        migrated = migrate_profile_to_intake_state(None, state)
        _write_json(self.project_dir(project_id) / "intake_state.json", migrated)
        self.audit.record("intake_saved", project_id=project_id,
                          detail={"completionPct": migrated["meta"]["completionPct"]})
        return migrated

    def _seed_intake_state(self, project_id: str, profile: dict[str, Any], intake_state: dict[str, Any] | None) -> dict[str, Any]:
        existing = _read_json(self.project_dir(project_id) / "intake_state.json")
        if intake_state:
            state = migrate_profile_to_intake_state(profile, {**(existing or {}), **intake_state} if existing else intake_state)
        else:
            state = migrate_profile_to_intake_state(profile, existing)
        _write_json(self.project_dir(project_id) / "intake_state.json", state)
        return state

    # ----------------------------------------------------------------- projects
    def create_project(self, *, name: str, profile: dict[str, Any], intake_state: dict[str, Any] | None = None) -> dict[str, Any]:
        timestamp = _now()
        project_id = str(uuid4())
        project = {
            "id": project_id,
            "name": name.strip() or profile.get("businessName") or profile.get("business_name") or "Untitled StewardPath project",
            "createdAt": timestamp,
            "updatedAt": timestamp,
            "latestAnalysisId": None,
            "analysisCount": 0,
        }
        directory = self.project_dir(project_id)
        _write_json(directory / "project.json", project)
        _write_json(directory / "profile.json", profile)
        (directory / "exports").mkdir(parents=True, exist_ok=True)
        state = self._seed_intake_state(project_id, profile, intake_state)
        self.audit.record("project_created", project_id=project_id, detail={"name": project["name"]})
        return {**project, "profile": profile, "intakeState": state}

    def list_projects(self) -> list[dict[str, Any]]:
        base = self.root / "projects"
        base.mkdir(parents=True, exist_ok=True)
        projects = [self.get_project(path.name) for path in base.iterdir() if path.is_dir()]
        return sorted([project for project in projects if project], key=lambda item: item["updatedAt"], reverse=True)

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        directory = self.project_dir(project_id)
        project = _read_json(directory / "project.json")
        if not project:
            return None
        profile = _read_json(directory / "profile.json", {})
        intake_raw = _read_json(directory / "intake_state.json")
        intake_state = migrate_profile_to_intake_state(None, intake_raw) if intake_raw else None
        return {**project, "profile": profile, "intakeState": intake_state}

    def update_project(
        self,
        project_id: str,
        *,
        name: str | None,
        profile: dict[str, Any] | None,
        intake_state: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        current = self.get_project(project_id)
        if not current:
            return None
        project = {
            "id": current["id"],
            "name": (name or current["name"]).strip() or current["name"],
            "createdAt": current["createdAt"],
            "updatedAt": _now(),
            "latestAnalysisId": current.get("latestAnalysisId"),
            "analysisCount": current.get("analysisCount", 0),
        }
        next_profile = profile if profile is not None else current.get("profile", {})
        directory = self.project_dir(project_id)
        _write_json(directory / "project.json", project)
        _write_json(directory / "profile.json", next_profile)

        next_state = current.get("intakeState")
        if intake_state is not None:
            # Treat incoming intake_state as a patch onto the durable record.
            base = current.get("intakeState") or migrate_profile_to_intake_state(next_profile, None)
            next_state = merge_intake_patch(base, intake_state)
            _write_json(directory / "intake_state.json", next_state)
            self.audit.record("intake_saved", project_id=project_id,
                              detail={"completionPct": next_state["meta"]["completionPct"]})
        return {**project, "profile": next_profile, "intakeState": next_state}

    # ----------------------------------------------------------------- analyses
    def append_analysis(
        self,
        project_id: str,
        *,
        profile_snapshot: dict[str, Any],
        analysis: dict[str, Any],
        intake_snapshot: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        current = self.get_project(project_id)
        if not current:
            return None
        timestamp = _now()
        readiness = ((analysis or {}).get("readiness") or {}).get("overall")
        entry = {
            "analysisId": str(uuid4()),
            "projectId": project_id,
            "createdAt": timestamp,
            "profileSnapshot": profile_snapshot or current.get("profile", {}),
            "intakeSnapshot": intake_snapshot or current.get("intakeState"),
            "analysis": analysis,
            "readinessScore": readiness,
            "analysisSource": analysis.get("analysis_source") or analysis.get("analysisSource") or "unknown",
            "llmModels": analysis.get("llm_models") or analysis.get("llmModels") or {},
            "llmErrors": analysis.get("llm_errors") or analysis.get("llmErrors") or [],
            "version": "stewardpath-backend-2",
        }
        directory = self.project_dir(project_id)
        with (directory / "analyses.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
        _write_json(directory / "latest_analysis.json", entry)

        # Longitudinal snapshot on the durable intake state (change-over-time).
        state = current.get("intakeState")
        if state is not None and readiness is not None:
            state = append_snapshot(state, readiness)
            _write_json(directory / "intake_state.json", state)

        project = {
            "id": current["id"],
            "name": current["name"],
            "createdAt": current["createdAt"],
            "updatedAt": timestamp,
            "latestAnalysisId": entry["analysisId"],
            "analysisCount": int(current.get("analysisCount", 0)) + 1,
        }
        _write_json(directory / "project.json", project)
        _write_json(directory / "profile.json", entry["profileSnapshot"])
        self.audit.record("analysis_saved", project_id=project_id,
                          detail={"readinessScore": readiness, "source": entry["analysisSource"]})
        return entry

    def list_analyses(self, project_id: str) -> list[dict[str, Any]]:
        path = self.project_dir(project_id) / "analyses.jsonl"
        if not path.exists():
            return []
        entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return sorted(entries, key=lambda item: item["createdAt"], reverse=True)

    def latest_analysis(self, project_id: str) -> dict[str, Any] | None:
        return _read_json(self.project_dir(project_id) / "latest_analysis.json")

    def snapshots(self, project_id: str) -> list[dict[str, Any]]:
        state = self.read_intake_state(project_id)
        return list((state or {}).get("meta", {}).get("snapshots", []))

    # ------------------------------------------------------------- data control
    def export_project(self, project_id: str) -> dict[str, Any] | None:
        """Everything stored for a project, for the owner's "your data" export."""

        project = self.get_project(project_id)
        if not project:
            return None
        self.audit.record("exported", project_id=project_id)
        return {
            "exportedAt": _now(),
            "project": {k: v for k, v in project.items() if k != "intakeState"},
            "intakeState": project.get("intakeState"),
            "analyses": self.list_analyses(project_id),
            "auditEvents": self.audit.events(project_id),
        }

    def delete_project(self, project_id: str) -> bool:
        """Hard delete: remove all stored data for a project. Irreversible."""

        directory = self.project_dir(project_id)
        if not directory.exists():
            return False
        shutil.rmtree(directory)
        # Audit entry persists after deletion (metadata only, no sensitive data).
        self.audit.record("deleted", project_id=project_id)
        return True

    # --------------------------------------------------------------------- leads
    def append_lead(self, lead: dict[str, Any]) -> dict[str, Any]:
        entry = {
            "id": str(uuid4()),
            "createdAt": _now(),
            "name": lead.get("name", ""),
            "email": lead.get("email", ""),
            "businessType": lead.get("businessType", ""),
            "timeline": lead.get("timeline", ""),
            "role": lead.get("role", ""),
            "intent": lead.get("intent", "general"),
        }
        path = self.root / "leads" / "leads.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
        return entry

    def list_leads(self) -> list[dict[str, Any]]:
        path = self.root / "leads" / "leads.jsonl"
        if not path.exists():
            return []
        entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return sorted(entries, key=lambda item: item["createdAt"], reverse=True)

    # -------------------------------------------------------------------- orders
    def _orders_path(self) -> Path:
        return self.root / "orders" / "orders.jsonl"

    def append_order(self, order: dict[str, Any]) -> dict[str, Any]:
        """Record a checkout intent. Status starts 'pending' until Stripe confirms."""

        entry = {
            "id": str(uuid4()),
            "createdAt": _now(),
            "product": order.get("product", ""),
            "amountCents": int(order.get("amountCents", 0)),
            "mode": order.get("mode", "payment"),
            "status": order.get("status", "pending"),
            "stripeSessionId": order.get("stripeSessionId", ""),
            "email": order.get("email", ""),
            "projectId": order.get("projectId") or "",
            "paidAt": order.get("paidAt") or "",
        }
        path = self._orders_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
        return entry

    def list_orders(self) -> list[dict[str, Any]]:
        path = self._orders_path()
        if not path.exists():
            return []
        entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return sorted(entries, key=lambda item: item["createdAt"], reverse=True)

    def get_order_by_session(self, session_id: str) -> dict[str, Any] | None:
        for entry in self.list_orders():
            if entry.get("stripeSessionId") == session_id:
                return entry
        return None

    def mark_order_paid(self, session_id: str, *, email: str = "") -> tuple[dict[str, Any] | None, bool]:
        """Flip an order to 'paid'. Returns (order, newly_paid).

        Idempotent: a second call on an already-paid order returns
        ``newly_paid=False`` so the confirmation email is sent only once. The
        orders file is small, so a read-modify-write rewrite is fine here.
        """

        path = self._orders_path()
        if not path.exists():
            return None, False
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        found: dict[str, Any] | None = None
        newly_paid = False
        for row in rows:
            if row.get("stripeSessionId") == session_id:
                found = row
                if row.get("status") != "paid":
                    row["status"] = "paid"
                    row["paidAt"] = _now()
                    newly_paid = True
                if email and not row.get("email"):
                    row["email"] = email
                break
        if found is None:
            return None, False
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")
        return found, newly_paid
