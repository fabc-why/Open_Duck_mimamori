"""Exceptions raised by the event infrastructure."""


class InvalidEventType(ValueError):
    """Raised when an event type or subscription pattern is invalid."""


class EventRouterStopped(RuntimeError):
    """Raised when an event is published after router shutdown begins."""


class EventRouterShutdownTimeout(TimeoutError):
    """Raised when graceful shutdown exceeds its timeout."""
