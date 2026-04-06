# app/schemas/reservation.py — Reservation request/response schemas

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ReserveRequest(BaseModel):
    book_id: int = Field(..., gt=0)


class ReservationResponse(BaseModel):
    id: int
    student_id: int
    book_id: int
    book_title: Optional[str] = None
    student_name: Optional[str] = None
    position: int
    status: str
    reserved_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    barcode: Optional[str] = None  # of held copy

    model_config = {"from_attributes": True}
