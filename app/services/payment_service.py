from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.student import Student
from app.schemas.payment import PaymentCreate, PaymentSyncResult
from app.services.student_service import get_student_or_404
from app.utils.logger import log_sync_event


def process_payment(db: Session, payload: PaymentCreate) -> PaymentSyncResult:
    """
    Process a payment event from CRM.

    Business rules:
      - Resolve the student by crm_student_id (must exist).
      - Upsert the payment record.
      - If payment_status == 'Paid', unlock the requested academic modules.
    """
    student = get_student_or_404(db, payload.crm_student_id)

    modules = list(payload.modules_to_unlock) if payload.modules_to_unlock else None

    existing = (
        db.query(Payment)
        .filter(Payment.crm_payment_id == payload.crm_payment_id)
        .first()
    )

    if existing:
        existing.amount = payload.amount
        existing.currency = payload.currency
        existing.payment_status = payload.payment_status.value
        existing.payment_date = payload.payment_date
        existing.invoice_number = payload.invoice_number
        existing.modules_unlocked = modules
        db.commit()
        db.refresh(existing)
        payment = existing
        action = "update"
    else:
        payment = Payment(
            crm_payment_id=payload.crm_payment_id,
            student_id=student.id,
            amount=payload.amount,
            currency=payload.currency,
            payment_status=payload.payment_status.value,
            payment_date=payload.payment_date,
            invoice_number=payload.invoice_number,
            modules_unlocked=modules,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        action = "create"

    unlocked: list[str] = []
    if payload.payment_status.value == "Paid" and payload.modules_to_unlock:
        unlocked = payload.modules_to_unlock
        # In a real system this would call an Academic System API
        # to enable the modules for the student.

    log_sync_event(
        db,
        direction="crm_to_academic",
        entity_type="payment",
        entity_id=payload.crm_payment_id,
        action=action,
        request_payload=payload.model_dump(),
        response_payload={"modules_unlocked": unlocked},
    )

    return PaymentSyncResult(
        payment_id=payment.id,
        student_id=student.id,
        status=payment.payment_status,
        modules_unlocked=unlocked,
        message=(
            f"Payment {action}d. "
            + (
                f"{len(unlocked)} module(s) unlocked."
                if unlocked
                else "No modules unlocked."
            )
        ),
    )


def list_payments(
    db: Session, *, crm_student_id: str | None = None, skip: int = 0, limit: int = 50
) -> list[Payment]:
    query = db.query(Payment)
    if crm_student_id:
        query = query.join(Student).filter(
            Student.crm_student_id == crm_student_id
        )
    return query.offset(skip).limit(limit).all()
