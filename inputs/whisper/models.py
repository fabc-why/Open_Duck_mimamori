"""Shared models for rule-based intent understanding."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


SlotParser = Callable[[str], dict[str, Any]]


@dataclass(frozen=True, slots=True)
class SlotDefinition:
    """Description of a slot extracted from an intent."""

    name: str
    description: str
    required: bool = False


@dataclass(frozen=True, slots=True)
class IntentDefinition:
    """A feature-owned intent definition."""

    name: str
    description: str
    examples: tuple[str, ...] = ()
    patterns: tuple[str, ...] = ()
    priority: int = 0
    slots: tuple[SlotDefinition, ...] = ()
    slot_parser: SlotParser | None = None


@dataclass(frozen=True, slots=True)
class IntentMatch:
    """A matching intent and its extracted parameters."""

    intent: str
    parameters: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
