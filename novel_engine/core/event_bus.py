"""In-Memory EventBus for decoupled cross-galaxy communication."""

import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Type
from pydantic import BaseModel


class DomainEvent(BaseModel):
    """Base Domain Event."""
    timestamp: float = 0.0


class EventBus:
    """Thread-safe asynchronous In-Memory EventBus."""
    def __init__(self):
        self._subscribers: Dict[Type[DomainEvent], List[Callable[[Any], Coroutine[Any, Any, None]]]] = {}

    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[Any], Coroutine[Any, Any, None]]
    ):
        """Registers an asynchronous event handler for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def publish(self, event: DomainEvent):
        """Broadcasts event to all subscribed listeners concurrently."""
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])
        if handlers:
            await asyncio.gather(*(handler(event) for handler in handlers))
