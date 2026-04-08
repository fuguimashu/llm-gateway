"""Request log query API. Requires master key."""

from fastapi import APIRouter, Depends, HTTPException, Query, Security, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.request_log import RequestLog
from app.schemas.logs import LogsPage, RequestLogResponse
from app.services.auth import authenticate, bearer

router = APIRouter(prefix="/v1/logs", tags=["logs"])


def _require_master(credentials, db):
    auth = authenticate(credentials, db)
    if not auth.is_master:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Master key required")
    return auth


@router.get("", response_model=LogsPage)
def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    model: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    virtual_key_id: str | None = Query(None),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer),
    db: Session = Depends(get_db),
):
    _require_master(credentials, db)

    q = db.query(RequestLog)
    if model:
        q = q.filter(RequestLog.model == model)
    if status_filter:
        q = q.filter(RequestLog.status == status_filter)
    if virtual_key_id:
        q = q.filter(RequestLog.virtual_key_id == virtual_key_id)

    total = q.count()
    items = (
        q.order_by(RequestLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return LogsPage(items=items, total=total, page=page, page_size=page_size)
