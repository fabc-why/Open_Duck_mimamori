"""COME_HERE feature registration."""

from .intent import COME_HERE
from .handler import COME_HERE_TOPIC, ComeHereHandler


class ComeHereFeature:
    name = "come_here"

    def register(self, context) -> None:
        context.intent_registry.register(COME_HERE)
        if context.event_router is None:
            return
        if context.command_publisher_factory is not None:
            publisher = context.command_publisher_factory(COME_HERE_TOPIC)
        else:
            publisher = context.command_publisher
        if publisher is None:
            return
        handler = ComeHereHandler(publisher)
        context.event_router.subscribe(
            pattern="dialogue.intent.recognized",
            handler=handler.handle,
            name="come_here_handler",
            event_filter=lambda event: event.data.get("intent") == COME_HERE.name,
        )
