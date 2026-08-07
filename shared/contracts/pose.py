from typing import Dict, Any, Optional
from shared.contracts.base import BaseContract


class PoseResult(BaseContract):
    def __init__(
        self,
        pose_name: str,
        confidence: float = 1.0,
        is_recognized: bool = True,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "pose_rule_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.pose_name = pose_name
        self.confidence = confidence
        self.is_recognized = is_recognized

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "pose_name": self.pose_name,
            "confidence": self.confidence,
            "is_recognized": self.is_recognized
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PoseResult':
        return cls(
            pose_name=data.get("pose_name", "Unknown Pose"),
            confidence=float(data.get("confidence", 1.0)),
            is_recognized=bool(data.get("is_recognized", True)),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "pose_rule_engine")
        )


class ExerciseResult(BaseContract):
    def __init__(
        self,
        exercise_name: str,
        rep_count: int = 0,
        current_phase: str = "idle",
        form_score: float = 100.0,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "movement_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.exercise_name = exercise_name
        self.rep_count = rep_count
        self.current_phase = current_phase
        self.form_score = form_score

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "exercise_name": self.exercise_name,
            "rep_count": self.rep_count,
            "current_phase": self.current_phase,
            "form_score": self.form_score
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExerciseResult':
        return cls(
            exercise_name=data.get("exercise_name", "unknown_exercise"),
            rep_count=int(data.get("rep_count", 0)),
            current_phase=data.get("current_phase", "idle"),
            form_score=float(data.get("form_score", 100.0)),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "movement_engine")
        )
