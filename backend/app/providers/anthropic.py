"""
Anthropic provider — translates OpenAI chat format to Anthropic Messages API
and converts the SSE stream back to OpenAI-compatible SSE chunks.
"""

import json
import time
import uuid
from typing import AsyncIterator

import httpx

from app.config import ModelConfig
from app.providers.base import BaseProvider
from app.schemas.chat import ChatCompletionRequest

ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


def _to_anthropic_payload(request: ChatCompletionRequest) -> dict:
    """Convert OpenAI messages format to Anthropic format."""
    system_parts = []
    messages = []

    for msg in request.messages:
        if msg.role == "system":
            system_parts.append(str(msg.content))
        else:
            role = "assistant" if msg.role == "assistant" else "user"
            messages.append({"role": role, "content": str(msg.content)})

    payload: dict = {
        "model": "",  # filled by caller
        "messages": messages,
        "stream": True,
        "max_tokens": request.max_tokens or 4096,
    }
    if system_parts:
        payload["system"] = "\n".join(system_parts)
    if request.temperature is not None:
        payload["temperature"] = request.temperature
    if request.top_p is not None:
        payload["top_p"] = request.top_p
    if request.stop:
        payload["stop_sequences"] = request.stop if isinstance(request.stop, list) else [request.stop]

    return payload


class AnthropicProvider(BaseProvider):
    def __init__(self, model_cfg: ModelConfig, timeout: int = 120):
        super().__init__(model_cfg, timeout)
        base = model_cfg.base_url or ANTHROPIC_API
        self.endpoint = base.rstrip("/") if "messages" in base else f"{base.rstrip('/')}/v1/messages"

    async def stream(self, request: ChatCompletionRequest) -> AsyncIterator[bytes]:
        headers = {
            "x-api-key": self.model_cfg.api_key or "",
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }

        payload = _to_anthropic_payload(request)
        payload["model"] = self.model_cfg.model_name

        completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created = int(time.time())
        model_id = request.model

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", self.endpoint, headers=headers, json=payload) as resp:
                resp.raise_for_status()

                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if not data_str:
                        continue

                    try:
                        event = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    event_type = event.get("type", "")

                    if event_type == "content_block_delta":
                        delta = event.get("delta", {})
                        text = delta.get("text", "")
                        chunk = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model_id,
                            "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}],
                        }
                        yield f"data: {json.dumps(chunk)}\n\n".encode()

                    elif event_type == "message_delta":
                        stop_reason = event.get("delta", {}).get("stop_reason")
                        usage = event.get("usage", {})
                        chunk = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model_id,
                            "choices": [{"index": 0, "delta": {}, "finish_reason": stop_reason or "stop"}],
                            "usage": {
                                "prompt_tokens": 0,
                                "completion_tokens": usage.get("output_tokens", 0),
                                "total_tokens": usage.get("output_tokens", 0),
                            },
                        }
                        yield f"data: {json.dumps(chunk)}\n\n".encode()

                    elif event_type == "message_start":
                        # Extract prompt token count
                        usage = event.get("message", {}).get("usage", {})
                        chunk = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created,
                            "model": model_id,
                            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
                            "usage": {
                                "prompt_tokens": usage.get("input_tokens", 0),
                                "completion_tokens": 0,
                                "total_tokens": usage.get("input_tokens", 0),
                            },
                        }
                        yield f"data: {json.dumps(chunk)}\n\n".encode()

                    elif event_type == "message_stop":
                        yield b"data: [DONE]\n\n"
