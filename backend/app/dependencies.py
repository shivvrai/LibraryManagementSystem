# app/dependencies.py — Dependency injection for database sessions and auth

import logging
from typing import Generator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.exceptions import AuthenticationError, ForbiddenError
from app.services.auth_service import decode_token

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── Database Session ──────────────────────────────────────────────────

def get_db() -> Generator[Session, None, None]:
    """Yields a SQLAlchemy session and ensures it is closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Auth Dependencies ─────────────────────────────────────────────────

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Decode JWT and return the claims dict. Raises 401 on failure."""
    claims = decode_token(token)
    if claims is None:
        raise AuthenticationError("Invalid or expired token")
    return claims


def require_admin(claims: dict = Depends(get_current_user)) -> dict:
    """Ensure the current user has admin role."""
    if claims.get("role") != "admin":
        raise ForbiddenError("Admin access required")
    return claims


def require_student(claims: dict = Depends(get_current_user)) -> dict:
    """Ensure the current user has student role and a valid id."""
    if claims.get("role") != "student":
        raise ForbiddenError("Student access required")
    if not claims.get("id"):
        raise AuthenticationError("Missing user id in token")
    return claims
