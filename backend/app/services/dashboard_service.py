from backend.app.repositories.session_repository import SessionRepository


class DashboardService:
    @staticmethod
    def get_user_dashboard_data(user_id):
        sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        
        total_sessions = len(sessions)
        total_duration = sum(s.duration for s in sessions)
        avg_accuracy = sum(s.accuracy for s in sessions) / total_sessions if total_sessions > 0 else 0
        
        avg_symmetry = sum(s.symmetry_score for s in sessions) / total_sessions if total_sessions > 0 else 100.0
        avg_balance = sum(s.balance_score for s in sessions) / total_sessions if total_sessions > 0 else 100.0
        avg_stability = sum(s.stability_score for s in sessions) / total_sessions if total_sessions > 0 else 100.0
        avg_rom = sum(s.rom_score for s in sessions) / total_sessions if total_sessions > 0 else 100.0
        avg_tracking_quality = sum(s.tracking_quality for s in sessions) / total_sessions if total_sessions > 0 else 100.0
        
        total_reps = sum(s.reps for s in sessions)
        total_hold_time = sum(s.hold_time for s in sessions)

        pose_counts = {}
        for session in sessions:
            pose_counts[session.pose_label] = pose_counts.get(session.pose_label, 0) + 1
            
        recent_sessions = []
        for session in sessions[:20]:
            recent_sessions.append({
                'session_id': session.id,
                'timestamp': session.timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(session.timestamp, 'strftime') else str(session.timestamp),
                'pose_label': session.pose_label,
                'duration': round(session.duration, 1),
                'accuracy': round(session.accuracy, 1),
                'reps': session.reps,
                'symmetry_score': round(session.symmetry_score, 1),
                'balance_score': round(session.balance_score, 1),
                'stability_score': round(session.stability_score, 1),
                'rom_score': round(session.rom_score, 1),
                'hold_time': round(session.hold_time, 1),
                'tracking_quality': round(session.tracking_quality, 1),
                'failed_rules': session.failed_rules
            })
            
        return {
            'sessions': sessions,
            'total_sessions': total_sessions,
            'total_duration': round(total_duration, 1),
            'avg_accuracy': round(avg_accuracy, 1),
            'biomechanics': {
                'symmetry': round(avg_symmetry, 1),
                'balance': round(avg_balance, 1),
                'stability': round(avg_stability, 1),
                'rom': round(avg_rom, 1),
                'tracking_quality': round(avg_tracking_quality, 1)
            },
            'totals': {
                'reps': total_reps,
                'hold_time': round(total_hold_time, 1)
            },
            'pose_counts': pose_counts,
            'recent_sessions': recent_sessions
        }

