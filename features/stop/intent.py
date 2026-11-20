"""STOP intent definition."""

from kernel.inputs.whisper.models import IntentDefinition


STOP = IntentDefinition(
    name="STOP",
    description="ロボットに安全のため直ちに停止を依頼する",
    examples=("止まって", "ストップ", "待って"),
    patterns=(r"(?:止まって|ストップ|待って)",),
    priority=100,
)
