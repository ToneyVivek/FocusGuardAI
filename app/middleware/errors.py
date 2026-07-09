from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

import logging

logger = logging.getLogger(__name__)

async def db_integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handles SQLAlchemy database integrity exceptions (e.g. duplicate keys)."""
    logger.error(f"Database integrity violation at {request.url}: {exc}")
    
    # Check common DB error signatures
    error_msg = str(exc).lower()
    detail = "Database integrity violation occurred."
    
    if "unique constraint" in error_msg or "duplicate key" in error_msg or "failed" in error_msg:
        detail = "A unique resource with this identifier already exists."
    elif "foreign key" in error_msg:
        detail = "Related database record references are invalid."
        
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": detail}
    )

async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles request body validation failures (Pydantic parsing failures)."""
    logger.warning(f"Request validation failure at {request.url}: {exc.errors()}")
    
    # Extract serializable error details (remove non-serializable objects)
    errors = []
    for error in exc.errors():
        serializable_error = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": error.get("input"),
        }
        errors.append(serializable_error)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors}
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler to catch any unhandled exceptions and prevent raw traceback leakage."""
    logger.error(f"Unhandled exception caught on request {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator."}
    )
