from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class PaymentStatusEnum(str, Enum):
    PAID = "Paid"
    PENDING = "Pending"
    FAILED = "Failed"
    REFUNDED = "Refunded"


class PaymentCreate(BaseModel):
    """Payload sent by CRM when a payment is processed."""

    crm_payment_id: str = Field(
        ..., min_length=1, max_length=64, examples=["PAY-20250901-001"]
    )
    crm_student_id: str = Field(
        ..., min_length=1, max_length=64, examples=["CRM-STU-10045"]
    )
    amount: float = Field(..., gt=0, examples=[350.00])
    currency: str = Field("USD", min_length=3, max_length=3, examples=["USD"])
    payment_status: PaymentStatusEnum = Field(..., examples=["Paid"])
    payment_date: date | None = Field(None, examples=["2025-09-01"])
    invoice_number: str | None = Field(None, max_length=64, examples=["INV-10045"])
    modules_to_unlock: list[str] | None = Field(
        None, examples=[["MOD-PY-101", "MOD-PY-102"]]
    )


class PaymentResponse(BaseModel):
    id: str
    crm_payment_id: str
    student_id: str
    amount: float
    currency: str
    payment_status: str
    payment_date: date | None = None
    invoice_number: str | None = None
    modules_unlocked: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentSyncResult(BaseModel):
    payment_id: str
    student_id: str
    status: str
    modules_unlocked: list[str]
    message: str
