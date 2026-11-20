"""Robot-called feature registration."""

from .intent import ROBOT_CALLED


class RobotCalledFeature:
    name = "robot_called"

    def register(self, context) -> None:
        context.intent_registry.register(ROBOT_CALLED)
