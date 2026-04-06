# app/models/notification.py — Notification ORM model

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(String(500), nullable=False)
    notification_type = Column(String(30), nullable=False)  # 'new_book', 'book_available'
    book_id = Column(Integer, ForeignKey("books.id", ondelete="SET NULL"), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    student = relationship("Student", backref="notifications", lazy="select")
    book = relationship("Book", lazy="select")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, student={self.student_id}, type='{self.notification_type}', read={self.is_read})>"
