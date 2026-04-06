# app/models/transaction.py — Transaction ORM model

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    book_copy_id = Column(Integer, ForeignKey("book_copies.id"), nullable=True, index=True)
    borrow_date = Column(DateTime, server_default=func.now())
    due_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="borrowed", index=True)  # borrowed | returned | lost
    fine = Column(Float, default=0.0)
    renewal_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    student = relationship("Student", back_populates="transactions", lazy="joined")
    book = relationship("Book", back_populates="transactions", lazy="joined")
    book_copy = relationship("BookCopy", lazy="joined")

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, student={self.student_id}, book={self.book_id}, status='{self.status}')>"
