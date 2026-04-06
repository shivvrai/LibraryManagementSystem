# app/services/preference_service.py — Book Preference business logic

import logging
from typing import List

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError, ConflictError, ValidationError
from app.models.book_preference import BookPreference
from app.repositories.preference_repo import PreferenceRepository

logger = logging.getLogger(__name__)

VALID_PREFERENCE_TYPES = {"category", "author", "title"}


def get_preferences(db: Session, student_id: int) -> List[dict]:
    """Get all preferences for a student."""
    repo = PreferenceRepository(db)
    prefs = repo.get_by_student(student_id)
    return [
        {
            "id": p.id,
            "preference_type": p.preference_type,
            "preference_value": p.preference_value,
            "created_at": p.created_at,
        }
        for p in prefs
    ]


def add_preference(
    db: Session, student_id: int, preference_type: str, preference_value: str
) -> dict:
    """Add a new book preference for a student."""
    # Validate type
    if preference_type not in VALID_PREFERENCE_TYPES:
        raise ValidationError(
            f"Invalid preference type '{preference_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_PREFERENCE_TYPES))}"
        )

    # Validate value
    value = preference_value.strip()
    if not value:
        raise ValidationError("Preference value cannot be empty")

    # Check for duplicates
    repo = PreferenceRepository(db)
    if repo.exists(student_id, preference_type, value):
        raise ConflictError(
            f"You already have a '{preference_type}' preference for '{value}'"
        )

    # Limit preferences per student (max 20)
    if repo.count_by_student(student_id) >= 20:
        raise ValidationError("Maximum of 20 preferences reached. Remove some before adding new ones.")

    pref = BookPreference(
        student_id=student_id,
        preference_type=preference_type,
        preference_value=value,
    )
    repo.create(pref)

    logger.info(
        "Preference added: student=%d, type='%s', value='%s'",
        student_id, preference_type, value,
    )

    return {
        "id": pref.id,
        "preference_type": pref.preference_type,
        "preference_value": pref.preference_value,
        "created_at": pref.created_at,
    }


def remove_preference(db: Session, preference_id: int, student_id: int) -> dict:
    """Remove a book preference."""
    repo = PreferenceRepository(db)
    pref = repo.get_by_id(preference_id)

    if not pref:
        raise NotFoundError("Preference", preference_id)
    if pref.student_id != student_id:
        raise ValidationError("This preference does not belong to you")

    repo.delete(pref)
    logger.info("Preference removed: id=%d, student=%d", preference_id, student_id)

    return {"message": "Preference removed successfully"}
