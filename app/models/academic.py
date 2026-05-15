import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.schemas.academic import AcademicStatusEnum


class AcademicRecord(Base):
    __tablename__ = "academic_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id"), nullable=False
    )
    course_code: Mapped[str] = mapped_column(String(32), nullable=False)
    module_name: Mapped[str] = mapped_column(String(256), nullable=False)
    attendance_pct: Mapped[float] = mapped_column(Float, default=0.0)
    grade: Mapped[str | None] = mapped_column(String(5), nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_classes: Mapped[int] = mapped_column(Integer, default=0)
    attended_classes: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(
        SAEnum(
            AcademicStatusEnum,
            values_callable=lambda e: [m.value for m in e],
            native_enum=False,
            length=20,
        ),
        default=AcademicStatusEnum.IN_PROGRESS.value,
    )
    instructor_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    student: Mapped["Student"] = relationship(back_populates="academic_records")  # type: ignore[name-defined] # noqa: F821

    def __repr__(self) -> str:
        return f"<AcademicRecord {self.course_code} – {self.student_id}>"
