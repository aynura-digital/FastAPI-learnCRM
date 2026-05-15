from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import verify_api_key
from app.models.user import APIUser
from app.schemas.auth import RegisterRequest, RegisterResponse, TokenRequest, TokenResponse
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new service account",
    description="Create a new API user (service account). Requires a valid API key.",
)
async def register(
    body: RegisterRequest,
    _api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    existing = db.query(APIUser).filter(APIUser.username == body.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )

    user = APIUser(
        username=body.username,
        hashed_password=hash_password(body.password),
        service_name=body.service_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return RegisterResponse(
        id=user.id,
        username=user.username,
        service_name=user.service_name,
        message="Service account created successfully",
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Obtain a JWT access token",
    description="Authenticate with username/password and receive a bearer token.",
)
async def login(body: TokenRequest, db: Session = Depends(get_db)):
    user = db.query(APIUser).filter(APIUser.username == body.username).first()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token = create_access_token(subject=user.username)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.access_token_expire_minutes,
    )
