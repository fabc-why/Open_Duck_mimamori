"""Event type validation and subscription pattern matching."""

import re

from .exceptions import InvalidEventType


_SEGMENT_PATTERN = re.compile(r"[a-z0-9_]+")


def validate_event_type(event_type: str) -> str:
    """Validate and return a dot-separated lower-case event type."""
    if not isinstance(event_type, str) or not event_type:
        raise InvalidEventType("event_type must be a non-empty string")
    if event_type != event_type.strip():
        raise InvalidEventType("event_type must not have surrounding whitespace")
    segments = event_type.split(".")
    if any(not segment or _SEGMENT_PATTERN.fullmatch(segment) is None for segment in segments):
        raise InvalidEventType(
            "event_type must contain lower-case dot-separated identifiers"
        )
    return event_type


def validate_subscription_pattern(pattern: str) -> str:
    """Validate a subscription pattern."""
    if not isinstance(pattern, str) or not pattern:
        raise InvalidEventType("subscription pattern must be a non-empty string")
    if pattern != pattern.strip():
        raise InvalidEventType("subscription pattern must not have surrounding whitespace")

    segments = pattern.split(".")
    wildcard_count = 0
    for index, segment in enumerate(segments):
        if segment == "*":
            wildcard_count += 1
            continue
        if segment == "#":
            if index != len(segments) - 1:
                raise InvalidEventType("# is only allowed as the last segment")
            continue
        if _SEGMENT_PATTERN.fullmatch(segment) is None:
            raise InvalidEventType("invalid subscription pattern")
    if wildcard_count > 1:
        raise InvalidEventType("* may appear only once in a pattern")
    return pattern


def match_event_type(pattern: str, event_type: str) -> bool:
    """Return whether an event type matches a subscription pattern."""
    validate_subscription_pattern(pattern)
    validate_event_type(event_type)

    pattern_segments = pattern.split(".")
    event_segments = event_type.split(".")

    if "#" in pattern_segments:
        prefix = pattern_segments[:-1]
        if len(event_segments) < len(prefix):
            return False
        return event_segments[: len(prefix)] == prefix

    if "*" in pattern_segments:
        if len(pattern_segments) != len(event_segments):
            return False
        return all(
            pattern_segment == "*" or pattern_segment == event_segment
            for pattern_segment, event_segment in zip(pattern_segments, event_segments)
        )

    return pattern_segments == event_segments
