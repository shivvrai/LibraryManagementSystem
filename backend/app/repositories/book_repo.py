# app/repositories/book_repo.py — Book data access

from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.book import Book
from app.repositories.base import BaseRepository


class BookRepository(BaseRepository[Book]):

    def __init__(self, db: Session):
        super().__init__(Book, db)

    def get_by_id_locked(self, book_id: int) -> Optional[Book]:
        """
        Get a book by ID with a row-level lock (SELECT FOR UPDATE).
        Prevents concurrent transactions from reading stale availability.
        Note: with_for_update() is a no-op on SQLite (safe for dev).
        """
        return (
            self.db.query(Book)
            .filter(Book.id == book_id)
            .with_for_update()
            .first()
        )

    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        return self.db.query(Book).filter(Book.isbn == isbn).first()

    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Book]:
        pattern = f"%{query}%"
        return (
            self.db.query(Book)
            .filter(
                or_(
                    Book.title.ilike(pattern),
                    Book.author.ilike(pattern),
                    Book.category.ilike(pattern),
                    Book.isbn.ilike(pattern),
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_count(self, query: str) -> int:
        pattern = f"%{query}%"
        return (
            self.db.query(Book)
            .filter(
                or_(
                    Book.title.ilike(pattern),
                    Book.author.ilike(pattern),
                    Book.category.ilike(pattern),
                    Book.isbn.ilike(pattern),
                )
            )
            .count()
        )

    def get_all_sorted(self, skip: int = 0, limit: int = 100) -> List[Book]:
        return (
            self.db.query(Book)
            .order_by(Book.title.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )
