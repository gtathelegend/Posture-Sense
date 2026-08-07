import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from shared.constants.scores import SCHEMA_VERSION_V2


class BaseContract:
    """Base class for all PostureSense data contracts."""

    def __init__(
        self,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = SCHEMA_VERSION_V2,
        source: str = "system"
    ):
        self.id = id or str(uuid.uuid4())
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.schema_version = schema_version
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "schema_version": self.schema_version,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        raise NotImplementedError("Subclasses must implement from_dict.")
