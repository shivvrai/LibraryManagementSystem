# app/models/student.py — Student ORM model

from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    registration_no = Column(String(20), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), default="")
    phone = Column(String(20), default="")
    borrowed_books = Column(Integer, default=0)
    fine_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    transactions = relationship("Transaction", back_populates="student", lazy="select")

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, username='{self.username}', reg='{self.registration_no}')>"
