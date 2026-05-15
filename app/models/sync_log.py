import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SyncLog(Base):
    """Centralized log of every synchronization attempt."""

    __tablename__ = "sync_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    direction: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )  # crm_to_academic | academic_to_crm
    entity_type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )  # student | payment | academic_record
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # create | update | sync | error
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="success", index=True
    )  # success | failure
    http_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    def __repr__(self) -> str:
        return f"<SyncLog {self.direction} {self.entity_type} – {self.status}>"
