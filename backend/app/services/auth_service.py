# app/services/auth_service.py — Authentication business logic

import logging
import random
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import AuthenticationError, ConflictError, ValidationError
from app.models.admin import Admin
from app.models.student import Student
from app.repositories.admin_repo import AdminRepository
from app.repositories.student_repo import StudentRepository
from app.services.bloom_service import bloom_service

logger = logging.getLogger(__name__)


# ── Password Hashing ─────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(password[:72].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain[:72].encode("utf-8"), hashed.encode("utf-8"))


# ── JWT Token Management ─────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    """Create a JWT access token with expiration."""
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns claims dict or None."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None


# ── Authentication ────────────────────────────────────────────────────

def authenticate(db: Session, username: str, password: str) -> dict:
    """
    Authenticate a user (admin or student).
    Returns dict with access_token, role, and user info.
    Raises AuthenticationError on failure.
    """
    # Try admin first
    admin_repo = AdminRepository(db)
    admin = admin_repo.get_by_username(username)
    if admin and verify_password(password, admin.password):
        token = create_access_token({
            "sub": admin.username,
            "role": "admin",
            "id": admin.id,
            "name": admin.name,
        })
        logger.info("Admin '%s' logged in", username)
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": "admin",
            "user": {
                "id": admin.id,
                "username": admin.username,
                "name": admin.name,
                "role": "admin",
            },
        }

    # Try student
    student_repo = StudentRepository(db)
    student = student_repo.get_by_username(username)
    if student and verify_password(password, student.password):
        token = create_access_token({
            "sub": student.username,
            "role": "student",
            "id": student.id,
            "name": student.name,
            "registration_no": student.registration_no,
        })
        logger.info("Student '%s' logged in (reg: %s)", username, student.registration_no)
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": "student",
            "user": {
                "id": student.id,
                "username": student.username,
                "name": student.name,
                "registration_no": student.registration_no,
                "role": "student",
            },
        }

    raise AuthenticationError("Invalid username or password")


# ── Registration ──────────────────────────────────────────────────────

def generate_registration_no(db: Session) -> str:
    """Generate a unique 8-digit registration number."""
    student_repo = StudentRepository(db)
    for _ in range(100):
        reg_no = str(random.randint(10000000, 99999999))
        if not student_repo.get_by_registration_no(reg_no):
            return reg_no
    raise ValidationError("Failed to generate unique registration number")


def register_student(db: Session, username: str, password: str, name: str,
                     email: str = "", phone: str = "") -> dict:
    """Register a new student account."""
    student_repo = StudentRepository(db)
    admin_repo = AdminRepository(db)

    # ── Bloom Filter pre-check (O(1), no DB I/O when username is clearly new) ──
    if bloom_service.might_exist_username(username):
        # Bloom says "might exist" — do authoritative DB checks
        if student_repo.get_by_username(username):
            raise ConflictError(f"Username '{username}' is already taken")
        if admin_repo.get_by_username(username):
            raise ConflictError(f"Username '{username}' is already taken")
    # else: Bloom says "definitely not" — skip both DB queries

    reg_no = generate_registration_no(db)

    student = Student(
        registration_no=reg_no,
        username=username,
        password=hash_password(password),
        name=name,
        email=email,
        phone=phone,
    )
    student_repo.create(student)

    # ── Keep Bloom filter current ─────────────────────────────────────
    bloom_service.add_username(username)

    logger.info("Student registered: %s (reg: %s)", username, reg_no)
    return {
        "message": "Registration successful",
        "registration_no": reg_no,
        "username": username,
    }


def check_username_available(db: Session, username: str) -> bool:
    """
    Check if a username is available.

    Two-phase lookup:
      Phase 1 — Bloom Filter (O(1), no DB):  if filter says "definitely not",
                return available=True immediately.
      Phase 2 — DB check: only when filter says "might exist" (includes all
                false-positives at the configured 0.1% rate).
    """
    # Phase 1: Bloom pre-check
    if not bloom_service.might_exist_username(username):
        logger.debug("Bloom filter: '%s' definitely not present — skipping DB", username)
        return True

    # Phase 2: authoritative DB check (filter said "might exist")
    logger.debug("Bloom filter: '%s' might exist — querying DB", username)
    student_repo = StudentRepository(db)
    admin_repo = AdminRepository(db)
    return (
        student_repo.get_by_username(username) is None
        and admin_repo.get_by_username(username) is None
    )
