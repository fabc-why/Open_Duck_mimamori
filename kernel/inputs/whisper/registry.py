"""Registry for feature-defined intents."""

from __future__ import annotations

from .models import IntentDefinition


class IntentRegistry:
    """Store and retrieve IntentDefinitions."""

    def __init__(self) -> None:
        self._intents: dict[str, IntentDefinition] = {}

    def register(self, intent: IntentDefinition) -> None:
        """Register an intent, replacing one with the same name."""
        if not isinstance(intent.name, str) or not intent.name.strip():
            raise ValueError("intent name must not be empty")
        self._intents[intent.name] = intent

    def unregister(self, name: str) -> bool:
        """Remove an intent definition."""
        return self._intents.pop(name, None) is not None

    def get(self, name: str) -> IntentDefinition | None:
        """Get an intent definition by name."""
        return self._intents.get(name)

    def all(self) -> tuple[IntentDefinition, ...]:
        """Return intents ordered by descending priority."""
        return tuple(
            sorted(
                self._intents.values(),
                key=lambda intent: (-intent.priority, intent.name),
            )
        )
