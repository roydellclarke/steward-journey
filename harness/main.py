"""CLI for the adversarial agent harness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from harness.config import HarnessConfig
from harness.connector_vault import ConnectorVault
from harness.doctor import Doctor
from harness.job_registry import JobRegistry
from harness.prefect_adapter import prefect_capability, run_job_with_optional_prefect
from harness.memory import MemoryIndex
from harness.orchestrator import Orchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-harness")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    run = sub.add_parser("run")
    run.add_argument("--goals", required=True, help="Path to Markdown goals file.")
    sub.add_parser("status")
    sub.add_parser("resume")
    abort = sub.add_parser("abort")
    abort.add_argument("--reason", default="manual abort")
    sub.add_parser("report")
    sub.add_parser("doctor")
    sub.add_parser("memory-index")
    job_create = sub.add_parser("job-create")
    job_create.add_argument("--name", required=True)
    job_create.add_argument("--kind", default="harness_goal")
    job_create.add_argument("--goal", default="")
    job_create.add_argument("--payload-json", default="")
    job_create.add_argument("--schedule", default=None)
    job_create.add_argument("--approval-required", action="store_true")
    sub.add_parser("jobs")
    job_approve = sub.add_parser("job-approve")
    job_approve.add_argument("--job-id", required=True)
    job_run = sub.add_parser("job-run")
    job_run.add_argument("--job-id", required=True)
    sub.add_parser("scheduler-status")
    connector_add = sub.add_parser("connector-add-meta")
    connector_add.add_argument("--name", required=True)
    connector_add.add_argument("--page-id", required=True)
    connector_add.add_argument("--token-env-var", default="META_PAGE_ACCESS_TOKEN")
    sub.add_parser("connectors")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    orchestrator = Orchestrator(HarnessConfig.from_env())

    if args.command == "init":
        orchestrator.init_workspace()
        print(f"Initialized workspace at {orchestrator.config.workspace_root}")
    elif args.command == "run":
        print(orchestrator.run(Path(args.goals).resolve()))
    elif args.command == "status":
        print(orchestrator.status())
    elif args.command == "resume":
        print(orchestrator.resume())
    elif args.command == "abort":
        print(orchestrator.abort(args.reason))
    elif args.command == "report":
        print(orchestrator.report())
    elif args.command == "doctor":
        for check in Doctor(orchestrator.config).run():
            print(f"{check.status:4} {check.name}: {check.detail}")
    elif args.command == "memory-index":
        orchestrator.init_workspace()
        docs = MemoryIndex(orchestrator.config.workspace_root).build_manifest()
        print(f"Indexed manifest entries: {len(docs)}")
    elif args.command == "job-create":
        orchestrator.init_workspace()
        payload = json.loads(args.payload_json) if args.payload_json else {}
        if args.goal:
            payload["goal"] = args.goal
        job = JobRegistry(orchestrator.config.workspace_root).create_job(
            name=args.name,
            kind=args.kind,
            payload=payload,
            schedule=args.schedule,
            approval_required=args.approval_required,
        )
        print(json.dumps(job.to_dict(), indent=2))
    elif args.command == "jobs":
        orchestrator.init_workspace()
        jobs = JobRegistry(orchestrator.config.workspace_root).list_jobs()
        print(json.dumps([job.to_dict() for job in jobs], indent=2))
    elif args.command == "job-approve":
        orchestrator.init_workspace()
        job = JobRegistry(orchestrator.config.workspace_root).approve_job(args.job_id)
        print(json.dumps(job.to_dict(), indent=2))
    elif args.command == "job-run":
        orchestrator.init_workspace()
        print(run_job_with_optional_prefect(orchestrator.config, args.job_id))
    elif args.command == "scheduler-status":
        capability = prefect_capability()
        print(json.dumps({"prefect_available": capability.available, "detail": capability.detail}, indent=2))
    elif args.command == "connector-add-meta":
        orchestrator.init_workspace()
        connector = ConnectorVault(orchestrator.config.workspace_root).upsert_meta_pages(
            name=args.name,
            page_id=args.page_id,
            token_env_var=args.token_env_var,
        )
        print(json.dumps(connector.to_dict(), indent=2))
    elif args.command == "connectors":
        orchestrator.init_workspace()
        connectors = ConnectorVault(orchestrator.config.workspace_root).list_connectors()
        print(json.dumps([connector.to_dict() for connector in connectors], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
