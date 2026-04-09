"""
Core proxy service.
Selects the appropriate provider for a model, handles streaming/non-streaming,
applies fallback logic, and records health + logs.
"""

import json
import time
import uuid
from typing import AsyncIterator

import httpx

from app.config import config, ModelConfig
from app.providers.base import BaseProvider, UnsupportedProviderRequestError
from app.providers.openai import OpenAIProvider
from app.providers.anthropic import AnthropicProvider
from app.schemas.chat import ChatCompletionRequest
from app.services.health_checker import health_checker
from app.services.logger import LogEntry, write_log


class NoAvailableModelError(Exception):
    pass


class ModelNotFoundError(Exception):
    pass


class MidStreamProviderError(Exception):
    pass


def _build_provider(model_cfg: ModelConfig) -> BaseProvider:
    provider = model_cfg.provider.lower()
    if provider == "anthropic":
        return AnthropicProvider(model_cfg, timeout=config.settings.request_timeout)
    # openai-compatible: openai, ollama, or any custom base_url
    return OpenAIProvider(model_cfg, timeout=config.settings.request_timeout)


def _get_candidates(model_id: str) -> list[ModelConfig]:
    """
    Return active model configs that match the requested model_id,
    sorted by priority (ascending = higher priority).
    """
    exact = [m for m in config.models if m.is_active and m.id == model_id]
    if not exact:
        raise ModelNotFoundError(f"Model '{model_id}' is not configured")
    return sorted(exact, key=lambda m: m.priority)


def get_available_candidates(request: ChatCompletionRequest) -> list[ModelConfig]:
    candidates = _get_candidates(request.model)
    available = [c for c in candidates if health_checker.is_available(c.id)]
    if not available:
        raise NoAvailableModelError(f"No available provider for model '{request.model}'")

    supported: list[ModelConfig] = []
    last_validation_error: UnsupportedProviderRequestError | None = None
    for model_cfg in available:
        provider = _build_provider(model_cfg)
        try:
            provider.validate_request(request)
        except UnsupportedProviderRequestError as exc:
            last_validation_error = exc
            continue
        supported.append(model_cfg)

    if not supported and last_validation_error is not None:
        raise last_validation_error

    return supported


async def proxy_stream(
    request: ChatCompletionRequest,
    virtual_key_id: str | None,
    candidates: list[ModelConfig],
) -> AsyncIterator[bytes]:
    """
    Stream SSE bytes to the caller. Tries candidates in priority order,
    falls back to next on transient errors. Logs each attempt.
    """
    last_error: Exception | None = None

    for model_cfg in candidates:
        request_id = uuid.uuid4().hex
        provider = _build_provider(model_cfg)
        start = time.monotonic()
        first_token_ms: int | None = None
        total_tokens = 0
        prompt_tokens = 0
        completion_tokens = 0
        got_first = False

        try:
            async for chunk in provider.stream(request):
                if not got_first:
                    first_token_ms = int((time.monotonic() - start) * 1000)
                    got_first = True
                yield chunk

                # Parse usage from SSE chunks (best-effort)
                if chunk.startswith(b"data:") and not chunk.strip().endswith(b"[DONE]"):
                    try:
                        data = json.loads(chunk[5:].strip())
                        usage = data.get("usage") or {}
                        if usage.get("prompt_tokens"):
                            prompt_tokens = usage["prompt_tokens"]
                        if usage.get("completion_tokens"):
                            completion_tokens = usage["completion_tokens"]
                        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
                    except Exception:
                        pass

            total_ms = int((time.monotonic() - start) * 1000)
            health_checker.record_success(model_cfg.id)
            write_log(LogEntry(
                request_id=request_id,
                virtual_key_id=virtual_key_id,
                model=model_cfg.id,
                status="success",
                prompt_tokens=prompt_tokens or None,
                completion_tokens=completion_tokens or None,
                total_tokens=total_tokens or None,
                latency_ms=first_token_ms,
                total_latency_ms=total_ms,
            ))
            return  # success — done

        except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as exc:
            total_ms = int((time.monotonic() - start) * 1000)
            health_checker.record_failure(model_cfg.id)
            last_error = exc
            write_log(LogEntry(
                request_id=request_id,
                virtual_key_id=virtual_key_id,
                model=model_cfg.id,
                status="error",
                total_latency_ms=total_ms,
                error_message=str(exc)[:512],
            ))
            if got_first:
                raise MidStreamProviderError(
                    f"Provider '{model_cfg.id}' failed after streaming began"
                ) from exc
            # Try next candidate before the client has seen any bytes.

    raise NoAvailableModelError(
        f"All providers for '{request.model}' failed. Last error: {last_error}"
    )
