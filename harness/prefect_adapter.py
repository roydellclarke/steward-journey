"""Optional Prefect integration for background jobs and schedules."""

from __future__ import annotations

from dataclasses import dataclass

from harness.config import HarnessConfig
from harness.job_runner import run_registered_job


try:  # pragma: no cover - covered through capability checks when installed.
    from prefect import flow, task
except Exception:  # Prefect is optional for local offline testing.
    flow = None
    task = None


@dataclass(frozen=True)
class PrefectCapability:
    available: bool
    detail: str


def prefect_capability() -> PrefectCapability:
    if flow is None or task is None:
        return PrefectCapability(
            available=False,
            detail="Prefect is not installed. Install the `scheduler` extra or use the synchronous job runner.",
        )
    return PrefectCapability(available=True, detail="Prefect is available.")


def run_job_with_optional_prefect(config: HarnessConfig, job_id: str) -> str:
    """Run through Prefect if installed, otherwise use the local runner."""

    if flow is None or task is None:
        return run_registered_job(config, job_id)
    return _prefect_run_job(config, job_id)


if flow is not None and task is not None:  # pragma: no cover

    @task(retries=2, retry_delay_seconds=10)
    def _prefect_task(config: HarnessConfig, job_id: str) -> str:
        return run_registered_job(config, job_id)

    @flow(name="agent-harness-job")
    def _prefect_run_job(config: HarnessConfig, job_id: str) -> str:
        return _prefect_task(config, job_id)

else:

    def _prefect_run_job(config: HarnessConfig, job_id: str) -> str:
        return run_registered_job(config, job_id)

