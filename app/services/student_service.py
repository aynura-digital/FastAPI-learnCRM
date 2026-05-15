from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate
from app.utils.logger import log_sync_event


def get_student_by_crm_id(db: Session, crm_student_id: str) -> Student | None:
    return (
        db.query(Student)
        .filter(Student.crm_student_id == crm_student_id)
        .first()
    )


def get_student_or_404(db: Session, crm_student_id: str) -> Student:
    student = get_student_by_crm_id(db, crm_student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with crm_student_id '{crm_student_id}' not found",
        )
    return student


def list_students(
    db: Session, *, skip: int = 0, limit: int = 50, active_only: bool = False
) -> list[Student]:
    query = db.query(Student)
    if active_only:
        query = query.filter(Student.is_active.is_(True))
    return (
        query.order_by(Student.created_at.desc(), Student.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_or_update_student(db: Session, payload: StudentCreate) -> tuple[Student, str]:
    """
    Upsert: if a student with the given crm_student_id already exists,
    update their record; otherwise create a new one.

    Returns (student, action) where action is 'created' or 'updated'.
    """
    existing = get_student_by_crm_id(db, payload.crm_student_id)

    if existing:
        for field, value in payload.model_dump(exclude_unset=True).items():
            if field != "crm_student_id":
                setattr(existing, field, value)
        db.commit()
        db.refresh(existing)

        log_sync_event(
            db,
            direction="crm_to_academic",
            entity_type="student",
            entity_id=payload.crm_student_id,
            action="update",
            request_payload=payload.model_dump(mode="json"),
        )
        return existing, "updated"

    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)

    log_sync_event(
        db,
        direction="crm_to_academic",
        entity_type="student",
        entity_id=payload.crm_student_id,
        action="create",
        request_payload=payload.model_dump(mode="json"),
    )
    return student, "created"


def update_student(
    db: Session, crm_student_id: str, payload: StudentUpdate
) -> Student:
    student = get_student_or_404(db, crm_student_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)

    log_sync_event(
        db,
        direction="crm_to_academic",
        entity_type="student",
        entity_id=crm_student_id,
        action="update",
        request_payload=payload.model_dump(mode="json", exclude_unset=True),
    )
    return student
