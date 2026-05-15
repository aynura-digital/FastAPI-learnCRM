"""
CRM → Academic System synchronization endpoints.

These endpoints are called by the CRM system to push student and
payment data into the Academic Progress Tracking System.
"""

import logging

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.middleware.rate_limiter import limiter
from app.models.user import APIUser
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentSyncResult
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate
from app.schemas.sync_log import SyncLogResponse
from app.services import payment_service, student_service, sync_service
from app.utils.logger import log_sync_event

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/crm",
    tags=["CRM Sync (CRM → Academic)"],
)


# ── Student endpoints ──────────────────────────────────────────────────


@router.post(
    "/students/sync",
    response_model=StudentResponse,
    responses={
        200: {"description": "Existing student updated"},
        201: {"description": "New student created"},
    },
    summary="Sync student from CRM",
    description=(
        "Create or update a student profile in the Academic System. "
        "If a student with the given `crm_student_id` already exists, "
        "the record is updated (HTTP 200); otherwise a new student is "
        "created (HTTP 201)."
    ),
)
@limiter.limit("60/minute")
async def sync_student(
    request: Request,
    body: StudentCreate,
    response: Response,
    db: Session = Depends(get_db),
    _user: APIUser = Depends(get_current_user),
):
    try:
        student, action = student_service.create_or_update_student(db, body)
        response.status_code = (
            status.HTTP_201_CREATED if action == "created" else status.HTTP_200_OK
        )
        logger.info("Student %s %s: %s", body.crm_student_id, action, student.id)
        return student
    except Exception as exc:
        log_sync_event(
            db,
            direction="crm_to_academic",
            entity_type="student",
            entity_id=body.crm_student_id,
            action="error",
            status="failure",
            error_message=str(exc),
            request_payload=body.model_dump(),
        )
        raise


@router.patch(
    "/students/{crm_student_id}",
    response_model=StudentResponse,
    summary="Partially update a student",
)
@limiter.limit("60/minute")
async def update_student(
    request: Request,
    crm_student_id: str,
    body: StudentUpdate,
    db: Session = Depends(get_db),
    _user: APIUser = Depends(get_current_user),
):
    return student_service.update_student(db, crm_student_id, body)


@router.get(
    "/students",
    response_model=list[StudentResponse],
    summary="List all synced students",
)
@limiter.limit("30/minute")
async def list_students(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    _user: APIUser = Depends(get_current_user),
):
    return student_service.list_students(
        db, skip=skip, limit=limit, active_only=active_only
    )


@router.get(
    "/students/{crm_student_id}",
    response_model=StudentResponse,
    summary="Get a single student by CRM ID",
)
@limiter.limit("60/minute")
async def get_student(
    request: Request,
    crm_student_id: str,
    db: Session = Depends(get_db),
    _user: APIUser = Depends(get_current_user),
):
    return student_service.get_student_or_404(db, crm_student_id)


# ── Payment endpoints ──────────────────────────────────────────────────


@router.post(
    "/payments/sync",
    response_model=PaymentSyncResult,
    summary="Sync payment from CRM",
    description=(
        "Process a payment event. If `payment_status` is **Paid**, "
        "the listed academic modules are automatically unlocked."
    ),
)
@limiter.limit("60/minute")
async def sync_payment(
    request: Request,
    body: PaymentCreate,
    db: Session = Depends(get_db),
    _user: APIUser = Depends(get_current_user),
):
    try:
        return payment_service.process_payment(db, body)
    except Exception as exc:
        log_sync_event(
            db,
            direction="crm_to_academic",
            entity_type="payment",
            entity_id=body.crm_payment_id,
            action="error",
            status="failure",
            error_message=str(exc),
            request_payload=body.model_dump(),
        )
        raise


@router.get(
    "/payments",
    response_model=list[PaymentResponse],
    summary="List payments",
)
@limiter.limit("30/minute")
async def list_payments(
    request: Request,
    crm_student_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: APIUser = Depends(get_current_user),
):
    return payment_service.list_payments(
        db, crm_student_id=crm_student_id, skip=skip, limit=limit
    )


# ── Sync Logs ──────────────────────────────────────────────────────────


@router.get(
    "/sync-logs",
    response_model=list[SyncLogResponse],
    summary="Query synchronization logs",
    description="Retrieve sync audit logs. Filter by direction, entity type, or status.",
)
@limiter.limit("30/minute")
async def get_sync_logs(
    request: Request,
    direction: str | None = Query(None, examples=["crm_to_academic"]),
    entity_type: str | None = Query(None, examples=["student"]),
    log_status: str | None = Query(None, alias="status", examples=["failure"]),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: APIUser = Depends(get_current_user),
):
    return sync_service.get_sync_logs(
        db,
        direction=direction,
        entity_type=entity_type,
        status=log_status,
        skip=skip,
        limit=limit,
    )
