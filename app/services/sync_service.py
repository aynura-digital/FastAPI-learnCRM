from sqlalchemy.orm import Session

from app.models.sync_log import SyncLog


def get_sync_logs(
    db: Session,
    *,
    direction: str | None = None,
    entity_type: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[SyncLog]:
    query = db.query(SyncLog)
    if direction:
        query = query.filter(SyncLog.direction == direction)
    if entity_type:
        query = query.filter(SyncLog.entity_type == entity_type)
    if status:
        query = query.filter(SyncLog.status == status)
    return query.order_by(SyncLog.created_at.desc()).offset(skip).limit(limit).all()
