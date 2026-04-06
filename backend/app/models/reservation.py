# app/models/reservation.py — Reservation ORM model (Waitlist queue)

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class Reservation(Base):
    """
    Represents a student's place in the waitlist queue for a book.
    When all copies are borrowed, students can reserve and get
    assigned a copy automatically when one is returned.

    Status Flow:
        waiting         → awaiting_pickup (copy returned, assigned to this student)
        awaiting_pickup → fulfilled       (student borrows the held copy)
        awaiting_pickup → expired         (student didn't pick up within 48h)
        waiting         → cancelled       (student cancels)
        expired         → (cascade)       next reservation in queue gets the copy
    """
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    book_copy_id = Column(Integer, ForeignKey("book_copies.id", ondelete="SET NULL"), nullable=True)
    position = Column(Integer, nullable=False)  # Queue position (1-based)
    status = Column(String(20), default="waiting", nullable=False, index=True)
    reserved_at = Column(DateTime, server_default=func.now())
    notified_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    student = relationship("Student", backref="reservations", lazy="joined")
    book = relationship("Book", backref="reservations", lazy="joined")
    book_copy = relationship("BookCopy", lazy="joined")

    def __repr__(self) -> str:
        return f"<Reservation(id={self.id}, student={self.student_id}, book={self.book_id}, pos={self.position}, status='{self.status}')>"
