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
    """
    Movement Engine output contract.
    Published with every `exercise.rep_completed` and `exercise.phase_changed` event.

    NOTE: `movement_quality` is derived from landmark tracking visibility only.
    It is NOT a posture score or coaching evaluation.
    """

    def __init__(
        self,
        exercise_name: str,
        exercise_id: str = "unknown",
        rep_count: int = 0,
        current_phase: str = "idle",
        current_rep_duration: float = 0.0,
        average_rep_duration: float = 0.0,
        current_cadence: float = 0.0,
        rom_percentage: float = 0.0,
        movement_quality: float = 100.0,
        hold_time: float = 0.0,
        tracking_quality: float = 100.0,
        # Backward-compat alias
        form_score: Optional[float] = None,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "movement_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.exercise_name = exercise_name
        self.exercise_id = exercise_id
        self.rep_count = rep_count
        self.current_phase = current_phase
        self.current_rep_duration = current_rep_duration
        self.average_rep_duration = average_rep_duration
        self.current_cadence = current_cadence
        self.rom_percentage = rom_percentage
        # form_score alias maps to movement_quality for backward compatibility
        self.movement_quality = form_score if form_score is not None else movement_quality
        self.hold_time = hold_time
        self.tracking_quality = tracking_quality

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercise_name,
            "current_phase": self.current_phase,
            "rep_count": self.rep_count,
            "current_rep_duration": round(self.current_rep_duration, 2),
            "average_rep_duration": round(self.average_rep_duration, 2),
            "current_cadence": round(self.current_cadence, 1),
            "rom_percentage": round(self.rom_percentage, 1),
            "movement_quality": round(self.movement_quality, 1),
            "hold_time": round(self.hold_time, 2),
            "tracking_quality": round(self.tracking_quality, 1),
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExerciseResult':
        return cls(
            exercise_name=data.get("exercise_name", "unknown_exercise"),
            exercise_id=data.get("exercise_id", "unknown"),
            rep_count=int(data.get("rep_count", 0)),
            current_phase=data.get("current_phase", "idle"),
            current_rep_duration=float(data.get("current_rep_duration", 0.0)),
            average_rep_duration=float(data.get("average_rep_duration", 0.0)),
            current_cadence=float(data.get("current_cadence", 0.0)),
            rom_percentage=float(data.get("rom_percentage", 0.0)),
            movement_quality=float(data.get("movement_quality", data.get("form_score", 100.0))),
            hold_time=float(data.get("hold_time", 0.0)),
            tracking_quality=float(data.get("tracking_quality", 100.0)),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "movement_engine")
        )
