import tempfile
import unittest
from pathlib import Path

from harness.config import HarnessConfig, ModelConfig
from harness.tools.file_tools import FileTools
from harness.workspace import WORKSPACE_DIRS, Workspace
from harness.observability import EventLogger


def config_for(root: Path) -> HarnessConfig:
    return HarnessConfig(
        workspace_root=root,
        use_llm=False,
        planner=ModelConfig("planner", "planner-model", 0.1),
        generator=ModelConfig("generator", "generator-model", 0.1),
        evaluator=ModelConfig("evaluator", "evaluator-model", 0.1),
        max_iterations_per_sprint=2,
        min_iterations_per_sprint=1,
        max_total_iterations=4,
        max_wall_clock_minutes=60,
        max_cost_usd=10,
        max_repeated_failure_count=2,
        max_contract_handshake_rounds=2,
        evaluator_recalibration_threshold=2,
        divergence_score_threshold=0.8,
        non_progress_threshold=2,
        allow_architecture_pivot=True,
        require_puppeteer_for_pass=True,
        require_design_review_pass=False,
        require_distinct_logical_models=True,
        context_reset_every_iterations=2,
        app_base_url="http://localhost:3000",
    )


class WorkspaceTests(unittest.TestCase):
    def test_initializes_required_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            for directory in WORKSPACE_DIRS:
                self.assertTrue((root / directory).is_dir())
            self.assertTrue((root / "rubrics" / "landing_page_design.md").is_file())
            self.assertTrue((root / "rubrics" / "saas_ui_quality.md").is_file())

    def test_file_tools_block_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            tools = FileTools(root)
            with self.assertRaises(ValueError):
                tools.write_file("../escape.txt", "nope")

    def test_event_logger_redacts_secret_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Workspace(config_for(root)).initialize()
            EventLogger(root).log(
                run_id="run",
                phase="TEST",
                event="secret_check",
                details={"DEEPSEEK_API_KEY": "sk-test", "safe": "ok"},
            )
            content = (root / "state" / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn("[REDACTED]", content)
            self.assertNotIn("sk-test", content)


if __name__ == "__main__":
    unittest.main()
