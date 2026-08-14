"""
ReportService
=============
Backend service layer for composing reports and generating PDF/JSON/CSV exports.
Enforces strict user isolation.
"""

from typing import Dict, Any, List, Optional
from shared.engines.report_engine import ReportEngine
from backend.app.repositories.analytics_repository import AnalyticsRepository
from backend.app.repositories.session_repository import SessionRepository


class ReportService:
    _engine = ReportEngine()
    _engine.initialize()
    _engine.start()

    @staticmethod
    def generate_session_report(user_id: Any, session_id: str) -> Dict[str, Any]:
        ReportService._engine.set_active_user(str(user_id))
        sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        
        target = None
        for s in sessions:
            if str(getattr(s, 'id', '')) == str(session_id):
                target = s
                break

        if not target and sessions and (str(session_id).startswith("sess_") or session_id == "latest"):
            target = sessions[0]

        if not target:
            session_dict = {
                "session_id": str(session_id),
                "user_id": str(user_id),
                "pose_label": "Unknown Pose",
                "duration": 0.0,
                "accuracy": 0.0,
                "reps": 0,
                "hold_time": 0.0,
                "symmetry_score": None,
                "balance_score": None,
                "stability_score": None,
                "rom_score": None,
                "tracking_quality": None,
                "failed_rules": []
            }
        else:
            ts = target.timestamp
            ts_str = ts.strftime('%Y-%m-%dT%H:%M:%SZ') if hasattr(ts, 'strftime') else str(ts)
            session_dict = {
                "session_id": str(target.id),
                "user_id": str(user_id),
                "pose_label": target.pose_label,
                "exercise_id": target.pose_label,
                "timestamp": ts_str,
                "duration": target.duration,
                "accuracy": target.accuracy,
                "average_score": target.accuracy,
                "reps": target.reps,
                "hold_time": target.hold_time,
                "symmetry_score": target.symmetry_score,
                "balance_score": target.balance_score,
                "stability_score": target.stability_score,
                "rom_score": target.rom_score,
                "tracking_quality": target.tracking_quality,
                "failed_rules": target.failed_rules
            }

        report = ReportService._engine.generate_session_report(session_dict)
        return report.to_dict()


    @staticmethod
    def generate_progress_report(user_id: Any) -> Dict[str, Any]:
        ReportService._engine.set_active_user(str(user_id))
        summary_dict = AnalyticsRepository.get_user_analytics_summary(user_id)
        report = ReportService._engine.generate_progress_report(summary_dict)
        return report.to_dict()

    @staticmethod
    def generate_exercise_report(user_id: Any, exercise_id: str) -> Dict[str, Any]:
        ReportService._engine.set_active_user(str(user_id))
        ex_history = AnalyticsRepository.get_exercise_history(user_id)
        ex_data = ex_history.get("exercises", {}).get(exercise_id, {
            "exercise_id": exercise_id,
            "total_sessions": 0,
            "average_score": 0.0
        })
        report = ReportService._engine.generate_exercise_report(ex_data)
        return report.to_dict()

    @staticmethod
    def generate_comprehensive_report(user_id: Any) -> Dict[str, Any]:
        ReportService._engine.set_active_user(str(user_id))
        summary_dict = AnalyticsRepository.get_user_analytics_summary(user_id)
        report = ReportService._engine.generate_comprehensive_report(summary_dict)
        return report.to_dict()

    @staticmethod
    def export_session_pdf(user_id: Any, session_id: str) -> Dict[str, Any]:
        rep_dict = ReportService.generate_session_report(user_id, session_id)
        export_res = ReportService._engine.export_pdf(rep_dict)
        return export_res.to_dict()

    @staticmethod
    def export_session_json(user_id: Any, session_id: str) -> Dict[str, Any]:
        rep_dict = ReportService.generate_session_report(user_id, session_id)
        export_res = ReportService._engine.export_json(rep_dict)
        return export_res.to_dict()

    @staticmethod
    def export_progress_csv(user_id: Any) -> Dict[str, Any]:
        summary_dict = AnalyticsRepository.get_user_analytics_summary(user_id)
        recent_sessions = summary_dict.get("recent_sessions", [])
        export_res = ReportService._engine.export_csv(recent_sessions)
        return export_res.to_dict()
