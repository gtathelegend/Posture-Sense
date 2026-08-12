"""
CompletedSessionContract
========================
Shared contract for finalizing completed pose/exercise session summaries.
Inherits from BaseContract for standardized JSON schema serialization.
Only includes fields genuinely produced by perception engines; uses None/null for unavailable metrics.
"""

from typing import Dict, Any, List, Optional
from shared.contracts.base import BaseContract


class CompletedSessionContract(BaseContract):
    def __init__(
        self,
        session_id: str,
        user_id: str,
        pose_id: str = "unknown",
        pose_name: str = "Unknown Pose",
        exercise_id: str = "unknown",
        exercise_name: str = "Unknown Exercise",
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        duration: float = 0.0,
        overall_score: float = 0.0,
        score_confidence: float = 1.0,
        score_category: str = "Needs Improvement",
        symmetry_score: Optional[float] = None,
        balance_score: Optional[float] = None,
        stability_score: Optional[float] = None,
        rom_score: Optional[float] = None,
        reps: int = 0,
        hold_time: float = 0.0,
        rom_percentage: Optional[float] = None,
        average_rep_duration: float = 0.0,
        average_cadence: float = 0.0,
        movement_quality: float = 100.0,
        tracking_quality: Optional[float] = None,
        quality_gate_passed: bool = True,
        failed_rules: Optional[List[Any]] = None,
        strengths: Optional[List[str]] = None,
        weak_areas: Optional[List[str]] = None,
        common_mistakes: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "session_controller"
    ):
        super().__init__(id=id or session_id, timestamp=timestamp or completed_at, schema_version=schema_version, source=source)
        self.session_id = session_id
        self.user_id = str(user_id)
        self.pose_id = pose_id
        self.pose_name = pose_name
        self.exercise_id = exercise_id
        self.exercise_name = exercise_name
        self.started_at = started_at or self.timestamp
        self.completed_at = completed_at or self.timestamp
        self.duration = float(duration)

        self.performance = {
            "overall_score": round(float(overall_score), 1),
            "score_confidence": float(score_confidence),
            "score_category": score_category
        }

        self.biomechanics = {
            "symmetry_score": round(float(symmetry_score), 1) if symmetry_score is not None else None,
            "balance_score": round(float(balance_score), 1) if balance_score is not None else None,
            "stability_score": round(float(stability_score), 1) if stability_score is not None else None,
            "rom_score": round(float(rom_score), 1) if rom_score is not None else None
        }

        self.movement = {
            "reps": int(reps),
            "hold_time": round(float(hold_time), 1),
            "rom_percentage": round(float(rom_percentage), 1) if rom_percentage is not None else None,
            "average_rep_duration": round(float(average_rep_duration), 1),
            "average_cadence": round(float(average_cadence), 1),
            "movement_quality": round(float(movement_quality), 1)
        }

        self.quality = {
            "tracking_quality": round(float(tracking_quality), 1) if tracking_quality is not None else None,
            "quality_gate_passed": bool(quality_gate_passed)
        }

        self.pose_rules = {
            "failed_rules": failed_rules if isinstance(failed_rules, list) else []
        }

        self.feedback = {
            "strengths": strengths or [],
            "weak_areas": weak_areas or [],
            "common_mistakes": common_mistakes or []
        }

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "session_id": self.session_id,
            "user_id": self.user_id,
            "pose_id": self.pose_id,
            "pose_name": self.pose_name,
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercise_name,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration": round(self.duration, 1),
            "performance": self.performance,
            "biomechanics": self.biomechanics,
            "movement": self.movement,
            "quality": self.quality,
            "pose_rules": self.pose_rules,
            "feedback": self.feedback
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompletedSessionContract':
        perf = data.get("performance", {})
        bio = data.get("biomechanics", {})
        mov = data.get("movement", {})
        qual = data.get("quality", {})
        prules = data.get("pose_rules", {})
        fb = data.get("feedback", {})

        return cls(
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            pose_id=data.get("pose_id", "unknown"),
            pose_name=data.get("pose_name", "Unknown Pose"),
            exercise_id=data.get("exercise_id", "unknown"),
            exercise_name=data.get("exercise_name", "Unknown Exercise"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            duration=data.get("duration", 0.0),
            overall_score=perf.get("overall_score", 0.0),
            score_confidence=perf.get("score_confidence", 1.0),
            score_category=perf.get("score_category", "Needs Improvement"),
            symmetry_score=bio.get("symmetry_score"),
            balance_score=bio.get("balance_score"),
            stability_score=bio.get("stability_score"),
            rom_score=bio.get("rom_score"),
            reps=mov.get("reps", 0),
            hold_time=mov.get("hold_time", 0.0),
            rom_percentage=mov.get("rom_percentage"),
            average_rep_duration=mov.get("average_rep_duration", 0.0),
            average_cadence=mov.get("average_cadence", 0.0),
            movement_quality=mov.get("movement_quality", 100.0),
            tracking_quality=qual.get("tracking_quality"),
            quality_gate_passed=qual.get("quality_gate_passed", True),
            failed_rules=prules.get("failed_rules", []),
            strengths=fb.get("strengths", []),
            weak_areas=fb.get("weak_areas", []),
            common_mistakes=fb.get("common_mistakes", []),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "session_controller")
        )
