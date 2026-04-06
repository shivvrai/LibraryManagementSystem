# app/repositories/preference_repo.py — BookPreference data access

from typing import List, Set

from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models.book_preference import BookPreference
from app.repositories.base import BaseRepository


class PreferenceRepository(BaseRepository[BookPreference]):

    def __init__(self, db: Session):
        super().__init__(BookPreference, db)

    def get_by_student(self, student_id: int) -> List[BookPreference]:
        """Get all preferences for a student."""
        return (
            self.db.query(BookPreference)
            .filter(BookPreference.student_id == student_id)
            .order_by(BookPreference.created_at.desc())
            .all()
        )

    def get_by_student_and_type(self, student_id: int, pref_type: str) -> List[BookPreference]:
        """Get preferences of a specific type for a student."""
        return (
            self.db.query(BookPreference)
            .filter(
                BookPreference.student_id == student_id,
                BookPreference.preference_type == pref_type,
            )
            .all()
        )

    def exists(self, student_id: int, pref_type: str, pref_value: str) -> bool:
        """Check if a preference already exists (case-insensitive)."""
        return (
            self.db.query(BookPreference)
            .filter(
                BookPreference.student_id == student_id,
                BookPreference.preference_type == pref_type,
                func.lower(BookPreference.preference_value) == pref_value.lower(),
            )
            .first()
            is not None
        )

    def find_matching_students(
        self, category: str = "", author: str = "", title: str = ""
    ) -> Set[int]:
        """
        Find student IDs whose preferences match a book's attributes.
        Bidirectional fuzzy:
          pref LIKE '%book_attr%'  OR  book_attr LIKE '%pref%'
        """
        filters = []

        if category:
            filters.append(
                (BookPreference.preference_type == "category")
                & (
                    BookPreference.preference_value.ilike(f"%{category}%")
                    | func.lower(func.trim(BookPreference.preference_value)).op("LIKE")(
                        "%" + func.lower(category) + "%"
                    )
                )
            )
            # Also: book category contains the preference value
            # e.g. pref="Fantasy", category="Dark Fantasy"
            cat_low = "%" + category.lower() + "%"
            pref_low = "%" + category.lower() + "%"
            filters.append(
                (BookPreference.preference_type == "category")
                & func.lower(func.trim(BookPreference.preference_value)).in_(
                    [category.lower()]
                )
            )

        if author:
            filters.append(
                (BookPreference.preference_type == "author")
                & BookPreference.preference_value.ilike(f"%{author}%")
            )

        if title:
            filters.append(
                (BookPreference.preference_type == "title")
                & BookPreference.preference_value.ilike(f"%{title}%")
            )

        if not filters:
            return set()

        results = (
            self.db.query(BookPreference.student_id)
            .filter(or_(*filters))
            .distinct()
            .all()
        )
        return {row[0] for row in results}

    def count_by_student(self, student_id: int) -> int:
        """Count total preferences for a student."""
        return (
            self.db.query(BookPreference)
            .filter(BookPreference.student_id == student_id)
            .count()
        )
