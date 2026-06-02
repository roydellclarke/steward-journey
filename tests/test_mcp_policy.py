import tempfile
import unittest
from pathlib import Path

from harness.mcp_policy import McpPolicy
from harness.workspace import Workspace
from tests.test_workspace import config_for


class McpPolicyTests(unittest.TestCase):
    def test_default_deny_and_evaluator_browser_allow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            policy = McpPolicy(root)
            self.assertTrue(policy.can_use(agent="evaluator", server="browser", tool="puppeteer_click").allowed)
            self.assertFalse(policy.can_use(agent="generator", server="browser", tool="puppeteer_click").allowed)
            self.assertFalse(policy.can_use(agent="planner", server="github", tool="create_issue").allowed)


if __name__ == "__main__":
    unittest.main()
