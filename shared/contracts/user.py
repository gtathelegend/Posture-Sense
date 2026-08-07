from typing import Dict, Any, Optional
from shared.contracts.base import BaseContract


class UserProfile(BaseContract):
    def __init__(
        self,
        user_id: str,
        username: str,
        email: str,
        preferred_mode: str = "exercise",
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "user_input"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.user_id = user_id
        self.username = username
        self.email = email
        self.preferred_mode = preferred_mode

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "preferred_mode": self.preferred_mode
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        return cls(
            user_id=data.get("user_id", ""),
            username=data.get("username", ""),
            email=data.get("email", ""),
            preferred_mode=data.get("preferred_mode", "exercise"),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "user_input")
        )
