"""Configurable token cost estimation for providers without cost metadata."""

from __future__ import annotations

import os
import re


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    input_rate, output_rate = _rates_for_model(model)
    return round(((input_tokens / 1_000_000) * input_rate) + ((output_tokens / 1_000_000) * output_rate), 8)


def _rates_for_model(model: str) -> tuple[float, float]:
    provider, model_name = _split(model)
    model_key = _env_key(f"{provider}_{model_name}")

    model_input = os.getenv(f"COST_{model_key}_INPUT_USD_PER_1M")
    model_output = os.getenv(f"COST_{model_key}_OUTPUT_USD_PER_1M")
    if model_input is not None or model_output is not None:
        return _float(model_input), _float(model_output)

    provider_key = _env_key(provider)
    provider_input = os.getenv(f"COST_{provider_key}_INPUT_USD_PER_1M")
    provider_output = os.getenv(f"COST_{provider_key}_OUTPUT_USD_PER_1M")
    if provider_input is not None or provider_output is not None:
        return _float(provider_input), _float(provider_output)

    return _default_rates(provider, model_name)


def _default_rates(provider: str, model_name: str) -> tuple[float, float]:
    normalized = model_name.lower()
    if provider == "deepseek" and "reasoner" in normalized:
        return 0.56, 2.24
    if provider == "deepseek":
        return 0.28, 1.12
    return 0.0, 0.0


def _split(model: str) -> tuple[str, str]:
    if "/" not in model:
        return "", model
    provider, model_name = model.split("/", 1)
    return provider.lower(), model_name.lower()


def _env_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper()


def _float(value: str | None) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)

