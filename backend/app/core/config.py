"""Runtime configuration for the StewardPath backend."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_env_file(path: Path | None = None) -> None:
    """Load simple KEY=value pairs from .env without overriding the process."""

    env_path = path or Path(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    data_root: Path
    use_llm: bool
    kimi_model: str
    deepseek_model: str
    kimi_temperature: float
    deepseek_temperature: float
    request_timeout_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_env_file()
        return cls(
            data_root=Path(os.getenv("STEWARDPATH_DATA_ROOT", "data/stewardpath")).resolve(),
            use_llm=_bool_env("STEWARDPATH_USE_LLM", False),
            kimi_model=os.getenv("STEWARDPATH_KIMI_MODEL", "moonshot/kimi-k2.5"),
            deepseek_model=os.getenv("STEWARDPATH_DEEPSEEK_MODEL", "deepseek/deepseek-reasoner"),
            kimi_temperature=float(os.getenv("STEWARDPATH_KIMI_TEMPERATURE", "1")),
            deepseek_temperature=float(os.getenv("STEWARDPATH_DEEPSEEK_TEMPERATURE", "0.15")),
            request_timeout_seconds=int(os.getenv("STEWARDPATH_LLM_TIMEOUT_SECONDS", "120")),
        )
