from typing import List, Dict, Any, Optional
from shared.contracts.base import BaseContract


class ScoreReport(BaseContract):
    def __init__(
        self,
        overall_score: float,
        posture_score: float = 100.0,
        alignment_score: float = 100.0,
        stability_score: float = 100.0,
        category: str = "Excellent",
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "scoring_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.overall_score = overall_score
        self.posture_score = posture_score
        self.alignment_score = alignment_score
        self.stability_score = stability_score
        self.category = category

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "overall_score": self.overall_score,
            "posture_score": self.posture_score,
            "alignment_score": self.alignment_score,
            "stability_score": self.stability_score,
            "category": self.category
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoreReport':
        return cls(
            overall_score=float(data.get("overall_score", 0.0)),
            posture_score=float(data.get("posture_score", 100.0)),
            alignment_score=float(data.get("alignment_score", 100.0)),
            stability_score=float(data.get("stability_score", 100.0)),
            category=data.get("category", "Excellent"),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "scoring_engine")
        )


class FeedbackMessage(BaseContract):
    def __init__(
        self,
        message: str,
        severity: str = "info",
        target_joint: Optional[str] = None,
        correction_angle: Optional[float] = None,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "feedback_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.message = message
        self.severity = severity
        self.target_joint = target_joint
        self.correction_angle = correction_angle

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "message": self.message,
            "severity": self.severity,
            "target_joint": self.target_joint,
            "correction_angle": self.correction_angle
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackMessage':
        return cls(
            message=data.get("message", ""),
            severity=data.get("severity", "info"),
            target_joint=data.get("target_joint"),
            correction_angle=float(data["correction_angle"]) if data.get("correction_angle") is not None else None,
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "feedback_engine")
        )
