"""Request log response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RequestLogResponse(BaseModel):
    id: int
    request_id: str
    virtual_key_id: Optional[str]
    model: str
    status: str
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    latency_ms: Optional[int]
    total_latency_ms: Optional[int]
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class LogsPage(BaseModel):
    items: list[RequestLogResponse]
    total: int
    page: int
    page_size: int
