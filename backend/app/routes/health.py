"""Health check endpoints."""

from fastapi import APIRouter

from app.config import config
from app.services.health_checker import health_checker

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/v1/models")
def list_models():
    """OpenAI-compatible model listing."""
    health_status = health_checker.get_status()
    models = []
    for m in config.models:
        if not m.is_active:
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
