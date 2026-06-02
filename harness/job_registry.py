"""Persistent job registry for scheduled and background harness work."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from harness.privacy import redact_text


PENDING = "PENDING"
RUNNING = "RUNNING"
SUCCEEDED = "SUCCEEDED"
FAILED = "FAILED"
ABORTED = "ABORTED"
PAUSED = "PAUSED"

TERMINAL_STATUSES = {SUCCEEDED, FAILED, ABORTED}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class JobRun:
    run_id: str = field(default_factory=lambda: uuid4().hex)
    status: str = PENDING
    started_at: str | None = None
    finished_at: str | None = None
    output: str = ""
    error: str = ""
    artifacts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["output"] = redact_text(payload["output"])
        payload["error"] = redact_text(payload["error"])
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobRun":
        return cls(
            run_id=str(data.get("run_id") or uuid4().hex),
            status=str(data.get("status") or PENDING),
            started_at=data.get("started_at"),
            finished_at=data.get("finished_at"),
            output=str(data.get("output") or ""),
            error=str(data.get("error") or ""),
            artifacts=list(data.get("artifacts") or []),
        )


@dataclass
class Job:
    job_id: str = field(default_factory=lambda: uuid4().hex)
    name: str = "Untitled job"
    kind: str = "harness_goal"
    status: str = PENDING
    schedule: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    approval_required: bool = False
    approved: bool = False
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    next_run_at: str | None = None
    last_run_id: str | None = None
    runs: list[JobRun] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["payload"] = redact_payload(payload["payload"])
        payload["runs"] = [run.to_dict() for run in self.runs]
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        return cls(
            job_id=str(data.get("job_id") or uuid4().hex),
            name=str(data.get("name") or "Untitled job"),
            kind=str(data.get("kind") or "harness_goal"),
            status=str(data.get("status") or PENDING),
            schedule=data.get("schedule"),
            payload=dict(data.get("payload") or {}),
            approval_required=bool(data.get("approval_required", False)),
            approved=bool(data.get("approved", False)),
            created_at=str(data.get("created_at") or utc_now()),
            updated_at=str(data.get("updated_at") or utc_now()),
            next_run_at=data.get("next_run_at"),
            last_run_id=data.get("last_run_id"),
            runs=[JobRun.from_dict(item) for item in data.get("runs", [])],
        )


def redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON-safe payload with obvious secrets redacted."""

    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        lowered = key.lower()
        if any(marker in lowered for marker in ["password", "token", "secret", "api_key", "access_key"]):
            redacted[key] = "[REDACTED]"
        elif isinstance(value, str):
            redacted[key] = redact_text(value)
        elif isinstance(value, dict):
            redacted[key] = redact_payload(value)
        elif isinstance(value, list):
            redacted[key] = [redact_text(item) if isinstance(item, str) else item for item in value]
        else:
            redacted[key] = value
    return redacted


class JobRegistry:
    """Small durable job store backed by workspace/state/jobs.json."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        self.path = workspace_root / "state" / "jobs.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write([])

    def create_job(
        self,
        *,
        name: str,
        kind: str,
        payload: dict[str, Any],
        schedule: str | None = None,
        approval_required: bool = False,
    ) -> Job:
        job = Job(
            name=name,
            kind=kind,
            payload=payload,
            schedule=schedule,
            approval_required=approval_required,
            status=PAUSED if approval_required else PENDING,
        )
        jobs = self.list_jobs()
        jobs.append(job)
        self._write_jobs(jobs)
        return job

    def list_jobs(self) -> list[Job]:
        raw = self._read()
        return [Job.from_dict(item) for item in raw]

    def get_job(self, job_id: str) -> Job:
        for job in self.list_jobs():
            if job.job_id == job_id:
                return job
        raise KeyError(f"Unknown job: {job_id}")

    def update_job(self, job: Job) -> Job:
        job.updated_at = utc_now()
        jobs = self.list_jobs()
        for index, current in enumerate(jobs):
            if current.job_id == job.job_id:
                jobs[index] = job
                self._write_jobs(jobs)
                return job
        raise KeyError(f"Unknown job: {job.job_id}")

    def approve_job(self, job_id: str) -> Job:
        job = self.get_job(job_id)
        job.approved = True
        if job.status == PAUSED:
            job.status = PENDING
        return self.update_job(job)

    def start_run(self, job_id: str) -> JobRun:
        job = self.get_job(job_id)
        if job.approval_required and not job.approved:
            raise PermissionError("Job requires approval before execution.")
        run = JobRun(status=RUNNING, started_at=utc_now())
        job.status = RUNNING
        job.last_run_id = run.run_id
        job.runs.append(run)
        self.update_job(job)
        return run

    def finish_run(
        self,
        job_id: str,
        run_id: str,
        *,
        status: str,
        output: str = "",
        error: str = "",
        artifacts: list[str] | None = None,
    ) -> Job:
        if status not in {SUCCEEDED, FAILED, ABORTED}:
            raise ValueError(f"Invalid terminal run status: {status}")
        job = self.get_job(job_id)
        for run in job.runs:
            if run.run_id == run_id:
                run.status = status
                run.finished_at = utc_now()
                run.output = output
                run.error = error
                run.artifacts = artifacts or []
                job.status = status
                return self.update_job(job)
        raise KeyError(f"Unknown run: {run_id}")

    def _read(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def _write(self, payload: list[dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _write_jobs(self, jobs: list[Job]) -> None:
        self._write([job.to_dict() for job in jobs])

