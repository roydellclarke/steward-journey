import tempfile
import unittest
from pathlib import Path

from harness.security_policy import SecurityPolicy
from harness.trust import QUARANTINED, TrustStore, USER_PROVIDED
from harness.workspace import Workspace
from tests.test_workspace import config_for


class SecurityPolicyTests(unittest.TestCase):
    def test_quarantined_content_cannot_be_sent_to_llm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            policy = SecurityPolicy(root)
            policy.quarantine_external_text(
                "quarantine/web.md",
                "email test@example.com and sk-testsecret123456",
                source="web",
            )
            record = TrustStore(root).get("quarantine/web.md")
            self.assertEqual(record.label, QUARANTINED)
            self.assertFalse(policy.can_send_to_llm("quarantine/web.md").allowed)
            self.assertNotIn("test@example.com", (root / "quarantine" / "web.md").read_text())

    def test_user_provided_content_cannot_directly_execute_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            TrustStore(root).label("goals/user_goals.md", USER_PROVIDED, source="test")
            decision = SecurityPolicy(root).can_execute_tool_from_content("goals/user_goals.md")
            self.assertFalse(decision.allowed)


if __name__ == "__main__":
    unittest.main()
