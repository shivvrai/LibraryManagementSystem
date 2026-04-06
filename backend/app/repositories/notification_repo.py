# app/repositories/notification_repo.py — Notification data access

from typing import List

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):

    def __init__(self, db: Session):
        super().__init__(Notification, db)

    def get_by_student(self, student_id: int, limit: int = 50) -> List[Notification]:
        """Get notifications for a student, unread first, newest first."""
        return (
            self.db.query(Notification)
            .filter(Notification.student_id == student_id)
            .order_by(Notification.is_read.asc(), Notification.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_unread(self, student_id: int) -> List[Notification]:
        """Get only unread notifications for a student."""
        return (
            self.db.query(Notification)
            .filter(
                Notification.student_id == student_id,
                Notification.is_read == False,
            )
            .order_by(Notification.created_at.desc())
            .all()
        )

    def count_unread(self, student_id: int) -> int:
        """Count unread notifications for a student."""
        return (
            self.db.query(Notification)
            .filter(
                Notification.student_id == student_id,
                Notification.is_read == False,
            )
            .count()
        )

    def mark_as_read(self, notification_id: int, student_id: int) -> bool:
        """Mark a single notification as read. Returns True if found and updated."""
        notif = (
            self.db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.student_id == student_id,
            )
            .first()
        )
        if notif:
            notif.is_read = True
            self.db.commit()
            return True
        return False

    def mark_all_read(self, student_id: int) -> int:
        """Mark all notifications as read for a student. Returns count updated."""
        count = (
            self.db.query(Notification)
            .filter(
                Notification.student_id == student_id,
                Notification.is_read == False,
            )
            .update({"is_read": True})
        )
        self.db.commit()
        return count
