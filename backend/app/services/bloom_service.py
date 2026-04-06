# app/services/bloom_service.py — In-memory Bloom Filter guard layer
#
# Design rationale:
#   Bloom Filters provide O(1) probabilistic membership tests. When a username
#   is clearly NOT in the set the filter answers immediately with zero DB I/O.
#   False positives (filter says "might exist" but DB says "no") are handled by
#   the existing DB uniqueness check — correctness is always guaranteed.
#
# Two filters:
#   _username_bloom  — guards /check-username and /register
#   _isbn_bloom      — guards add_book ISBN uniqueness
#
# Thread safety:
#   pybloom-live is not thread-safe. For a single-process Uvicorn server this is
#   fine. We protect mutations with a threading.Lock just in case.

import logging
import threading
from typing import Optional

from pybloom_live import BloomFilter
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)

_lock = threading.Lock()


class BloomService:
    """Singleton service managing username and ISBN Bloom Filters."""

    def __init__(self) -> None:
        self._username_bloom: Optional[BloomFilter] = None
        self._isbn_bloom: Optional[BloomFilter] = None
        self._ready: bool = False

    # ── Lifecycle ─────────────────────────────────────────────────────

    def initialize(self, db: Session) -> None:
        """
        Seed both Bloom Filters from the current database state.
        Must be called once during application startup.
        """
        from app.models.student import Student
        from app.models.admin import Admin
        from app.models.book import Book

        capacity = settings.BLOOM_CAPACITY
        error_rate = settings.BLOOM_ERROR_RATE

        # ── Username filter ──────────────────────────────────────────
        username_filter = BloomFilter(capacity=capacity, error_rate=error_rate)

        student_usernames = db.query(Student.username).all()
        admin_usernames = db.query(Admin.username).all()

        count = 0
        for (uname,) in student_usernames:
            username_filter.add(uname.lower())
            count += 1
        for (uname,) in admin_usernames:
            username_filter.add(uname.lower())
            count += 1

        # ── ISBN filter ──────────────────────────────────────────────
        isbn_filter = BloomFilter(capacity=capacity, error_rate=error_rate)
        isbns = db.query(Book.isbn).all()
        isbn_count = 0
        for (isbn,) in isbns:
            isbn_filter.add(isbn.upper())
            isbn_count += 1

        with _lock:
            self._username_bloom = username_filter
            self._isbn_bloom = isbn_filter
            self._ready = True

        logger.info(
            "Bloom filters initialized — usernames: %d, ISBNs: %d "
            "(capacity: %d, error_rate: %.3f)",
            count, isbn_count, capacity, error_rate,
        )

    # ── Username API ──────────────────────────────────────────────────

    def might_exist_username(self, username: str) -> bool:
        """
        Return True if username *might* exist (proceed to DB check).
        Return False if username *definitely* does not exist (skip DB).
        Always returns True when filter is not yet initialized (safe default).
        """
        if not self._ready or self._username_bloom is None:
            return True  # safe fallback — hit the DB
        return username.lower() in self._username_bloom

    def add_username(self, username: str) -> None:
        """Add a newly registered username to the filter."""
        if not self._ready or self._username_bloom is None:
            return
        with _lock:
            self._username_bloom.add(username.lower())
        logger.debug("Bloom filter: added username '%s'", username)

    # ── ISBN API ──────────────────────────────────────────────────────

    def might_exist_isbn(self, isbn: str) -> bool:
        """
        Return True if ISBN *might* exist (proceed to DB check).
        Return False if ISBN *definitely* does not exist (skip DB).
        Always returns True when filter is not yet initialized (safe default).
        """
        if not self._ready or self._isbn_bloom is None:
            return True  # safe fallback — hit the DB
        return isbn.upper() in self._isbn_bloom

    def add_isbn(self, isbn: str) -> None:
        """Add a newly indexed ISBN to the filter."""
        if not self._ready or self._isbn_bloom is None:
            return
        with _lock:
            self._isbn_bloom.add(isbn.upper())
        logger.debug("Bloom filter: added ISBN '%s'", isbn)

    # ── Status ────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Return health/debug information about the filters."""
        return {
            "ready": self._ready,
            "username_filter": {
                "capacity": settings.BLOOM_CAPACITY,
                "error_rate": settings.BLOOM_ERROR_RATE,
                "count": len(self._username_bloom) if self._username_bloom else 0,
            },
            "isbn_filter": {
                "capacity": settings.BLOOM_CAPACITY,
                "error_rate": settings.BLOOM_ERROR_RATE,
                "count": len(self._isbn_bloom) if self._isbn_bloom else 0,
            },
        }


# Singleton instance — import this everywhere
bloom_service = BloomService()
