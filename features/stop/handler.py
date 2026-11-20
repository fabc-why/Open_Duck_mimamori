"""STOP intent handler."""

from typing import Any

from features.robot_commands import RobotCommandPublisher



STOP_TOPIC = "/openduck/operation/actions"


class StopHandler:
    """Request the separate robot process to stop safely."""

    def __init__(self, command_publisher: RobotCommandPublisher) -> None:
        self.command_publisher = command_publisher

    def handle(self, event: Any) -> None:
        """Publish a STOP command without controlling the robot directly."""
        self.command_publisher.publish("stop")
