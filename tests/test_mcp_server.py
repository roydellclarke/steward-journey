import tempfile
import unittest
from pathlib import Path

from harness.mcp_server import TOOL_DESCRIPTIONS, call_tool, handle_mcp_request, self_test
from harness.workspace import Workspace
from tests.test_workspace import config_for


class McpServerTests(unittest.TestCase):
    def test_exposes_safe_tool_catalog(self) -> None:
        self.assertIn("harness_create_job", TOOL_DESCRIPTIONS)
        self.assertIn("harness_list_artifacts", TOOL_DESCRIPTIONS)
        self.assertNotIn("read_file", TOOL_DESCRIPTIONS)
        self.assertNotIn("write_file", TOOL_DESCRIPTIONS)

    def test_can_create_and_list_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = config_for(root)
            Workspace(config).initialize()
            created = call_tool(
                "harness_create_job",
                {"name": "MCP scheduled goal", "payload": {"goal": "Build."}, "schedule": "0 9 * * *"},
                config,
            )
            listed = call_tool("harness_list_jobs", {}, config)
            self.assertEqual(created["name"], "MCP scheduled goal")
            self.assertEqual(len(listed), 1)

    def test_can_set_goal_without_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = config_for(root)
            Workspace(config).initialize()
            result = call_tool("harness_set_goal", {"goal": "Build a careful local app."}, config)
            saved = (root / "goals" / "user_goals.md").read_text(encoding="utf-8")
            self.assertEqual(result["path"], "goals/user_goals.md")
            self.assertIn("careful local app", saved)

    def test_fallback_initialize_uses_json_rpc_shape(self) -> None:
        response = handle_mcp_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], 1)
        self.assertEqual(response["result"]["serverInfo"]["name"], "agent-harness")

    def test_fallback_lists_tools_in_mcp_shape(self) -> None:
        response = handle_mcp_request({"jsonrpc": "2.0", "id": "tools", "method": "tools/list"})
        self.assertEqual(response["jsonrpc"], "2.0")
        tool_names = {tool["name"] for tool in response["result"]["tools"]}
        self.assertIn("harness_create_job", tool_names)
        self.assertIn("harness_set_goal", tool_names)
        self.assertIn("harness_status", tool_names)

    def test_fallback_calls_tool_with_content_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = config_for(root)
            Workspace(config).initialize()
            response = handle_mcp_request(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "harness_create_job",
                        "arguments": {"name": "JSON-RPC job", "payload": {"goal": "Build."}},
                    },
                },
                config,
            )
            self.assertEqual(response["jsonrpc"], "2.0")
            self.assertFalse(response["result"]["isError"])
            self.assertEqual(response["result"]["content"][0]["type"], "text")

    def test_self_test_reports_json_rpc_ok(self) -> None:
        result = self_test()
        self.assertTrue(result["jsonrpc_ok"])
        self.assertGreater(result["tool_count"], 0)


if __name__ == "__main__":
    unittest.main()
