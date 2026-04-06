# app/models/book_copy.py — BookCopy ORM model (Physical copy tracking)

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class BookCopy(Base):
    """
    Represents a single physical copy of a book.
    Each Book has N BookCopy records (1:N relationship).

    Status State Machine:
        available → borrowed  (on borrow)
        borrowed  → available (on return, no reservation)
        borrowed  → held      (on return, reservation exists)
        held      → borrowed  (reservation fulfilled / student picks up)
        held      → available (reservation expired)
        any       → lost      (admin marks lost)
    """
    __tablename__ = "book_copies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    barcode = Column(String(50), unique=True, nullable=False, index=True)
    condition = Column(String(20), default="new", nullable=False)  # new | good | fair | damaged
    status = Column(String(20), default="available", nullable=False, index=True)  # available | borrowed | held | lost
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    book = relationship("Book", back_populates="copies", lazy="joined")

    def __repr__(self) -> str:
        return f"<BookCopy(id={self.id}, barcode='{self.barcode}', status='{self.status}', condition='{self.condition}')>"
