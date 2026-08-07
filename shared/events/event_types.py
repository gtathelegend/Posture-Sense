from datetime import datetime
from typing import Any, Dict, Optional
import uuid


class Event:
    """Strongly typed wrapper for Event Bus payload."""

    def __init__(self, name: str, data: Any = None, event_id: Optional[str] = None, timestamp: Optional[str] = None):
        self.event_id = event_id or str(uuid.uuid4())
        self.name = name
        self.data = data
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        data_serialized = self.data.to_dict() if hasattr(self.data, 'to_dict') else self.data
        return {
            "event_id": self.event_id,
            "name": self.name,
            "data": data_serialized,
            "timestamp": self.timestamp
        }
