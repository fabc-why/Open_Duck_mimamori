"""Kernel input subscribers."""

from .whisper.transcription_subscriber import (
    TRANSCRIPTION_MESSAGE_TYPE,
    TRANSCRIPTION_TOPIC,
    TranscriptionMessage,
    TranscriptionSubscriber,
)

__all__ = [
    "TRANSCRIPTION_MESSAGE_TYPE",
    "TRANSCRIPTION_TOPIC",
    "TranscriptionMessage",
    "TranscriptionSubscriber",
    "InputManager",
]


def __getattr__(name: str):
    """Load the input facade only when requested."""
    if name == "InputManager":
        from .input import InputManager

        return InputManager
    raise AttributeError(name)
