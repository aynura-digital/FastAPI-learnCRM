"""
Academic System → CRM synchronization endpoints.

These endpoints are used by the Academic / LMS system to record
student progress and to push that data back to the CRM.
"""

import logging

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.middleware.rate_limiter import limiter
from app.models.user import APIUser
from app.schemas.academic import (
    AcademicProgressCRMPayload,
    AcademicRecordCreate,
    AcademicRecordResponse,
    AcademicRecordUpdate,
)
from app.services import academic_service
from app.utils.logger import log_sync_event

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/academic",
    tags=["Academic Sync (Academic → CRM)"],
)


@router.post(
    "/records",
    response_model=AcademicRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an academic record",
    description=(
        "Record attendance, grade, and progress for a student's module. "
        "The student must already exist (synced from CRM)."
    ),
)
@limiter.limit("60/minute")
async def create_record(
    request: Request,
    body: AcademicRecordCreate,
    db: Session = Depends(get_db),
    _user: APIUser = Depends(get_current_user),
):
    try:
        return academic_service.create_academic_record(db, body)
    except Exception as exc:
        log_sync_event(
            db,
            direction="academic_to_crm",
            entity_type="academic_record",
            entity_id=body.crm_student_id,
            action="error",
            status="failure",
            error_message=str(exc),
            request_payload=body.model_dump(mode="json"),
        )
        raise


@router.patch(
    "/records/{record_id}",
    response_model=AcademicRecordResponse,
    summary="Update an academic record",
)
@limiter.limit("60/minute")
async def update_record(
    request: Request,
    record_id: str,
    body: AcademicRecordUpdate,
    db: Session = Depends(get_db),
    _user: APIUser = Depends(get_current_user),
):
    try:
        return academic_service.update_academic_record(db, record_id, body)
    except Exception as exc:
        log_sync_event(
            db,
            direction="academic_to_crm",
            entity_type="academic_record",
            entity_id=record_id,
            action="error",
            status="failure",
            error_message=str(exc),
            request_payload=body.model_dump(mode="json", exclude_unset=True),
        )
        raise


@router.get(
    "/records/{crm_student_id}",
    response_model=list[AcademicRecordResponse],
    summary="Get academic records for a student",
)
@limiter.limit("30/minute")
async def get_student_records(
    request: Request,
    crm_student_id: str,
    db: Session = Depends(get_db),
    _user: APIUser = Depends(get_current_user),
):
    return academic_service.list_records_for_student(db, crm_student_id)


@router.get(
    "/progress/{crm_student_id}/crm-payload",
    response_model=list[AcademicProgressCRMPayload],
    summary="Build CRM progress payload",
    description=(
        "Generate the payload that would be sent to the CRM system "
        "containing a student's full academic progress."
    ),
)
@limiter.limit("30/minute")
async def crm_payload(
    request: Request,
    crm_student_id: str,
    db: Session = Depends(get_db),
    _user: APIUser = Depends(get_current_user),
):
    return academic_service.build_crm_payload(db, crm_student_id)
