# app/models/book_preference.py — BookPreference ORM model

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class BookPreference(Base):
    __tablename__ = "book_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    preference_type = Column(String(20), nullable=False)  # 'category', 'author', 'title'
    preference_value = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    student = relationship("Student", backref="preferences", lazy="select")

    def __repr__(self) -> str:
        return f"<BookPreference(id={self.id}, student={self.student_id}, type='{self.preference_type}', value='{self.preference_value}')>"
