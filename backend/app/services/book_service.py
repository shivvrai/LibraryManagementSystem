# app/services/book_service.py — Book business logic

import logging
import math
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import NotFoundError, ConflictError, ValidationError
from app.models.book import Book
from app.models.book_copy import BookCopy
from app.repositories.book_repo import BookRepository
from app.repositories.book_copy_repo import BookCopyRepository
from app.repositories.transaction_repo import TransactionRepository
from app.services.event_bus import event_bus, BOOK_ADDED, BOOK_AVAILABLE
from app.services.bloom_service import bloom_service
from app.services.search_service import search_service

logger = logging.getLogger(__name__)


# ── BookCopy Helpers ──────────────────────────────────────────────────

def _generate_copies(db: Session, book_id: int, count: int, start_seq: int = 1) -> list:
    """
    Generate BookCopy records for a book.
    Barcodes follow the pattern BC-{book_id}-{sequence}.
    """
    copy_repo = BookCopyRepository(db)
    copies = []
    for i in range(count):
        seq = start_seq + i
        copy = BookCopy(
            book_id=book_id,
            barcode=f"BC-{book_id}-{seq:03d}",
            condition="new",
            status="available",
        )
        db.add(copy)
        copies.append(copy)
    db.commit()
    for c in copies:
        db.refresh(c)
    return copies


def reconcile_book_counts(db: Session, book_id: int) -> None:
    """
    Single Source of Truth: recomputes Book.available and Book.quantity
    from the actual BookCopy records. Called after every borrow/return.
    
    System Invariant:
        Book.quantity  == count(BookCopy WHERE status != 'lost')
        Book.available == count(BookCopy WHERE status == 'available')
    """
    copy_repo = BookCopyRepository(db)
    book_repo = BookRepository(db)

    book = book_repo.get_by_id(book_id)
    if not book:
        return

    book.quantity = copy_repo.count_active(book_id)
    book.available = copy_repo.count_by_status(book_id, "available")
    db.commit()
    db.refresh(book)

    logger.debug(
        "Reconciled book counts: id=%d, quantity=%d, available=%d",
        book_id, book.quantity, book.available,
    )


# ── Book CRUD ─────────────────────────────────────────────────────────

def get_books(db: Session, page: int = 1, per_page: int = 50,
              search: Optional[str] = None, category: Optional[str] = None) -> dict:
    """
    Get paginated list of books with optional search.
    When a search query is provided:
      1. Try Elasticsearch (fuzzy, relevance-scored).
      2. Fall back to SQLite ILIKE if ES is unavailable.
    """
    repo = BookRepository(db)
    skip = (page - 1) * per_page

    if search and search.strip():
        # ── Elasticsearch path ───────────────────────────────────────
        es_result = search_service.search(
            query=search.strip(), page=page, per_page=per_page, category=category
        )
        if es_result is not None:
            logger.debug("Book search via Elasticsearch for query='%s'", search)
            return es_result

        # ── SQL fallback ─────────────────────────────────────────────
        logger.debug("Book search via SQL fallback for query='%s'", search)
        items = repo.search(search.strip(), skip=skip, limit=per_page)
        total = repo.search_count(search.strip())
    else:
        items = repo.get_all_sorted(skip=skip, limit=per_page)
        total = repo.count()

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page else 1,
        "engine": "sql",
    }


def get_book_by_id(db: Session, book_id: int) -> Book:
    """Get a single book by ID. Raises NotFoundError."""
    repo = BookRepository(db)
    book = repo.get_by_id(book_id)
    if not book:
        raise NotFoundError("Book", book_id)
    return book


def add_book(db: Session, title: str, author: str, isbn: str,
             pages: int, price: float, category: str, quantity: int = 1) -> Book:
    """Add a new book. Validates ISBN uniqueness. Auto-generates BookCopy records."""
    repo = BookRepository(db)

    # ── Bloom Filter fast-path: skip DB query when ISBN is clearly new ──
    if bloom_service.might_exist_isbn(isbn):
        # Bloom says "might exist" — do the authoritative DB check
        existing = repo.get_by_isbn(isbn)
        if existing:
            raise ConflictError(f"A book with ISBN '{isbn}' already exists")
    # else: Bloom says "definitely not" — skip the DB round-trip entirely

    book = Book(
        title=title,
        author=author,
        isbn=isbn,
        pages=pages,
        price=price,
        category=category,
        quantity=quantity,
        available=quantity,
    )
    repo.create(book)
    logger.info("Book added: '%s' by %s (ISBN: %s)", title, author, isbn)

    # Auto-generate physical copies
    _generate_copies(db, book.id, quantity)
    logger.info("Generated %d BookCopy records for book id=%d", quantity, book.id)

    # ── Keep Bloom filter and Elasticsearch in sync ───────────────────
    bloom_service.add_isbn(isbn)
    search_service.index_book(book)

    # Publish event for notification system (Observer Pattern)
    event_bus.publish(BOOK_ADDED, {
        "book_id": book.id,
        "title": book.title,
        "author": book.author,
        "category": book.category,
    })

    return book


def update_book(db: Session, book_id: int, **updates) -> Book:
    """Update a book's details. Adjusts availability when quantity changes."""
    repo = BookRepository(db)
    book = repo.get_by_id(book_id)
    if not book:
        raise NotFoundError("Book", book_id)

    # If quantity changes, adjust available accordingly
    if "quantity" in updates and updates["quantity"] is not None:
        new_qty = updates["quantity"]
        borrowed = book.quantity - book.available
        if new_qty < borrowed:
            raise ValidationError(
                f"Cannot reduce quantity below {borrowed} (currently borrowed)"
            )
        book.available = new_qty - borrowed
        book.quantity = new_qty

    # Apply other updates
    for field in ("title", "author", "pages", "price", "category"):
        if field in updates and updates[field] is not None:
            setattr(book, field, updates[field])

    repo.update(book)
    logger.info("Book updated: id=%d", book_id)

    # ── Keep Elasticsearch document in sync ───────────────────────────
    search_service.index_book(book)

    return book


def increase_quantity(db: Session, book_id: int, amount: int = 1) -> Book:
    """Increase book quantity (add more copies). Auto-generates new BookCopy records."""
    repo = BookRepository(db)
    copy_repo = BookCopyRepository(db)
    book = repo.get_by_id(book_id)
    if not book:
        raise NotFoundError("Book", book_id)
    if amount <= 0:
        raise ValidationError("Amount must be positive")

    was_unavailable = book.available == 0

    # Determine next sequence number for barcode generation
    existing_copies = copy_repo.get_copies_for_book(book_id)
    start_seq = len(existing_copies) + 1

    # Generate new physical copies
    _generate_copies(db, book_id, amount, start_seq=start_seq)

    # Reconcile from copies (single source of truth)
    reconcile_book_counts(db, book_id)
    db.refresh(book)

    logger.info("Book quantity increased: id=%d, +%d (now %d)", book_id, amount, book.quantity)

    # If book was out of stock and is now available, notify relevant students
    if was_unavailable:
        event_bus.publish(BOOK_AVAILABLE, {
            "book_id": book.id,
            "title": book.title,
            "author": book.author,
            "category": book.category,
        })

    return book


def decrease_quantity(db: Session, book_id: int, amount: int = 1) -> Book:
    """
    Decrease book quantity (remove copies).
    Cannot decrease below the number currently borrowed.
    Only removes 'available' copies.
    """
    repo = BookRepository(db)
    copy_repo = BookCopyRepository(db)
    book = repo.get_by_id(book_id)
    if not book:
        raise NotFoundError("Book", book_id)
    if amount <= 0:
        raise ValidationError("Amount must be positive")

    available_count = copy_repo.count_by_status(book_id, "available")
    if amount > available_count:
        raise ValidationError(
            f"Cannot remove {amount} copies — only {available_count} are available. "
            f"The rest are currently borrowed or held."
        )

    # Mark copies as lost (remove from system)
    copies = copy_repo.get_copies_for_book(book_id)
    removed = 0
    for copy in copies:
        if removed >= amount:
            break
        if copy.status == "available":
            copy.status = "lost"
            copy_repo.update(copy)
            removed += 1

    # Reconcile from copies (single source of truth)
    reconcile_book_counts(db, book_id)
    db.refresh(book)

    logger.info("Book quantity decreased: id=%d, -%d (now %d)", book_id, amount, book.quantity)
    return book


def get_book_copies(db: Session, book_id: int) -> list:
    """Get all physical copies for a book."""
    repo = BookRepository(db)
    book = repo.get_by_id(book_id)
    if not book:
        raise NotFoundError("Book", book_id)

    copy_repo = BookCopyRepository(db)
    return copy_repo.get_copies_for_book(book_id)
