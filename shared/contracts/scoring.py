from typing import List, Dict, Any, Optional
from shared.contracts.base import BaseContract


class ScoreReport(BaseContract):
    def __init__(
        self,
        overall_score: float,
        score_confidence: float = 1.0,
        category: str = "Excellent",
        components: Optional[Dict[str, Any]] = None,
        exercise_id: str = "unknown",
        exercise_name: str = "Unknown",
        rep_scores: Optional[List[Dict[str, Any]]] = None,
        hold_score: Optional[Dict[str, Any]] = None,
        session_summary: Optional[Dict[str, Any]] = None,
        missing_metrics: Optional[List[str]] = None,
        quality_gate_passed: bool = True,
        quality_warning: Optional[str] = None,
        # Backward-compatibility parameters
        posture_score: Optional[float] = None,
        alignment_score: Optional[float] = None,
        stability_score: Optional[float] = None,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "scoring_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.overall_score = float(overall_score)
        self.score_confidence = float(score_confidence)
        self.category = category
        self.components = components or {}
        self.exercise_id = exercise_id
        self.exercise_name = exercise_name
        self.rep_scores = rep_scores or []
        self.hold_score = hold_score
        self.session_summary = session_summary
        self.missing_metrics = missing_metrics or []
        self.quality_gate_passed = quality_gate_passed
        self.quality_warning = quality_warning

        # Backward compatibility field mapping
        if posture_score is not None:
            self.posture_score = float(posture_score)
        else:
            form_val = self.components.get("form", {}).get("score") if isinstance(self.components, dict) else None
            self.posture_score = float(form_val) if form_val is not None else self.overall_score

        if alignment_score is not None:
            self.alignment_score = float(alignment_score)
        else:
            symm_val = self.components.get("symmetry", {}).get("score") if isinstance(self.components, dict) else None
            self.alignment_score = float(symm_val) if symm_val is not None else self.overall_score

        if stability_score is not None:
            self.stability_score = float(stability_score)
        else:
            stab_val = self.components.get("stability", {}).get("score") if isinstance(self.components, dict) else None
            self.stability_score = float(stab_val) if stab_val is not None else self.overall_score

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "overall_score": round(self.overall_score, 1),
            "score_confidence": round(self.score_confidence, 2),
            "category": self.category,
            "components": self.components,
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercise_name,
            "rep_scores": self.rep_scores,
            "hold_score": self.hold_score,
            "session_summary": self.session_summary,
            "missing_metrics": self.missing_metrics,
            "quality_gate_passed": self.quality_gate_passed,
            "quality_warning": self.quality_warning,
            # Backward-compat fields
            "posture_score": round(self.posture_score, 1) if self.posture_score is not None else round(self.overall_score, 1),
            "alignment_score": round(self.alignment_score, 1) if self.alignment_score is not None else round(self.overall_score, 1),
            "stability_score": round(self.stability_score, 1) if self.stability_score is not None else round(self.overall_score, 1),
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScoreReport':
        return cls(
            overall_score=float(data.get("overall_score", 0.0)),
            score_confidence=float(data.get("score_confidence", 1.0)),
            category=data.get("category", "Excellent"),
            components=data.get("components"),
            exercise_id=data.get("exercise_id", "unknown"),
            exercise_name=data.get("exercise_name", "Unknown"),
            rep_scores=data.get("rep_scores"),
            hold_score=data.get("hold_score"),
            session_summary=data.get("session_summary"),
            missing_metrics=data.get("missing_metrics"),
            quality_gate_passed=bool(data.get("quality_gate_passed", True)),
            quality_warning=data.get("quality_warning"),
            posture_score=float(data["posture_score"]) if data.get("posture_score") is not None else None,
            alignment_score=float(data["alignment_score"]) if data.get("alignment_score") is not None else None,
            stability_score=float(data["stability_score"]) if data.get("stability_score") is not None else None,
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
