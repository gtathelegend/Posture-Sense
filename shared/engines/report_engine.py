"""
ReportEngine
============
Production-grade Reports & Export Engine for PostureSense v2.

Priority    : 11
Dependencies: analytics_engine, feedback_engine, scoring_engine, movement_engine, pose_rule_engine, biomechanics_engine
Publishes   : report.generated
              report.exported

DO NOT recalculate biomechanics, scores, pose rules, or analytics.
DO NOT generate new coaching advice or feedback.
DO NOT process camera frames or raw landmarks.
DO NOT introduce ML or create a second analytics system.
DO NOT store raw video or landmark streams.
"""

from __future__ import annotations

import csv
import io
import json
import time
from typing import Any, Dict, List, Optional

from shared.engines.interfaces import ReportEngineInterface
from shared.events.event_bus import EventBus
from shared.types.enums import EngineStatus
from shared.contracts.report import (
    ReportMetadata,
    SessionReport,
    ExerciseReport,
    ProgressReport,
    ComprehensiveReport,
    ExportResult,
)


class ReportEngine(ReportEngineInterface):
    """
    ReportEngine composes human-readable evaluation reports and downloadable exports
    (PDF, JSON, CSV) from finalized upstream assessment and analytics outputs.
    """

    def __init__(self, name: str = "ReportEngine", event_bus: Optional[EventBus] = None):
        super().__init__(name=name, event_bus=event_bus)
        self.version = "2.0.0"
        self.priority = 11
        self.dependencies = [
            "analytics_engine",
            "feedback_engine",
            "scoring_engine",
            "movement_engine",
            "pose_rule_engine",
            "biomechanics_engine"
        ]

        self.config: Dict[str, Any] = {
            "version": "2.0.0",
            "application_name": "PostureSense AI Pipeline",
            "pdf_branding": "PostureSense Performance Analytics"
        }

        self._active_user_id: str = "anonymous"
        self._reports_generated_count: int = 0
        self._last_export_format: str = "json"
        self._processing_time_ms: float = 0.0

    def initialize(self, config: Optional[dict] = None) -> bool:
        if config:
            self.config.update(config)

        self._status = EngineStatus.INITIALIZED
        self.publish("report.initialized", self.get_diagnostics())
        return True

    def start(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("report.started", self.get_diagnostics())
        return True

    def pause(self) -> bool:
        self._status = EngineStatus.PAUSED
        self.publish("report.paused", self.get_diagnostics())
        return True

    def resume(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("report.resumed", self.get_diagnostics())
        return True

    def stop(self) -> bool:
        self._status = EngineStatus.STOPPED
        self.publish("report.stopped", self.get_diagnostics())
        return True

    def dispose(self) -> bool:
        self._status = EngineStatus.DISPOSED
        self.publish("report.disposed", self.get_diagnostics())
        return True

    def set_active_user(self, user_id: str) -> None:
        self._active_user_id = str(user_id) if user_id else "anonymous"

    # ---------------------------------------------------------------------------
    # Report Composition Methods
    # ---------------------------------------------------------------------------

    def generate_session_report(self, session_data: Dict[str, Any], score_report: Optional[Dict[str, Any]] = None, feedback_items: Optional[List[Dict[str, Any]]] = None) -> SessionReport:
        """
        Composes a SessionReport from finalized session analytics, score report, and feedback items.
        Does NOT generate new feedback or compute new scores.
        """
        t0 = time.time()
        user_id = session_data.get("user_id", self._active_user_id)
        session_id = session_data.get("session_id", "sess_unknown")

        meta = ReportMetadata(
            report_type="session",
            user_id=user_id,
            source_data_version=self.config.get("version", "2.0.0"),
            application_version=self.config.get("version", "2.0.0")
        )

        session_info = {
            "session_id": session_id,
            "exercise_id": session_data.get("exercise_id", "unknown"),
            "duration": session_data.get("duration", 0.0),
            "completed_reps": session_data.get("completed_reps", 0),
            "valid_reps": session_data.get("valid_reps", 0),
            "invalid_reps": session_data.get("invalid_reps", 0),
            "timestamp": session_data.get("timestamp")
        }

        perf = {
            "overall_score": session_data.get("average_score", 0.0),
            "best_score": session_data.get("best_score", 0.0),
            "worst_score": session_data.get("worst_score", 0.0),
            "consistency": session_data.get("consistency", 100.0),
            "components": score_report.get("components", {}) if score_report else {}
        }

        assessment = {
            "feedback_messages": feedback_items or [],
            "strengths": score_report.get("strengths", []) if score_report else [],
            "areas_requiring_attention": score_report.get("missing_metrics", []) if score_report else []
        }

        quality = {
            "tracking_quality": session_data.get("tracking_quality", 100.0),
            "quality_gate_passed": score_report.get("quality_gate_passed", True) if score_report else True,
            "quality_warning": score_report.get("quality_warning") if score_report else None,
            "confidence": score_report.get("score_confidence", 1.0) if score_report else 1.0
        }

        report = SessionReport(
            metadata=meta,
            session_info=session_info,
            performance=perf,
            assessment=assessment,
            data_quality=quality,
            source=self.name
        )

        self._reports_generated_count += 1
        self._processing_time_ms = (time.time() - t0) * 1000.0
        self.publish("report.generated", report.to_dict())
        return report

    def generate_exercise_report(self, exercise_data: Dict[str, Any], recent_sessions: Optional[List[Dict[str, Any]]] = None) -> ExerciseReport:
        t0 = time.time()
        user_id = exercise_data.get("user_id", self._active_user_id)

        meta = ReportMetadata(
            report_type="exercise",
            user_id=user_id
        )

        ex_info = {
            "exercise_id": exercise_data.get("exercise_id", "unknown"),
            "total_sessions": exercise_data.get("total_sessions", 0),
            "total_repetitions": exercise_data.get("total_repetitions", 0),
            "last_performed": exercise_data.get("last_performed")
        }

        perf_summary = {
            "best_score": exercise_data.get("best_score", 0.0),
            "average_score": exercise_data.get("average_score", 0.0),
            "best_rom": exercise_data.get("best_rom", 0.0),
            "average_rom": exercise_data.get("average_rom", 0.0),
            "average_stability": exercise_data.get("average_stability", 0.0),
            "average_symmetry": exercise_data.get("average_symmetry", 0.0),
            "average_form": exercise_data.get("average_form", 0.0),
            "improvement_percentage": exercise_data.get("improvement_percentage", 0.0)
        }

        report = ExerciseReport(
            metadata=meta,
            exercise_info=ex_info,
            performance_summary=perf_summary,
            recent_history=recent_sessions or [],
            source=self.name
        )

        self._reports_generated_count += 1
        self._processing_time_ms = (time.time() - t0) * 1000.0
        self.publish("report.generated", report.to_dict())
        return report

    def generate_progress_report(self, summary_data: Dict[str, Any]) -> ProgressReport:
        """
        Composes ProgressReport using finalized AnalyticsSummary output.
        Does NOT recalculate trend algorithms or averages.
        """
        t0 = time.time()
        user_id = summary_data.get("user_id", self._active_user_id)

        meta = ReportMetadata(
            report_type="progress",
            user_id=user_id
        )

        overall = {
            "total_sessions": summary_data.get("total_sessions", 0),
            "total_duration": summary_data.get("total_duration", 0.0),
            "overall_average_score": summary_data.get("overall_average_score", 0.0),
            "streak_days": summary_data.get("streak_days", 0)
        }

        trends = summary_data.get("active_trends", {})
        records = summary_data.get("personal_records", [])
        comparison = summary_data.get("comparison", {})

        report = ProgressReport(
            metadata=meta,
            overall_summary=overall,
            trends=trends,
            personal_records=records,
            comparison=comparison,
            source=self.name
        )

        self._reports_generated_count += 1
        self._processing_time_ms = (time.time() - t0) * 1000.0
        self.publish("report.generated", report.to_dict())
        return report

    def generate_comprehensive_report(self, summary_data: Dict[str, Any], session_reports: Optional[List[Dict[str, Any]]] = None) -> ComprehensiveReport:
        t0 = time.time()
        user_id = summary_data.get("user_id", self._active_user_id)

        meta = ReportMetadata(
            report_type="comprehensive",
            user_id=user_id
        )

        report = ComprehensiveReport(
            metadata=meta,
            progress_summary=summary_data,
            session_reports=session_reports or [],
            exercise_reports=summary_data.get("exercise_history", {}),
            personal_records=summary_data.get("personal_records", []),
            source=self.name
        )

        self._reports_generated_count += 1
        self._processing_time_ms = (time.time() - t0) * 1000.0
        self.publish("report.generated", report.to_dict())
        return report

    # ---------------------------------------------------------------------------
    # Exporters (JSON, CSV, PDF)
    # ---------------------------------------------------------------------------

    def export_json(self, report_dict: Dict[str, Any]) -> ExportResult:
        """Serializes report into structured JSON export."""
        t0 = time.time()
        rep_type = report_dict.get("metadata", {}).get("report_type", "session")
        filename = f"posturesense_{rep_type}_report_{int(time.time())}.json"
        content = json.dumps(report_dict, indent=2)

        res = ExportResult(
            report_type=rep_type,
            format="json",
            filename=filename,
            content=content,
            content_type="application/json",
            source=self.name
        )

        self._last_export_format = "json"
        self._processing_time_ms = (time.time() - t0) * 1000.0
        self.publish("report.exported", res.to_dict())
        return res

    def export_csv(self, sessions_list: List[Dict[str, Any]]) -> ExportResult:
        """Formats session history into spreadsheet-compatible CSV."""
        t0 = time.time()
        filename = f"posturesense_progress_{int(time.time())}.csv"
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([
            "Date", "Exercise", "Score", "ROM", "Stability",
            "Symmetry", "Cadence", "Repetitions", "Duration", "Tracking Quality"
        ])

        for s in sessions_list:
            writer.writerow([
                s.get("timestamp", "N/A"),
                s.get("exercise_id", "unknown"),
                s.get("average_score", s.get("accuracy", 0.0)),
                s.get("rom", "N/A"),
                s.get("stability", "N/A"),
                s.get("symmetry", "N/A"),
                s.get("cadence", "N/A"),
                s.get("completed_reps", s.get("total_reps", 0)),
                s.get("duration", 0.0),
                s.get("tracking_quality", 100.0)
            ])

        content = output.getvalue()
        res = ExportResult(
            report_type="progress_csv",
            format="csv",
            filename=filename,
            content=content,
            content_type="text/csv",
            source=self.name
        )

        self._last_export_format = "csv"
        self._processing_time_ms = (time.time() - t0) * 1000.0
        self.publish("report.exported", res.to_dict())
        return res

    def export_pdf(self, report_dict: Dict[str, Any]) -> ExportResult:
        """
        Renders a clean, styled HTML/PDF report featuring PostureSense branding,
        title, metric summary cards, score breakdown, feedback, and data quality notice.
        """
        t0 = time.time()
        meta = report_dict.get("metadata", {})
        rep_type = meta.get("report_type", "session").upper()
        user_id = meta.get("user_id", "anonymous")
        filename = f"posturesense_{rep_type.lower()}_report_{int(time.time())}.pdf.html"

        perf = report_dict.get("performance", report_dict.get("overall_summary", {}))
        overall_score = perf.get("overall_score", perf.get("overall_average_score", 0.0))
        quality = report_dict.get("data_quality", {})

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>PostureSense AI — {rep_type} REPORT</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; margin: 20px; background: #0f172a; color: #f8fafc; }}
        .header {{ border-bottom: 2px solid #38bdf8; padding-bottom: 12px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; color: #38bdf8; font-size: 24px; }}
        .header p {{ margin: 4px 0 0 0; color: #94a3b8; font-size: 12px; }}
        .card {{ background: #1e293b; border-radius: 8px; padding: 16px; margin-bottom: 16px; border: 1px solid #334155; }}
        .metric-title {{ color: #94a3b8; font-size: 11px; text-transform: uppercase; font-weight: 700; }}
        .metric-score {{ color: #4ade80; font-size: 28px; font-weight: 700; margin: 4px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #334155; font-size: 13px; }}
        th {{ color: #38bdf8; font-weight: 600; background: #0f172a; }}
        .notice {{ background: #0f172a; border-left: 4px solid #eab308; padding: 8px 12px; font-size: 11px; color: #cbd5e1; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 PostureSense AI Performance Report</h1>
        <p>Report Type: {rep_type} | User: {user_id} | Generated: {meta.get("generated_at", "N/A")} | Schema v{meta.get("schema_version", "2.0.0")}</p>
    </div>

    <div class="card">
        <div class="metric-title">OVERALL PERFORMANCE SCORE</div>
        <div class="metric-score">{overall_score:.1f} / 100</div>
        <p style="color:#94a3b8;font-size:12px;margin:0;">Status: {report_dict.get("performance", {}).get("category", "Evaluated")}</p>
    </div>

    <div class="card">
        <div class="metric-title">SESSION DETAILS</div>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Duration</td><td>{report_dict.get("session_info", {}).get("duration", 0.0)}s</td></tr>
            <tr><td>Completed Reps</td><td>{report_dict.get("session_info", {}).get("completed_reps", 0)}</td></tr>
            <tr><td>Tracking Quality</td><td>{quality.get("tracking_quality", 100.0)}%</td></tr>
            <tr><td>Quality Gate</td><td>{"PASSED" if quality.get("quality_gate_passed", True) else "WARNING"}</td></tr>
        </table>
    </div>

    <div class="notice">
        <strong>DATA QUALITY NOTICE:</strong> Generated deterministically by PostureSense v2 Report Engine. Upstream posture, score, and feedback metrics are preserved without modification.
    </div>
</body>
</html>"""

        res = ExportResult(
            report_type=rep_type.lower(),
            format="pdf",
            filename=filename,
            content=html_content,
            content_type="application/pdf",
            source=self.name
        )

        self._last_export_format = "pdf"
        self._processing_time_ms = (time.time() - t0) * 1000.0
        self.publish("report.exported", res.to_dict())
        return res

    # ---------------------------------------------------------------------------
    # Diagnostics & Telemetry
    # ---------------------------------------------------------------------------

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "priority": self.priority,
            "dependencies": self.dependencies,
            "metrics": {
                "activeUserId": self._active_user_id,
                "reportsGeneratedCount": self._reports_generated_count,
                "lastExportFormat": self._last_export_format,
                "processingLatencyMs": round(self._processing_time_ms, 2)
            }
        }
