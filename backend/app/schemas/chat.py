"""OpenAI-compatible chat completion request/response schemas."""

from typing import Any, Literal, Optional

from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[Any]
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[Message]
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    stop: Optional[str | list[str]] = None
    # Pass-through: any extra fields forwarded to provider as-is
    model_config = {"extra": "allow"}


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChoiceDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class StreamChoice(BaseModel):
    index: int = 0
    delta: ChoiceDelta
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[StreamChoice]


class Choice(BaseModel):
    index: int = 0
    message: Message
    finish_reason: Optional[str] = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[Choice]
    usage: UsageInfo
