"""MCP server entrypoint for Claude Desktop and other local clients.

The module exposes a small, safe tool surface. It deliberately does not expose
generic filesystem read/write tools because the harness workspace is the trust
boundary.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

from harness.config import HarnessConfig
from harness.connector_vault import ConnectorVault
from harness.doctor import Doctor
from harness.job_registry import JobRegistry
from harness.prefect_adapter import run_job_with_optional_prefect
from harness.orchestrator import Orchestrator


ToolHandler = Callable[[dict[str, Any]], Any]


def tool_handlers(config: HarnessConfig | None = None) -> dict[str, ToolHandler]:
    cfg = config or HarnessConfig.from_env()

    def doctor(_: dict[str, Any]) -> dict[str, Any]:
        return {"checks": [check.__dict__ for check in Doctor(cfg).run()]}

    def status(_: dict[str, Any]) -> dict[str, Any]:
        output = Orchestrator(cfg).status()
        return json.loads(output)

    def create_job(args: dict[str, Any]) -> dict[str, Any]:
        Orchestrator(cfg).init_workspace()
        job = JobRegistry(cfg.workspace_root).create_job(
            name=str(args.get("name") or "MCP job"),
            kind=str(args.get("kind") or "harness_goal"),
            payload=dict(args.get("payload") or {}),
            schedule=args.get("schedule"),
            approval_required=bool(args.get("approval_required", False)),
        )
        return job.to_dict()

    def set_goal(args: dict[str, Any]) -> dict[str, Any]:
        goal = str(args.get("goal") or args.get("goals") or "").strip()
        if not goal:
            raise ValueError("`goal` is required.")
        orchestrator = Orchestrator(cfg)
        orchestrator.init_workspace()
        with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as handle:
            handle.write(goal)
            temp_path = handle.name
        try:
            orchestrator.workspace.save_goals(Path(temp_path))
        finally:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
        return {
            "path": "goals/user_goals.md",
            "characters": len(goal),
            "message": "Goal saved. Use harness_run_goal to run immediately or harness_create_job to schedule it.",
        }

    def run_goal(args: dict[str, Any]) -> dict[str, Any]:
        goal = str(args.get("goal") or "").strip()
        if not goal:
            raise ValueError("`goal` is required.")
        job = JobRegistry(cfg.workspace_root).create_job(
            name=str(args.get("name") or "MCP harness goal"),
            kind="harness_goal",
            payload={"goal": goal},
        )
        output = run_job_with_optional_prefect(cfg, job.job_id)
        return {"job": JobRegistry(cfg.workspace_root).get_job(job.job_id).to_dict(), "output": output}

    def list_jobs(_: dict[str, Any]) -> list[dict[str, Any]]:
        Orchestrator(cfg).init_workspace()
        return [job.to_dict() for job in JobRegistry(cfg.workspace_root).list_jobs()]

    def approve_job(args: dict[str, Any]) -> dict[str, Any]:
        return JobRegistry(cfg.workspace_root).approve_job(str(args["job_id"])).to_dict()

    def run_job(args: dict[str, Any]) -> dict[str, Any]:
        job_id = str(args["job_id"])
        output = run_job_with_optional_prefect(cfg, job_id)
        return {"job": JobRegistry(cfg.workspace_root).get_job(job_id).to_dict(), "output": output}

    def read_report(_: dict[str, Any]) -> dict[str, str]:
        return {"report": Orchestrator(cfg).report()}

    def list_artifacts(_: dict[str, Any]) -> dict[str, list[str]]:
        Orchestrator(cfg).init_workspace()
        artifacts: dict[str, list[str]] = {}
        for root in ["reports", "feedback", "state", "screenshots", "src"]:
            base = cfg.workspace_root / root
            artifacts[root] = [str(path.relative_to(cfg.workspace_root)) for path in base.rglob("*") if path.is_file()] if base.exists() else []
        return artifacts

    def add_meta_connector(args: dict[str, Any]) -> dict[str, Any]:
        Orchestrator(cfg).init_workspace()
        connector = ConnectorVault(cfg.workspace_root).upsert_meta_pages(
            name=str(args.get("name") or "Meta Pages"),
            page_id=str(args["page_id"]),
            token_env_var=str(args.get("token_env_var") or "META_PAGE_ACCESS_TOKEN"),
        )
        return connector.to_dict()

    def list_connectors(_: dict[str, Any]) -> list[dict[str, Any]]:
        Orchestrator(cfg).init_workspace()
        return [connector.to_dict() for connector in ConnectorVault(cfg.workspace_root).list_connectors()]

    return {
        "harness_doctor": doctor,
        "harness_status": status,
        "harness_set_goal": set_goal,
        "harness_create_job": create_job,
        "harness_run_goal": run_goal,
        "harness_list_jobs": list_jobs,
        "harness_approve_job": approve_job,
        "harness_run_job": run_job,
        "harness_read_report": read_report,
        "harness_list_artifacts": list_artifacts,
        "harness_add_meta_connector": add_meta_connector,
        "harness_list_connectors": list_connectors,
    }


TOOL_DESCRIPTIONS = {
    "harness_doctor": "Run preflight checks for the local harness.",
    "harness_status": "Read current loop state.",
    "harness_set_goal": "Save the current goal to the harness workspace without running it.",
    "harness_create_job": "Create a persistent harness job with optional schedule and approval gate.",
    "harness_run_goal": "Create and run a harness goal immediately.",
    "harness_list_jobs": "List persistent jobs and run history.",
    "harness_approve_job": "Approve a paused approval-gated job.",
    "harness_run_job": "Run an existing job by id.",
    "harness_read_report": "Read completion or abort report.",
    "harness_list_artifacts": "List generated workspace artifacts.",
    "harness_add_meta_connector": "Register a Meta Pages connector using an environment variable token reference.",
    "harness_list_connectors": "List configured connector metadata without exposing secrets.",
}


TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "harness_doctor": {"type": "object", "properties": {}, "additionalProperties": False},
    "harness_status": {"type": "object", "properties": {}, "additionalProperties": False},
    "harness_set_goal": {
        "type": "object",
        "properties": {
            "goal": {"type": "string"},
        },
        "required": ["goal"],
        "additionalProperties": False,
    },
    "harness_create_job": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "kind": {"type": "string"},
            "payload": {"type": "object"},
            "schedule": {"type": "string"},
            "approval_required": {"type": "boolean"},
        },
        "required": ["name"],
        "additionalProperties": True,
    },
    "harness_run_goal": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "goal": {"type": "string"},
        },
        "required": ["goal"],
        "additionalProperties": False,
    },
    "harness_list_jobs": {"type": "object", "properties": {}, "additionalProperties": False},
    "harness_approve_job": {
        "type": "object",
        "properties": {"job_id": {"type": "string"}},
        "required": ["job_id"],
        "additionalProperties": False,
    },
    "harness_run_job": {
        "type": "object",
        "properties": {"job_id": {"type": "string"}},
        "required": ["job_id"],
        "additionalProperties": False,
    },
    "harness_read_report": {"type": "object", "properties": {}, "additionalProperties": False},
    "harness_list_artifacts": {"type": "object", "properties": {}, "additionalProperties": False},
    "harness_add_meta_connector": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "page_id": {"type": "string"},
            "token_env_var": {"type": "string"},
        },
        "required": ["page_id"],
        "additionalProperties": False,
    },
    "harness_list_connectors": {"type": "object", "properties": {}, "additionalProperties": False},
}


def call_tool(name: str, args: dict[str, Any] | None = None, config: HarnessConfig | None = None) -> Any:
    handlers = tool_handlers(config)
    if name not in handlers:
        raise KeyError(f"Unknown MCP tool: {name}")
    return handlers[name](args or {})


def _run_official_mcp() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Official MCP package is not installed.") from exc

    server = FastMCP("agent-harness")

    @server.tool()
    def harness_doctor() -> str:
        """Run preflight checks for the local harness."""
        return json.dumps(call_tool("harness_doctor"), indent=2)

    @server.tool()
    def harness_status() -> str:
        """Read current loop state."""
        return json.dumps(call_tool("harness_status"), indent=2)

    @server.tool()
    def harness_set_goal(goal: str) -> str:
        """Save the current goal to the harness workspace without running it."""
        return json.dumps(call_tool("harness_set_goal", {"goal": goal}), indent=2)

    @server.tool()
    def harness_create_job(
        name: str,
        kind: str = "harness_goal",
        payload: dict[str, Any] | None = None,
        schedule: str | None = None,
        approval_required: bool = False,
    ) -> str:
        """Create a persistent harness job with optional schedule and approval gate."""
        return json.dumps(
            call_tool(
                "harness_create_job",
                {
                    "name": name,
                    "kind": kind,
                    "payload": payload or {},
                    "schedule": schedule,
                    "approval_required": approval_required,
                },
            ),
            indent=2,
        )

    @server.tool()
    def harness_run_goal(goal: str, name: str = "MCP harness goal") -> str:
        """Create and run a harness goal immediately."""
        return json.dumps(call_tool("harness_run_goal", {"goal": goal, "name": name}), indent=2)

    @server.tool()
    def harness_list_jobs() -> str:
        """List persistent jobs and run history."""
        return json.dumps(call_tool("harness_list_jobs"), indent=2)

    @server.tool()
    def harness_approve_job(job_id: str) -> str:
        """Approve a paused approval-gated job."""
        return json.dumps(call_tool("harness_approve_job", {"job_id": job_id}), indent=2)

    @server.tool()
    def harness_run_job(job_id: str) -> str:
        """Run an existing job by id."""
        return json.dumps(call_tool("harness_run_job", {"job_id": job_id}), indent=2)

    @server.tool()
    def harness_read_report() -> str:
        """Read completion or abort report."""
        return json.dumps(call_tool("harness_read_report"), indent=2)

    @server.tool()
    def harness_list_artifacts() -> str:
        """List generated workspace artifacts."""
        return json.dumps(call_tool("harness_list_artifacts"), indent=2)

    @server.tool()
    def harness_add_meta_connector(
        page_id: str,
        name: str = "Meta Pages",
        token_env_var: str = "META_PAGE_ACCESS_TOKEN",
    ) -> str:
        """Register a Meta Pages connector using an environment variable token reference."""
        return json.dumps(
            call_tool(
                "harness_add_meta_connector",
                {"page_id": page_id, "name": name, "token_env_var": token_env_var},
            ),
            indent=2,
        )

    @server.tool()
    def harness_list_connectors() -> str:
        """List configured connector metadata without exposing secrets."""
        return json.dumps(call_tool("harness_list_connectors"), indent=2)

    server.run()


def handle_mcp_request(request: dict[str, Any], config: HarnessConfig | None = None) -> dict[str, Any] | None:
    """Handle one JSON-RPC MCP request.

    This fallback implements the small MCP subset Claude Desktop needs for
    stdio tool discovery and tool calls. Notifications return `None` because
    JSON-RPC notifications must not receive responses.
    """

    method = request.get("method")
    request_id = request.get("id")

    if request_id is None and isinstance(method, str) and method.startswith("notifications/"):
        return None

    def response(result: dict[str, Any]) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    def error(code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    if method == "initialize":
        return response(
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "agent-harness", "version": "0.1.0"},
            }
        )

    if method == "ping":
        return response({})

    if method == "tools/list":
        tools = [
            {
                "name": name,
                "description": description,
                "inputSchema": TOOL_SCHEMAS.get(name, {"type": "object", "properties": {}}),
            }
            for name, description in TOOL_DESCRIPTIONS.items()
        ]
        return response({"tools": tools})

    if method == "tools/call":
        params = dict(request.get("params") or {})
        name = str(params.get("name") or "")
        args = dict(params.get("arguments") or {})
        try:
            result = call_tool(name, args, config)
        except Exception as exc:
            return response(
                {
                    "content": [{"type": "text", "text": str(exc)}],
                    "isError": True,
                }
            )
        return response(
            {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                "isError": False,
            }
        )

    if method in {"resources/list", "prompts/list"}:
        key = "resources" if method == "resources/list" else "prompts"
        return response({key: []})

    return error(-32601, f"Method not found: {method}")


def _run_json_lines_fallback() -> None:
    """MCP-over-stdio fallback for environments without the `mcp` package."""

    for line in sys.stdin:
        try:
            request = json.loads(line)
            result = handle_mcp_request(request)
            if result is None:
                continue
            sys.stdout.write(json.dumps(result) + "\n")
        except Exception as exc:  # pragma: no cover
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}) + "\n")
        sys.stdout.flush()


def self_test() -> dict[str, Any]:
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]
    responses = [response for request in requests if (response := handle_mcp_request(request)) is not None]
    return {
        "server_file": __file__,
        "jsonrpc_ok": all(response.get("jsonrpc") == "2.0" for response in responses),
        "tool_count": len(responses[-1]["result"]["tools"]),
        "responses": responses,
    }


def main() -> int:
    if "--self-test" in sys.argv:
        print(json.dumps(self_test(), indent=2))
        return 0
    if os.getenv("HARNESS_MCP_USE_SDK", "").strip().lower() not in {"1", "true", "yes", "on"}:
        _run_json_lines_fallback()
        return 0
    try:
        _run_official_mcp()
    except RuntimeError:
        _run_json_lines_fallback()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
