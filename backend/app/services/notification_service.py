# app/services/notification_service.py — Notification business logic & event handlers

import logging
from typing import List, Dict, Any

from app.database import SessionLocal
from app.models.notification import Notification
from app.repositories.notification_repo import NotificationRepository
from app.repositories.preference_repo import PreferenceRepository
from app.services.event_bus import event_bus, BOOK_ADDED, BOOK_AVAILABLE

logger = logging.getLogger(__name__)


# ── Event Handlers ────────────────────────────────────────────────────

def _handle_book_added(event_data: Dict[str, Any]) -> None:
    """
    Called when a new book is added to the library.
    Finds students whose preferences match and creates notifications.
    """
    db = SessionLocal()
    try:
        book_id = event_data["book_id"]
        title = event_data.get("title", "")
        author = event_data.get("author", "")
        category = event_data.get("category", "")

        pref_repo = PreferenceRepository(db)
        notif_repo = NotificationRepository(db)

        matching_students = pref_repo.find_matching_students(
            category=category, author=author, title=title
        )

        if not matching_students:
            logger.info("No preference matches for new book '%s'", title)
            return

        logger.info(
            "Book '%s' matches preferences of %d student(s)",
            title, len(matching_students),
        )

        for student_id in matching_students:
            notification = Notification(
                student_id=student_id,
                message=f"📚 New arrival! \"{title}\" by {author} ({category}) has been added to the library.",
                notification_type="new_book",
                book_id=book_id,
            )
            notif_repo.create(notification)

        logger.info("Created %d notifications for new book '%s'", len(matching_students), title)

    except Exception:
        logger.exception("Failed to process BOOK_ADDED event")
        db.rollback()
    finally:
        db.close()


def _handle_book_available(event_data: Dict[str, Any]) -> None:
    """
    Called when a previously unavailable book (stock=0) becomes available again.
    Finds students whose preferences match and creates notifications.
    """
    db = SessionLocal()
    try:
        book_id = event_data["book_id"]
        title = event_data.get("title", "")
        author = event_data.get("author", "")
        category = event_data.get("category", "")

        pref_repo = PreferenceRepository(db)
        notif_repo = NotificationRepository(db)

        matching_students = pref_repo.find_matching_students(
            category=category, author=author, title=title
        )

        if not matching_students:
            return

        logger.info(
            "Book '%s' is back in stock — notifying %d student(s)",
            title, len(matching_students),
        )

        for student_id in matching_students:
            notification = Notification(
                student_id=student_id,
                message=f"🔔 Back in stock! \"{title}\" by {author} is now available to borrow.",
                notification_type="book_available",
                book_id=book_id,
            )
            notif_repo.create(notification)

    except Exception:
        logger.exception("Failed to process BOOK_AVAILABLE event")
        db.rollback()
    finally:
        db.close()


# ── Register event handlers on import ─────────────────────────────────
event_bus.subscribe(BOOK_ADDED, _handle_book_added)
event_bus.subscribe(BOOK_AVAILABLE, _handle_book_available)


# ── Query Functions (called by routes) ────────────────────────────────

def get_notifications(db, student_id: int) -> List[dict]:
    """Get all notifications for a student."""
    repo = NotificationRepository(db)
    notifications = repo.get_by_student(student_id)
    return [
        {
            "id": n.id,
            "message": n.message,
            "notification_type": n.notification_type,
            "book_id": n.book_id,
            "is_read": n.is_read,
            "created_at": n.created_at,
        }
        for n in notifications
    ]


def get_unread_count(db, student_id: int) -> int:
    """Get unread notification count."""
    repo = NotificationRepository(db)
    return repo.count_unread(student_id)


def mark_as_read(db, notification_id: int, student_id: int) -> bool:
    """Mark a notification as read."""
    repo = NotificationRepository(db)
    return repo.mark_as_read(notification_id, student_id)


def mark_all_read(db, student_id: int) -> int:
    """Mark all notifications as read for a student."""
    repo = NotificationRepository(db)
    return repo.mark_all_read(student_id)
