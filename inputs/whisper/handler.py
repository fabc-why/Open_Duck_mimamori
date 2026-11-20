"""Event adaptation for speech intent classification."""

from __future__ import annotations

from typing import Any

from kernel.event import Event
from kernel.event_router import EventRouter

from .classifier import IntentClassifier
from .normalizer import SpeechNormalizer
from .registry import IntentRegistry


class UnderstandingHandler:
    """Classify recognized speech and publish an intent Event."""

    def __init__(
        self,
        event_router: EventRouter,
        registry: IntentRegistry,
        classifier: IntentClassifier | None = None,
        normalizer: SpeechNormalizer | None = None,
        conversation_intent: str = "CONVERSATION",
        robot_called_intent: str = "ROBOT_CALLED",
    ) -> None:
        self.event_router = event_router
        self.registry = registry
        self.classifier = classifier or IntentClassifier(registry)
        self.normalizer = normalizer or SpeechNormalizer()
        self.conversation_intent = conversation_intent
        self.robot_called_intent = robot_called_intent

    async def handle(self, event: Event) -> None:
        """Publish a dialogue intent Event for a recognized utterance."""
        if event.event_type != "speech.utterance.recognized":
            return

        text = event.data.get("text", "")
        if not isinstance(text, str):
            text = ""

        _, wake_name_included, command_text = self.normalizer.normalize(text)
        confidence = 1.0
        if wake_name_included and not command_text:
            intent = self.robot_called_intent
            parameters: dict[str, Any] = {}
        elif not command_text:
            intent = self.conversation_intent
            parameters = {}
        else:
            match = self.classifier.classify(command_text)
            if match is None:
                intent = self.conversation_intent
                parameters = {"text": command_text}
                confidence = 1.0
            else:
                intent = match.intent
                parameters = match.parameters
                confidence = match.confidence

        intent_event = Event.create(
            event_type="dialogue.intent.recognized",
            source="speech_understanding",
            data={
                "intent": intent,
                "parameters": parameters,
                "original_text": text,
                "speaker_id": event.data.get("speaker_id"),
                "wake_name_included": wake_name_included,
                "classifier": "rule",
            },
            confidence=confidence,
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
        )
        await self.event_router.publish(intent_event)
