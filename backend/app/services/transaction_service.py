# app/services/transaction_service.py — Borrow/return/renew/fine business logic
#
# Concurrency Control:
#   All mutations use pessimistic locking (SELECT FOR UPDATE) on the Book row.
#   Consistent lock ordering: Book → BookCopy → Student → Transaction
#   This prevents race conditions on concurrent borrows and deadlocks.

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import NotFoundError, ValidationError
from app.models.transaction import Transaction
from app.repositories.book_repo import BookRepository
from app.repositories.book_copy_repo import BookCopyRepository
from app.repositories.student_repo import StudentRepository
from app.repositories.transaction_repo import TransactionRepository
from app.services.event_bus import event_bus, BOOK_AVAILABLE

logger = logging.getLogger(__name__)


def borrow_book(db: Session, student_id: int, book_id: int) -> dict:
    """
    Process a book borrow request.
    Uses pessimistic locking to prevent race conditions.
    Assigns a specific physical BookCopy to the transaction.
    
    Lock ordering: Book → BookCopy → Student → Transaction
    """
    book_repo = BookRepository(db)
    copy_repo = BookCopyRepository(db)
    student_repo = StudentRepository(db)
    txn_repo = TransactionRepository(db)

    # Step 1: Lock the book row (prevents concurrent borrows)
    book = book_repo.get_by_id_locked(book_id)
    if not book:
        raise NotFoundError("Book", book_id)
    if book.available <= 0:
        raise ValidationError(f"'{book.title}' is not available for borrowing")

    # Step 2: Claim a specific physical copy (also locked)
    copy = copy_repo.get_available_copy_locked(book_id)
    if not copy:
        raise ValidationError(f"No available copies of '{book.title}'")

    # Step 3: Validate student
    student = student_repo.get_by_id(student_id)
    if not student:
        raise NotFoundError("Student", student_id)

    # Check borrow limit
    if student.borrowed_books >= settings.MAX_BOOKS_PER_STUDENT:
        raise ValidationError(
            f"Maximum borrow limit of {settings.MAX_BOOKS_PER_STUDENT} books reached"
        )

    # Check for duplicate borrow
    existing = txn_repo.get_active_borrow(student_id, book_id)
    if existing:
        raise ValidationError(f"You have already borrowed '{book.title}'")

    # Step 4: Create transaction with copy assignment
    now = datetime.utcnow()
    due_date = now + timedelta(days=settings.RETURN_DAYS)

    transaction = Transaction(
        student_id=student_id,
        book_id=book_id,
        book_copy_id=copy.id,
        borrow_date=now,
        due_date=due_date,
        status="borrowed",
    )
    txn_repo.create(transaction)

    # Update copy status
    copy.status = "borrowed"
    copy_repo.update(copy)

    # Update student borrow count
    student.borrowed_books += 1
    student_repo.update(student)

    # Reconcile book counts from copies (single source of truth)
    from app.services.book_service import reconcile_book_counts
    reconcile_book_counts(db, book_id)

    logger.info(
        "Book borrowed: student=%d, book=%d, copy=%s, due=%s",
        student_id, book_id, copy.barcode, due_date.isoformat(),
    )

    return {
        "message": f"Successfully borrowed '{book.title}'",
        "transaction_id": transaction.id,
        "due_date": due_date.strftime("%Y-%m-%d"),
        "barcode": copy.barcode,
    }


def return_book(db: Session, transaction_id: int, student_id: int) -> dict:
    """
    Process a book return. Deterministic flow:
    1. Lock book row
    2. Update copy status to 'available' (temporarily)
    3. Check reservations — may change copy to 'held'
    4. Reconcile book counts from copies
    5. Update student counts
    
    Lock ordering: Book → BookCopy → Reservation → Student → Transaction
    """
    txn_repo = TransactionRepository(db)
    book_repo = BookRepository(db)
    copy_repo = BookCopyRepository(db)
    student_repo = StudentRepository(db)

    transaction = txn_repo.get_by_id(transaction_id)
    if not transaction:
        raise NotFoundError("Transaction", transaction_id)
    if transaction.student_id != student_id:
        raise ValidationError("This transaction does not belong to you")
    if transaction.status == "returned":
        raise ValidationError("This book has already been returned")

    # Step 1: Lock the book row
    book = book_repo.get_by_id_locked(transaction.book_id)

    # Calculate fine
    now = datetime.utcnow()
    days_overdue = max(0, (now - transaction.due_date).days)
    fine = days_overdue * settings.FINE_PER_DAY

    # Step 2: Update transaction
    transaction.return_date = now
    transaction.status = "returned"
    transaction.fine = fine
    txn_repo.update(transaction)

    # Step 3: Update copy status to available (temporarily)
    returned_copy_id = transaction.book_copy_id
    if returned_copy_id:
        copy = copy_repo.get_by_id(returned_copy_id)
        if copy:
            copy.status = "available"
            copy_repo.update(copy)

            # Step 4: Check reservations — may change copy to 'held'
            from app.services.reservation_service import fulfill_next_reservation
            reservation_fulfilled = fulfill_next_reservation(db, transaction.book_id, returned_copy_id)

            if reservation_fulfilled:
                logger.info(
                    "Returned copy assigned to reservation: book=%d, copy=%s",
                    transaction.book_id, copy.barcode,
                )
    else:
        # Legacy transaction without copy tracking — just increment availability
        if book:
            was_unavailable = book.available == 0
            book.available += 1
            book_repo.update(book)

            if was_unavailable:
                event_bus.publish(BOOK_AVAILABLE, {
                    "book_id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "category": book.category,
                })

    # Step 5: Reconcile book counts from copies (single source of truth)
    from app.services.book_service import reconcile_book_counts
    reconcile_book_counts(db, transaction.book_id)

    # Step 6: Update student
    student = student_repo.get_by_id(student_id)
    if student:
        student.borrowed_books = max(0, student.borrowed_books - 1)
        student.fine_amount += fine
        student_repo.update(student)

    logger.info(
        "Book returned: txn=%d, student=%d, fine=%.2f, overdue=%d days",
        transaction_id, student_id, fine, days_overdue,
    )

    return {
        "message": "Book returned successfully",
        "fine": fine,
        "days_overdue": days_overdue,
    }


def admin_return_book(db: Session, transaction_id: int) -> dict:
    """Admin-initiated return (uses the student_id from the transaction)."""
    txn_repo = TransactionRepository(db)
    transaction = txn_repo.get_by_id(transaction_id)
    if not transaction:
        raise NotFoundError("Transaction", transaction_id)
    return return_book(db, transaction_id, transaction.student_id)


# ── Renewal Logic ─────────────────────────────────────────────────────

def renew_book(db: Session, transaction_id: int, student_id: int) -> dict:
    """
    Renew a borrowed book, extending the due date.
    
    Business Rules:
    1. Transaction must belong to the student and be in 'borrowed' status
    2. renewal_count < MAX_RENEWALS
    3. Student must have no unpaid fines
    4. No other student is waiting in the reservation queue for this book
    5. Due date is extended from the EXISTING due_date (not from now) to prevent gaming
    
    Lock ordering: Book → Transaction (check reservations under lock)
    """
    txn_repo = TransactionRepository(db)
    book_repo = BookRepository(db)

    transaction = txn_repo.get_by_id(transaction_id)
    if not transaction:
        raise NotFoundError("Transaction", transaction_id)
    if transaction.student_id != student_id:
        raise ValidationError("This transaction does not belong to you")
    if transaction.status != "borrowed":
        raise ValidationError("Only active borrows can be renewed")

    # Lock the book to prevent reservation slip-in between check and update
    book = book_repo.get_by_id_locked(transaction.book_id)
    if not book:
        raise NotFoundError("Book", transaction.book_id)

    # Rule 1: Check renewal limit
    if transaction.renewal_count >= settings.MAX_RENEWALS:
        raise ValidationError(
            f"Maximum renewal limit of {settings.MAX_RENEWALS} reached for this book"
        )

    # Rule 2: Check unpaid fines
    from app.repositories.student_repo import StudentRepository
    student_repo = StudentRepository(db)
    student = student_repo.get_by_id(student_id)
    if not student:
        raise NotFoundError("Student", student_id)
    if student.fine_amount > 0:
        raise ValidationError(
            f"Cannot renew — you have unpaid fines of ₹{student.fine_amount:.2f}. "
            f"Please clear your fines first."
        )

    # Rule 3: Check reservation queue (under lock)
    from app.repositories.reservation_repo import ReservationRepository
    reservation_repo = ReservationRepository(db)
    waiting_count = reservation_repo.count_waiting(transaction.book_id)
    if waiting_count > 0:
        raise ValidationError(
            f"Cannot renew — {waiting_count} student(s) are waiting in the reservation queue"
        )

    # All checks passed — extend due date from EXISTING due_date (not now)
    old_due_date = transaction.due_date
    new_due_date = old_due_date + timedelta(days=settings.RETURN_DAYS)
    transaction.due_date = new_due_date
    transaction.renewal_count += 1
    txn_repo.update(transaction)

    logger.info(
        "Book renewed: txn=%d, student=%d, renewal=%d/%d, new_due=%s",
        transaction_id, student_id, transaction.renewal_count,
        settings.MAX_RENEWALS, new_due_date.isoformat(),
    )

    return {
        "message": f"Successfully renewed '{book.title}'",
        "renewal_count": transaction.renewal_count,
        "max_renewals": settings.MAX_RENEWALS,
        "old_due_date": old_due_date.strftime("%Y-%m-%d"),
        "new_due_date": new_due_date.strftime("%Y-%m-%d"),
    }


# ── Read Operations ───────────────────────────────────────────────────

def get_overdue_books(db: Session) -> list:
    """Get all overdue transactions with calculated fines."""
    txn_repo = TransactionRepository(db)
    overdue = txn_repo.get_overdue_transactions()
    now = datetime.utcnow()

    result = []
    for txn in overdue:
        days = (now - txn.due_date).days
        result.append({
            "transaction_id": txn.id,
            "student_id": txn.student_id,
            "student_name": txn.student.name if txn.student else "Unknown",
            "book_id": txn.book_id,
            "book_title": txn.book.title if txn.book else "Unknown",
            "barcode": txn.book_copy.barcode if txn.book_copy else None,
            "borrow_date": txn.borrow_date,
            "due_date": txn.due_date,
            "days_overdue": days,
            "fine": days * settings.FINE_PER_DAY,
        })
    return result


def get_all_transactions(db: Session, skip: int = 0, limit: int = 200) -> list:
    """Get all transactions with student/book details."""
    txn_repo = TransactionRepository(db)
    transactions = txn_repo.get_all_with_details(skip=skip, limit=limit)

    result = []
    for txn in transactions:
        result.append({
            "id": txn.id,
            "student_id": txn.student_id,
            "student_name": txn.student.name if txn.student else "Unknown",
            "book_id": txn.book_id,
            "book_title": txn.book.title if txn.book else "Unknown",
            "barcode": txn.book_copy.barcode if txn.book_copy else None,
            "borrow_date": txn.borrow_date,
            "due_date": txn.due_date,
            "return_date": txn.return_date,
            "status": txn.status,
            "fine": txn.fine or 0,
            "renewal_count": txn.renewal_count or 0,
        })
    return result


def get_student_borrowed_books(db: Session, student_id: int) -> list:
    """Get currently borrowed books for a student."""
    txn_repo = TransactionRepository(db)
    borrows = txn_repo.get_student_active_borrows(student_id)
    now = datetime.utcnow()

    result = []
    for txn in borrows:
        days_overdue = max(0, (now - txn.due_date).days)
        fine = days_overdue * settings.FINE_PER_DAY
        result.append({
            "id": txn.id,
            "transaction_id": txn.id,
            "book": {
                "id": txn.book.id,
                "title": txn.book.title,
                "author": txn.book.author,
                "isbn": txn.book.isbn,
                "category": txn.book.category,
            } if txn.book else {},
            "barcode": txn.book_copy.barcode if txn.book_copy else None,
            "borrow_date": txn.borrow_date,
            "due_date": txn.due_date,
            "fine": fine,
            "status": txn.status,
            "renewal_count": txn.renewal_count or 0,
            "max_renewals": settings.MAX_RENEWALS,
        })
    return result


def get_student_history(db: Session, student_id: int) -> list:
    """Get full transaction history for a student."""
    txn_repo = TransactionRepository(db)
    transactions = txn_repo.get_student_history(student_id)

    result = []
    for txn in transactions:
        result.append({
            "id": txn.id,
            "book_title": txn.book.title if txn.book else "Unknown",
            "barcode": txn.book_copy.barcode if txn.book_copy else None,
            "borrow_date": txn.borrow_date,
            "due_date": txn.due_date,
            "return_date": txn.return_date,
            "status": txn.status,
            "fine": txn.fine or 0,
            "renewal_count": txn.renewal_count or 0,
        })
    return result


def get_student_fines(db: Session, student_id: int) -> dict:
    """Get fine summary for a student."""
    student_repo = StudentRepository(db)
    student = student_repo.get_by_id(student_id)
    if not student:
        raise NotFoundError("Student", student_id)
    return {
        "fine_amount": student.fine_amount,
        "borrowed_books": student.borrowed_books,
    }


def get_dashboard_stats(db: Session) -> dict:
    """Get aggregate statistics for the admin dashboard."""
    book_repo = BookRepository(db)
    student_repo = StudentRepository(db)
    txn_repo = TransactionRepository(db)

    total_fines = sum(
        s.fine_amount for s in student_repo.get_all(limit=10000)
    )

    return {
        "total_books": book_repo.count(),
        "total_students": student_repo.count(),
        "active_borrows": txn_repo.count_active_borrows(),
        "overdue_books": txn_repo.count_overdue(),
        "total_fines": round(total_fines, 2),
        "total_transactions": txn_repo.count(),
    }
