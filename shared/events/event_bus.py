from typing import Callable, Dict, List, Any, Optional
from shared.events.event_types import Event


class EventBus:
    """Lightweight in-memory event bus supporting pub/sub, once, clear, and history."""

    def __init__(self, debug_mode: bool = False, history_limit: int = 1000):
        self._listeners: Dict[str, List[Callable[[Event], None]]] = {}
        self._once_listeners: Dict[str, List[Callable[[Event], None]]] = {}
        self.debug_mode = debug_mode
        self.history_limit = history_limit
        self.event_history: List[Dict[str, Any]] = []

    def subscribe(self, event_name: str, handler: Callable[[Event], None]) -> None:
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        if handler not in self._listeners[event_name]:
            self._listeners[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: Callable[[Event], None]) -> bool:
        removed = False
        if event_name in self._listeners and handler in self._listeners[event_name]:
            self._listeners[event_name].remove(handler)
            removed = True
        if event_name in self._once_listeners and handler in self._once_listeners[event_name]:
            self._once_listeners[event_name].remove(handler)
            removed = True
        return removed

    def once(self, event_name: str, handler: Callable[[Event], None]) -> None:
        if event_name not in self._once_listeners:
            self._once_listeners[event_name] = []
        if handler not in self._once_listeners[event_name]:
            self._once_listeners[event_name].append(handler)

    def publish(self, event_name: str, data: Any = None) -> Event:
        event = data if isinstance(data, Event) else Event(name=event_name, data=data)

        if self.debug_mode:
            self.event_history.append(event.to_dict())
            if len(self.event_history) > self.history_limit:
                self.event_history.pop(0)

        # Notify persistent listeners
        if event_name in self._listeners:
            for handler in list(self._listeners[event_name]):
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error executing listener for {event_name}: {e}")

        # Notify once listeners and clear them
        if event_name in self._once_listeners:
            listeners = list(self._once_listeners[event_name])
            self._once_listeners[event_name].clear()
            for handler in listeners:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error executing once listener for {event_name}: {e}")

        return event

    def clear(self, event_name: Optional[str] = None) -> None:
        if event_name:
            if event_name in self._listeners:
                self._listeners[event_name].clear()
            if event_name in self._once_listeners:
                self._once_listeners[event_name].clear()
        else:
            self._listeners.clear()
            self._once_listeners.clear()
            self.event_history.clear()

    def get_listener_count(self, event_name: str) -> int:
        count = len(self._listeners.get(event_name, []))
        count += len(self._once_listeners.get(event_name, []))
        return count
