"""CREATE_REMINDER intent definition."""

from inputs.whisper.models import IntentDefinition

from .datetime_parser import parse_reminder


CREATE_REMINDER = IntentDefinition(
    name="CREATE_REMINDER",
    description="指定時刻または一定時間後に、話者へ通知や起床を行う",
    examples=("7時に起こして", "7時30分に起こして", "10分後に教えて", "明日の朝に知らせて"),
    patterns=(
        r"(?=.*(?:明日の朝|[0-9０-９]+時(?:[0-9０-９]+分)?|[0-9０-９]+分後))"
        r"(?=.*(?:教えて|知らせて|起こして|リマインドして)).*",
    ),
    priority=70,
    slot_parser=parse_reminder,
)
