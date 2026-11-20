"""COME_HERE intent handler."""

from typing import Any

from features.robot_commands import RobotCommandPublisher



COME_HERE_TOPIC = "/openduck/operation/actions"


class ComeHereHandler:
    """Request the separate robot process to approach the speaker."""

    def __init__(self, command_publisher: RobotCommandPublisher) -> None:
        self.command_publisher = command_publisher

    def handle(self, event: Any) -> None:
        """Publish a COME_HERE command without moving the robot directly."""
        self.command_publisher.publish("come_here", target="speaker")
        #print("COME_HERE command published to robot process.")


def handle_come_here(event: Any, command_publisher: RobotCommandPublisher) -> None:
    """Publish a COME_HERE command for compatibility with function-style handlers."""
    ComeHereHandler(command_publisher).handle(event)
