"""Virtual Key request/response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VirtualKeyCreate(BaseModel):
    name: str
    models: Optional[str] = None  # comma-separated model IDs, None = all


class VirtualKeyResponse(BaseModel):
    id: str
    name: str
    models: Optional[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    is_active: bool

    model_config = {"from_attributes": True}


class VirtualKeyCreated(VirtualKeyResponse):
    """Returned only on creation — includes the raw key."""
    key: str  # same as id, shown once
