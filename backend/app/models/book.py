# app/models/book.py — Book ORM model

from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(150), nullable=False, index=True)
    isbn = Column(String(20), unique=True, nullable=False, index=True)
    pages = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    available = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    transactions = relationship("Transaction", back_populates="book", lazy="select")
    copies = relationship("BookCopy", back_populates="book", lazy="select")

    def __repr__(self) -> str:
        return f"<Book(id={self.id}, title='{self.title}', available={self.available}/{self.quantity})>"
