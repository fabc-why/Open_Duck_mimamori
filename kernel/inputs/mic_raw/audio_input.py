"""ROS2 raw audio input subscriber."""

from __future__ import annotations

import base64
import binascii
import logging
from collections.abc import Callable
from typing import Any

try:
    import roslibpy
except ModuleNotFoundError:
    roslibpy = None


RAW_AUDIO_TOPIC = "/openduck/audio/raw"
RAW_AUDIO_TYPE = "std_msgs/UInt8MultiArray"
AudioCallback = Callable[[bytes], None]


def decode_audio_message(message: Any) -> bytes:
    """Convert a rosbridge audio message into raw bytes."""
    value = message.get("data") if isinstance(message, dict) else getattr(message, "data", None)
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, list):
        try:
            return bytes(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("audio data contains invalid byte values") from exc
    if isinstance(value, str):
        try:
            return base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("audio data is not valid base64") from exc
    raise ValueError("audio message has no valid data field")


class RawAudioSubscriber:
    """Subscribe to externally supplied microphone audio."""

    def __init__(
        self,
        client: Any,
        callback: AudioCallback | None = None,
        topic: str = RAW_AUDIO_TOPIC,
        message_type: str = RAW_AUDIO_TYPE,
    ) -> None:
        if roslibpy is None:
            raise ModuleNotFoundError("roslibpy is required to subscribe to ROS audio")
        if not topic.strip():
            raise ValueError("audio topic must not be empty")

        self.topic_name = topic.strip()
        self.callback = callback
        self.topic = roslibpy.Topic(client, self.topic_name, message_type)
        self.topic.subscribe(self._handle_message)
        self.cleaned_up = False

    def _handle_message(self, message: Any) -> None:
        try:
            audio = decode_audio_message(message)
        except ValueError:
            logging.exception("failed to decode raw audio message")
            return
        if self.callback is not None:
            try:
                self.callback(audio)
            except Exception:
                logging.exception("raw audio callback failed")

    def cleanup(self) -> None:
        """Unsubscribe safely without terminating the shared ROS client."""
        if self.cleaned_up:
            return
        self.cleaned_up = True
        self.topic.unsubscribe()
