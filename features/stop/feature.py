"""Stop feature registration."""

from .intent import STOP
from .handler import STOP_TOPIC, StopHandler


class StopFeature:
    name = "stop"

    def register(self, context) -> None:
        context.intent_registry.register(STOP)
        if context.event_router is None:
            return
        if context.command_publisher_factory is not None:
            publisher = context.command_publisher_factory(STOP_TOPIC)
        else:
            publisher = context.command_publisher
        if publisher is None:
            return
        handler = StopHandler(publisher)
        context.event_router.subscribe(
            pattern="dialogue.intent.recognized",
            handler=handler.handle,
            name="stop_handler",
            event_filter=lambda event: event.data.get("intent") == STOP.name,
        )
