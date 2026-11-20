"""ROS transcription input subscriber."""

from __future__ import annotations

import json
import logging
import threading
from collections import OrderedDict
from collections.abc import Mapping
from concurrent.futures import Future
from dataclasses import dataclass
from datetime import datetime
from typing import Any

try:
    import roslibpy
except ModuleNotFoundError:
    roslibpy = None

from kernel.event import Event
from kernel.event_router import EventRouter


TRANSCRIPTION_TOPIC = "/openduck/speech/transcription"
TRANSCRIPTION_MESSAGE_TYPE = "std_msgs/String"


@dataclass(frozen=True, slots=True)
class TranscriptionMessage:
    """Validated transcription received from ROS."""

    segment_id: str
    text: str
    language: str
    started_at: datetime
    ended_at: datetime

    @classmethod
    def from_ros_message(cls, message: Any) -> "TranscriptionMessage":
        """Validate and convert a rosbridge String message."""
        if isinstance(message, Mapping):
            data = message.get("data")
        else:
            data = getattr(message, "data", None)

        if not isinstance(data, str):
            raise ValueError("ROS message data must be a string")

        try:
            value = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ValueError("ROS message data must contain valid JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("ROS message data JSON must be an object")

        required = ("segment_id", "text", "language", "started_at", "ended_at")
        missing = [field for field in required if field not in value]
        if missing:
            raise ValueError(
                f"missing required transcription fields: {', '.join(missing)}"
            )

        segment_id = value["segment_id"]
        text = value["text"]
        language = value["language"]
        if not isinstance(segment_id, str) or not segment_id.strip():
            raise ValueError("segment_id must not be empty")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must not be empty")
        if not isinstance(language, str) or not language.strip():
            raise ValueError("language must not be empty")

        started_at = cls._parse_datetime(value["started_at"], "started_at")
        ended_at = cls._parse_datetime(value["ended_at"], "ended_at")
        if ended_at < started_at:
            raise ValueError("ended_at must not be before started_at")

        return cls(
            segment_id=segment_id.strip(),
            text=text.strip(),
            language=language.strip(),
            started_at=started_at,
            ended_at=ended_at,
        )

    @staticmethod
    def _parse_datetime(value: Any, field_name: str) -> datetime:
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be an ISO 8601 string")
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an ISO 8601 datetime") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError(f"{field_name} must be timezone-aware")
        return parsed


class TranscriptionSubscriber:
    """Receive transcription results and publish them as Events."""

    def __init__(
        self,
        client: Any,
        event_router: EventRouter,
        topic: str = TRANSCRIPTION_TOPIC,
        message_type: str = TRANSCRIPTION_MESSAGE_TYPE,
        *,
        deduplication_capacity: int = 1000,
    ) -> None:
        if roslibpy is None:
            raise ModuleNotFoundError("roslibpy is required to subscribe to ROS")
        if (
            isinstance(deduplication_capacity, bool)
            or not isinstance(deduplication_capacity, int)
            or deduplication_capacity <= 0
        ):
            raise ValueError("deduplication_capacity must be greater than zero")

        topic = topic.strip()
        if not topic:
            raise ValueError("topic must not be empty")

        self.event_router = event_router
        self.topic_name = topic
        self.deduplication_capacity = deduplication_capacity
        self.accepted_messages = 0
        self.duplicate_messages = 0
        self.invalid_messages = 0
        self.publish_failures = 0

        self._seen_segment_ids: OrderedDict[str, None] = OrderedDict()
        self._lock = threading.Lock()
        self._cleaned_up = False
        self.topic = roslibpy.Topic(client, topic, message_type)
        self.topic.subscribe(self._handle_message)

    def _handle_message(self, message: Any) -> None:
        with self._lock:
            if self._cleaned_up:
                return

        try:
            transcription = TranscriptionMessage.from_ros_message(message)
        except (TypeError, ValueError):
            with self._lock:
                self.invalid_messages += 1
            logging.exception("invalid transcription message")
            return

        with self._lock:
            if transcription.segment_id in self._seen_segment_ids:
                self.duplicate_messages += 1
                return
            self._seen_segment_ids[transcription.segment_id] = None
            if len(self._seen_segment_ids) > self.deduplication_capacity:
                self._seen_segment_ids.popitem(last=False)
            self.accepted_messages += 1

        try:
            event = Event.create(
                event_type="speech.utterance.recognized",
                source="whisper.transcription",
                occurred_at=transcription.ended_at,
                data={
                    "segment_id": transcription.segment_id,
                    "text": transcription.text,
                    "language": transcription.language,
                    "started_at": transcription.started_at.isoformat(),
                    "ended_at": transcription.ended_at.isoformat(),
                    "speaker_id": None,
                },
                # No transcription confidence is provided; 1.0 represents receipt certainty.
                confidence=1.0,
            )
            future = self.event_router.publish_threadsafe(event)
            future.add_done_callback(self._on_publish_done)
        except Exception:
            with self._lock:
                self.publish_failures += 1
            logging.exception("failed to publish transcription Event")

    def _on_publish_done(self, future: Future[bool]) -> None:
        try:
            future.result()
        except Exception:
            with self._lock:
                self.publish_failures += 1
            logging.exception("transcription Event publish failed")

    def cleanup(self) -> None:
        """Unsubscribe without terminating the shared ROS client."""
        with self._lock:
            if self._cleaned_up:
                return
            self._cleaned_up = True

        try:
            self.topic.unsubscribe()
        except Exception:
            logging.exception("failed to unsubscribe transcription Topic")
