# app/__init__.py — FastAPI Application Factory

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, init_db
from app.exceptions import register_exception_handlers
from app.middleware.logging_middleware import RequestLoggingMiddleware


def create_app() -> FastAPI:
    """Factory function that creates and configures the FastAPI application."""

    app = FastAPI(
        title="Library Management System",
        description="Industrial-grade Library Management API",
        version="3.0.0",
    )

    # ── CORS ──────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Custom Middleware ─────────────────────────────────────────────
    app.add_middleware(RequestLoggingMiddleware)

    # ── Exception Handlers ────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────
    from app.routes import auth, admin, student, notification, preference  # noqa: E402

    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
    app.include_router(student.router, prefix="/api/student", tags=["Student"])
    app.include_router(notification.router, prefix="/api/student", tags=["Notifications"])
    app.include_router(preference.router, prefix="/api/student", tags=["Preferences"])

    # ── Lifecycle Events ──────────────────────────────────────────────
    @app.on_event("startup")
    async def startup():
        # 1. Ensure DB tables exist and seed default data
        Base.metadata.create_all(bind=engine)
        init_db()

        # 2. Import notification_service to register event handlers (Observer Pattern)
        import app.services.notification_service  # noqa: F401

        # 3. ── Bloom Filter initialization ────────────────────────────
        #    Seed both filters (username + ISBN) from the live DB so that
        #    every register/check-username/add-book call benefits immediately.
        from app.services.bloom_service import bloom_service
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            bloom_service.initialize(db)
        finally:
            db.close()

        # 4. ── Elasticsearch initialization + full reindex ────────────
        #    Connect to ES, ensure the index exists, then bulk-upsert all
        #    books so the search engine is immediately in sync with the DB.
        from app.services.search_service import search_service
        from app.repositories.book_repo import BookRepository
        search_service.initialize()
        if search_service.is_available():
            db2 = SessionLocal()
            try:
                all_books = BookRepository(db2).get_all_sorted(skip=0, limit=100_000)
                search_service.reindex_all(all_books)
            finally:
                db2.close()

    # ── Root & Health ─────────────────────────────────────────────────
    @app.get("/", tags=["Health"])
    async def root():
        return {
            "message": "Library Management System API",
            "version": "3.0.0",
            "docs": "/docs",
        }

    @app.get("/api/health", tags=["Health"])
    async def health():
        from sqlalchemy import text as sa_text
        from app.database import SessionLocal

        try:
            db = SessionLocal()
            db.execute(sa_text("SELECT 1"))
            db.close()
            db_status = "connected"
        except Exception:
            db_status = "disconnected"
        return {"status": "healthy", "database": db_status}

    @app.get("/api/health/advanced", tags=["Health"])
    async def health_advanced():
        """Extended health check showing Bloom Filter and Elasticsearch status."""
        from sqlalchemy import text as sa_text
        from app.database import SessionLocal
        from app.services.bloom_service import bloom_service
        from app.services.search_service import search_service

        try:
            db = SessionLocal()
            db.execute(sa_text("SELECT 1"))
            db.close()
            db_status = "connected"
        except Exception:
            db_status = "disconnected"

        return {
            "status": "healthy",
            "database": db_status,
            "bloom_filters": bloom_service.status(),
            "elasticsearch": search_service.status(),
        }

    return app

