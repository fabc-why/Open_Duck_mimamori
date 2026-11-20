"""Asyncio event router."""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from concurrent.futures import Future
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from .event import Event
from .event_types import match_event_type, validate_subscription_pattern
from .exceptions import EventRouterShutdownTimeout, EventRouterStopped, InvalidEventType


EventHandler = Callable[[Event], None | Awaitable[None]]
EventFilter = Callable[[Event], bool]


class RouterState(Enum):
    """Lifecycle state of an event router."""

    CREATED = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()


_SENTINEL = object()


@dataclass(frozen=True, slots=True)
class Subscription:
    """A named event subscription."""

    pattern: str
    handler: EventHandler
    name: str
    event_filter: EventFilter | None = None

    def __post_init__(self) -> None:
        validate_subscription_pattern(self.pattern)
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("subscription name must not be empty")


class EventRouter:
    """Queue-based, sequential Event delivery."""

    def __init__(self, deduplication_capacity: int = 10_000) -> None:
        if (
            isinstance(deduplication_capacity, bool)
            or not isinstance(deduplication_capacity, int)
            or deduplication_capacity < 1
        ):
            raise ValueError("deduplication_capacity must be at least 1")
        self.state = RouterState.CREATED
        self._queue: asyncio.Queue[Event | object] = asyncio.Queue()
        self._subscriptions: list[Subscription] = []
        self._subscription_names: set[str] = set()
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._deduplication_capacity = deduplication_capacity
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_task: asyncio.Task[None] | None = None
        self._shutdown_waiter: asyncio.Future[None] | None = None

    def subscribe(
        self,
        pattern: str,
        handler: EventHandler,
        *,
        name: str,
        event_filter: EventFilter | None = None,
    ) -> None:
        """Register a subscription; names must be unique."""
        if self.state in (RouterState.STOPPING, RouterState.STOPPED):
            raise EventRouterStopped("cannot subscribe while the router is stopping or stopped")
        subscription = Subscription(pattern, handler, name.strip(), event_filter)
        if subscription.name in self._subscription_names:
            raise ValueError(f"subscription name already registered: {subscription.name}")
        self._subscription_names.add(subscription.name)
        self._subscriptions.append(subscription)

    def unsubscribe(self, name: str) -> bool:
        """Unregister a subscription by name."""
        if name not in self._subscription_names:
            return False
        self._subscription_names.remove(name)
        for index, subscription in enumerate(self._subscriptions):
            if subscription.name == name:
                del self._subscriptions[index]
                return True
        return False

    def _mark_seen(self, event_id: str) -> bool:
        if event_id in self._seen:
            return False
        self._seen[event_id] = None
        if len(self._seen) > self._deduplication_capacity:
            self._seen.popitem(last=False)
        return True

    async def publish(self, event: Event) -> bool:
        """Queue an Event unless it was already published."""
        if self.state in (RouterState.STOPPING, RouterState.STOPPED):
            raise EventRouterStopped("event publishing is stopped")
        if not isinstance(event, Event):
            raise TypeError("event must be an Event")
        if not self._mark_seen(event.event_id):
            return False
        await self._queue.put(event)
        return True

    async def run(self) -> None:
        """Run the event delivery loop."""
        if self.state is not RouterState.CREATED:
            raise RuntimeError("EventRouter.run() may only be started once")

        self.state = RouterState.RUNNING
        self._loop = asyncio.get_running_loop()
        self._loop_task = asyncio.current_task()
        try:
            while True:
                item = await self._queue.get()
                try:
                    if item is _SENTINEL:
                        return
                    await self._process_event(item)
                finally:
                    self._queue.task_done()
        finally:
            if self.state is RouterState.STOPPING:
                self.state = RouterState.STOPPED
            elif self.state is RouterState.RUNNING:
                self.state = RouterState.STOPPED

    async def wait_until_idle(self) -> None:
        """Wait until all currently queued Events are processed."""
        await self._queue.join()

    def publish_threadsafe(self, event: Event) -> Future[bool]:
        """Publish an Event from a thread outside the Router loop."""
        if self.state is not RouterState.RUNNING:
            raise EventRouterStopped("EventRouter is not running")
        if self._loop is None:
            raise EventRouterStopped("EventRouter loop is unavailable")
        return asyncio.run_coroutine_threadsafe(self.publish(event), self._loop)

    def _is_error_subscription(self, subscription: Subscription) -> bool:
        try:
            return match_event_type(subscription.pattern, "system.component.failed")
        except InvalidEventType:
            return False

    async def _process_event(self, event: Event) -> None:
        for subscription in tuple(self._subscriptions):
            if not match_event_type(subscription.pattern, event.event_type):
                continue
            try:
                if subscription.event_filter is not None:
                    if not subscription.event_filter(event):
                        continue
            except Exception as exc:
                logging.exception(
                    "event filter failed",
                    extra={
                        "subscription_name": subscription.name,
                        "original_event_id": event.event_id,
                    },
                )
                await self._emit_error(
                    subscription,
                    event,
                    "filter",
                    exc,
                )
                continue

            try:
                result = subscription.handler(event)
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:
                logging.exception(
                    "event handler failed",
                    extra={
                        "subscription_name": subscription.name,
                        "original_event_id": event.event_id,
                    },
                )
                await self._emit_error(
                    subscription,
                    event,
                    "handler",
                    exc,
                )

    async def _emit_error(
        self,
        subscription: Subscription,
        original_event: Event,
        component_type: str,
        exc: Exception,
    ) -> None:
        if (
            original_event.event_type == "system.component.failed"
            or self._is_error_subscription(subscription)
            or self.state is RouterState.STOPPING
        ):
            return
        try:
            error_event = Event.create(
                event_type="system.component.failed",
                source="event_router",
                data={
                    "component_type": component_type,
                    "subscription_name": subscription.name,
                    "original_event_id": original_event.event_id,
                    "original_event_type": original_event.event_type,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
                correlation_id=original_event.correlation_id,
                causation_id=original_event.event_id,
            )
            await self.publish(error_event)
        except Exception:
            logging.exception("failed to create or queue an error Event")

    async def stop(
        self,
        *,
        drain: bool = True,
        timeout: float | None = 5.0,
    ) -> None:
        """Stop the Router, optionally draining queued Events."""
        if timeout is not None and timeout < 0:
            raise ValueError("timeout must be non-negative or None")

        if self.state is RouterState.STOPPED:
            return

        if self.state is RouterState.STOPPING:
            if self._shutdown_waiter is not None:
                await asyncio.shield(self._shutdown_waiter)
            return

        if self.state is RouterState.CREATED:
            self.state = RouterState.STOPPING
            while True:
                try:
                    item = self._queue.get_nowait()
                    self._queue.task_done()
                    if item is _SENTINEL:
                        continue
                    if not drain:
                        continue
                    await self._process_event(item)
                except asyncio.QueueEmpty:
                    break
            self.state = RouterState.STOPPED
            return

        self.state = RouterState.STOPPING
        loop = asyncio.get_running_loop()
        waiter = loop.create_future()
        self._shutdown_waiter = waiter

        if not drain:
            while True:
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except asyncio.QueueEmpty:
                    break

        await self._queue.put(_SENTINEL)

        try:
            if timeout is None:
                await asyncio.shield(self._loop_task)
            else:
                await asyncio.wait_for(
                    asyncio.shield(self._loop_task),
                    timeout=timeout,
                )
        except asyncio.TimeoutError as exc:
            if self._loop_task is not None:
                self._loop_task.cancel()
                try:
                    await self._loop_task
                except asyncio.CancelledError:
                    pass
            self.state = RouterState.STOPPED
            waiter.set_result(None)
            raise EventRouterShutdownTimeout(
                f"EventRouter shutdown timed out after {timeout} seconds"
            ) from exc
        finally:
            if not waiter.done():
                waiter.set_result(None)

        self.state = RouterState.STOPPED
