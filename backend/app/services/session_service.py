from backend.app.repositories.session_repository import SessionRepository


class SessionService:
    @staticmethod
    def save_session(user_id, pose_label, duration, accuracy):
        if not pose_label or pose_label in ['Unknown', 'Scanning ...']:
            return None, 'Invalid pose data'
        
        session = SessionRepository.create_session(user_id, pose_label, duration, accuracy)
        if session:
            return session, None
        return None, 'Failed to save session'
