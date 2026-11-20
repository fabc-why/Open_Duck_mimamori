"""OpenDuck event infrastructure."""

from .event import Event
from .event_router import EventRouter, RouterState
from .event_router import Subscription
from .event_types import (
    match_event_type,
    validate_event_type,
    validate_subscription_pattern,
)
from .exceptions import (
    EventRouterShutdownTimeout,
    EventRouterStopped,
    InvalidEventType,
)

__all__ = [
    "Event",
    "EventRouter",
    "EventRouterShutdownTimeout",
    "EventRouterStopped",
    "InvalidEventType",
    "RouterState",
    "Subscription",
    "match_event_type",
    "validate_event_type",
    "validate_subscription_pattern",
]
