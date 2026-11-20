"""Reminder feature registration."""

from .intent import CREATE_REMINDER


class ReminderFeature:
    name = "reminder"

    def register(self, context) -> None:
        context.intent_registry.register(CREATE_REMINDER)
