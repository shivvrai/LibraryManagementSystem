# app/schemas/notification.py — Notification request/response schemas

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    message: str
    notification_type: str
    book_id: Optional[int] = None
    is_read: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int
