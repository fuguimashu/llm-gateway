"""Base provider interface."""

from abc import ABC, abstractmethod
from typing import AsyncIterator

from app.config import ModelConfig
from app.schemas.chat import ChatCompletionRequest


class BaseProvider(ABC):
    def __init__(self, model_cfg: ModelConfig, timeout: int = 120):
        self.model_cfg = model_cfg
        self.timeout = timeout

    @abstractmethod
    async def stream(self, request: ChatCompletionRequest) -> AsyncIterator[bytes]:
        """
        Stream raw SSE bytes from the upstream provider.
        Each yielded chunk is a b"data: {...}\\n\\n" SSE line, or b"data: [DONE]\\n\\n".
        """
        ...
