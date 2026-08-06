from fastapi import APIRouter, Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config.config import settings
from app.core.logging_config import setup_logging
import logging
from app.dependencies.deps import get_db
from app.middleware.errors import (
    db_integrity_error_handler,
    global_exception_handler,
    validation_error_handler,
)
from app.middleware.rate_limit import limiter, custom_rate_limit_exceeded_handler
from app.routes import admin, analytics, auth, organization
from app.ai.routes import router as ai_router

# Initialize centralized logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-grade workforce productivity & onboarding platform backend.",
    version="1.0.0",
)

# Rate limiting setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(IntegrityError, db_integrity_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, global_exception_handler)

# API Versioning - Centralized v1 Router
api_v1_router = APIRouter(prefix=settings.API_V1_STR)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(organization.router)
api_v1_router.include_router(admin.router)
api_v1_router.include_router(analytics.router)
api_v1_router.include_router(ai_router)

app.include_router(api_v1_router)


@app.get("/health")
def health_check() -> dict[str, object]:
    """
    Health check endpoint for load balancers and monitoring systems.
    Returns service health status without dependency checks.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
    }


@app.get("/ready")
def readiness_check(db: Session = Depends(get_db)) -> dict[str, object]:
    """
    Readiness check endpoint with database connectivity verification.
    Returns service readiness status with dependency health.
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "service": settings.PROJECT_NAME,
            "version": "1.0.0",
            "dependencies": {
                "database": "healthy",
            },
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": settings.PROJECT_NAME,
                "version": "1.0.0",
                "dependencies": {
                    "database": "unhealthy",
                },
            },
        )
