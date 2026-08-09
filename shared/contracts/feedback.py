from typing import List, Dict, Any, Optional
from shared.contracts.base import BaseContract


class FeedbackResult(BaseContract):
    """
    Feedback Engine output contract.
    Published whenever actionable, evidence-based feedback is generated.
    """

    def __init__(
        self,
        category: str,
        type: str = "correction",  # positive, correction, warning, achievement
        severity: str = "medium",  # critical, high, medium, low, info
        message: str = "",
        evidence: Optional[Dict[str, Any]] = None,
        metric_source: str = "unknown",
        confidence: float = 1.0,
        exercise_id: str = "unknown",
        pose_id: Optional[str] = None,
        rule_triggered: str = "default_rule",
        template_key: str = "feedback.generic",
        variables: Optional[Dict[str, Any]] = None,
        feedback_id: Optional[str] = None,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "feedback_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.feedback_id = feedback_id or self.id
        self.category = category
        self.type = type
        self.severity = severity
        self.message = message
        self.evidence = evidence or {}
        self.metric_source = metric_source
        self.confidence = float(confidence)
        self.exercise_id = exercise_id
        self.pose_id = pose_id
        self.rule_triggered = rule_triggered
        self.template_key = template_key
        self.variables = variables or {}

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "feedback_id": self.feedback_id,
            "category": self.category,
            "type": self.type,
            "severity": self.severity,
            "message": self.message,
            "evidence": self.evidence,
            "metric_source": self.metric_source,
            "confidence": round(self.confidence, 2),
            "exercise_id": self.exercise_id,
            "pose_id": self.pose_id,
            "rule_triggered": self.rule_triggered,
            "template_key": self.template_key,
            "variables": self.variables,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackResult':
        return cls(
            category=data.get("category", "Form"),
            type=data.get("type", "correction"),
            severity=data.get("severity", "medium"),
            message=data.get("message", ""),
            evidence=data.get("evidence"),
            metric_source=data.get("metric_source", "unknown"),
            confidence=float(data.get("confidence", 1.0)),
            exercise_id=data.get("exercise_id", "unknown"),
            pose_id=data.get("pose_id"),
            rule_triggered=data.get("rule_triggered", "default_rule"),
            template_key=data.get("template_key", "feedback.generic"),
            variables=data.get("variables"),
            feedback_id=data.get("feedback_id"),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "feedback_engine")
        )


class FeedbackSessionSummary(BaseContract):
    """
    Session-level aggregate feedback summary.
    Published at session completion.
    """

    def __init__(
        self,
        session_id: str,
        exercise_id: str,
        strengths: Optional[List[str]] = None,
        weak_areas: Optional[List[str]] = None,
        common_mistakes: Optional[List[str]] = None,
        improvement_areas: Optional[List[str]] = None,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "feedback_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.session_id = session_id
        self.exercise_id = exercise_id
        self.strengths = strengths or []
        self.weak_areas = weak_areas or []
        self.common_mistakes = common_mistakes or []
        self.improvement_areas = improvement_areas or []

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "session_id": self.session_id,
            "exercise_id": self.exercise_id,
            "strengths": self.strengths,
            "weak_areas": self.weak_areas,
            "common_mistakes": self.common_mistakes,
            "improvement_areas": self.improvement_areas,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackSessionSummary':
        return cls(
            session_id=data.get("session_id", ""),
            exercise_id=data.get("exercise_id", "unknown"),
            strengths=data.get("strengths"),
            weak_areas=data.get("weak_areas"),
            common_mistakes=data.get("common_mistakes"),
            improvement_areas=data.get("improvement_areas"),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "feedback_engine")
        )
