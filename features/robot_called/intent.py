"""ROBOT_CALLED intent definition."""

from inputs.whisper.models import IntentDefinition


ROBOT_CALLED = IntentDefinition(
    name="ROBOT_CALLED",
    description="呼び名だけでOpenDuckを呼び出した発話",
    examples=("オープンダック", "おーぷんだっく"),
    priority=90,
)
