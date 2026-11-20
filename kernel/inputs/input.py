"""Application-level input composition."""

from __future__ import annotations

from typing import Any

from .image_raw.image_input import RawImageSubscriber
from .mic_raw.audio_input import RawAudioSubscriber
from .whisper.event_issue import WhisperEventIssuer
from .whisper.transcription_subscriber import TranscriptionSubscriber


class InputManager:
    """Create and clean up all external input subscribers."""

    def __init__(
        self,
        client: Any,
        event_router: Any,
        command_publisher_factory: Any | None = None,
    ) -> None:
        self.event_issue = WhisperEventIssuer(
            event_router=event_router,
            command_publisher_factory=command_publisher_factory,
        )
        self.raw_audio = RawAudioSubscriber(client=client)
        self.raw_image = RawImageSubscriber(client=client)
        self.whisper = TranscriptionSubscriber(
            client=client,
            event_router=event_router,
        )
        self._cleaned_up = False

    def cleanup(self) -> None:
        """Clean up every input subscriber exactly once."""
        if self._cleaned_up:
            return
        self._cleaned_up = True
        self.whisper.cleanup()
        self.raw_image.cleanup()
        self.raw_audio.cleanup()