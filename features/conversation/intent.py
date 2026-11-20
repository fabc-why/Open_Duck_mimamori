"""CONVERSATION fallback intent definition."""

from inputs.whisper.models import IntentDefinition


CONVERSATION = IntentDefinition(
    name="CONVERSATION",
    description="上記機能に該当しない一般的な発話",
    priority=0,
)
