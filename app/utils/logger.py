import logging

from sqlalchemy.orm import Session

from app.models.sync_log import SyncLog

logger = logging.getLogger("sync_logger")


def log_sync_event(
    db: Session,
    *,
    direction: str,
    entity_type: str,
    entity_id: str | None = None,
    action: str,
    status: str = "success",
    http_status_code: int | None = None,
    request_payload: dict | list | None = None,
    response_payload: dict | list | None = None,
    error_message: str | None = None,
) -> SyncLog | None:
    """Write a sync event to both the database and the Python logger.

    A failure to persist the audit row must not mask the success of the
    operation that triggered logging — we swallow DB errors and only emit
    a warning to the application logger.
    """
    entry = SyncLog(
        direction=direction,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        status=status,
        http_status_code=http_status_code,
        request_payload=request_payload,
        response_payload=response_payload,
        error_message=error_message,
    )
    try:
        db.add(entry)
        db.commit()
        db.refresh(entry)
    except Exception as exc:  # pragma: no cover - defensive
        db.rollback()
        logger.warning("Failed to persist SyncLog entry: %s", exc)
        entry = None

    log_fn = logger.info if status == "success" else logger.error
    log_fn(
        "SYNC %s | %s | %s | %s | %s | %s",
        direction,
        entity_type,
        entity_id or "-",
        action,
        status,
        error_message or "OK",
    )
    return entry
