"""FastAPI control plane for local and VPS deployments."""

from __future__ import annotations

from typing import Any

from harness.config import HarnessConfig
from harness.connector_vault import ConnectorVault
from harness.job_registry import JobRegistry
from harness.prefect_adapter import prefect_capability, run_job_with_optional_prefect
from harness.orchestrator import Orchestrator


try:  # pragma: no cover - exercised when FastAPI is installed.
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except Exception:  # FastAPI is optional in offline test mode.
    FastAPI = None
    HTTPException = None
    BaseModel = object
    Field = None


class JobCreateRequest(BaseModel):  # type: ignore[misc]
    name: str
    kind: str = "harness_goal"
    payload: dict[str, Any] = {}  # noqa: RUF012
    schedule: str | None = None
    approval_required: bool = False


class GoalRunRequest(BaseModel):  # type: ignore[misc]
    name: str = "Harness goal"
    goal: str
    schedule: str | None = None


def create_app(config: HarnessConfig | None = None):
    if FastAPI is None or HTTPException is None:
        raise RuntimeError("FastAPI is not installed. Install `agent-harness[api]` or use environment.yml.")

    cfg = config or HarnessConfig.from_env()
    orchestrator = Orchestrator(cfg)
    orchestrator.init_workspace()
    registry = JobRegistry(cfg.workspace_root)
    app = FastAPI(title="Agent Harness Control API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, Any]:
        capability = prefect_capability()
        return {
            "ok": True,
            "workspace": str(cfg.workspace_root),
            "prefect_available": capability.available,
        }

    @app.post("/jobs")
    def create_job(request: JobCreateRequest) -> dict[str, Any]:
        job = registry.create_job(
            name=request.name,
            kind=request.kind,
            payload=request.payload,
            schedule=request.schedule,
            approval_required=request.approval_required,
        )
        return job.to_dict()

    @app.post("/runs")
    def create_goal_run(request: GoalRunRequest) -> dict[str, Any]:
        job = registry.create_job(
            name=request.name,
            kind="scheduled_goal" if request.schedule else "harness_goal",
            payload={"goal": request.goal},
            schedule=request.schedule,
        )
        return job.to_dict()

    @app.get("/jobs")
    def list_jobs() -> list[dict[str, Any]]:
        return [job.to_dict() for job in registry.list_jobs()]

    @app.get("/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, Any]:
        try:
            return registry.get_job(job_id).to_dict()
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/jobs/{job_id}/approve")
    def approve_job(job_id: str) -> dict[str, Any]:
        try:
            return registry.approve_job(job_id).to_dict()
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/jobs/{job_id}/run")
    def run_job(job_id: str) -> dict[str, Any]:
        try:
            output = run_job_with_optional_prefect(cfg, job_id)
            return {"job_id": job_id, "output": output}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.get("/runs")
    def list_runs() -> list[dict[str, Any]]:
        runs: list[dict[str, Any]] = []
        for job in registry.list_jobs():
            for run in job.runs:
                item = run.to_dict()
                item["job_id"] = job.job_id
                item["job_name"] = job.name
                runs.append(item)
        return runs

    @app.get("/artifacts")
    def list_artifacts() -> dict[str, list[str]]:
        roots = ["reports", "feedback", "state", "screenshots", "src"]
        artifacts: dict[str, list[str]] = {}
        for root in roots:
            base = cfg.workspace_root / root
            if base.exists():
                artifacts[root] = [str(path.relative_to(cfg.workspace_root)) for path in base.rglob("*") if path.is_file()]
            else:
                artifacts[root] = []
        return artifacts

    @app.get("/connectors")
    def list_connectors() -> dict[str, Any]:
        return {"connectors": [connector.to_dict() for connector in ConnectorVault(cfg.workspace_root).list_connectors()]}

    return app


app = create_app() if FastAPI is not None else None
