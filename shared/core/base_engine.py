from abc import ABC, abstractmethod
from typing import Callable, Any, Optional
from shared.types.enums import EngineStatus
from shared.events.event_bus import EventBus
from shared.events.event_types import Event


class BaseEngine(ABC):
    """Abstract base class for all 12 PostureSense system engines."""

    def __init__(self, name: str, event_bus: Optional[EventBus] = None):
        self.name = name
        self.event_bus = event_bus or EventBus()
        self._status = EngineStatus.UNINITIALIZED

    @abstractmethod
    def initialize(self, config: Optional[dict] = None) -> bool:
        """Initialize engine resources and load configuration."""
        pass

    @abstractmethod
    def start(self) -> bool:
        """Start engine processing loop."""
        pass

    @abstractmethod
    def stop(self) -> bool:
        """Stop engine processing loop."""
        pass

    @abstractmethod
    def dispose(self) -> bool:
        """Release engine resources."""
        pass

    def status(self) -> EngineStatus:
        """Get current engine status."""
        return self._status

    def publish(self, event_name: str, data: Any = None) -> Event:
        """Publish event to the EventBus."""
        return self.event_bus.publish(event_name, data)

    def subscribe(self, event_name: str, handler: Callable[[Event], None]) -> None:
        """Subscribe handler to EventBus event."""
        self.event_bus.subscribe(event_name, handler)
