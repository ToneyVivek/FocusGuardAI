from fastapi import APIRouter, Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError

from app.config.config import settings
from app.core.logging_config import setup_logging
from app.dependencies.deps import get_db
from app.middleware.errors import (
    db_integrity_error_handler,
    global_exception_handler,
    validation_error_handler,
)
from app.middleware.rate_limit import limiter, custom_rate_limit_exceeded_handler
from app.routes import admin, auth, organization

# Initialize centralized logging
setup_logging()

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

app.include_router(api_v1_router)


@app.get("/")
def read_root():
    """Service status health check endpoint."""
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
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
def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check endpoint with database connectivity verification.
    Returns service readiness status with dependency health.
    """
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {
            "status": "ready",
            "service": settings.PROJECT_NAME,
            "version": "1.0.0",
            "dependencies": {
                "database": "healthy",
            },
        }
    except Exception as e:
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "service": settings.PROJECT_NAME,
            "version": "1.0.0",
            "dependencies": {
                "database": "unhealthy",
            },
        }
