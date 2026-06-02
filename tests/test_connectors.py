import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from harness.connector_vault import ConnectorVault
from harness.meta_publisher import MetaPagesPublisher
from harness.workspace import Workspace
from tests.test_workspace import config_for


class ConnectorTests(unittest.TestCase):
    def test_vault_stores_env_reference_not_raw_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            connector = ConnectorVault(root).upsert_meta_pages(
                name="Main page",
                page_id="12345",
                token_env_var="META_PAGE_ACCESS_TOKEN",
            )
            raw = (root / "state" / "connectors.json").read_text(encoding="utf-8")
            self.assertEqual(connector.config["page_id"], "12345")
            self.assertIn("META_PAGE_ACCESS_TOKEN", raw)
            self.assertNotIn("access_token=", raw)

    def test_vault_rejects_raw_token_like_env_var(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            with self.assertRaises(ValueError):
                ConnectorVault(root).upsert_meta_pages(name="Bad", page_id="1", token_env_var="sk-token-value")

    def test_meta_publisher_requires_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            connector = ConnectorVault(root).upsert_meta_pages(name="Main", page_id="123")
            publisher = MetaPagesPublisher(connector)
            with patch.dict(os.environ, {"META_PAGE_ACCESS_TOKEN": "token"}, clear=False):
                with self.assertRaises(PermissionError):
                    publisher.publish({"post_text": "Hello"})

    def test_meta_publisher_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            connector = ConnectorVault(root).upsert_meta_pages(name="Main", page_id="123")
            publisher = MetaPagesPublisher(connector, dry_run=True)
            with patch.dict(os.environ, {"META_PAGE_ACCESS_TOKEN": "token"}, clear=False):
                output = publisher.publish({"post_text": "Approved post", "approved": True})
            self.assertIn("DRY_RUN", output)
            self.assertIn("123", output)


if __name__ == "__main__":
    unittest.main()

