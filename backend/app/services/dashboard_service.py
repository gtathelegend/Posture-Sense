from backend.app.repositories.session_repository import SessionRepository


class DashboardService:
    @staticmethod
    def get_user_dashboard_data(user_id):
        sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        
        total_sessions = len(sessions)
        total_duration = sum(s.duration for s in sessions)
        avg_accuracy = sum(s.accuracy for s in sessions) / total_sessions if total_sessions > 0 else 0
        
        pose_counts = {}
        for session in sessions:
            pose_counts[session.pose_label] = pose_counts.get(session.pose_label, 0) + 1
            
        recent_sessions = []
        for session in sessions[:20]:
            recent_sessions.append({
                'timestamp': session.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'pose_label': session.pose_label,
                'duration': round(session.duration, 1),
                'accuracy': round(session.accuracy, 1)
            })
            
        return {
            'sessions': sessions,
            'total_sessions': total_sessions,
            'total_duration': total_duration,
            'avg_accuracy': round(avg_accuracy, 1),
            'pose_counts': pose_counts,
            'recent_sessions': recent_sessions
        }
