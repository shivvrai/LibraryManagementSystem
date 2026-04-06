# app/services/reservation_service.py — Waitlist & Reservation queue business logic

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError, ValidationError, ConflictError
from app.repositories.book_repo import BookRepository
from app.repositories.book_copy_repo import BookCopyRepository
from app.repositories.reservation_repo import ReservationRepository
from app.services.event_bus import event_bus, RESERVATION_READY

logger = logging.getLogger(__name__)

# How long a student has to pick up a reserved book
PICKUP_WINDOW_HOURS = 48


def reserve_book(db: Session, student_id: int, book_id: int) -> dict:
    """
    Add a student to the waitlist for a book.
    Only allowed when all copies are unavailable.
    """
    book_repo = BookRepository(db)
    reservation_repo = ReservationRepository(db)

    book = book_repo.get_by_id(book_id)
    if not book:
        raise NotFoundError("Book", book_id)

    if book.available > 0:
        raise ValidationError(
            f"'{book.title}' is currently available — borrow it directly instead of reserving."
        )

    # Check for duplicate reservation
    existing = reservation_repo.get_active_reservation(student_id, book_id)
    if existing:
        raise ConflictError(f"You already have an active reservation for '{book.title}'")

    # Assign next position in queue
    position = reservation_repo.get_next_position(book_id)

    from app.models.reservation import Reservation
    reservation = Reservation(
        student_id=student_id,
        book_id=book_id,
        position=position,
        status="waiting",
    )
    reservation_repo.create(reservation)

    logger.info(
        "Reservation created: student=%d, book=%d, position=%d",
        student_id, book_id, position,
    )

    return {
        "message": f"You are #{position} in the waitlist for '{book.title}'",
        "reservation_id": reservation.id,
        "position": position,
    }


def cancel_reservation(db: Session, reservation_id: int, student_id: int) -> dict:
    """Cancel a student's reservation."""
    reservation_repo = ReservationRepository(db)
    reservation = reservation_repo.get_by_id(reservation_id)

    if not reservation:
        raise NotFoundError("Reservation", reservation_id)
    if reservation.student_id != student_id:
        raise ValidationError("This reservation does not belong to you")
    if reservation.status not in ("waiting", "awaiting_pickup"):
        raise ValidationError(f"Cannot cancel a reservation with status '{reservation.status}'")

    # If a copy was held, release it
    if reservation.book_copy_id:
        copy_repo = BookCopyRepository(db)
        copy = copy_repo.get_by_id(reservation.book_copy_id)
        if copy and copy.status == "held":
            copy.status = "available"
            copy_repo.update(copy)

            # Reconcile book counts
            from app.services.book_service import reconcile_book_counts
            reconcile_book_counts(db, reservation.book_id)

    reservation.status = "cancelled"
    reservation_repo.update(reservation)

    logger.info("Reservation cancelled: id=%d, student=%d", reservation_id, student_id)
    return {"message": "Reservation cancelled successfully"}


def expire_stale_reservations(db: Session, book_id: int) -> int:
    """
    Lazy expiry: expire any 'awaiting_pickup' reservations that have passed
    their expires_at time. Releases held copies back to available.
    Returns the count of expired reservations.
    """
    reservation_repo = ReservationRepository(db)
    copy_repo = BookCopyRepository(db)

    expired_list = reservation_repo.get_expired_awaiting(book_id)
    expired_count = 0

    for res in expired_list:
        res.status = "expired"
        # Release the held copy
        if res.book_copy_id:
            copy = copy_repo.get_by_id(res.book_copy_id)
            if copy and copy.status == "held":
                copy.status = "available"
                copy_repo.update(copy)
        reservation_repo.update(res)
        expired_count += 1

        logger.info(
            "Reservation expired: id=%d, student=%d, book=%d",
            res.id, res.student_id, book_id,
        )

    if expired_count > 0:
        from app.services.book_service import reconcile_book_counts
        reconcile_book_counts(db, book_id)

    return expired_count


def fulfill_next_reservation(db: Session, book_id: int, returned_copy_id: int) -> bool:
    """
    Called when a book is returned. Checks the waitlist and assigns
    the returned copy to the next student in line.

    Returns True if a reservation was fulfilled (copy is held),
    False if no reservation exists (copy stays available).
    """
    reservation_repo = ReservationRepository(db)
    copy_repo = BookCopyRepository(db)

    # First, clean up any stale reservations
    expire_stale_reservations(db, book_id)

    # Get next in queue
    next_reservation = reservation_repo.get_next_waiting(book_id)

    if not next_reservation:
        return False  # No one waiting — copy stays available

    # Bind the physical copy to the reservation
    copy = copy_repo.get_by_id(returned_copy_id)
    if not copy:
        return False

    now = datetime.utcnow()

    # Hold the copy for the reserved student
    copy.status = "held"
    copy_repo.update(copy)

    # Update reservation
    next_reservation.status = "awaiting_pickup"
    next_reservation.book_copy_id = copy.id
    next_reservation.notified_at = now
    next_reservation.expires_at = now + timedelta(hours=PICKUP_WINDOW_HOURS)
    reservation_repo.update(next_reservation)

    logger.info(
        "Reservation fulfilled: reservation=%d, student=%d, book=%d, copy=%d, expires=%s",
        next_reservation.id, next_reservation.student_id, book_id,
        copy.id, next_reservation.expires_at.isoformat(),
    )

    # Publish event for notification
    book_repo = BookRepository(db)
    book = book_repo.get_by_id(book_id)
    event_bus.publish(RESERVATION_READY, {
        "student_id": next_reservation.student_id,
        "book_id": book_id,
        "title": book.title if book else "Unknown",
        "reservation_id": next_reservation.id,
        "expires_at": next_reservation.expires_at.isoformat(),
    })

    return True  # Copy is held, not available


def get_student_reservations(db: Session, student_id: int) -> list:
    """Get all active reservations for a student."""
    reservation_repo = ReservationRepository(db)
    reservations = reservation_repo.get_student_reservations(student_id)

    result = []
    for res in reservations:
        result.append({
            "id": res.id,
            "book_id": res.book_id,
            "book_title": res.book.title if res.book else "Unknown",
            "position": res.position,
            "status": res.status,
            "reserved_at": res.reserved_at,
            "expires_at": res.expires_at,
            "barcode": res.book_copy.barcode if res.book_copy else None,
        })
    return result


def get_all_reservations(db: Session) -> list:
    """Get all active reservations (admin view)."""
    reservation_repo = ReservationRepository(db)
    reservations = reservation_repo.get_all_active()

    result = []
    for res in reservations:
        result.append({
            "id": res.id,
            "student_id": res.student_id,
            "student_name": res.student.name if res.student else "Unknown",
            "book_id": res.book_id,
            "book_title": res.book.title if res.book else "Unknown",
            "position": res.position,
            "status": res.status,
            "reserved_at": res.reserved_at,
            "expires_at": res.expires_at,
            "barcode": res.book_copy.barcode if res.book_copy else None,
        })
    return result


def get_book_reservations(db: Session, book_id: int) -> list:
    """Get waitlist queue for a specific book."""
    book_repo = BookRepository(db)
    book = book_repo.get_by_id(book_id)
    if not book:
        raise NotFoundError("Book", book_id)

    reservation_repo = ReservationRepository(db)

    # Clean up stale before viewing
    expire_stale_reservations(db, book_id)

    queue = reservation_repo.get_queue_for_book(book_id)

    result = []
    for res in queue:
        result.append({
            "id": res.id,
            "student_id": res.student_id,
            "student_name": res.student.name if res.student else "Unknown",
            "position": res.position,
            "status": res.status,
            "reserved_at": res.reserved_at,
            "expires_at": res.expires_at,
        })
    return result
