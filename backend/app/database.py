# app/database.py — SQLAlchemy engine, session factory, and DB initialisation

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

logger = logging.getLogger(__name__)

# ── Engine ────────────────────────────────────────────────────────────
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

# ── Session Factory ───────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Declarative Base ──────────────────────────────────────────────────
Base = declarative_base()


def init_db() -> None:
    """Seed the database with default admin accounts and sample data
    if the admins table is empty (first run)."""
    from app.models.admin import Admin
    from app.models.student import Student
    from app.models.book import Book
    from app.services.auth_service import hash_password

    db = SessionLocal()
    try:
        # Only seed if no admins exist
        existing = db.query(Admin).first()
        if existing:
            logger.info("Database already seeded — skipping init")
            return

        logger.info("Seeding database with default data...")

        # ── Default admins ────────────────────────────────────────────
        admins = [
            Admin(
                username="admin",
                password=hash_password("admin123"),
                name="System Administrator",
                role="admin",
            ),
            Admin(
                username="librarian",
                password=hash_password("lib@2025"),
                name="Library Staff",
                role="admin",
            ),
        ]
        db.add_all(admins)

        # ── Default students ──────────────────────────────────────────
        import random

        student_pw = hash_password("pass123")
        students_data = [
            ("Rahul Kumar", "rahul.kumar", "rahul.kumar@college.edu", "9876543210"),
            ("Priya Sharma", "priya.sharma", "priya.sharma@college.edu", "9876543211"),
            ("Amit Patel", "amit.patel", "amit.patel@college.edu", "9876543212"),
        ]
        for name, username, email, phone in students_data:
            reg_no = str(random.randint(10000000, 99999999))
            db.add(
                Student(
                    registration_no=reg_no,
                    username=username,
                    password=student_pw,
                    name=name,
                    email=email,
                    phone=phone,
                )
            )

        # ── Default books ─────────────────────────────────────────────
        from app.models.book_copy import BookCopy

        books_data = [
            ("Harry Potter and the Philosopher's Stone", "J.K. Rowling", "9780439708180", 309, 12.99, "Fantasy", 5),
            ("The Hobbit", "J.R.R. Tolkien", "9780547928227", 310, 10.99, "Fantasy", 3),
            ("1984", "George Orwell", "9780451524935", 328, 9.99, "Fiction", 4),
            ("To Kill a Mockingbird", "Harper Lee", "9780061120084", 324, 11.99, "Fiction", 6),
            ("Pride and Prejudice", "Jane Austen", "9780141439518", 279, 8.99, "Romance", 4),
            ("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", 180, 10.50, "Fiction", 5),
        ]
        seeded_books = []
        for title, author, isbn, pages, price, category, qty in books_data:
            book = Book(
                title=title,
                author=author,
                isbn=isbn,
                pages=pages,
                price=price,
                category=category,
                quantity=qty,
                available=qty,
            )
            db.add(book)
            seeded_books.append((book, qty))

        db.commit()

        # Generate BookCopy records for each seeded book
        for book, qty in seeded_books:
            db.refresh(book)
            for i in range(1, qty + 1):
                db.add(BookCopy(
                    book_id=book.id,
                    barcode=f"BC-{book.id}-{i:03d}",
                    condition="new",
                    status="available",
                ))
        db.commit()

        logger.info("Database seeded successfully (with BookCopy records)")
        logger.info("Default admin: admin / admin123")
        logger.info("Default students: rahul.kumar / pass123")

    except Exception:
        db.rollback()
        logger.exception("Failed to seed database")
        raise
    finally:
        db.close()
