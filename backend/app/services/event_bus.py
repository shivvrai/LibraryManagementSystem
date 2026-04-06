# app/services/event_bus.py — Observer Pattern Event Bus for notification system
#
# Design Pattern: Observer (Pub/Sub)
# - Publishers (book_service, transaction_service) emit events
# - Subscribers (notification_service) react to events
# - Loose coupling: publishers don't know about subscribers

import logging
from typing import Callable, Dict, List, Any

logger = logging.getLogger(__name__)


class EventBus:
    """
    In-process event bus implementing the Observer Pattern.
    Provides publish/subscribe mechanism for decoupled communication
    between services.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Register a handler for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info("EventBus: subscribed handler '%s' to event '%s'",
                     handler.__name__, event_type)

    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Publish an event to all subscribers.
        Each handler receives the event data dict.
        Errors in one handler don't block others.
        """
        handlers = self._subscribers.get(event_type, [])
        if not handlers:
            return

        logger.info("EventBus: publishing '%s' to %d handler(s)", event_type, len(handlers))
        for handler in handlers:
            try:
                handler(data)
            except Exception:
                logger.exception(
                    "EventBus: handler '%s' failed for event '%s'",
                    handler.__name__, event_type,
                )

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Remove a handler from a specific event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]


# ── Event Type Constants ──────────────────────────────────────────────
BOOK_ADDED = "book.added"
BOOK_AVAILABLE = "book.available"
RESERVATION_READY = "reservation.ready"

# ── Global Event Bus Singleton ────────────────────────────────────────
event_bus = EventBus()
