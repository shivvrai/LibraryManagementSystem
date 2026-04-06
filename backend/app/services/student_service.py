# app/services/student_service.py — Student business logic

import logging
import math
from typing import Optional

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError, ConflictError, ValidationError
from app.models.student import Student
from app.repositories.student_repo import StudentRepository
from app.repositories.transaction_repo import TransactionRepository
from app.services.auth_service import hash_password

logger = logging.getLogger(__name__)


def get_students(db: Session, page: int = 1, per_page: int = 50,
                 search: Optional[str] = None) -> dict:
    """Get paginated list of students with optional search."""
    repo = StudentRepository(db)
    skip = (page - 1) * per_page

    if search and search.strip():
        items = repo.search(search.strip(), skip=skip, limit=per_page)
        total = repo.search_count(search.strip())
    else:
        items = repo.get_all(skip=skip, limit=per_page)
        total = repo.count()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page else 1,
    }


def get_student_by_id(db: Session, student_id: int) -> Student:
    """Get a student by ID. Raises NotFoundError."""
    repo = StudentRepository(db)
    student = repo.get_by_id(student_id)
    if not student:
        raise NotFoundError("Student", student_id)
    return student


def add_student(db: Session, username: str, password: str, name: str,
                email: str = "", phone: str = "") -> Student:
    """Add a new student (admin-initiated)."""
    from app.services.auth_service import generate_registration_no, check_username_available

    repo = StudentRepository(db)

    if not check_username_available(db, username):
        raise ConflictError(f"Username '{username}' is already taken")

    reg_no = generate_registration_no(db)

    student = Student(
        registration_no=reg_no,
        username=username,
        password=hash_password(password),
        name=name,
        email=email,
        phone=phone,
    )
    repo.create(student)
    logger.info("Student added by admin: %s (reg: %s)", username, reg_no)
    return student


def update_student(db: Session, student_id: int, **updates) -> Student:
    """Update student details."""
    repo = StudentRepository(db)
    student = repo.get_by_id(student_id)
    if not student:
        raise NotFoundError("Student", student_id)

    for field in ("name", "email", "phone"):
        if field in updates and updates[field] is not None:
            setattr(student, field, updates[field])

    # Handle password update
    if "password" in updates and updates["password"]:
        student.password = hash_password(updates["password"])

    repo.update(student)
    logger.info("Student updated: id=%d", student_id)
    return student


def delete_student(db: Session, student_id: int, force: bool = False) -> dict:
    """
    Delete a student.

    Normal mode (force=False):
      Only succeeds if the student has NO active borrows.

    Force mode (force=True):
      Student has unreturned books → charge full book price as "lost book fine"
      (this is DIFFERENT from the ₹10/day late fine).
      Books are marked as lost, availability is NOT restored.
    """
    from app.repositories.book_repo import BookRepository

    repo = StudentRepository(db)
    txn_repo = TransactionRepository(db)
    book_repo = BookRepository(db)

    student = repo.get_by_id(student_id)
    if not student:
        raise NotFoundError("Student", student_id)

    active_borrows = txn_repo.get_student_active_borrows(student_id)

    if active_borrows and not force:
        # Build a summary of what they owe
        lost_book_fine = sum(
            txn.book.price for txn in active_borrows if txn.book
        )
        raise ValidationError(
            f"Student has {len(active_borrows)} unreturned book(s). "
            f"Either have them return all books, or force-delete with a "
            f"lost-book fine of ₹{lost_book_fine:.2f} (full book replacement cost)."
        )

    lost_book_fine_total = 0.0

    if active_borrows and force:
        # Charge full book price for each unreturned book
        for txn in active_borrows:
            if txn.book:
                book_price = txn.book.price
                lost_book_fine_total += book_price

                # Mark transaction as "lost" (not returned)
                txn.status = "lost"
                txn.fine = book_price
                txn_repo.update(txn)

                # Reduce book quantity (it's gone — not available, not coming back)
                txn.book.quantity = max(0, txn.book.quantity - 1)
                book_repo.update(txn.book)

        logger.info(
            "Lost-book fine charged: student=%d, fine=₹%.2f for %d book(s)",
            student_id, lost_book_fine_total, len(active_borrows),
        )

    repo.delete(student)
    logger.info("Student deleted: id=%d, name='%s'", student_id, student.name)

    return {
        "message": "Student deleted successfully",
        "lost_book_fine": lost_book_fine_total,
        "books_lost": len(active_borrows) if active_borrows else 0,
    }

