"""LiteLLM-backed model calls."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from urllib import request
from urllib.error import HTTPError

from harness.config import ModelConfig
from harness.cost_estimator import estimate_cost_usd


@dataclass(frozen=True)
class LlmResult:
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0


class LlmClient:
    def complete(self, *, model_config: ModelConfig, system: str, user: str) -> LlmResult:
        try:
            from litellm import completion
        except Exception as exc:
            return self._openai_compatible_complete(
                model_config=model_config,
                system=system,
                user=user,
                import_error=exc,
            )

        response = completion(
            model=model_config.model,
            temperature=model_config.temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        message = response["choices"][0]["message"]["content"] or ""
        usage = getattr(response, "usage", None) or response.get("usage", {}) or {}
        input_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
        cost = float(getattr(response, "_hidden_params", {}).get("response_cost", 0.0) or 0.0)
        if cost == 0.0:
            cost = estimate_cost_usd(model_config.model, input_tokens, output_tokens)
        return LlmResult(
            content=message,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost,
        )

    def _openai_compatible_complete(
        self,
        *,
        model_config: ModelConfig,
        system: str,
        user: str,
        import_error: Exception,
    ) -> LlmResult:
        provider, model = self._split_provider_model(model_config.model)
        endpoint, api_key = self._provider_settings(provider)
        if not endpoint or not api_key:
            raise RuntimeError(
                "HARNESS_USE_LLM=true needs litellm or a configured OpenAI-compatible "
                f"provider key for model `{model_config.model}`. Original litellm import "
                f"error: {type(import_error).__name__}"
            )

        payload = {
            "model": model,
            "temperature": model_config.temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{provider} API request failed with HTTP {exc.code}: {details}") from exc

        content = data["choices"][0]["message"]["content"] or ""
        usage = data.get("usage", {}) or {}
        input_tokens = int(usage.get("prompt_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or 0)
        return LlmResult(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimate_cost_usd(model_config.model, input_tokens, output_tokens),
        )

    def _split_provider_model(self, model: str) -> tuple[str, str]:
        if "/" not in model:
            return "", model
        provider, model_name = model.split("/", 1)
        return provider.lower(), model_name

    def _provider_settings(self, provider: str) -> tuple[str, str]:
        if provider == "deepseek":
            return "https://api.deepseek.com/chat/completions", os.getenv("DEEPSEEK_API_KEY", "")
        if provider in {"moonshot", "kimi"}:
            return "https://api.moonshot.ai/v1/chat/completions", os.getenv("MOONSHOT_API_KEY", "")
        return "", ""
