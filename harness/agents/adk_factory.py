"""Google ADK agent construction with graceful local fallback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from harness.config import ModelConfig


@dataclass(frozen=True)
class ADKAgentHandle:
    name: str
    model: str
    temperature: float
    instruction: str
    tools: tuple[str, ...]
    native_agent: Any = None

    @property
    def is_native(self) -> bool:
        return self.native_agent is not None


def create_adk_agent(
    *,
    name: str,
    model_config: ModelConfig,
    instruction: str,
    tools: tuple[str, ...],
    tool_objects: tuple[Callable[..., Any], ...] = (),
) -> ADKAgentHandle:
    """Create a Google ADK agent when available.

    The harness remains testable without credentials or the optional ADK
    package. In a configured runtime, install `google-adk` and set model
    variables to real endpoints.
    """

    try:
        from google.adk.agents import LlmAgent  # type: ignore
    except Exception:
        return ADKAgentHandle(
            name=name,
            model=model_config.model,
            temperature=model_config.temperature,
            instruction=instruction,
            tools=tools,
        )

    native = LlmAgent(
        name=name,
        model=model_config.model,
        instruction=instruction,
        tools=list(tool_objects),
    )
    return ADKAgentHandle(
        name=name,
        model=model_config.model,
        temperature=model_config.temperature,
        instruction=instruction,
        tools=tools,
        native_agent=native,
    )
