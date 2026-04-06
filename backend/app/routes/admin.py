# app/routes/admin.py — Admin endpoints (thin controllers)

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies import get_db, require_admin
from app.schemas.book import BookCreate, BookUpdate, BookResponse
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.services import book_service, student_service, transaction_service
from app.services.auth_service import verify_password, hash_password

router = APIRouter()


class AdminProfileUpdate(BaseModel):
    name: Optional[str] = None
    old_password: Optional[str] = None
    new_password: Optional[str] = None


# ── Dashboard Stats ───────────────────────────────────────────────────

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    """Get dashboard statistics."""
    return transaction_service.get_dashboard_stats(db)


# ── Books ─────────────────────────────────────────────────────────────

@router.get("/books")
def get_books(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Get paginated list of books."""
    return book_service.get_books(db, page=page, per_page=per_page, search=search)


@router.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    """Get a single book by ID."""
    return book_service.get_book_by_id(db, book_id)


@router.post("/books", response_model=BookResponse)
def add_book(book: BookCreate, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    """Add a new book to the library. Auto-generates physical BookCopy records."""
    return book_service.add_book(
        db,
        title=book.title,
        author=book.author,
        isbn=book.isbn,
        pages=book.pages,
        price=book.price,
        category=book.category,
        quantity=book.quantity,
    )


@router.put("/books/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    book: BookUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Update a book's details."""
    updates = book.model_dump(exclude_unset=True)
    return book_service.update_book(db, book_id, **updates)


@router.patch("/books/{book_id}/increase")
def increase_book_quantity(
    book_id: int,
    amount: int = Query(1, ge=1, le=100),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Increase book quantity (add copies). Auto-generates new BookCopy records."""
    book = book_service.increase_quantity(db, book_id, amount)
    return {"message": f"Added {amount} copies", "quantity": book.quantity, "available": book.available}


@router.patch("/books/{book_id}/decrease")
def decrease_book_quantity(
    book_id: int,
    amount: int = Query(1, ge=1, le=100),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Decrease book quantity (remove copies). Cannot go below borrowed count."""
    book = book_service.decrease_quantity(db, book_id, amount)
    return {"message": f"Removed {amount} copies", "quantity": book.quantity, "available": book.available}


# ── Book Copies (Physical Inventory) ─────────────────────────────────

@router.get("/books/{book_id}/copies")
def get_book_copies(
    book_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """View all physical copies of a book with their status and condition."""
    copies = book_service.get_book_copies(db, book_id)
    return [
        {
            "id": c.id,
            "barcode": c.barcode,
            "condition": c.condition,
            "status": c.status,
            "created_at": c.created_at,
        }
        for c in copies
    ]


# ── Students ──────────────────────────────────────────────────────────

@router.get("/students")
def get_students(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Get paginated list of students."""
    return student_service.get_students(db, page=page, per_page=per_page, search=search)


@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    """Get a single student by ID."""
    return student_service.get_student_by_id(db, student_id)


@router.post("/students", response_model=StudentResponse)
def add_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Add a new student (admin-initiated)."""
    return student_service.add_student(
        db,
        username=student.username,
        password=student.password,
        name=student.name,
        email=student.email,
        phone=student.phone,
    )


@router.put("/students/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    student: StudentUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Update a student's details."""
    updates = student.model_dump(exclude_unset=True)
    return student_service.update_student(db, student_id, **updates)


@router.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    force: bool = Query(False, description="Force delete with lost-book fine (full book price)"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """
    Delete a student.
    Without force: fails if student has unreturned books.
    With force=true: charges full book price as lost-book fine and deletes.
    """
    return student_service.delete_student(db, student_id, force=force)


# ── Transactions ──────────────────────────────────────────────────────

@router.get("/transactions")
def get_transactions(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    """Get all transaction history."""
    return transaction_service.get_all_transactions(db)


@router.get("/overdue")
def get_overdue(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    """Get all overdue books."""
    return transaction_service.get_overdue_books(db)


@router.post("/return/{transaction_id}")
def process_return(
    transaction_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Admin-initiated book return."""
    return transaction_service.admin_return_book(db, transaction_id)


# ── Reservations (Admin View) ─────────────────────────────────────────

@router.get("/reservations")
def get_all_reservations(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """View all active reservations across all books."""
    from app.services import reservation_service
    return reservation_service.get_all_reservations(db)


@router.get("/books/{book_id}/reservations")
def get_book_reservations(
    book_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """View the waitlist queue for a specific book."""
    from app.services import reservation_service
    return reservation_service.get_book_reservations(db, book_id)


# ── Admin Profile (Settings) ──────────────────────────────────────────

@router.get("/profile")
def get_admin_profile(
    db: Session = Depends(get_db),
    claims: dict = Depends(require_admin),
):
    """Get admin's own profile data."""
    from app.models.admin import Admin
    admin = db.query(Admin).filter(Admin.id == claims["id"]).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    return {
        "id": admin.id,
        "username": admin.username,
        "name": admin.name,
        "role": admin.role,
        "created_at": admin.created_at,
    }


@router.put("/profile")
def update_admin_profile(
    payload: AdminProfileUpdate,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_admin),
):
    """Update admin's own profile (name, optional password change)."""
    from app.models.admin import Admin
    admin = db.query(Admin).filter(Admin.id == claims["id"]).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    if payload.name is not None:
        admin.name = payload.name.strip()

    if payload.new_password:
        if not payload.old_password:
            raise HTTPException(status_code=400, detail="Old password is required to set a new password")
        old_pw = payload.old_password[:72]
        new_pw = payload.new_password[:72]
        if not verify_password(old_pw, admin.password):
            raise HTTPException(status_code=400, detail="Old password is incorrect")
        if len(new_pw) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
        admin.password = hash_password(new_pw)

    db.commit()
    db.refresh(admin)
    return {
        "message": "Profile updated successfully",
        "name": admin.name,
    }
