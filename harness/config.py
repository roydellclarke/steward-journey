"""Configuration and bounded-autonomy hyperknobs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from pathlib import Path

from harness.env_loader import load_env_file


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ModelConfig:
    logical_name: str
    model: str
    temperature: float


@dataclass(frozen=True)
class HarnessConfig:
    workspace_root: Path
    use_llm: bool
    planner: ModelConfig
    generator: ModelConfig
    evaluator: ModelConfig
    max_iterations_per_sprint: int
    min_iterations_per_sprint: int
    max_total_iterations: int
    max_wall_clock_minutes: int
    max_cost_usd: float
    max_repeated_failure_count: int
    max_contract_handshake_rounds: int
    evaluator_recalibration_threshold: int
    divergence_score_threshold: float
    non_progress_threshold: int
    allow_architecture_pivot: bool
    require_puppeteer_for_pass: bool
    require_design_review_pass: bool
    require_distinct_logical_models: bool
    context_reset_every_iterations: int
    app_base_url: str

    @classmethod
    def from_env(cls) -> "HarnessConfig":
        load_env_file()
        return cls(
            workspace_root=Path(os.getenv("HARNESS_WORKSPACE", "workspace")).resolve(),
            use_llm=_bool_env("HARNESS_USE_LLM", False),
            planner=ModelConfig(
                logical_name="planner",
                model=os.getenv("PLANNER_MODEL", "gemini/gemini-2.5-pro"),
                temperature=float(os.getenv("PLANNER_TEMPERATURE", "0.25")),
            ),
            generator=ModelConfig(
                logical_name="generator",
                model=os.getenv("GENERATOR_MODEL", "gemini/gemini-2.0-flash"),
                temperature=float(os.getenv("GENERATOR_TEMPERATURE", "0.35")),
            ),
            evaluator=ModelConfig(
                logical_name="evaluator",
                model=os.getenv("EVALUATOR_MODEL", "gemini/gemini-2.5-pro"),
                temperature=float(os.getenv("EVALUATOR_TEMPERATURE", "0.15")),
            ),
            max_iterations_per_sprint=int(os.getenv("MAX_ITERATIONS_PER_SPRINT", "8")),
            min_iterations_per_sprint=int(os.getenv("MIN_ITERATIONS_PER_SPRINT", "1")),
            max_total_iterations=int(os.getenv("MAX_TOTAL_ITERATIONS", "30")),
            max_wall_clock_minutes=int(os.getenv("MAX_WALL_CLOCK_MINUTES", "180")),
            max_cost_usd=float(os.getenv("MAX_COST_USD", "25")),
            max_repeated_failure_count=int(os.getenv("MAX_REPEATED_FAILURE_COUNT", "3")),
            max_contract_handshake_rounds=int(os.getenv("MAX_CONTRACT_HANDSHAKE_ROUNDS", "5")),
            evaluator_recalibration_threshold=int(os.getenv("EVALUATOR_RECALIBRATION_THRESHOLD", "2")),
            divergence_score_threshold=float(os.getenv("DIVERGENCE_SCORE_THRESHOLD", "0.35")),
            non_progress_threshold=int(os.getenv("NON_PROGRESS_THRESHOLD", "3")),
            allow_architecture_pivot=_bool_env("ALLOW_ARCHITECTURE_PIVOT", True),
            require_puppeteer_for_pass=_bool_env("REQUIRE_PUPPETEER_FOR_PASS", True),
            require_design_review_pass=_bool_env("REQUIRE_DESIGN_REVIEW_PASS", False),
            require_distinct_logical_models=_bool_env("REQUIRE_DISTINCT_LOGICAL_MODELS", True),
            context_reset_every_iterations=int(os.getenv("CONTEXT_RESET_EVERY_ITERATIONS", "5")),
            app_base_url=os.getenv("APP_BASE_URL", "http://localhost:3000"),
        )

    def hyperknobs(self) -> dict[str, object]:
        return {
            "max_iterations_per_sprint": self.max_iterations_per_sprint,
            "min_iterations_per_sprint": self.min_iterations_per_sprint,
            "max_total_iterations": self.max_total_iterations,
            "max_wall_clock_minutes": self.max_wall_clock_minutes,
            "max_cost_usd": self.max_cost_usd,
            "max_repeated_failure_count": self.max_repeated_failure_count,
            "max_contract_handshake_rounds": self.max_contract_handshake_rounds,
            "evaluator_recalibration_threshold": self.evaluator_recalibration_threshold,
            "divergence_score_threshold": self.divergence_score_threshold,
            "non_progress_threshold": self.non_progress_threshold,
            "allow_architecture_pivot": self.allow_architecture_pivot,
            "require_puppeteer_for_pass": self.require_puppeteer_for_pass,
            "require_design_review_pass": self.require_design_review_pass,
            "require_distinct_logical_models": self.require_distinct_logical_models,
            "context_reset_every_iterations": self.context_reset_every_iterations,
        }

    def model_table(self) -> dict[str, dict[str, object]]:
        return {
            "planner": asdict(self.planner),
            "generator": asdict(self.generator),
            "evaluator": asdict(self.evaluator),
        }
