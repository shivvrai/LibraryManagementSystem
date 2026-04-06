# app/schemas/book_copy.py — BookCopy request/response schemas

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class BookCopyResponse(BaseModel):
    id: int
    book_id: int
    barcode: str
    condition: str
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
