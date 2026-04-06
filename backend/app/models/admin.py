# app/models/admin.py — Admin ORM model

from sqlalchemy import Column, Integer, String, DateTime, func

from app.database import Base


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(20), default="admin")
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Admin(id={self.id}, username='{self.username}')>"
