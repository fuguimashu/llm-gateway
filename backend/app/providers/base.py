"""Base provider interface."""

from abc import ABC, abstractmethod
from typing import AsyncIterator

from app.config import ModelConfig
from app.schemas.chat import ChatCompletionRequest


class UnsupportedProviderRequestError(Exception):
    """Raised when a provider cannot safely serve the requested payload."""


class BaseProvider(ABC):
    def __init__(self, model_cfg: ModelConfig, timeout: int = 120):
        self.model_cfg = model_cfg
        self.timeout = timeout

    def validate_request(self, request: ChatCompletionRequest) -> None:
        """Provider-specific preflight validation."""
        return None

    @abstractmethod
    async def stream(self, request: ChatCompletionRequest) -> AsyncIterator[bytes]:
        """
        Stream raw SSE bytes from the upstream provider.
        Each yielded chunk is a b"data: {...}\\n\\n" SSE line, or b"data: [DONE]\\n\\n".
        """
        ...
