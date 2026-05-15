from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/", summary="Root")
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
    }


@router.get("/health", summary="Health check")
async def health_check():
    return {"status": "healthy"}
