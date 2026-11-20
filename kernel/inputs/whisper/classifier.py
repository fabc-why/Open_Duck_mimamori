"""Generic pattern classifier with no feature-specific names."""

from __future__ import annotations

import re

from .models import IntentMatch
from .registry import IntentRegistry
from .fuzzy import find_fuzzy_match


class IntentClassifier:
    """Compare normalized text against registered intent patterns."""

    def __init__(self, registry: IntentRegistry, fuzzy_threshold: float = 0.8) -> None:
        self.registry = registry
        self.fuzzy_threshold = fuzzy_threshold

    def classify(self, command_text: str) -> IntentMatch | None:
        """Return the first highest-priority pattern match."""
        for intent in self.registry.all():
            for pattern in intent.patterns:
                if re.search(pattern, command_text):
                    return self._build_match(intent.name, command_text, 1.0)

        for intent in self.registry.all():
            match = find_fuzzy_match(
                command_text,
                intent.examples,
                threshold=self.fuzzy_threshold,
            )
            if match is not None:
                return self._build_match(intent.name, command_text, match.score)
        return None

    def _build_match(
        self,
        intent_name: str,
        command_text: str,
        confidence: float,
    ) -> IntentMatch:
        intent = self.registry.get(intent_name)
        if intent is None:
            raise RuntimeError(f"registered intent disappeared: {intent_name}")
        parameters = {}
        if intent.slot_parser is not None:
            parameters = intent.slot_parser(command_text)
        return IntentMatch(
            intent=intent.name,
            parameters=parameters,
            confidence=confidence,
        )
