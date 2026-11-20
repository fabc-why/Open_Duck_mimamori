"""ROS raw camera image subscriber."""

from __future__ import annotations

from typing import Any

try:
    import roslibpy
except ModuleNotFoundError:
    roslibpy = None


IMAGE_TOPIC = "/openduck/head_cam/compress"
IMAGE_MESSAGE_TYPE = "sensor_msgs/CompressedImage"


class RawImageSubscriber:
    """Subscribe to raw compressed images and discard received messages."""

    def __init__(
        self,
        client: Any,
        topic: str = IMAGE_TOPIC,
        message_type: str = IMAGE_MESSAGE_TYPE,
    ) -> None:
        if roslibpy is None:
            raise ModuleNotFoundError("roslibpy is required to subscribe to ROS images")
        topic = topic.strip()
        if not topic:
            raise ValueError("image topic must not be empty")

        self.topic_name = topic
        self.topic = roslibpy.Topic(client, topic, message_type)
        self.topic.subscribe(self._handle_message)
        self._cleaned_up = False

    def _handle_message(self, message: Any) -> None:
        """Receive and intentionally discard a camera message."""

    def cleanup(self) -> None:
        """Unsubscribe safely without terminating the shared ROS client."""
        if self._cleaned_up:
            return
        self._cleaned_up = True
        self.topic.unsubscribe()