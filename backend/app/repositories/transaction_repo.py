# app/repositories/transaction_repo.py — Transaction data access

from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.transaction import Transaction
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):

    def __init__(self, db: Session):
        super().__init__(Transaction, db)

    def get_active_borrow(self, student_id: int, book_id: int) -> Optional[Transaction]:
        """Check if student already has this book borrowed."""
        return (
            self.db.query(Transaction)
            .filter(
                and_(
                    Transaction.student_id == student_id,
                    Transaction.book_id == book_id,
                    Transaction.status == "borrowed",
                )
            )
            .first()
        )

    def get_student_active_borrows(self, student_id: int) -> List[Transaction]:
        """Get all currently borrowed books for a student."""
        return (
            self.db.query(Transaction)
            .filter(
                and_(
                    Transaction.student_id == student_id,
                    Transaction.status == "borrowed",
                )
            )
            .all()
        )

    def get_overdue_transactions(self) -> List[Transaction]:
        """Get all transactions that are past due date and not returned."""
        now = datetime.utcnow()
        return (
            self.db.query(Transaction)
            .filter(
                and_(
                    Transaction.status == "borrowed",
                    Transaction.due_date < now,
                )
            )
            .all()
        )

    def get_all_with_details(self, skip: int = 0, limit: int = 200) -> List[Transaction]:
        """Get all transactions with student and book eagerly loaded."""
        return (
            self.db.query(Transaction)
            .order_by(Transaction.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_active_borrows(self) -> int:
        return (
            self.db.query(Transaction)
            .filter(Transaction.status == "borrowed")
            .count()
        )

    def count_overdue(self) -> int:
        now = datetime.utcnow()
        return (
            self.db.query(Transaction)
            .filter(
                and_(
                    Transaction.status == "borrowed",
                    Transaction.due_date < now,
                )
            )
            .count()
        )

    def get_student_history(self, student_id: int) -> List[Transaction]:
        return (
            self.db.query(Transaction)
            .filter(Transaction.student_id == student_id)
            .order_by(Transaction.created_at.desc())
            .all()
        )
