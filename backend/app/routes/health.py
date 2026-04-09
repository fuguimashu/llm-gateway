"""Health check endpoints."""

from fastapi import APIRouter, Depends, Security
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import config
from app.database import get_db
from app.services.auth import authenticate, bearer
from app.services.health_checker import health_checker

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/v1/models")
def list_models(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer),
    db: Session = Depends(get_db),
):
    """OpenAI-compatible model listing."""
    auth = authenticate(credentials, db)
    health_status = health_checker.get_status()
    models = []
    for m in config.models:
        if not m.is_active:
            continue
        allowed = auth.virtual_key.allowed_models if auth.virtual_key else None
        if allowed is not None and m.id not in allowed:
            continue
        hs = health_status.get(m.id, {})
        models.append({
            "id": m.id,
            "object": "model",
            "provider": m.provider,
            "available": hs.get("available", True),
            "consecutive_failures": hs.get("consecutive_failures", 0),
            "cooldown_remaining_seconds": hs.get("cooldown_remaining_seconds", 0),
        })
    return {"object": "list", "data": models}
