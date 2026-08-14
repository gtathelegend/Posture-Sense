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
    def generate_progress_report(user_id: Any, timeframe: str = "30d") -> Dict[str, Any]:
        from backend.app.services.dashboard_service import DashboardService
        ReportService._engine.set_active_user(str(user_id))
        overview_dict = DashboardService.get_user_dashboard_overview(user_id, timeframe=timeframe)
        report = ReportService._engine.generate_progress_report(overview_dict, timeframe=timeframe)
        return report.to_dict()

    @staticmethod
    def generate_exercise_report(user_id: Any, exercise_id: str) -> Dict[str, Any]:
        from backend.app.services.dashboard_service import DashboardService
        ReportService._engine.set_active_user(str(user_id))
        overview_dict = DashboardService.get_user_dashboard_overview(user_id, timeframe="all")
        pose_cards = overview_dict.get("pose_cards", [])
        
        target_card = None
        for p in pose_cards:
            p_label = p.get("pose_label", "")
            if p_label.lower().replace(" ", "_") == exercise_id.lower().replace(" ", "_") or p_label.lower() == exercise_id.lower():
                target_card = p
                break

        if not target_card:
            target_card = {
                "exercise_id": exercise_id,
                "pose_label": exercise_id,
                "sessions": 0,
                "avg_score": 0.0
            }

        sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        recent_for_pose = []
        for s in sessions:
            if s.pose_label.lower().replace(" ", "_") == exercise_id.lower().replace(" ", "_") or s.pose_label.lower() == exercise_id.lower():
                ts_str = s.timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(s.timestamp, 'strftime') else str(s.timestamp)
                recent_for_pose.append({
                    "session_id": str(s.id),
                    "timestamp": ts_str,
                    "pose_label": s.pose_label,
                    "accuracy": round(s.accuracy, 1),
                    "duration": round(s.duration, 1),
                    "hold_time": round(s.hold_time, 1),
                    "reps": s.reps,
                    "symmetry_score": round(s.symmetry_score, 1) if s.symmetry_score is not None else None,
                    "balance_score": round(s.balance_score, 1) if s.balance_score is not None else None,
                    "stability_score": round(s.stability_score, 1) if s.stability_score is not None else None,
                    "rom_score": round(s.rom_score, 1) if s.rom_score is not None else None
                })

        report = ReportService._engine.generate_exercise_report(target_card, recent_sessions=recent_for_pose)
        return report.to_dict()

    @staticmethod
    def generate_comprehensive_report(user_id: Any) -> Dict[str, Any]:
        from backend.app.services.dashboard_service import DashboardService
        ReportService._engine.set_active_user(str(user_id))
        overview_dict = DashboardService.get_user_dashboard_overview(user_id, timeframe="all")
        report = ReportService._engine.generate_comprehensive_report(overview_dict)
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
    def export_progress_csv(user_id: Any, timeframe: str = "30d") -> Dict[str, Any]:
        from backend.app.services.dashboard_service import DashboardService
        overview_dict = DashboardService.get_user_dashboard_overview(user_id, timeframe=timeframe)
        recent_sessions = overview_dict.get("recent_sessions", [])
        export_res = ReportService._engine.export_csv(recent_sessions)
        return export_res.to_dict()
