"""Immutable event model."""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from .event_types import validate_event_type


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return copy.deepcopy(value)


def _to_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _to_json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_to_json_value(item) for item in value]
    return copy.deepcopy(value)


def _parse_datetime(value: Any, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an ISO 8601 datetime") from exc
    else:
        raise ValueError(f"{field_name} must be a datetime or ISO 8601 string")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class Event:
    """An immutable fact that occurred in the system."""

    event_id: str
    event_type: str
    source: str
    occurred_at: datetime
    received_at: datetime
    data: dict[str, Any]
    confidence: float
    correlation_id: str | None
    causation_id: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, str) or not self.event_type.strip():
            raise ValueError("event_type must not be empty")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must not be empty")
        event_type = self.event_type.strip()
        source = self.source.strip()
        validate_event_type(event_type)
        object.__setattr__(self, "event_type", event_type)
        object.__setattr__(self, "source", source)

        occurred_at = _parse_datetime(self.occurred_at, "occurred_at")
        received_at = _parse_datetime(self.received_at, "received_at")
        object.__setattr__(self, "occurred_at", occurred_at)
        object.__setattr__(self, "received_at", received_at)

        if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
            raise ValueError("confidence must be a number")
        confidence = float(self.confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        object.__setattr__(self, "confidence", confidence)

        if not isinstance(self.data, Mapping):
            raise TypeError("data must be a dict")
        try:
            json.dumps(_to_json_value(self.data), allow_nan=False)
        except (TypeError, ValueError, OverflowError) as exc:
            raise TypeError("data must be JSON serializable") from exc
        object.__setattr__(self, "data", _freeze(self.data))

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        source: str,
        occurred_at: datetime | None = None,
        data: dict[str, Any] | None = None,
        confidence: float = 1.0,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> "Event":
        """Create a validated, immutable event."""
        if not isinstance(event_type, str):
            raise ValueError("event_type must be a string")
        if not isinstance(source, str):
            raise ValueError("source must be a string")
        event_type = event_type.strip()
        source = source.strip()
        if not event_type:
            raise ValueError("event_type must not be empty")
        if not source:
            raise ValueError("source must not be empty")
        validate_event_type(event_type)

        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            raise ValueError("confidence must be a number")
        confidence = float(confidence)
        if confidence < 0.0 or confidence > 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        event_data = {} if data is None else data
        if not isinstance(event_data, dict):
            raise TypeError("data must be a dict")
        try:
            json.dumps(event_data, allow_nan=False)
        except (TypeError, ValueError, OverflowError) as exc:
            raise TypeError("data must be JSON serializable") from exc

        now = _utc_now()
        occurred = now if occurred_at is None else _parse_datetime(occurred_at, "occurred_at")

        if correlation_id is None:
            correlation_id = str(uuid4())

        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            source=source,
            occurred_at=occurred,
            received_at=now,
            data=_freeze(event_data),
            confidence=confidence,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a normal mutable JSON-compatible dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "occurred_at": self.occurred_at.isoformat(),
            "received_at": self.received_at.isoformat(),
            "data": _to_json_value(self.data),
            "confidence": self.confidence,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
        }

    def to_json(self) -> str:
        """Serialize the event to JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Event":
        """Create an event from a mapping."""
        required = {
            "event_id",
            "event_type",
            "source",
            "occurred_at",
            "received_at",
            "data",
            "confidence",
            "correlation_id",
            "causation_id",
        }
        missing = required.difference(value)
        if missing:
            raise ValueError(f"missing event fields: {', '.join(sorted(missing))}")

        confidence = value["confidence"]
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            raise ValueError("confidence must be a number")
        confidence = float(confidence)
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        event_id = str(value["event_id"])
        event_type = str(value["event_type"]).strip()
        source = str(value["source"]).strip()
        if not event_type:
            raise ValueError("event_type must not be empty")
        if not source:
            raise ValueError("source must not be empty")
        validate_event_type(event_type)

        data = value["data"]
        if not isinstance(data, dict):
            raise TypeError("data must be a dict")
        try:
            json.dumps(data, allow_nan=False)
        except (TypeError, ValueError, OverflowError) as exc:
            raise TypeError("data must be JSON serializable") from exc

        return cls(
            event_id=event_id,
            event_type=event_type,
            source=source,
            occurred_at=_parse_datetime(value["occurred_at"], "occurred_at"),
            received_at=_parse_datetime(value["received_at"], "received_at"),
            data=_freeze(data),
            confidence=confidence,
            correlation_id=value["correlation_id"],
            causation_id=value["causation_id"],
        )

    @classmethod
    def from_json(cls, value: str) -> "Event":
        """Create an event from JSON."""
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("value must contain valid JSON") from exc
        if not isinstance(decoded, dict):
            raise ValueError("event JSON must decode to an object")
        return cls.from_dict(decoded)
