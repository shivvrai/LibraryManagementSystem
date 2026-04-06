# app/services/search_service.py — Elasticsearch full-text search layer
#
# Design rationale:
#   Elasticsearch replaces SQLite's ILIKE search with:
#     - Multi-field full-text search (title + author) with English stemming
#     - Fuzzy matching (AUTO fuzziness) to tolerate typos
#     - Relevance scoring (_score) — most relevant result listed first
#     - Keyword filtering on category / isbn for exact matches
#
# Fallback strategy:
#   If Elasticsearch is unavailable (not running, misconfigured, etc.) every
#   method returns None. Callers (book_service.py) detect None and fall back
#   to the existing SQLite ILIKE search — the app always remains functional.
#
# Index: "library_books"
#   Each document mirrors the Book model. Documents are upserted on every
#   add/update and deleted on removal. On startup the entire books table is
#   bulk-indexed so ES stays in sync with the DB.

import logging
import math
from typing import Optional, List

from app.config import settings

logger = logging.getLogger(__name__)

# ── Index mapping ─────────────────────────────────────────────────────
_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "id":        {"type": "integer"},
            "title":     {"type": "text",    "analyzer": "english"},
            "author":    {"type": "text",    "analyzer": "english"},
            "isbn":      {"type": "keyword"},
            "category":  {"type": "keyword"},
            "pages":     {"type": "integer"},
            "price":     {"type": "float"},
            "quantity":  {"type": "integer"},
            "available": {"type": "integer"},
        }
    },
    "settings": {
        "number_of_shards":   1,
        "number_of_replicas": 0,  # single-node dev setup
    },
}


def _book_to_doc(book) -> dict:
    """Convert a SQLAlchemy Book ORM object to an ES document dict."""
    return {
        "id":        book.id,
        "title":     book.title,
        "author":    book.author,
        "isbn":      book.isbn,
        "category":  book.category,
        "pages":     book.pages,
        "price":     float(book.price),
        "quantity":  book.quantity,
        "available": book.available,
    }


class SearchService:
    """Singleton service for Elasticsearch-backed book search."""

    def __init__(self) -> None:
        self._client = None
        self._available: bool = False

    # ── Lifecycle ─────────────────────────────────────────────────────

    def initialize(self) -> None:
        """
        Connect to Elasticsearch and ensure the index exists.
        Safe to call even if ES is not running — sets _available=False in that case.
        """
        if not settings.ELASTICSEARCH_URL:
            logger.info("Elasticsearch disabled (ELASTICSEARCH_URL is empty)")
            return

        try:
            from elasticsearch import Elasticsearch, ConnectionError as ESConnectionError

            client = Elasticsearch(
                settings.ELASTICSEARCH_URL,
                request_timeout=5,
                max_retries=1,
                retry_on_timeout=False,
            )

            if not client.ping():
                logger.warning(
                    "Elasticsearch not reachable at %s — falling back to SQL search",
                    settings.ELASTICSEARCH_URL,
                )
                return

            self._client = client
            self._available = True
            self._ensure_index()
            logger.info(
                "Elasticsearch connected at %s, index '%s' ready",
                settings.ELASTICSEARCH_URL, settings.ES_INDEX_BOOKS,
            )

        except Exception as exc:
            logger.warning("Elasticsearch initialization failed (%s) — SQL fallback active", exc)

    def _ensure_index(self) -> None:
        """Create the books index if it doesn't already exist."""
        idx = settings.ES_INDEX_BOOKS
        if not self._client.indices.exists(index=idx):
            self._client.indices.create(index=idx, body=_INDEX_MAPPING)
            logger.info("Created Elasticsearch index '%s'", idx)

    def reindex_all(self, books: List) -> None:
        """
        Bulk-upsert all books into Elasticsearch.
        Called once on startup to ensure ES is in sync with the DB.
        """
        if not self._available or not self._client:
            return

        if not books:
            logger.info("No books to reindex")
            return

        from elasticsearch.helpers import bulk

        actions = [
            {
                "_index": settings.ES_INDEX_BOOKS,
                "_id":    str(book.id),
                "_source": _book_to_doc(book),
            }
            for book in books
        ]

        success, errors = bulk(self._client, actions, raise_on_error=False)
        if errors:
            logger.warning("Elasticsearch bulk reindex: %d failures", len(errors))
        logger.info(
            "Elasticsearch reindex complete: %d books indexed, %d errors",
            success, len(errors),
        )

    # ── CRUD ─────────────────────────────────────────────────────────

    def index_book(self, book) -> None:
        """Upsert a single book document into Elasticsearch."""
        if not self._available or not self._client:
            return
        try:
            self._client.index(
                index=settings.ES_INDEX_BOOKS,
                id=str(book.id),
                document=_book_to_doc(book),
            )
            logger.debug("Elasticsearch: indexed book id=%d", book.id)
        except Exception as exc:
            logger.warning("Elasticsearch index_book failed for id=%d: %s", book.id, exc)

    def delete_book(self, book_id: int) -> None:
        """Delete a book document from Elasticsearch."""
        if not self._available or not self._client:
            return
        try:
            self._client.delete(
                index=settings.ES_INDEX_BOOKS,
                id=str(book_id),
                ignore=[404],
            )
            logger.debug("Elasticsearch: deleted book id=%d", book_id)
        except Exception as exc:
            logger.warning("Elasticsearch delete_book failed for id=%d: %s", book_id, exc)

    # ── Search ────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 50,
        category: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Full-text fuzzy search over title and author.
        Returns None if ES is not available (caller should fall back to SQL).

        Query strategy:
          - multi_match with fuzziness=AUTO across title + author (weighted)
          - optional term filter on category
          - pagination via from/size
        """
        if not self._available or not self._client:
            return None

        try:
            must_clauses = [
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "author^2"],   # title ranked highest
                        "fuzziness": "AUTO",
                        "prefix_length": 1,                  # first char must match
                        "type": "best_fields",
                    }
                }
            ]

            filter_clauses = []
            if category:
                filter_clauses.append({"term": {"category": category}})

            es_query = {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses,
                }
            }

            from_offset = (page - 1) * per_page

            response = self._client.search(
                index=settings.ES_INDEX_BOOKS,
                body={
                    "query": es_query,
                    "from": from_offset,
                    "size": per_page,
                    "_source": True,
                    "highlight": {
                        "fields": {
                            "title":  {"number_of_fragments": 0},
                            "author": {"number_of_fragments": 0},
                        }
                    },
                },
            )

            hits = response["hits"]
            total = hits["total"]["value"]
            items = []
            for hit in hits["hits"]:
                doc = hit["_source"]
                doc["_score"] = hit["_score"]
                # Attach highlight snippets if available
                if "highlight" in hit:
                    doc["_highlight"] = hit["highlight"]
                items.append(doc)

            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": math.ceil(total / per_page) if per_page else 1,
                "engine": "elasticsearch",
                "fuzzy": True,
            }

        except Exception as exc:
            logger.warning("Elasticsearch search failed: %s — falling back to SQL", exc)
            return None

    # ── Status ────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Return True if Elasticsearch is connected and ready."""
        return self._available

    def status(self) -> dict:
        """Return health/debug information."""
        info: dict = {
            "available": self._available,
            "url": settings.ELASTICSEARCH_URL,
            "index": settings.ES_INDEX_BOOKS,
        }
        if self._available and self._client:
            try:
                count_resp = self._client.count(index=settings.ES_INDEX_BOOKS)
                info["indexed_books"] = count_resp["count"]
            except Exception:
                info["indexed_books"] = "unknown"
        return info


# Singleton instance — import this everywhere
search_service = SearchService()
