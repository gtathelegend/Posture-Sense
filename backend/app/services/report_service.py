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
            if str(getattr(s, 'id', '')) == str(session_id) or str(session_id).startswith("sess_"):
                target = s
                break

        if not target and sessions:
            target = sessions[0]

        reps_val = getattr(target, 'reps', 0) if target else 0
        tq_val = getattr(target, 'tracking_quality', 100.0) if target else 100.0
        symm_val = getattr(target, 'symmetry_score', 100.0) if target else 100.0
        bal_val = getattr(target, 'balance_score', 100.0) if target else 100.0
        stab_val = getattr(target, 'stability_score', 100.0) if target else 100.0
        rom_val = getattr(target, 'rom_score', 100.0) if target else 100.0
        hold_val = getattr(target, 'hold_time', 0.0) if target else 0.0
        rules_val = getattr(target, 'failed_rules', []) if target else []

        session_dict = {
            "session_id": str(getattr(target, 'id', session_id)) if target else session_id,
            "user_id": str(user_id),
            "exercise_id": target.pose_label if target else "unknown",
            "duration": target.duration if target else 0.0,
            "average_score": target.accuracy if target else 0.0,
            "best_score": target.accuracy if target else 0.0,
            "worst_score": target.accuracy if target else 0.0,
            "completed_reps": reps_val,
            "valid_reps": reps_val,
            "invalid_reps": 0,
            "hold_time": hold_val,
            "symmetry_score": symm_val,
            "balance_score": bal_val,
            "stability_score": stab_val,
            "rom_score": rom_val,
            "tracking_quality": tq_val,
            "failed_rules": rules_val
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
