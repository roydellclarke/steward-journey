"""Execution helpers for jobs stored in the registry."""

from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Protocol

from harness.config import HarnessConfig
from harness.job_registry import ABORTED, FAILED, SUCCEEDED, JobRegistry
from harness.orchestrator import Orchestrator


class Publisher(Protocol):
    def publish(self, payload: dict) -> str:
        ...


def run_registered_job(config: HarnessConfig, job_id: str, publisher: Publisher | None = None) -> str:
    """Run one registry job and persist run history.

    The default supported job is `harness_goal`, which invokes the existing
    Planner -> Generator -> Evaluator loop. Publisher jobs are intentionally
    approval-gated and use an injected publisher so tests never call networks.
    """

    registry = JobRegistry(config.workspace_root)
    run = registry.start_run(job_id)
    job = registry.get_job(job_id)
    try:
        if job.kind in {"harness_goal", "scheduled_goal"}:
            output = _run_harness_goal(config, job.payload)
            status = SUCCEEDED if "# Completion Report" in output else ABORTED
            registry.finish_run(
                job_id,
                run.run_id,
                status=status,
                output=output,
                artifacts=["reports/completion_report.md" if status == SUCCEEDED else "reports/abort_report.md"],
            )
            return output

        if job.kind == "meta_publish":
            if publisher is None:
                raise RuntimeError("No publisher configured for meta_publish job.")
            output = publisher.publish(job.payload)
            registry.finish_run(job_id, run.run_id, status=SUCCEEDED, output=output, artifacts=["state/jobs.json"])
            return output

        raise ValueError(f"Unsupported job kind: {job.kind}")
    except Exception as exc:
        registry.finish_run(job_id, run.run_id, status=FAILED, error=str(exc))
        raise


def _run_harness_goal(config: HarnessConfig, payload: dict) -> str:
    goals = str(payload.get("goals") or payload.get("goal") or "").strip()
    if not goals:
        raise ValueError("Job payload must include `goal` or `goals`.")
    with tempfile.TemporaryDirectory(prefix="agent-harness-job-") as tmp:
        goals_path = Path(tmp) / "goals.md"
        goals_path.write_text(goals, encoding="utf-8")
        return Orchestrator(config).run(goals_path)

