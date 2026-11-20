"""Whisper Event and Intent pipeline setup."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from features.come_here.feature import ComeHereFeature
from features.conversation.feature import ConversationFeature
from features.reminder.feature import ReminderFeature
from features.robot_called.feature import RobotCalledFeature
from features.stop.feature import StopFeature
from .feature_context import FeatureContext
from .handler import UnderstandingHandler
from .registry import IntentRegistry


class WhisperEventIssuer:
    """Register Whisper Event understanding and feature subscriptions."""

    def __init__(
        self,
        event_router: Any,
        command_publisher_factory: Callable[[str], object] | None = None,
    ) -> None:
        self.event_router = event_router
        self.intent_registry = IntentRegistry()
        self.understanding_handler = UnderstandingHandler(
            event_router=event_router,
            registry=self.intent_registry,
        )
        self.features = (
            StopFeature(),
            RobotCalledFeature(),
            ComeHereFeature(),
            ReminderFeature(),
            ConversationFeature(),
        )
        context = FeatureContext(
            intent_registry=self.intent_registry,
            event_router=event_router,
            command_publisher_factory=command_publisher_factory,
        )
        for feature in self.features:
            feature.register(context)

        event_router.subscribe(
            pattern="speech.utterance.recognized",
            handler=self.understanding_handler.handle,
            name="speech_understanding",
        )