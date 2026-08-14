"""
shared/contracts/report.py
==========================
Data contracts for PostureSense v2 Reports & Export Subsystem.
Canonical schemas for Session, Exercise, Progress, Comprehensive reports and ExportResult payloads.
"""

from typing import List, Dict, Any, Optional
from shared.contracts.base import BaseContract


class ReportMetadata(BaseContract):
    """Metadata container for all generated PostureSense reports."""

    def __init__(
        self,
        report_type: str,  # session, exercise, progress, comprehensive
        user_id: str = "anonymous",
        generated_at: Optional[str] = None,
        source_data_version: str = "2.0.0",
        application_version: str = "2.0.0",
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "report_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.report_type = report_type
        self.user_id = user_id
        self.generated_at = generated_at or self.timestamp
        self.source_data_version = source_data_version
        self.application_version = application_version

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "report_type": self.report_type,
            "user_id": self.user_id,
            "generated_at": self.generated_at,
            "source_data_version": self.source_data_version,
            "application_version": self.application_version,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReportMetadata':
        return cls(
            report_type=data.get("report_type", "session"),
            user_id=data.get("user_id", "anonymous"),
            generated_at=data.get("generated_at"),
            source_data_version=data.get("source_data_version", "2.0.0"),
            application_version=data.get("application_version", "2.0.0"),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "report_engine")
        )


class SessionReport(BaseContract):
    """Single-session evaluation report contract."""

    def __init__(
        self,
        metadata: ReportMetadata,
        session_info: Dict[str, Any],
        performance: Dict[str, Any],
        movement: Dict[str, Any],
        biomechanics: Dict[str, Any],
        tracking: Dict[str, Any],
        pose_rules: Dict[str, Any],
        feedback: Dict[str, Any],
        data_quality: Dict[str, Any],
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "report_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.metadata = metadata
        self.session_info = session_info
        self.performance = performance
        self.movement = movement
        self.biomechanics = biomechanics
        self.tracking = tracking
        self.pose_rules = pose_rules
        self.feedback = feedback
        self.data_quality = data_quality

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "metadata": self.metadata.to_dict() if isinstance(self.metadata, ReportMetadata) else self.metadata,
            "session_info": self.session_info,
            "performance": self.performance,
            "movement": self.movement,
            "biomechanics": self.biomechanics,
            "tracking": self.tracking,
            "pose_rules": self.pose_rules,
            "feedback": self.feedback,
            "data_quality": self.data_quality,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionReport':
        meta = data.get("metadata", {})
        metadata_obj = ReportMetadata.from_dict(meta) if isinstance(meta, dict) else meta
        return cls(
            metadata=metadata_obj,
            session_info=data.get("session_info", {}),
            performance=data.get("performance", {}),
            movement=data.get("movement", {}),
            biomechanics=data.get("biomechanics", {}),
            tracking=data.get("tracking", {}),
            pose_rules=data.get("pose_rules", {}),
            feedback=data.get("feedback", {}),
            data_quality=data.get("data_quality", {}),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "report_engine")
        )


class ExerciseReport(BaseContract):
    """Exercise history evaluation report contract."""

    def __init__(
        self,
        metadata: ReportMetadata,
        exercise_info: Dict[str, Any],
        performance_summary: Dict[str, Any],
        recent_history: List[Dict[str, Any]],
        data_quality: Dict[str, Any],
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "report_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.metadata = metadata
        self.exercise_info = exercise_info
        self.performance_summary = performance_summary
        self.recent_history = recent_history
        self.data_quality = data_quality

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "metadata": self.metadata.to_dict() if isinstance(self.metadata, ReportMetadata) else self.metadata,
            "exercise_info": self.exercise_info,
            "performance_summary": self.performance_summary,
            "recent_history": self.recent_history,
            "data_quality": self.data_quality,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExerciseReport':
        meta = data.get("metadata", {})
        metadata_obj = ReportMetadata.from_dict(meta) if isinstance(meta, dict) else meta
        return cls(
            metadata=metadata_obj,
            exercise_info=data.get("exercise_info", {}),
            performance_summary=data.get("performance_summary", {}),
            recent_history=data.get("recent_history", []),
            data_quality=data.get("data_quality", {}),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "report_engine")
        )


class ProgressReport(BaseContract):
    """Longitudinal user progress evaluation report contract."""

    def __init__(
        self,
        metadata: ReportMetadata,
        reporting_period: str,
        overall_summary: Dict[str, Any],
        trends: Dict[str, Any],
        personal_records: List[Dict[str, Any]],
        comparison: Dict[str, Any],
        data_quality: Dict[str, Any],
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "report_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.metadata = metadata
        self.reporting_period = reporting_period
        self.overall_summary = overall_summary
        self.trends = trends
        self.personal_records = personal_records
        self.comparison = comparison
        self.data_quality = data_quality

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "metadata": self.metadata.to_dict() if isinstance(self.metadata, ReportMetadata) else self.metadata,
            "reporting_period": self.reporting_period,
            "overall_summary": self.overall_summary,
            "trends": self.trends,
            "personal_records": self.personal_records,
            "comparison": self.comparison,
            "data_quality": self.data_quality,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProgressReport':
        meta = data.get("metadata", {})
        metadata_obj = ReportMetadata.from_dict(meta) if isinstance(meta, dict) else meta
        return cls(
            metadata=metadata_obj,
            reporting_period=data.get("reporting_period", "30d"),
            overall_summary=data.get("overall_summary", {}),
            trends=data.get("trends", {}),
            personal_records=data.get("personal_records", []),
            comparison=data.get("comparison", {}),
            data_quality=data.get("data_quality", {}),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "report_engine")
        )


class ComprehensiveReport(BaseContract):
    """Comprehensive all-in-one user evaluation report contract."""

    def __init__(
        self,
        metadata: ReportMetadata,
        executive_summary: Dict[str, Any],
        overall_progress: Dict[str, Any],
        score_trends: Dict[str, Any],
        biomechanics_trends: Dict[str, Any],
        personal_records: List[Dict[str, Any]],
        pose_performance: List[Dict[str, Any]],
        recent_sessions: List[Dict[str, Any]],
        session_comparison: Dict[str, Any],
        feedback_summary: Dict[str, Any],
        data_quality_notice: Dict[str, Any],
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "report_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.metadata = metadata
        self.executive_summary = executive_summary
        self.overall_progress = overall_progress
        self.score_trends = score_trends
        self.biomechanics_trends = biomechanics_trends
        self.personal_records = personal_records
        self.pose_performance = pose_performance
        self.recent_sessions = recent_sessions
        self.session_comparison = session_comparison
        self.feedback_summary = feedback_summary
        self.data_quality_notice = data_quality_notice

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "metadata": self.metadata.to_dict() if isinstance(self.metadata, ReportMetadata) else self.metadata,
            "executive_summary": self.executive_summary,
            "overall_progress": self.overall_progress,
            "score_trends": self.score_trends,
            "biomechanics_trends": self.biomechanics_trends,
            "personal_records": self.personal_records,
            "pose_performance": self.pose_performance,
            "recent_sessions": self.recent_sessions,
            "session_comparison": self.session_comparison,
            "feedback_summary": self.feedback_summary,
            "data_quality_notice": self.data_quality_notice,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComprehensiveReport':
        meta = data.get("metadata", {})
        metadata_obj = ReportMetadata.from_dict(meta) if isinstance(meta, dict) else meta
        return cls(
            metadata=metadata_obj,
            executive_summary=data.get("executive_summary", {}),
            overall_progress=data.get("overall_progress", {}),
            score_trends=data.get("score_trends", {}),
            biomechanics_trends=data.get("biomechanics_trends", {}),
            personal_records=data.get("personal_records", []),
            pose_performance=data.get("pose_performance", []),
            recent_sessions=data.get("recent_sessions", []),
            session_comparison=data.get("session_comparison", {}),
            feedback_summary=data.get("feedback_summary", {}),
            data_quality_notice=data.get("data_quality_notice", {}),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "report_engine")
        )


class ExportResult(BaseContract):
    """Export container payload for downloadable report files."""

    def __init__(
        self,
        report_type: str,
        format: str,  # json, csv, pdf
        filename: str,
        content: str,  # raw string, base64 PDF, or formatted text
        content_type: str = "application/json",
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "report_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.report_type = report_type
        self.format = format
        self.filename = filename
        self.content = content
        self.content_type = content_type

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "report_type": self.report_type,
            "format": self.format,
            "filename": self.filename,
            "content": self.content,
            "content_type": self.content_type,
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExportResult':
        return cls(
            report_type=data.get("report_type", "session"),
            format=data.get("format", "json"),
            filename=data.get("filename", "report.json"),
            content=data.get("content", ""),
            content_type=data.get("content_type", "application/json"),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "report_engine")
        )
