from typing import List, Dict, Any, Optional
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


class SessionAnalytics(BaseContract):
    """Detailed analytics record for a single completed session."""

    def __init__(
        self,
        session_id: str,
        user_id: str = "anonymous",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        duration: float = 0.0,
        exercise_id: str = "unknown",
        completed_reps: int = 0,
        valid_reps: int = 0,
        invalid_reps: int = 0,
        average_score: float = 0.0,
        best_score: float = 0.0,
        worst_score: float = 0.0,
        consistency: float = 100.0,
        tracking_quality: float = 100.0,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "analytics_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.session_id = session_id
        self.user_id = user_id
        self.start_time = start_time or self.timestamp
        self.end_time = end_time or self.timestamp
        self.duration = float(duration)
        self.exercise_id = exercise_id
        self.completed_reps = int(completed_reps)
        self.valid_reps = int(valid_reps)
        self.invalid_reps = int(invalid_reps)
        self.average_score = float(average_score)
        self.best_score = float(best_score)
        self.worst_score = float(worst_score)
        self.consistency = float(consistency)
        self.tracking_quality = float(tracking_quality)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "session_id": self.session_id,
            "user_id": self.user_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": round(self.duration, 1),
            "exercise_id": self.exercise_id,
            "completed_reps": self.completed_reps,
            "valid_reps": self.valid_reps,
            "invalid_reps": self.invalid_reps,
            "average_score": round(self.average_score, 1),
            "best_score": round(self.best_score, 1),
            "worst_score": round(self.worst_score, 1),
            "consistency": round(self.consistency, 1),
            "tracking_quality": round(self.tracking_quality, 1),
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionAnalytics':
        return cls(
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", "anonymous"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            duration=float(data.get("duration", 0.0)),
            exercise_id=data.get("exercise_id", "unknown"),
            completed_reps=int(data.get("completed_reps", 0)),
            valid_reps=int(data.get("valid_reps", 0)),
            invalid_reps=int(data.get("invalid_reps", 0)),
            average_score=float(data.get("average_score", 0.0)),
            best_score=float(data.get("best_score", 0.0)),
            worst_score=float(data.get("worst_score", 0.0)),
            consistency=float(data.get("consistency", 100.0)),
            tracking_quality=float(data.get("tracking_quality", 100.0)),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "analytics_engine")
        )


class ExerciseAnalytics(BaseContract):
    """Historical analytics record per exercise."""

    def __init__(
        self,
        exercise_id: str,
        total_sessions: int = 0,
        total_repetitions: int = 0,
        best_score: float = 0.0,
        average_score: float = 0.0,
        best_rom: float = 0.0,
        average_rom: float = 0.0,
        best_cadence: float = 0.0,
        average_cadence: float = 0.0,
        average_stability: float = 0.0,
        average_symmetry: float = 0.0,
        average_form: float = 0.0,
        last_performed: Optional[str] = None,
        improvement_percentage: float = 0.0,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "analytics_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.exercise_id = exercise_id
        self.total_sessions = int(total_sessions)
        self.total_repetitions = int(total_repetitions)
        self.best_score = float(best_score)
        self.average_score = float(average_score)
        self.best_rom = float(best_rom)
        self.average_rom = float(average_rom)
        self.best_cadence = float(best_cadence)
        self.average_cadence = float(average_cadence)
        self.average_stability = float(average_stability)
        self.average_symmetry = float(average_symmetry)
        self.average_form = float(average_form)
        self.last_performed = last_performed or self.timestamp
        self.improvement_percentage = float(improvement_percentage)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "exercise_id": self.exercise_id,
            "total_sessions": self.total_sessions,
            "total_repetitions": self.total_repetitions,
            "best_score": round(self.best_score, 1),
            "average_score": round(self.average_score, 1),
            "best_rom": round(self.best_rom, 1),
            "average_rom": round(self.average_rom, 1),
            "best_cadence": round(self.best_cadence, 1),
            "average_cadence": round(self.average_cadence, 1),
            "average_stability": round(self.average_stability, 1),
            "average_symmetry": round(self.average_symmetry, 1),
            "average_form": round(self.average_form, 1),
            "last_performed": self.last_performed,
            "improvement_percentage": round(self.improvement_percentage, 1),
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExerciseAnalytics':
        return cls(
            exercise_id=data.get("exercise_id", "unknown"),
            total_sessions=int(data.get("total_sessions", 0)),
            total_repetitions=int(data.get("total_repetitions", 0)),
            best_score=float(data.get("best_score", 0.0)),
            average_score=float(data.get("average_score", 0.0)),
            best_rom=float(data.get("best_rom", 0.0)),
            average_rom=float(data.get("average_rom", 0.0)),
            best_cadence=float(data.get("best_cadence", 0.0)),
            average_cadence=float(data.get("average_cadence", 0.0)),
            average_stability=float(data.get("average_stability", 0.0)),
            average_symmetry=float(data.get("average_symmetry", 0.0)),
            average_form=float(data.get("average_form", 0.0)),
            last_performed=data.get("last_performed"),
            improvement_percentage=float(data.get("improvement_percentage", 0.0)),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "analytics_engine")
        )


class TrendMetric(BaseContract):
    """Statistical trend evaluation for a specific performance metric."""

    def __init__(
        self,
        metric_name: str,
        timeframe: str = "session",  # daily, weekly, monthly, session
        trend_direction: str = "INSUFFICIENT_DATA",  # IMPROVING, STABLE, DECLINING, INSUFFICIENT_DATA
        observation_count: int = 0,
        slope: float = 0.0,
        percentage_change: float = 0.0,
        sample_values: Optional[List[float]] = None,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "analytics_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.metric_name = metric_name
        self.timeframe = timeframe
        self.trend_direction = trend_direction
        self.observation_count = int(observation_count)
        self.slope = float(slope)
        self.percentage_change = float(percentage_change)
        self.sample_values = sample_values or []

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "metric_name": self.metric_name,
            "timeframe": self.timeframe,
            "trend_direction": self.trend_direction,
            "observation_count": self.observation_count,
            "slope": round(self.slope, 4),
            "percentage_change": round(self.percentage_change, 2),
            "sample_values": [round(v, 1) for v in self.sample_values],
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrendMetric':
        return cls(
            metric_name=data.get("metric_name", "overall_score"),
            timeframe=data.get("timeframe", "session"),
            trend_direction=data.get("trend_direction", "INSUFFICIENT_DATA"),
            observation_count=int(data.get("observation_count", 0)),
            slope=float(data.get("slope", 0.0)),
            percentage_change=float(data.get("percentage_change", 0.0)),
            sample_values=data.get("sample_values"),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "analytics_engine")
        )


class PersonalRecord(BaseContract):
    """Personal record achievement payload."""

    def __init__(
        self,
        record_type: str,  # Highest Score, Best ROM, Best Stability, Best Symmetry, Longest Hold, Most Reps, Best Consistency
        exercise_id: str,
        value: float,
        unit: str = "points",
        achieved_at: Optional[str] = None,
        previous_value: Optional[float] = None,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "analytics_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.record_type = record_type
        self.exercise_id = exercise_id
        self.value = float(value)
        self.unit = unit
        self.achieved_at = achieved_at or self.timestamp
        self.previous_value = float(previous_value) if previous_value is not None else None

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "record_type": self.record_type,
            "exercise_id": self.exercise_id,
            "value": round(self.value, 1),
            "unit": self.unit,
            "achieved_at": self.achieved_at,
            "previous_value": round(self.previous_value, 1) if self.previous_value is not None else None,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonalRecord':
        return cls(
            record_type=data.get("record_type", "Highest Score"),
            exercise_id=data.get("exercise_id", "unknown"),
            value=float(data.get("value", 0.0)),
            unit=data.get("unit", "points"),
            achieved_at=data.get("achieved_at"),
            previous_value=float(data["previous_value"]) if data.get("previous_value") is not None else None,
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "analytics_engine")
        )


class AnalyticsSummary(BaseContract):
    """Aggregate analytics summary payload for user progress dashboard."""

    def __init__(
        self,
        user_id: str = "anonymous",
        total_sessions: int = 0,
        total_duration: float = 0.0,
        overall_average_score: float = 0.0,
        streak_days: int = 0,
        recent_sessions: Optional[List[Dict[str, Any]]] = None,
        exercise_history: Optional[Dict[str, Dict[str, Any]]] = None,
        active_trends: Optional[Dict[str, Dict[str, Any]]] = None,
        personal_records: Optional[List[Dict[str, Any]]] = None,
        comparison: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "analytics_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.user_id = user_id
        self.total_sessions = int(total_sessions)
        self.total_duration = float(total_duration)
        self.overall_average_score = float(overall_average_score)
        self.streak_days = int(streak_days)
        self.recent_sessions = recent_sessions or []
        self.exercise_history = exercise_history or {}
        self.active_trends = active_trends or {}
        self.personal_records = personal_records or []
        self.comparison = comparison or {}

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "user_id": self.user_id,
            "total_sessions": self.total_sessions,
            "total_duration": round(self.total_duration, 1),
            "overall_average_score": round(self.overall_average_score, 1),
            "streak_days": self.streak_days,
            "recent_sessions": self.recent_sessions,
            "exercise_history": self.exercise_history,
            "active_trends": self.active_trends,
            "personal_records": self.personal_records,
            "comparison": self.comparison,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyticsSummary':
        return cls(
            user_id=data.get("user_id", "anonymous"),
            total_sessions=int(data.get("total_sessions", 0)),
            total_duration=float(data.get("total_duration", 0.0)),
            overall_average_score=float(data.get("overall_average_score", 0.0)),
            streak_days=int(data.get("streak_days", 0)),
            recent_sessions=data.get("recent_sessions"),
            exercise_history=data.get("exercise_history"),
            active_trends=data.get("active_trends"),
            personal_records=data.get("personal_records"),
            comparison=data.get("comparison"),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "analytics_engine")
        )
