import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import Base, engine
from app.middleware.rate_limiter import limiter
from app.routers import academic_sync, auth, crm_sync, health

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Alembic is the canonical migration tool for this project. The
    # create_all fallback below is intentional and used ONLY in DEBUG mode
    # for quick local bootstrapping and tests; it must never run against a
    # database whose schema is owned by Alembic, as the two can diverge.
    if settings.debug:
        logger.info("DEBUG mode: creating database tables via metadata.create_all ...")
        Base.metadata.create_all(bind=engine)
    else:
        logger.info("Production mode: schema is managed by Alembic.")
    logger.info("%s v%s started.", settings.app_name, settings.app_version)

    yield

    logger.info("Application shutdown...")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "RESTful API microservice for automated data synchronization "
        "between a corporate CRM system and an internal Academic "
        "Progress Tracking System."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(crm_sync.router)
app.include_router(academic_sync.router)

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------



