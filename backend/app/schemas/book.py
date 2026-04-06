# app/schemas/book.py — Book request/response schemas

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=150)
    isbn: str = Field(..., min_length=10, max_length=20)
    pages: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=50)
    quantity: int = Field(default=1, gt=0)

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str) -> str:
        clean = v.replace("-", "").replace(" ", "")
        if len(clean) != 13 or not clean.isdigit():
            raise ValueError("ISBN must be a valid 13-digit number")
        return v


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=150)
    pages: Optional[int] = Field(None, gt=0)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    quantity: Optional[int] = Field(None, gt=0)


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    isbn: str
    pages: int
    price: float
    category: str
    quantity: int
    available: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaginatedBooksResponse(BaseModel):
    items: List[BookResponse]
    total: int
    page: int
    per_page: int
    pages: int
