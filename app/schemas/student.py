import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class StudentCreate(BaseModel):
    """Payload sent by CRM when a new student is registered."""

    crm_student_id: str = Field(
        ..., min_length=1, max_length=64, examples=["CRM-STU-10045"]
    )
    first_name: str = Field(..., min_length=1, max_length=128, examples=["Aisha"])
    last_name: str = Field(..., min_length=1, max_length=128, examples=["Karimova"])
    email: EmailStr = Field(..., examples=["aisha.karimova@example.com"])
    phone: str | None = Field(
        None, max_length=20, examples=["+998901234567"]
    )
    date_of_birth: str | None = Field(
        None, pattern=r"^\d{4}-\d{2}-\d{2}$", examples=["2005-03-15"]
    )
    enrollment_date: str | None = Field(
        None, pattern=r"^\d{4}-\d{2}-\d{2}$", examples=["2025-09-01"]
    )
    course_name: str | None = Field(
        None, max_length=256, examples=["Python Backend Development"]
    )
    group_id: str | None = Field(None, max_length=64, examples=["GRP-2025-PY-03"])
    notes: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^\+?\d{7,15}$", v):
            raise ValueError(
                "Phone must be 7–15 digits, optionally prefixed with +"
            )
        return v


class StudentUpdate(BaseModel):
    """Partial update payload."""

    first_name: str | None = Field(None, min_length=1, max_length=128)
    last_name: str | None = Field(None, min_length=1, max_length=128)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=20)
    date_of_birth: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    enrollment_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    course_name: str | None = Field(None, max_length=256)
    group_id: str | None = Field(None, max_length=64)
    is_active: bool | None = None
    notes: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^\+?\d{7,15}$", v):
            raise ValueError(
                "Phone must be 7–15 digits, optionally prefixed with +"
            )
        return v


class StudentResponse(BaseModel):
    id: str
    crm_student_id: str
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    date_of_birth: str | None = None
    enrollment_date: str | None = None
    course_name: str | None = None
    group_id: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
