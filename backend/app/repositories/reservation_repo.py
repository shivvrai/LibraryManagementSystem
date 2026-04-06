# app/repositories/reservation_repo.py — Reservation data access

from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, func as sa_func

from app.models.reservation import Reservation
from app.repositories.base import BaseRepository


class ReservationRepository(BaseRepository[Reservation]):

    def __init__(self, db: Session):
        super().__init__(Reservation, db)

    def get_next_waiting(self, book_id: int) -> Optional[Reservation]:
        """Get the next reservation in the queue (lowest position, status=waiting)."""
        return (
            self.db.query(Reservation)
            .filter(
                and_(
                    Reservation.book_id == book_id,
                    Reservation.status == "waiting",
                )
            )
            .order_by(Reservation.position.asc())
            .first()
        )

    def get_active_reservation(self, student_id: int, book_id: int) -> Optional[Reservation]:
        """Check if student already has an active reservation for this book."""
        return (
            self.db.query(Reservation)
            .filter(
                and_(
                    Reservation.student_id == student_id,
                    Reservation.book_id == book_id,
                    Reservation.status.in_(["waiting", "awaiting_pickup"]),
                )
            )
            .first()
        )

    def get_student_reservations(self, student_id: int) -> List[Reservation]:
        """Get all active reservations for a student."""
        return (
            self.db.query(Reservation)
            .filter(
                and_(
                    Reservation.student_id == student_id,
                    Reservation.status.in_(["waiting", "awaiting_pickup"]),
                )
            )
            .order_by(Reservation.created_at.desc())
            .all()
        )

    def get_queue_for_book(self, book_id: int) -> List[Reservation]:
        """Get the entire waitlist queue for a book."""
        return (
            self.db.query(Reservation)
            .filter(
                and_(
                    Reservation.book_id == book_id,
                    Reservation.status.in_(["waiting", "awaiting_pickup"]),
                )
            )
            .order_by(Reservation.position.asc())
            .all()
        )

    def count_waiting(self, book_id: int) -> int:
        """Count students still waiting in the queue."""
        return (
            self.db.query(Reservation)
            .filter(
                and_(
                    Reservation.book_id == book_id,
                    Reservation.status == "waiting",
                )
            )
            .count()
        )

    def get_next_position(self, book_id: int) -> int:
        """Get the next queue position for a new reservation."""
        max_pos = (
            self.db.query(sa_func.max(Reservation.position))
            .filter(Reservation.book_id == book_id)
            .scalar()
        )
        return (max_pos or 0) + 1

    def get_expired_awaiting(self, book_id: int) -> List[Reservation]:
        """Get awaiting_pickup reservations that have expired."""
        now = datetime.utcnow()
        return (
            self.db.query(Reservation)
            .filter(
                and_(
                    Reservation.book_id == book_id,
                    Reservation.status == "awaiting_pickup",
                    Reservation.expires_at < now,
                )
            )
            .all()
        )

    def get_all_active(self, skip: int = 0, limit: int = 200) -> List[Reservation]:
        """Get all active reservations (admin view)."""
        return (
            self.db.query(Reservation)
            .filter(Reservation.status.in_(["waiting", "awaiting_pickup"]))
            .order_by(Reservation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
