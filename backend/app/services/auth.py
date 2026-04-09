"""Virtual Key authentication."""

from datetime import UTC, datetime

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import config
from app.models.virtual_key import VirtualKey

bearer = HTTPBearer(auto_error=False)


class AuthResult:
    def __init__(self, virtual_key: VirtualKey | None = None, is_master: bool = False):
        self.virtual_key = virtual_key
        self.is_master = is_master


def authenticate(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
) -> AuthResult:
    """
    Validates Bearer token. Accepts:
    - Master key (full access)
    - Virtual key (access restricted by allowed models)
    Raises HTTP 401 on invalid/missing token.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    token = credentials.credentials

    # Master key check
    if token == config.settings.master_key:
        return AuthResult(is_master=True)

    # Virtual key lookup
    vk = db.query(VirtualKey).filter(VirtualKey.id == token, VirtualKey.is_active == True).first()  # noqa: E712
    if vk is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
        )

    # Update last used
    vk.last_used_at = datetime.now(UTC)
    db.commit()

    return AuthResult(virtual_key=vk)


def check_model_access(auth: AuthResult, model: str) -> None:
    """Raises 403 if the virtual key doesn't allow the requested model."""
    if auth.is_master:
        return
    if auth.virtual_key is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No key")

    allowed = auth.virtual_key.allowed_models
    if allowed is not None and model not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Model '{model}' is not allowed for this key",
        )
