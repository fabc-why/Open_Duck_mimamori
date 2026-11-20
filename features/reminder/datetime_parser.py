"""Reminder time-expression parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ReminderSlots:
    time_expression: str
    trigger_kind: str
    hour: int | None
    minute: int | None
    duration_seconds: int | None
    action: str
    needs_confirmation: bool


def parse_time_expression(text: str) -> tuple[str | None, str | None, int | None]:
    normalized = text.replace("０", "0").replace("１", "1").replace("２", "2")
    normalized = normalized.replace("３", "3").replace("４", "4").replace("５", "5")
    normalized = normalized.replace("６", "6").replace("７", "7").replace("８", "8")
    normalized = normalized.replace("９", "9")

    relative = re.search(r"([0-9]+)分後", normalized)
    if relative:
        duration = int(relative.group(1)) * 60
        return relative.group(0), "relative_duration", duration
    if "明日の朝" in normalized:
        return "明日の朝", "absolute_time", None

    absolute = re.search(r"([0-9]+)時(?:([0-9]+)分)?", normalized)
    if absolute:
        return absolute.group(0), "absolute_time", None
    return None, None, None


def parse_reminder(text: str) -> dict[str, Any]:
    """Return generic reminder parameters."""
    time_expression, trigger_kind, duration_seconds = parse_time_expression(text)
    if trigger_kind == "relative_duration":
        hour = None
        minute = None
    else:
        match = re.search(r"([0-9]+)時(?:([0-9]+)分)?", text)
        hour = int(match.group(1)) if match else None
        minute = int(match.group(2)) if match and match.group(2) else 0 if match else None

    if "起こして" in text:
        action = "WAKE_PERSON"
    else:
        action = "NOTIFY"
    return {
        "time_expression": time_expression,
        "trigger_kind": trigger_kind,
        "hour": hour,
        "minute": minute,
        "duration_seconds": duration_seconds,
        "action": action,
        "needs_confirmation": trigger_kind == "absolute_time",
    }
