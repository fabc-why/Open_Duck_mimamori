"""Whisper input subscribers."""

from .classifier import IntentClassifier
from .feature_context import FeatureContext
from .fuzzy import FuzzyMatch, find_fuzzy_match, normalize_for_fuzzy_matching
from .handler import UnderstandingHandler
from .models import IntentDefinition, IntentMatch, SlotDefinition
from .normalizer import SpeechNormalizer
from .registry import IntentRegistry
from .transcription_subscriber import (
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
    "IntentClassifier",
    "FeatureContext",
    "FuzzyMatch",
    "find_fuzzy_match",
    "normalize_for_fuzzy_matching",
    "UnderstandingHandler",
    "IntentDefinition",
    "IntentMatch",
    "SlotDefinition",
    "SpeechNormalizer",
    "IntentRegistry",
    "WhisperEventIssuer",
]


def __getattr__(name: str):
    """Load the Event issuer lazily to avoid package import cycles."""
    if name == "WhisperEventIssuer":
        from .event_issue import WhisperEventIssuer

        return WhisperEventIssuer
    raise AttributeError(name)
