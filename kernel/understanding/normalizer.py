"""Feature-independent spoken-text normalization."""

from __future__ import annotations


WAKE_NAMES = (
    "openduck",
    "open duck",
    "オープンダック",
    "おーぷんだっく",
)


class SpeechNormalizer:
    """Normalize spacing and remove an optional wake name."""

    def normalize(self, text: str) -> tuple[str, bool, str]:
        """Return normalized text, wake-name presence, and command text."""
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        original = " ".join(text.strip().split())
        lowered = original.lower()
        for wake_name in WAKE_NAMES:
            if lowered.startswith(wake_name.lower()):
                command = original[len(wake_name):].strip()
                command = command.lstrip(" 、,。")
                command = " ".join(command.split())
                return original, True, command
        return original, False, original
