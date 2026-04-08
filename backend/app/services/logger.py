"""
Asynchronous request logger.
Writes to SQLite in a background thread to avoid blocking the response stream.
"""

import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.database import SessionLocal
from app.models.request_log import RequestLog


@dataclass
class LogEntry:
    request_id: str
    model: str
    status: str
    virtual_key_id: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    total_latency_ms: Optional[int] = None
    error_message: Optional[str] = None


def write_log(entry: LogEntry) -> None:
    """Write a log entry in a background thread."""
    t = threading.Thread(target=_write_sync, args=(entry,), daemon=True)
    t.start()


def _write_sync(entry: LogEntry) -> None:
    db = SessionLocal()
    try:
        log = RequestLog(
            request_id=entry.request_id,
            virtual_key_id=entry.virtual_key_id,
            model=entry.model,
            status=entry.status,
            prompt_tokens=entry.prompt_tokens,
            completion_tokens=entry.completion_tokens,
            total_tokens=entry.total_tokens,
            latency_ms=entry.latency_ms,
            total_latency_ms=entry.total_latency_ms,
            error_message=entry.error_message,
            created_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
