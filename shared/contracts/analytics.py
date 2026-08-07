from typing import Dict, Any, Optional
from shared.contracts.base import BaseContract


class AnalyticsSnapshot(BaseContract):
    def __init__(
        self,
        session_id: str,
        current_score: float,
        frame_rate: float = 30.0,
        elapsed_seconds: float = 0.0,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "analytics_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.session_id = session_id
        self.current_score = current_score
        self.frame_rate = frame_rate
        self.elapsed_seconds = elapsed_seconds

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "session_id": self.session_id,
            "current_score": self.current_score,
            "frame_rate": self.frame_rate,
            "elapsed_seconds": self.elapsed_seconds
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyticsSnapshot':
        return cls(
            session_id=data.get("session_id", ""),
            current_score=float(data.get("current_score", 0.0)),
            frame_rate=float(data.get("frame_rate", 30.0)),
            elapsed_seconds=float(data.get("elapsed_seconds", 0.0)),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "analytics_engine")
        )


class SessionSummary(BaseContract):
    def __init__(
        self,
        session_id: str,
        user_id: str,
        pose_label: str,
        duration: float,
        avg_accuracy: float,
        total_reps: int = 0,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "persistence_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.session_id = session_id
        self.user_id = user_id
        self.pose_label = pose_label
        self.duration = duration
        self.avg_accuracy = avg_accuracy
        self.total_reps = total_reps

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "session_id": self.session_id,
            "user_id": self.user_id,
            "pose_label": self.pose_label,
            "duration": self.duration,
            "avg_accuracy": self.avg_accuracy,
            "total_reps": self.total_reps
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionSummary':
        return cls(
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            pose_label=data.get("pose_label", "Unknown Pose"),
            duration=float(data.get("duration", 0.0)),
            avg_accuracy=float(data.get("avg_accuracy", 0.0)),
            total_reps=int(data.get("total_reps", 0)),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "persistence_engine")
        )
