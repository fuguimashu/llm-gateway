"""OpenAI provider — also used for any OpenAI-compatible endpoint."""

from typing import AsyncIterator

import httpx

from app.config import ModelConfig
from app.providers.base import BaseProvider
from app.schemas.chat import ChatCompletionRequest


class OpenAIProvider(BaseProvider):
    def __init__(self, model_cfg: ModelConfig, timeout: int = 120):
        super().__init__(model_cfg, timeout)
        base = model_cfg.base_url or "https://api.openai.com"
        self.endpoint = f"{base.rstrip('/')}/v1/chat/completions"

    async def stream(self, request: ChatCompletionRequest) -> AsyncIterator[bytes]:
        headers = {
            "Authorization": f"Bearer {self.model_cfg.api_key}",
            "Content-Type": "application/json",
        }

        payload = request.model_dump(exclude_none=True, exclude={"model"})
        payload["model"] = self.model_cfg.model_name
        payload["stream"] = True

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", self.endpoint, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        yield (line + "\n").encode()
                    else:
                        yield b"\n"
