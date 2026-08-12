from backend.app.extensions import require_supabase
from backend.app.models.pose_session import build_pose_session


class SessionRepository:
    @staticmethod
    def fetch_sessions_by_user_id(user_id):
        response = (
            require_supabase()
            .table('pose_sessions')
            .select('*')
            .eq('user_id', str(user_id))
            .order('timestamp', desc=True)
            .execute()
        )
        return [build_pose_session(record) for record in (response.data or [])]

    @staticmethod
    def fetch_session_by_id(user_id, session_id):
        try:
            response = (
                require_supabase()
                .table('pose_sessions')
                .select('*')
                .eq('user_id', str(user_id))
                .eq('id', session_id)
                .execute()
            )
            data = response.data or []
            return build_pose_session(data[0]) if data else None
        except Exception:
            return None

    @staticmethod
    def create_session(
        user_id,
        pose_label,
        duration,
        accuracy,
        reps=0,
        symmetry_score=100.0,
        balance_score=100.0,
        stability_score=100.0,
        rom_score=100.0,
        hold_time=0.0,
        tracking_quality=100.0,
        failed_rules=None
    ):
        payload = {
            'user_id': str(user_id),
            'pose_label': pose_label,
            'duration': float(duration or 0.0),
            'accuracy': float(accuracy or 0.0),
            'reps': int(reps or 0),
            'symmetry_score': float(symmetry_score if symmetry_score is not None else 100.0),
            'balance_score': float(balance_score if balance_score is not None else 100.0),
            'stability_score': float(stability_score if stability_score is not None else 100.0),
            'rom_score': float(rom_score if rom_score is not None else 100.0),
            'hold_time': float(hold_time or 0.0),
            'tracking_quality': float(tracking_quality if tracking_quality is not None else 100.0),
            'failed_rules': failed_rules if isinstance(failed_rules, list) else []
        }
        response = require_supabase().table('pose_sessions').insert(payload).execute()
        data = response.data or []
        return build_pose_session(data[0]) if data else None

