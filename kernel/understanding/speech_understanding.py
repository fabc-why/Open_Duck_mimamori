"""Compatibility wrapper for the rule-based understanding API."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from features.come_here.feature import ComeHereFeature
from features.reminder.feature import ReminderFeature
from features.robot_called.feature import RobotCalledFeature
from features.stop.feature import StopFeature
from kernel.understanding.feature_context import FeatureContext

from .classifier import IntentClassifier
from .handler import UnderstandingHandler
from .normalizer import SpeechNormalizer
from .registry import IntentRegistry


ROBOT_CALLED = "ROBOT_CALLED"
COME_HERE = "COME_HERE"
STOP = "STOP"
CREATE_REMINDER = "CREATE_REMINDER"
CONVERSATION = "CONVERSATION"
UNKNOWN = "UNKNOWN"


class Intent(str, Enum):
    """Compatibility enum for existing imports."""

    ROBOT_CALLED = ROBOT_CALLED
    COME_HERE = COME_HERE
    STOP = STOP
    CREATE_REMINDER = CREATE_REMINDER
    CONVERSATION = CONVERSATION
    UNKNOWN = UNKNOWN


@dataclass(frozen=True, slots=True)
class UnderstandingResult:
    """Compatibility result for existing callers."""

    intent: str
    parameters: dict[str, Any]
    confidence: float
    wake_name_included: bool
    command_text: str
    classifier: str = "rule"


class RuleBasedSpeechUnderstanding:
    """Compatibility classifier backed by the feature registry."""

    def __init__(self) -> None:
        self.registry = IntentRegistry()
        context = FeatureContext(self.registry, event_router=None)
        for feature in (
            StopFeature(),
            RobotCalledFeature(),
            ComeHereFeature(),
            ReminderFeature(),
        ):
            feature.register(context)
        self.normalizer = SpeechNormalizer()
        self.classifier = IntentClassifier(self.registry)

    def classify(self, text: str) -> UnderstandingResult:
        _, wake_name_included, command_text = self.normalizer.normalize(text)
        if wake_name_included and not command_text:
            return UnderstandingResult(
                ROBOT_CALLED, {}, 1.0, True, "", "rule"
            )
        if not command_text:
            return UnderstandingResult(UNKNOWN, {}, 1.0, False, "", "rule")

        match = self.classifier.classify(command_text)
        if match is None:
            return UnderstandingResult(
                CONVERSATION,
                {"text": command_text},
                1.0,
                wake_name_included,
                command_text,
                "rule",
            )
        return UnderstandingResult(
            match.intent,
            match.parameters,
            match.confidence,
            wake_name_included,
            command_text,
            "rule",
        )


class SpeechUnderstandingHandler:
    """Compatibility handler for existing RuleBasedSpeechUnderstanding callers."""

    def __init__(self, event_router, classifier) -> None:
        self.event_router = event_router
        self.classifier = classifier

    async def handle(self, event) -> None:
        """Publish an intent Event using the compatibility classifier."""
        if event.event_type != "speech.utterance.recognized":
            return

        text = event.data.get("text", "")
        if not isinstance(text, str):
            text = ""
        result = self.classifier.classify(text)
        from kernel.event import Event

        intent_event = Event.create(
            event_type="dialogue.intent.recognized",
            source="speech_understanding",
            data={
                "intent": result.intent,
                "parameters": result.parameters,
                "original_text": text,
                "speaker_id": event.data.get("speaker_id"),
                "wake_name_included": result.wake_name_included,
                "classifier": result.classifier,
            },
            confidence=result.confidence,
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
        )
        await self.event_router.publish(intent_event)


def register_speech_understanding(router, handler) -> None:
    """Register the compatibility speech understanding handler."""
    router.subscribe(
        pattern="speech.utterance.recognized",
        handler=handler.handle,
        name="speech_understanding",
    )
