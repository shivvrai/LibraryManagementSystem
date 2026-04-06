# app/exceptions.py — Custom exception hierarchy & global handlers

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# ── Custom Exceptions ─────────────────────────────────────────────────

class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    """Resource not found (404)."""

    def __init__(self, resource: str, identifier: str | int = ""):
        detail = f"{resource} not found" if not identifier else f"{resource} with id '{identifier}' not found"
        super().__init__(detail, status_code=404)


class ConflictError(AppException):
    """Duplicate or conflicting resource (409)."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status_code=409)


class ValidationError(AppException):
    """Business rule validation failure (400)."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class AuthenticationError(AppException):
    """Invalid credentials or token (401)."""

    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, status_code=401)


class ForbiddenError(AppException):
    """Insufficient permissions (403)."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)


# ── Exception Handlers ────────────────────────────────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning("AppException [%d]: %s", exc.status_code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", str(exc))
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": "Internal server error"},
        )
