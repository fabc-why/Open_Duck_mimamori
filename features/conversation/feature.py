"""Conversation feature registration."""

from .intent import CONVERSATION


class ConversationFeature:
    name = "conversation"

    def register(self, context) -> None:
        context.intent_registry.register(CONVERSATION)
