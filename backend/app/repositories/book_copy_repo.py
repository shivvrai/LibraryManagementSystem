# app/repositories/book_copy_repo.py — BookCopy data access

from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.book_copy import BookCopy
from app.repositories.base import BaseRepository


class BookCopyRepository(BaseRepository[BookCopy]):

    def __init__(self, db: Session):
        super().__init__(BookCopy, db)

    def get_available_copy_locked(self, book_id: int) -> Optional[BookCopy]:
        """
        Get one available copy with a row-level lock (SELECT FOR UPDATE).
        This prevents two concurrent borrow requests from claiming the same copy.
        Note: with_for_update() is a no-op on SQLite (safe for dev).
        """
        return (
            self.db.query(BookCopy)
            .filter(
                and_(
                    BookCopy.book_id == book_id,
                    BookCopy.status == "available",
                )
            )
            .with_for_update()
            .first()
        )

    def get_copies_for_book(self, book_id: int) -> List[BookCopy]:
        """Get all copies for a specific book."""
        return (
            self.db.query(BookCopy)
            .filter(BookCopy.book_id == book_id)
            .order_by(BookCopy.id.asc())
            .all()
        )

    def count_by_status(self, book_id: int, status: str) -> int:
        """Count copies of a book with a specific status."""
        return (
            self.db.query(BookCopy)
            .filter(
                and_(
                    BookCopy.book_id == book_id,
                    BookCopy.status == status,
                )
            )
            .count()
        )

    def count_active(self, book_id: int) -> int:
        """Count non-lost copies of a book (available + borrowed + held)."""
        return (
            self.db.query(BookCopy)
            .filter(
                and_(
                    BookCopy.book_id == book_id,
                    BookCopy.status != "lost",
                )
            )
            .count()
        )

    def get_by_barcode(self, barcode: str) -> Optional[BookCopy]:
        return self.db.query(BookCopy).filter(BookCopy.barcode == barcode).first()
