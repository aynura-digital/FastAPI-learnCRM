from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AcademicStatusEnum(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    WITHDRAWN = "withdrawn"


class AcademicRecordCreate(BaseModel):
    """Payload from Academic System to record progress."""

    crm_student_id: str = Field(
        ..., min_length=1, max_length=64, examples=["CRM-STU-10045"]
    )
    course_code: str = Field(
        ..., min_length=1, max_length=32, examples=["PY-BACKEND-2025"]
    )
    module_name: str = Field(
        ..., min_length=1, max_length=256, examples=["Django REST Framework"]
    )
    attendance_pct: float = Field(
        ..., ge=0, le=100, examples=[92.5]
    )
    grade: str | None = Field(None, max_length=5, examples=["A"])
    score: float | None = Field(None, ge=0, le=100, examples=[95.0])
    total_classes: int = Field(..., ge=0, examples=[24])
    attended_classes: int = Field(..., ge=0, examples=[22])
    status: AcademicStatusEnum = Field(..., examples=["in_progress"])
    instructor_notes: str | None = Field(
        None, examples=["Excellent participation"]
    )


class AcademicRecordUpdate(BaseModel):
    attendance_pct: float | None = Field(None, ge=0, le=100)
    grade: str | None = Field(None, max_length=5)
    score: float | None = Field(None, ge=0, le=100)
    total_classes: int | None = Field(None, ge=0)
    attended_classes: int | None = Field(None, ge=0)
    status: AcademicStatusEnum | None = None
    instructor_notes: str | None = None


class AcademicRecordResponse(BaseModel):
    id: str
    student_id: str
    course_code: str
    module_name: str
    attendance_pct: float
    grade: str | None = None
    score: float | None = None
    total_classes: int
    attended_classes: int
    status: str
    instructor_notes: str | None = None
    recorded_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AcademicProgressCRMPayload(BaseModel):
    """Payload shape expected by the CRM when receiving academic data."""

    crm_student_id: str
    student_name: str
    course_code: str
    module_name: str
    attendance_pct: float
    grade: str | None = None
    score: float | None = None
    status: str
    synced_at: datetime
