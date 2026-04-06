# app/routes/student.py — Student endpoints (thin controllers)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.dependencies import get_db, require_student
from app.schemas.transaction import BorrowRequest
from app.schemas.reservation import ReserveRequest
from app.services import book_service, transaction_service
from app.services.auth_service import verify_password, hash_password

router = APIRouter()


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    old_password: Optional[str] = None
    new_password: Optional[str] = None


@router.get("/books")
def get_available_books(
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Get all available books for browsing (paginated)."""
    result = book_service.get_books(db, page=page, per_page=per_page)
    return result["items"]


@router.get("/books/search")
def search_books(
    q: str = Query(..., min_length=1, description="Search query (supports fuzzy matching)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """
    Full-text book search with fuzzy matching powered by Elasticsearch.
    Falls back to SQL ILIKE search if Elasticsearch is unavailable.
    Supports typo tolerance — e.g. 'hary poter' finds 'Harry Potter'.
    """
    result = book_service.get_books(
        db, search=q, page=page, per_page=per_page, category=category
    )
    return result


@router.post("/borrow")
def borrow_book(
    request: BorrowRequest,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Borrow a book. A specific physical copy is assigned automatically."""
    return transaction_service.borrow_book(db, student_id=claims["id"], book_id=request.book_id)


@router.post("/return/{transaction_id}")
def return_book(
    transaction_id: int,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Return a borrowed book."""
    return transaction_service.return_book(db, transaction_id, student_id=claims["id"])


@router.post("/renew/{transaction_id}")
def renew_book(
    transaction_id: int,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """
    Renew a borrowed book (extend due date).
    Rules: max 2 renewals, no unpaid fines, no waitlist for this book.
    """
    return transaction_service.renew_book(db, transaction_id, student_id=claims["id"])


@router.get("/my-books")
def get_my_books(
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Get currently borrowed books with copy barcode and renewal info."""
    return transaction_service.get_student_borrowed_books(db, student_id=claims["id"])


@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Get full borrow/return history."""
    return transaction_service.get_student_history(db, student_id=claims["id"])


@router.get("/fines")
def get_fines(
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Get pending fines and borrow count."""
    return transaction_service.get_student_fines(db, student_id=claims["id"])


# ── Reservations (Waitlist) ───────────────────────────────────────────

@router.post("/reserve")
def reserve_book(
    request: ReserveRequest,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Reserve a book when all copies are unavailable. Join the waitlist."""
    from app.services import reservation_service
    return reservation_service.reserve_book(db, student_id=claims["id"], book_id=request.book_id)


@router.delete("/reserve/{reservation_id}")
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Cancel a reservation."""
    from app.services import reservation_service
    return reservation_service.cancel_reservation(db, reservation_id, student_id=claims["id"])


@router.get("/reservations")
def get_my_reservations(
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """View your active reservations (waitlist positions)."""
    from app.services import reservation_service
    return reservation_service.get_student_reservations(db, student_id=claims["id"])


# ── Profile (Settings) ────────────────────────────────────────────────

@router.get("/profile")
def get_student_profile(
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Get student's own profile data."""
    from app.models.student import Student
    student = db.query(Student).filter(Student.id == claims["id"]).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return {
        "id": student.id,
        "username": student.username,
        "registration_no": student.registration_no,
        "name": student.name,
        "email": student.email or "",
        "phone": student.phone or "",
        "borrowed_books": student.borrowed_books,
        "fine_amount": student.fine_amount,
        "created_at": student.created_at,
    }


@router.put("/profile")
def update_student_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Update student's own profile (name, email, phone, optional password change)."""
    from app.models.student import Student
    student = db.query(Student).filter(Student.id == claims["id"]).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if payload.name is not None:
        student.name = payload.name.strip()
    if payload.email is not None:
        student.email = payload.email.strip()
    if payload.phone is not None:
        student.phone = payload.phone.strip()

    # Password change
    if payload.new_password:
        if not payload.old_password:
            raise HTTPException(status_code=400, detail="Old password is required to set a new password")
        old_pw = payload.old_password[:72]
        new_pw = payload.new_password[:72]
        if not verify_password(old_pw, student.password):
            raise HTTPException(status_code=400, detail="Old password is incorrect")
        if len(new_pw) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
        student.password = hash_password(new_pw)

    db.commit()
    db.refresh(student)
    return {
        "message": "Profile updated successfully",
        "name": student.name,
        "email": student.email,
        "phone": student.phone,
    }
