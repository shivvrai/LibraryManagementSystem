# app/routes/notification.py — Notification endpoints for students

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_student
from app.services import notification_service

router = APIRouter()


@router.get("/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Get all notifications for the current student (unread first)."""
    student_id = claims["id"]
    notifications = notification_service.get_notifications(db, student_id)
    unread_count = notification_service.get_unread_count(db, student_id)
    return {
        "notifications": notifications,
        "unread_count": unread_count,
    }


@router.get("/notifications/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Get the unread notification count."""
    count = notification_service.get_unread_count(db, claims["id"])
    return {"unread_count": count}


@router.patch("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Mark a single notification as read."""
    success = notification_service.mark_as_read(db, notification_id, claims["id"])
    if not success:
        return {"message": "Notification not found"}
    return {"message": "Notification marked as read"}


@router.patch("/notifications/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    claims: dict = Depends(require_student),
):
    """Mark all notifications as read."""
    count = notification_service.mark_all_read(db, claims["id"])
    return {"message": f"Marked {count} notifications as read", "count": count}
