# app/schemas/student.py — Student request/response schemas

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class StudentCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(default="", max_length=100)
    phone: str = Field(default="", max_length=20)


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    password: Optional[str] = Field(None, min_length=4)


class StudentResponse(BaseModel):
    id: int
    registration_no: str
    username: str
    name: str
    email: str
    phone: str
    borrowed_books: int
    fine_amount: float
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaginatedStudentsResponse(BaseModel):
    items: List[StudentResponse]
    total: int
    page: int
    per_page: int
    pages: int


class StudentFinesResponse(BaseModel):
    fine_amount: float
    borrowed_books: int
