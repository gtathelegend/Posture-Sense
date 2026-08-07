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
    def create_session(user_id, pose_label, duration, accuracy):
        payload = {
            'user_id': str(user_id),
            'pose_label': pose_label,
            'duration': float(duration or 0.0),
            'accuracy': float(accuracy or 0.0),
        }
        response = require_supabase().table('pose_sessions').insert(payload).execute()
        data = response.data or []
        return build_pose_session(data[0]) if data else None
