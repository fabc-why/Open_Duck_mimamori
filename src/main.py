"""OpenDuck application entry point."""

from __future__ import annotations

import argparse
import asyncio
import logging
import subprocess
import sys
import threading
from typing import Final
from pathlib import Path

import roslibpy

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from features.robot_commands import RobotCommandPublisher
from kernel.event_router import EventRouter
from inputs.input import InputManager


#らくするために無理くり入れた機能なので、本番では使わないでください。
#operatoｒの方の実行は、本来はここと独立してやつ感じなので
ROS_HOST: Final = "localhost"
ROS_PORT: Final = 9090
OPERATOR_PYTHON: Final = "/home/openduck/openduck_function/operator/.venv/bin/python"
OPERATOR_MAIN: Final = "/home/openduck/openduck_function/operator/src/main.py"
OPERATOR_CWD: Final = "/home/openduck/openduck_function/operator"
OPERATOR_STOP_TIMEOUT: Final = 5.0


class Mimamori:
    """Receive transcriptions, classify intents, and publish robot commands."""

    def __init__(self, host: str = ROS_HOST, port: int = ROS_PORT) -> None:
        self.client = roslibpy.Ros(host=host, port=port)
        self.client.run()
        self.running = True
        self.operator_process = subprocess.Popen(
            [OPERATOR_PYTHON, "-u", OPERATOR_MAIN],
            cwd=OPERATOR_CWD,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.operator_output_thread = threading.Thread(
            target=self._forward_operator_output,
            name="operation-output",
            daemon=True,
        )
        self.operator_output_thread.start()

        self.event_router = EventRouter()
        self.command_publishers: list[RobotCommandPublisher] = []

        def create_command_publisher(topic: str) -> RobotCommandPublisher:
            publisher = RobotCommandPublisher(self.client, topic)
            self.command_publishers.append(publisher)
            return publisher

        self.inputs = InputManager(
            client=self.client,
            event_router=self.event_router,
            command_publisher_factory=create_command_publisher,
        )

    async def _run(self) -> None:
        router_task = asyncio.create_task(self.event_router.run())
        await asyncio.sleep(0)
        try:
            while self.running and self.client.is_connected:
                if self.operator_process.poll() is not None:
                    logging.error(
                        "operator process exited with code %s",
                        self.operator_process.returncode,
                    )
                    break
                await asyncio.sleep(0.1)
        finally:
            self.running = False
            self.inputs.cleanup()
            for publisher in self.command_publishers:
                publisher.cleanup()
            await self.event_router.stop(drain=True)
            await router_task
            await self._stop_operator()
            self.client.terminate()

    async def _stop_operator(self) -> None:
        """Stop the separate operator process without blocking the event loop."""
        if self.operator_process.poll() is None:
            self.operator_process.terminate()
            try:
                await asyncio.wait_for(
                    asyncio.to_thread(self.operator_process.wait),
                    timeout=OPERATOR_STOP_TIMEOUT,
                )
            except asyncio.TimeoutError:
                logging.warning("operator process did not stop; killing it")
                self.operator_process.kill()
                await asyncio.to_thread(self.operator_process.wait)
        if self.operator_output_thread.is_alive():
            await asyncio.to_thread(self.operator_output_thread.join, 1.0)

    def _forward_operator_output(self) -> None:
        """Prefix output from the separate operation process."""
        if self.operator_process.stdout is None:
            return
        for line in self.operator_process.stdout:
            print(f"[operation] {line.rstrip()}")

    def loop(self) -> None:
        """Run the application until ROS disconnects or Ctrl+C is pressed."""
        try:
            asyncio.run(self._run())
        except KeyboardInterrupt:
            self.running = False
            print("KeyboardInterrupt")
        finally:
            if self.client.is_connected:
                self.client.terminate()
            print("Mimamori shutdown complete")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=ROS_HOST)
    parser.add_argument("--port", type=int, default=ROS_PORT)
    args = parser.parse_args()
    Mimamori(host=args.host, port=args.port).loop()


if __name__ == "__main__":
    main()
