# app/config.py — Centralized configuration via environment variables

import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # ── Security ──────────────────────────────────────────────────────
    SECRET_KEY: str = Field(
        default="change-me-in-production-use-a-long-random-string",
        description="JWT signing key — MUST be overridden in production",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── Database ──────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="sqlite:///./library.db",
        description="SQLAlchemy connection string. Use postgresql://... for production",
    )

    # ── CORS ──────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://127.0.0.1",
    ]

    # Set this to your EC2 public IP on AWS, e.g. "http://13.235.50.100"
    EXTRA_CORS_ORIGIN: str = ""

    # ── Business Rules ────────────────────────────────────────────────
    FINE_PER_DAY: float = 10.0
    MAX_BOOKS_PER_STUDENT: int = 3
    RETURN_DAYS: int = 7
    MAX_RENEWALS: int = 2

    # ── Logging ───────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── Elasticsearch ─────────────────────────────────────────────────
    ELASTICSEARCH_URL: str = Field(
        default="http://localhost:9200",
        description="Elasticsearch connection URL. Set to empty string to disable ES.",
    )
    ES_INDEX_BOOKS: str = "library_books"

    # ── Bloom Filters ─────────────────────────────────────────────────
    BLOOM_CAPACITY: int = Field(
        default=10000,
        description="Expected maximum number of usernames/ISBNs. Resize if DB grows beyond this.",
    )
    BLOOM_ERROR_RATE: float = Field(
        default=0.001,
        description="Acceptable false-positive rate for Bloom filters (0.1%).",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    def get_cors_origins(self) -> List[str]:
        """Return CORS origins including the optional extra origin."""
        origins = list(self.CORS_ORIGINS)
        if self.EXTRA_CORS_ORIGIN:
            origins.append(self.EXTRA_CORS_ORIGIN)
        return origins


settings = Settings()
