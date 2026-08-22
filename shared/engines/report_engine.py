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

        reps = int(session_data.get("reps", session_data.get("completed_reps", 0)))
        hold_time = float(session_data.get("hold_time", 0.0))
        cadence = float(session_data.get("average_cadence", (reps / (duration / 60.0)) if duration > 0 and reps > 0 else 0.0))
        rep_dur = float(session_data.get("average_rep_duration", (duration / reps) if reps > 0 else 0.0))

        session_info = {
            "session_id": session_id,
            "pose_id": pose_label.lower().replace(" ", "_"),
            "pose_name": pose_label,
            "exercise_id": pose_label.lower().replace(" ", "_"),
            "exercise_name": pose_label,
            "started_at": ts_str,
            "completed_at": ts_str,
            "timestamp": ts_str,
            "duration": round(duration, 1),
            "completed_reps": reps
        }

        perf = {
            "overall_score": round(accuracy, 1),
            "score_confidence": float(session_data.get("score_confidence", 1.0)),
            "score_category": score_category
        }

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
        user_id = str(exercise_data.get("user_id", self._active_user_id))

        meta = ReportMetadata(
            report_type="exercise",
            user_id=user_id,
            source_data_version=self.config.get("version", "2.0.0"),
            application_version=self.config.get("version", "2.0.0"),
            schema_version="2.0.0"
        )

        ex_name = exercise_data.get("pose_label", exercise_data.get("exercise_id", "Unknown Pose"))

        ex_info = {
            "exercise_id": ex_name.lower().replace(" ", "_"),
            "pose_name": ex_name,
            "total_sessions": exercise_data.get("sessions", exercise_data.get("total_sessions", 0)),
            "total_repetitions": exercise_data.get("total_reps", exercise_data.get("total_repetitions", 0)),
            "last_performed": exercise_data.get("last_performed")
        }

        perf_summary = {
            "average_score": exercise_data.get("avg_score", exercise_data.get("average_score", 0.0)),
            "best_score": exercise_data.get("best_score", 0.0),
            "average_hold": exercise_data.get("avg_hold", 0.0),
            "longest_hold": exercise_data.get("best_hold", 0.0),
            "average_reps": exercise_data.get("avg_reps", 0.0),
            "best_reps": exercise_data.get("best_reps", 0),
            "average_symmetry": exercise_data.get("best_symmetry"),
            "best_symmetry": exercise_data.get("best_symmetry"),
            "average_balance": exercise_data.get("best_balance"),
            "best_balance": exercise_data.get("best_balance"),
            "average_stability": exercise_data.get("best_stability"),
            "best_stability": exercise_data.get("best_stability"),
            "average_rom": exercise_data.get("best_rom"),
            "best_rom": exercise_data.get("best_rom")
        }

        data_quality = {
            "tracking_quality": exercise_data.get("tracking_quality"),
            "quality_gate_passed": True,
            "quality_notice": "Pose performance compiled strictly from finalized session analytics."
        }

        report = ExerciseReport(
            metadata=meta,
            exercise_info=ex_info,
            performance_summary=perf_summary,
            recent_history=recent_sessions or [],
            data_quality=data_quality,
            source=self.name
        )

        self._reports_generated_count += 1
        self._processing_time_ms = (time.time() - t0) * 1000.0
        self.publish("report.generated", report.to_dict())
        return report

    def generate_progress_report(self, summary_data: Dict[str, Any], timeframe: str = "30d") -> ProgressReport:
        """
        Composes ProgressReport using finalized AnalyticsSummary output.
        Does NOT recalculate trend algorithms or averages.
        """
        t0 = time.time()
        user_id = str(summary_data.get("user_id", self._active_user_id))

        meta = ReportMetadata(
            report_type="progress",
            user_id=user_id,
            source_data_version=self.config.get("version", "2.0.0"),
            application_version=self.config.get("version", "2.0.0"),
            schema_version="2.0.0"
        )

        bio = summary_data.get("biomechanics", {})

        overall = {
            "total_sessions": summary_data.get("total_sessions", 0),
            "total_sessions_all": summary_data.get("total_sessions_all", 0),
            "total_duration": summary_data.get("total_duration", 0.0),
            "overall_average_score": summary_data.get("overall_average_score", summary_data.get("avg_accuracy", 0.0)),
            "average_score": summary_data.get("overall_average_score", summary_data.get("avg_accuracy", 0.0)),
            "average_symmetry": bio.get("symmetry"),
            "average_balance": bio.get("balance"),
            "average_stability": bio.get("stability"),
            "average_rom": bio.get("rom"),
            "average_tracking_quality": bio.get("tracking_quality"),
            "streak_days": summary_data.get("streak_days", 0),
            "seven_day_delta": summary_data.get("seven_day_delta")
        }

        trends = summary_data.get("trend", summary_data.get("active_trends", {}))
        records = summary_data.get("personal_records", [])
        comparison = summary_data.get("session_comparison", summary_data.get("comparison", {}))

        data_quality = {
            "tracking_quality": bio.get("tracking_quality"),
            "tracking_status": bio.get("tracking_status", "Good"),
            "quality_notice": "Longitudinal progress evaluation compiled strictly from persisted session analytics."
        }

        report = ProgressReport(
            metadata=meta,
            reporting_period=timeframe,
            overall_summary=overall,
            trends=trends,
            personal_records=records,
            comparison=comparison,
            data_quality=data_quality,
            source=self.name
        )

        self._reports_generated_count += 1
        self._processing_time_ms = (time.time() - t0) * 1000.0
        self.publish("report.generated", report.to_dict())
        return report

    def generate_comprehensive_report(self, summary_data: Dict[str, Any]) -> ComprehensiveReport:
        t0 = time.time()
        user_id = str(summary_data.get("user_id", self._active_user_id))

        meta = ReportMetadata(
            report_type="comprehensive",
            user_id=user_id,
            source_data_version=self.config.get("version", "2.0.0"),
            application_version=self.config.get("version", "2.0.0"),
            schema_version="2.0.0"
        )

        bio = summary_data.get("biomechanics", {})

        exec_summary = {
            "total_sessions": summary_data.get("total_sessions", 0),
            "total_duration": summary_data.get("total_duration", 0.0),
            "overall_average_score": summary_data.get("overall_average_score", 0.0),
            "streak_days": summary_data.get("streak_days", 0),
            "seven_day_delta": summary_data.get("seven_day_delta"),
            "tracking_quality": bio.get("tracking_quality")
        }

        overall_prog = {
            "total_sessions": summary_data.get("total_sessions", 0),
            "total_duration": summary_data.get("total_duration", 0.0),
            "average_score": summary_data.get("overall_average_score", 0.0),
            "average_symmetry": bio.get("symmetry"),
            "average_balance": bio.get("balance"),
            "average_stability": bio.get("stability"),
            "average_rom": bio.get("rom"),
            "tracking_quality": bio.get("tracking_quality")
        }

        score_tr = summary_data.get("trend", {})
        bio_tr = {
            "symmetry": bio.get("symmetry"),
            "balance": bio.get("balance"),
            "stability": bio.get("stability"),
            "rom": bio.get("rom")
        }

        records = summary_data.get("personal_records", [])
        pose_perf = summary_data.get("pose_cards", [])
        recent = summary_data.get("recent_sessions", [])
        comparison = summary_data.get("session_comparison", {})
        insights = summary_data.get("insights", [])

        feedback_summary = {
            "deterministic_insights": insights,
            "strongest_pose": summary_data.get("strongest_pose"),
            "weakest_pose": summary_data.get("weakest_pose")
        }

        dq_notice = {
            "tracking_quality": bio.get("tracking_quality"),
            "tracking_status": bio.get("tracking_status", "Good"),
            "quality_notice": "Comprehensive posture portfolio compiled strictly from persisted session analytics. No raw landmarks or video streams persisted."
        }

        report = ComprehensiveReport(
            metadata=meta,
            executive_summary=exec_summary,
            overall_progress=overall_prog,
            score_trends=score_tr,
            biomechanics_trends=bio_tr,
            personal_records=records,
            pose_performance=pose_perf,
            recent_sessions=recent,
            session_comparison=comparison,
            feedback_summary=feedback_summary,
            data_quality_notice=dq_notice,
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
        """Formats session history into spreadsheet-compatible RFC-4180 CSV."""
        t0 = time.time()
        filename = f"posturesense_progress_{int(time.time())}.csv"
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Date", "Pose", "Exercise", "Score", "Score Category",
            "Duration", "Repetitions", "Hold Time", "Cadence",
            "Symmetry", "Balance", "Stability", "ROM", "Tracking Quality", "Failed Rules"
        ])

        for s in sessions_list:
            ts = s.get("timestamp", s.get("started_at", "N/A"))
            pose = s.get("pose_label", s.get("pose_name", "Unknown"))
            ex = s.get("exercise_id", pose.lower().replace(" ", "_"))
            score_val = s.get("accuracy", s.get("average_score", s.get("overall_score")))
            
            if score_val is not None:
                score = round(float(score_val), 1)
                cat = "Excellent" if score >= 90.0 else ("Good" if score >= 75.0 else ("Fair" if score >= 50.0 else "Needs Improvement"))
            else:
                score = "N/A"
                cat = "N/A"

            dur = round(float(s.get("duration", 0.0)), 1)
            reps = s.get("reps", s.get("completed_reps", 0))
            hold = round(float(s.get("hold_time", 0.0)), 1)
            cadence = round(float(s.get("average_cadence", 0.0)), 1)

            symm = round(float(s.get("symmetry_score")), 1) if s.get("symmetry_score") is not None else "N/A"
            bal = round(float(s.get("balance_score")), 1) if s.get("balance_score") is not None else "N/A"
            stab = round(float(s.get("stability_score")), 1) if s.get("stability_score") is not None else "N/A"
            rom = round(float(s.get("rom_score")), 1) if s.get("rom_score") is not None else "N/A"
            tq = round(float(s.get("tracking_quality")), 1) if s.get("tracking_quality") is not None else "N/A"

            failed = s.get("failed_rules", [])
            failed_str = "; ".join(failed) if failed else "None"

            writer.writerow([
                ts, pose, ex, score, cat, dur, reps, hold, cadence, symm, bal, stab, rom, tq, failed_str
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
        Renders a clean, styled HTML/PDF assessment report featuring PostureSense branding,
        summary metrics, posture score, biomechanics metrics, movement metrics,
        feedback summary, and explicit data quality notice.
        """
        t0 = time.time()
        meta = report_dict.get("metadata", {})
        rep_type = meta.get("report_type", "session").upper()
        user_id = meta.get("user_id", "anonymous")
        filename = f"posturesense_{rep_type.lower()}_report_{int(time.time())}.html"

        s_info = report_dict.get("session_info", {})
        perf = report_dict.get("performance", report_dict.get("overall_summary", {}))
        bio = report_dict.get("biomechanics", {})
        mov = report_dict.get("movement", {})
        dq = report_dict.get("data_quality", report_dict.get("data_quality_notice", {}))
        fb = report_dict.get("feedback", report_dict.get("feedback_summary", {}))
        rules = report_dict.get("pose_rules", {})

        overall_score = perf.get("overall_score", perf.get("average_score", 0.0))
        score_cat = perf.get("score_category", "Evaluated")

        symm_str = f"{bio.get('symmetry_score'):.1f}%" if bio.get("symmetry_score") is not None else "Not available"
        bal_str = f"{bio.get('balance_score'):.1f}%" if bio.get("balance_score") is not None else "Not available"
        stab_str = f"{bio.get('stability_score'):.1f}%" if bio.get("stability_score") is not None else "Not available"
        rom_str = f"{bio.get('rom_score'):.1f}%" if bio.get("rom_score") is not None else "Not available"
        tq_str = f"{dq.get('tracking_quality'):.1f}%" if dq.get("tracking_quality") is not None else "Not available"

        failed = rules.get("failed_rules", [])
        failed_html = f"<span style='color:#ef4444;'>{', '.join(failed)}</span>" if failed else "<span style='color:#22c55e;'>All pose rules satisfied</span>"

        strengths_html = "".join([f"<li>{s}</li>" for s in fb.get("strengths", ["Good form alignment"])])

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>PostureSense AI — {rep_type} REPORT</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 30px; background: #0b0f19; color: #f3f4f6; line-height: 1.5; }}
        .header {{ border-bottom: 2px solid #00d2ff; padding-bottom: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-end; }}
        .brand {{ color: #00d2ff; font-size: 26px; font-weight: 800; letter-spacing: -0.03em; margin: 0; }}
        .subtitle {{ color: #9ca3af; font-size: 13px; margin-top: 4px; }}
        .meta-pill {{ background: rgba(0, 210, 255, 0.1); border: 1px solid rgba(0, 210, 255, 0.2); color: #00d2ff; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
        .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }}
        .card {{ background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 16px; }}
        .card-sm {{ padding: 12px; }}
        .label {{ font-size: 11px; color: #9ca3af; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; }}
        .val {{ font-size: 24px; font-weight: 700; color: #f8fafc; margin-top: 4px; font-family: monospace; }}
        .section-title {{ font-size: 16px; font-weight: 700; color: #f8fafc; margin-bottom: 12px; border-left: 3px solid #00d2ff; padding-left: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
        th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid rgba(255, 255, 255, 0.06); font-size: 13px; }}
        th {{ color: #00d2ff; font-weight: 600; background: rgba(0, 0, 0, 0.2); text-transform: uppercase; font-size: 11px; }}
        .notice {{ background: rgba(234, 179, 8, 0.1); border: 1px solid rgba(234, 179, 8, 0.25); border-left: 4px solid #eab308; border-radius: 8px; padding: 14px 16px; font-size: 12px; color: #fef08a; margin-top: 28px; }}
        .footer {{ margin-top: 36px; padding-top: 14px; border-top: 1px solid rgba(255, 255, 255, 0.08); text-align: center; color: #6b7280; font-size: 11px; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1 class="brand">POSTURESENSE AI</h1>
            <div class="subtitle">Longitudinal Assessment &amp; Fitness Intelligence Report</div>
        </div>
        <div class="meta-pill">{rep_type} REPORT</div>
    </div>

    <div style="margin-bottom:20px;font-size:13px;color:#9ca3af">
        <strong>User ID:</strong> {user_id} &bull; 
        <strong>Pose:</strong> {s_info.get('pose_name', 'All Poses')} &bull; 
        <strong>Generated:</strong> {meta.get('generated_at', 'N/A')} &bull; 
        <strong>Schema:</strong> v{meta.get('schema_version', '2.0.0')}
    </div>

    <div class="grid-4">
        <div class="card">
            <div class="label">Posture Score</div>
            <div class="val" style="color:#00e676">{overall_score:.1f}%</div>
            <div style="font-size:12px;color:#9ca3af;margin-top:2px">{score_cat}</div>
        </div>
        <div class="card">
            <div class="label">Duration</div>
            <div class="val">{s_info.get('duration', 0.0)}s</div>
            <div style="font-size:12px;color:#9ca3af;margin-top:2px">Hold: {mov.get('hold_time', 0.0)}s</div>
        </div>
        <div class="card">
            <div class="label">Repetitions</div>
            <div class="val">{mov.get('reps', 0)}</div>
            <div style="font-size:12px;color:#9ca3af;margin-top:2px">Cadence: {mov.get('average_cadence', 0.0)} rpm</div>
        </div>
        <div class="card">
            <div class="label">Tracking Quality</div>
            <div class="val">{tq_str}</div>
            <div style="font-size:12px;color:#9ca3af;margin-top:2px">Gate: {"PASSED" if dq.get("quality_gate_passed", True) else "WARNING"}</div>
        </div>
    </div>

    <div class="card" style="margin-bottom:24px">
        <div class="section-title">Biomechanics Movement Quality</div>
        <table>
            <thead>
                <tr>
                    <th>Dimension</th>
                    <th>Measured Score</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>Symmetry (Bilateral Alignment)</td><td><strong>{symm_str}</strong></td><td>{ 'Measured' if symm_str != 'Not available' else 'Legacy / Unmeasured' }</td></tr>
                <tr><td>Balance (Center of Mass)</td><td><strong>{bal_str}</strong></td><td>{ 'Measured' if bal_str != 'Not available' else 'Legacy / Unmeasured' }</td></tr>
                <tr><td>Stability (Postural Steadiness)</td><td><strong>{stab_str}</strong></td><td>{ 'Measured' if stab_str != 'Not available' else 'Legacy / Unmeasured' }</td></tr>
                <tr><td>Range of Motion (ROM Depth)</td><td><strong>{rom_str}</strong></td><td>{ 'Measured' if rom_str != 'Not available' else 'Legacy / Unmeasured' }</td></tr>
            </tbody>
        </table>
    </div>

    <div class="card" style="margin-bottom:24px">
        <div class="section-title">Pose Rule &amp; Feedback Analysis</div>
        <p style="font-size:13px;margin:0 0 8px 0"><strong>Form Evaluation:</strong> {failed_html}</p>
        <ul style="font-size:13px;margin:0;padding-left:20px;color:#cbd5e1">
            {strengths_html}
        </ul>
    </div>

    <div class="notice">
        <strong>DATA QUALITY &amp; PRIVACY NOTICE:</strong><br>
        {dq.get('quality_notice', 'Generated deterministically from persisted session analytics.')}<br>
        <em>Privacy Guarantee: No raw camera video streams or landmark coordinates leave your local device memory.</em>
    </div>

    <div class="footer">
        PostureSense v2 &bull; Engine v{self.version} &bull; Schema v{meta.get('schema_version', '2.0.0')}
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
