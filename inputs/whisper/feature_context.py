"""Context passed to feature registration."""

from dataclasses import dataclass
from typing import Callable

from kernel.event_router import EventRouter

from .registry import IntentRegistry


@dataclass(frozen=True, slots=True)
class FeatureContext:
    """Shared infrastructure available to a feature."""

    intent_registry: IntentRegistry
    event_router: EventRouter
    command_publisher: object | None = None
    command_publisher_factory: Callable[[str], object] | None = None
