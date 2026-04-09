"""Virtual Key management API. All endpoints require the master key."""

import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.virtual_key import VirtualKey
from app.schemas.keys import VirtualKeyCreate, VirtualKeyCreated, VirtualKeyResponse
from app.services.auth import authenticate, bearer

router = APIRouter(prefix="/v1/keys", tags=["keys"])


def _require_master(credentials, db):
    auth = authenticate(credentials, db)
    if not auth.is_master:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Master key required for key management",
        )
    return auth


@router.post("", response_model=VirtualKeyCreated, status_code=201)
def create_key(
    body: VirtualKeyCreate,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer),
    db: Session = Depends(get_db),
):
    _require_master(credentials, db)
    key = f"sk-{secrets.token_urlsafe(32)}"
    vk = VirtualKey(
        id=key,
        name=body.name,
        models=body.models,
        created_at=datetime.now(UTC),
        is_active=True,
    )
    db.add(vk)
    db.commit()
    db.refresh(vk)
    return VirtualKeyCreated(
        id=vk.id,
        name=vk.name,
        models=vk.models,
        created_at=vk.created_at,
        last_used_at=vk.last_used_at,
        is_active=vk.is_active,
        key=key,
    )


@router.get("", response_model=list[VirtualKeyResponse])
def list_keys(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer),
    db: Session = Depends(get_db),
):
    _require_master(credentials, db)
    return db.query(VirtualKey).order_by(VirtualKey.created_at.desc()).all()


@router.delete("/{key_id}", status_code=204)
def delete_key(
    key_id: str,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer),
    db: Session = Depends(get_db),
):
    _require_master(credentials, db)
    vk = db.query(VirtualKey).filter(VirtualKey.id == key_id).first()
    if vk is None:
        raise HTTPException(status_code=404, detail="Key not found")
    vk.is_active = False
    db.commit()


@router.post("/{key_id}/activate", response_model=VirtualKeyResponse)
def activate_key(
    key_id: str,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer),
    db: Session = Depends(get_db),
):
    _require_master(credentials, db)
    vk = db.query(VirtualKey).filter(VirtualKey.id == key_id).first()
    if vk is None:
        raise HTTPException(status_code=404, detail="Key not found")
    vk.is_active = True
    db.commit()
    db.refresh(vk)
    return vk
