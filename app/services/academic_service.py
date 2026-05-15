from datetime import datetime, timezone

from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from app.models.academic import AcademicRecord
from app.schemas.academic import (
    AcademicProgressCRMPayload,
    AcademicRecordCreate,
    AcademicRecordUpdate,
)
from app.services.student_service import get_student_or_404
from app.utils.logger import log_sync_event


def create_academic_record(
    db: Session, payload: AcademicRecordCreate
) -> AcademicRecord:
    student = get_student_or_404(db, payload.crm_student_id)

    record = AcademicRecord(
        student_id=student.id,
        course_code=payload.course_code,
        module_name=payload.module_name,
        attendance_pct=payload.attendance_pct,
        grade=payload.grade,
        score=payload.score,
        total_classes=payload.total_classes,
        attended_classes=payload.attended_classes,
        status=payload.status.value,
        instructor_notes=payload.instructor_notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    log_sync_event(
        db,
        direction="academic_to_crm",
        entity_type="academic_record",
        entity_id=record.id,
        action="create",
        request_payload=payload.model_dump(),
    )
    return record


def update_academic_record(
    db: Session, record_id: str, payload: AcademicRecordUpdate
) -> AcademicRecord:
    record = db.query(AcademicRecord).filter(AcademicRecord.id == record_id).first()
    if record is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Academic record '{record_id}' not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] is not None:
        update_data["status"] = update_data["status"].value
    for field, value in update_data.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)

    log_sync_event(
        db,
        direction="academic_to_crm",
        entity_type="academic_record",
        entity_id=record.id,
        action="update",
        request_payload=update_data,
    )
    return record


def list_records_for_student(
    db: Session, crm_student_id: str
) -> list[AcademicRecord]:
    student = get_student_or_404(db, crm_student_id)
    return (
        db.query(AcademicRecord)
        .filter(AcademicRecord.student_id == student.id)
        .all()
    )


def build_crm_payload(
    db: Session, crm_student_id: str
) -> list[AcademicProgressCRMPayload]:
    """
    Build the payload that would be pushed to the CRM for a given student.
    """
    student = get_student_or_404(db, crm_student_id)
    records = (
        db.query(AcademicRecord)
        .filter(AcademicRecord.student_id == student.id)
        .all()
    )

    payloads = []
    for r in records:
        payloads.append(
            AcademicProgressCRMPayload(
                crm_student_id=student.crm_student_id,
                student_name=f"{student.first_name} {student.last_name}",
                course_code=r.course_code,
                module_name=r.module_name,
                attendance_pct=r.attendance_pct,
                grade=r.grade,
                score=r.score,
                status=r.status,
                synced_at=datetime.now(timezone.utc),
            )
        )

    log_sync_event(
        db,
        direction="academic_to_crm",
        entity_type="academic_record",
        entity_id=crm_student_id,
        action="sync",
        response_payload=[p.model_dump(mode="json") for p in payloads],
    )
    return payloads
