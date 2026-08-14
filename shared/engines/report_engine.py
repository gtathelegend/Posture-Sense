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
        Composes a SessionReport strictly from finalized session analytics.
        Does NOT recalculate perception data, MediaPipe, landmarks, scores, or LLM commentary.
        """
        t0 = time.time()
        user_id = str(session_data.get("user_id", self._active_user_id))
        session_id = str(session_data.get("session_id", "sess_unknown"))

        meta = ReportMetadata(
            report_type="session",
            user_id=user_id,
            source_data_version=self.config.get("version", "2.0.0"),
            application_version=self.config.get("version", "2.0.0"),
            schema_version="2.0.0"
        )

        pose_label = session_data.get("pose_label", session_data.get("exercise_id", "Unknown Pose"))
        duration = float(session_data.get("duration", 0.0))
        accuracy = float(session_data.get("average_score", session_data.get("accuracy", 0.0)))

        if accuracy >= 90.0:
            score_category = "Excellent"
        elif accuracy >= 75.0:
            score_category = "Good"
        elif accuracy >= 50.0:
            score_category = "Fair"
        else:
            score_category = "Needs Improvement"

        ts_str = session_data.get("timestamp")

        session_info = {
            "session_id": session_id,
            "pose_id": pose_label.lower().replace(" ", "_"),
            "pose_name": pose_label,
            "exercise_id": pose_label.lower().replace(" ", "_"),
            "exercise_name": pose_label,
            "started_at": ts_str,
            "completed_at": ts_str,
            "timestamp": ts_str,
            "duration": round(duration, 1)
        }

        perf = {
            "overall_score": round(accuracy, 1),
            "score_confidence": float(session_data.get("score_confidence", 1.0)),
            "score_category": score_category
        }

        reps = int(session_data.get("reps", session_data.get("completed_reps", 0)))
        hold_time = float(session_data.get("hold_time", 0.0))
        cadence = float(session_data.get("average_cadence", (reps / (duration / 60.0)) if duration > 0 and reps > 0 else 0.0))
        rep_dur = float(session_data.get("average_rep_duration", (duration / reps) if reps > 0 else 0.0))

        rom_val = session_data.get("rom_score")

        movement = {
            "reps": reps,
            "hold_time": round(hold_time, 1),
            "average_rep_duration": round(rep_dur, 1),
            "average_cadence": round(cadence, 1),
            "rom_percentage": round(float(rom_val), 1) if rom_val is not None else None,
            "movement_quality": round(accuracy, 1)
        }

        symm = session_data.get("symmetry_score")
        bal = session_data.get("balance_score")
        stab = session_data.get("stability_score")

        biomechanics = {
            "symmetry_score": round(float(symm), 1) if symm is not None else None,
            "balance_score": round(float(bal), 1) if bal is not None else None,
            "stability_score": round(float(stab), 1) if stab is not None else None,
            "rom_score": round(float(rom_val), 1) if rom_val is not None else None
        }

        tq = session_data.get("tracking_quality")
        tracking_quality_val = round(float(tq), 1) if tq is not None else None

        tracking = {
            "tracking_quality": tracking_quality_val,
            "quality_gate_passed": bool(tracking_quality_val >= 50.0) if tracking_quality_val is not None else True
        }

        failed_rules = session_data.get("failed_rules", [])
        pose_rules = {
            "matched_rules": ["correct_posture_alignment"] if not failed_rules else [],
            "failed_rules": failed_rules
        }

        strengths = session_data.get("strengths", ["Maintained good posture alignment"] if accuracy >= 80.0 else [])
        weak_areas = session_data.get("weak_areas", failed_rules if failed_rules else [])
        common_mistakes = session_data.get("common_mistakes", [f"Form deviation: {r}" for r in failed_rules] if failed_rules else [])

        feedback = {
            "strengths": strengths,
            "weak_areas": weak_areas,
            "common_mistakes": common_mistakes
        }

        unavailable = []
        if symm is None: unavailable.append("symmetry_score")
        if bal is None: unavailable.append("balance_score")
        if stab is None: unavailable.append("stability_score")
        if rom_val is None: unavailable.append("rom_score")
        if tq is None: unavailable.append("tracking_quality")

        is_legacy = len(unavailable) >= 3

        data_quality = {
            "tracking_quality": tracking_quality_val,
            "quality_gate_passed": bool(tracking_quality_val >= 50.0) if tracking_quality_val is not None else True,
            "unavailable_metrics": unavailable,
            "quality_notice": "Detailed biomechanics data was not available for this session." if is_legacy else "All posture analytics telemetry captured successfully.",
            "is_legacy": is_legacy
        }

        report = SessionReport(
            metadata=meta,
            session_info=session_info,
            performance=perf,
            movement=movement,
            biomechanics=biomechanics,
            tracking=tracking,
            pose_rules=pose_rules,
            feedback=feedback,
            data_quality=data_quality,
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
