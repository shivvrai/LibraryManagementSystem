# app/schemas/transaction.py — Transaction request/response schemas

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class BorrowRequest(BaseModel):
    book_id: int = Field(..., gt=0)


class ReturnRequest(BaseModel):
    transaction_id: int = Field(..., gt=0)


class TransactionResponse(BaseModel):
    id: int
    student_id: int
    book_id: int
    student_name: Optional[str] = None
    book_title: Optional[str] = None
    borrow_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    return_date: Optional[datetime] = None
    status: str
    fine: float = 0.0

    model_config = {"from_attributes": True}


class OverdueResponse(BaseModel):
    transaction_id: int
    student_id: int
    student_name: str
    book_id: int
    book_title: str
    borrow_date: datetime
    due_date: datetime
    days_overdue: int
    fine: float


class StatsResponse(BaseModel):
    total_books: int
    total_students: int
    active_borrows: int
    overdue_books: int
    total_fines: float
    total_transactions: int


class BorrowResponse(BaseModel):
    message: str
    transaction_id: int
    due_date: str


class ReturnResponse(BaseModel):
    message: str
    fine: float
    days_overdue: int


class StudentBorrowedBook(BaseModel):
    id: int
    transaction_id: int
    book: dict
    borrow_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    fine: float = 0.0
    status: str
