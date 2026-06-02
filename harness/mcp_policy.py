"""Guardrails for future MCP tool integrations."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


DEFAULT_MCP_POLICY = {
    "version": 1,
    "default": "deny",
    "rules": [
        {
            "server": "filesystem",
            "tool": "read_file",
            "agents": ["planner", "generator", "evaluator"],
            "decision": "allow",
            "notes": "Workspace-scoped reads only."
        },
        {
            "server": "filesystem",
            "tool": "write_file",
            "agents": ["planner", "generator", "evaluator"],
            "decision": "allow",
            "notes": "Workspace-scoped writes only."
        },
        {
            "server": "browser",
            "tool": "puppeteer_*",
            "agents": ["evaluator"],
            "decision": "allow",
            "notes": "Only Evaluator may actively validate browser state."
        }
    ]
}


@dataclass(frozen=True)
class McpDecision:
    allowed: bool
    reason: str


class McpPolicy:
    def __init__(self, workspace_root: Path) -> None:
        self.path = workspace_root / "state" / "mcp_policy.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps(DEFAULT_MCP_POLICY, indent=2), encoding="utf-8")

    def can_use(self, *, agent: str, server: str, tool: str) -> McpDecision:
        policy = json.loads(self.path.read_text(encoding="utf-8"))
        for rule in policy.get("rules", []):
            if rule.get("server") != server:
                continue
            if not _tool_matches(rule.get("tool", ""), tool):
                continue
            if agent not in rule.get("agents", []):
                continue
            return McpDecision(rule.get("decision") == "allow", rule.get("notes", "matched rule"))
        return McpDecision(False, "default deny")


def _tool_matches(pattern: str, tool: str) -> bool:
    if pattern.endswith("*"):
        return tool.startswith(pattern[:-1])
    return pattern == tool
