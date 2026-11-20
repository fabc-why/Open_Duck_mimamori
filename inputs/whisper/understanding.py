"""Feature-independent speech understanding infrastructure."""

from .classifier import IntentClassifier
from .feature_context import FeatureContext
from .fuzzy import FuzzyMatch, find_fuzzy_match, normalize_for_fuzzy_matching
from .handler import UnderstandingHandler
from .models import IntentDefinition, IntentMatch, SlotDefinition
from .normalizer import SpeechNormalizer
from .registry import IntentRegistry

__all__ = [
    "IntentClassifier",
    "FeatureContext",
    "UnderstandingHandler",
    "IntentDefinition",
    "IntentMatch",
    "SlotDefinition",
    "SpeechNormalizer",
    "IntentRegistry",
    "FuzzyMatch",
    "find_fuzzy_match",
    "normalize_for_fuzzy_matching",
    "CREATE_REMINDER",
    "COME_HERE",
    "CONVERSATION",
    "ROBOT_CALLED",
    "STOP",
    "UNKNOWN",
    "Intent",
    "RuleBasedSpeechUnderstanding",
    "SpeechUnderstandingHandler",
    "UnderstandingResult",
    "register_speech_understanding",
]


def __getattr__(name: str):
    """Load the legacy compatibility API only when explicitly requested."""
    if name in {
        "CREATE_REMINDER",
        "COME_HERE",
        "CONVERSATION",
        "ROBOT_CALLED",
        "STOP",
        "UNKNOWN",
        "Intent",
        "RuleBasedSpeechUnderstanding",
        "SpeechUnderstandingHandler",
        "UnderstandingResult",
        "register_speech_understanding",
    }:
        from . import speech_understanding

        return getattr(speech_understanding, name)
    raise AttributeError(name)
