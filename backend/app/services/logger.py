"""
Asynchronous request logger.
Writes to SQLite through a single background worker to avoid thread explosions.
"""

import logging
import queue
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

from app.database import SessionLocal
from app.models.request_log import RequestLog

logger = logging.getLogger(__name__)
_LOG_QUEUE: queue.Queue["LogEntry"] = queue.Queue(maxsize=1000)
_WORKER_STARTED = False
_WORKER_LOCK = threading.Lock()


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
    """Queue a log entry for asynchronous persistence."""
    _ensure_worker()
    try:
        _LOG_QUEUE.put_nowait(entry)
    except queue.Full:
        logger.warning("Log queue is full; writing request log synchronously")
        _write_sync(entry)


def flush_logs() -> None:
    """Block until queued log entries are written."""
    _LOG_QUEUE.join()


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
            created_at=datetime.now(UTC),
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to persist request log")
    finally:
        db.close()


def _ensure_worker() -> None:
    global _WORKER_STARTED
    if _WORKER_STARTED:
        return

    with _WORKER_LOCK:
        if _WORKER_STARTED:
            return
        worker = threading.Thread(target=_logging_worker, name="request-log-writer", daemon=True)
        worker.start()
        _WORKER_STARTED = True


def _logging_worker() -> None:
    while True:
        entry = _LOG_QUEUE.get()
        try:
            _write_sync(entry)
        finally:
            _LOG_QUEUE.task_done()
