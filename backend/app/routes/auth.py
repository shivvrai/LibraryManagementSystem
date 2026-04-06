# app/routes/auth.py — Authentication endpoints (thin controllers)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UsernameCheckRequest,
    UsernameCheckResponse,
)
from app.services import auth_service

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate admin or student and return JWT token."""
    return auth_service.authenticate(db, request.username, request.password)


@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new student account."""
    return auth_service.register_student(
        db,
        username=request.username,
        password=request.password,
        name=request.name,
        email=request.email,
        phone=request.phone,
    )


@router.post("/check-username", response_model=UsernameCheckResponse)
def check_username(request: UsernameCheckRequest, db: Session = Depends(get_db)):
    """Check if a username is available for registration."""
    available = auth_service.check_username_available(db, request.username)
    return {"available": available, "username": request.username}
