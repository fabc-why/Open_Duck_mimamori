"""ROS command publishing for feature handlers."""

from __future__ import annotations

import json
from typing import Any

try:
    import roslibpy
except ModuleNotFoundError:
    roslibpy = None


ROBOT_COMMAND_MESSAGE_TYPE = "std_msgs/String"


class RobotCommandPublisher:
    """Publish commands for the separate robot-control process."""

    def __init__(
        self,
        client: Any,
        topic: str,
    ) -> None:
        if roslibpy is None:
            raise ModuleNotFoundError(
                "roslibpy is required to publish robot commands"
            )
        topic = topic.strip()
        if not topic:
            raise ValueError("robot command topic must not be empty")
        self.topic = roslibpy.Topic(client, topic, ROBOT_COMMAND_MESSAGE_TYPE)
        self.topic.advertise()
        self._cleaned_up = False

    def publish(self, command: str, **parameters: Any) -> None:
        """Publish a command name and its parameters as JSON."""
        if self._cleaned_up:
            return
        payload = {"command": command, **parameters}
        self.topic.publish(roslibpy.Message({"data": json.dumps(payload)}))

    def cleanup(self) -> None:
        """Stop publishing without terminating the shared ROS client."""
        if self._cleaned_up:
            return
        self._cleaned_up = True
        self.topic.unadvertise()
