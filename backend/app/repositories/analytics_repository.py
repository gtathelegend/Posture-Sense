"""
AnalyticsRepository
===================
Data access layer for user progress analytics, trends, exercise histories, and personal records.
Scoped strictly to user_id for strict user data isolation.
"""

from typing import Dict, Any, List, Optional
from backend.app.repositories.session_repository import SessionRepository


class AnalyticsRepository:
    """
    Data repository for user-level progress analytics.
    Enforces strict user isolation.
    """

    @staticmethod
    def get_user_analytics_summary(user_id: Any) -> Dict[str, Any]:
        sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        total_sessions = len(sessions)
        total_duration = sum(s.duration for s in sessions)
        avg_accuracy = sum(s.accuracy for s in sessions) / total_sessions if total_sessions > 0 else 0.0

        # Exercise history breakdown
        exercise_counts = {}
        for session in sessions:
            label = session.pose_label
            exercise_counts[label] = exercise_counts.get(label, 0) + 1

        recent_sessions = []
        for session in sessions[:10]:
            recent_sessions.append({
                'session_id': getattr(session, 'id', 'sess_unknown'),
                'timestamp': session.timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(session.timestamp, 'strftime') else str(session.timestamp),
                'pose_label': session.pose_label,
                'duration': round(session.duration, 1),
                'accuracy': round(session.accuracy, 1)
            })

        return {
            'user_id': str(user_id),
            'total_sessions': total_sessions,
            'total_duration': round(total_duration, 1),
            'overall_average_score': round(avg_accuracy, 1),
            'exercise_counts': exercise_counts,
            'recent_sessions': recent_sessions
        }

    @staticmethod
    def get_user_progress(user_id: Any) -> Dict[str, Any]:
        summary = AnalyticsRepository.get_user_analytics_summary(user_id)
        sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        
        scores = [s.accuracy for s in sessions]
        improvement_pct = 0.0
        if len(scores) >= 2 and scores[-1] > 0:
            first_score = scores[-1] # oldest session
            latest_score = scores[0]  # newest session
            improvement_pct = ((latest_score - first_score) / first_score) * 100.0

        return {
            'user_id': str(user_id),
            'total_sessions': summary['total_sessions'],
            'latest_score': scores[0] if scores else 0.0,
            'overall_average': summary['overall_average_score'],
            'improvement_percentage': round(improvement_pct, 1)
        }

    @staticmethod
    def get_exercise_history(user_id: Any) -> Dict[str, Any]:
        sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        exercises = {}
        for s in sessions:
            label = s.pose_label
            if label not in exercises:
                exercises[label] = {
                    'exercise_id': label,
                    'total_sessions': 0,
                    'total_duration': 0.0,
                    'best_score': 0.0,
                    'scores': []
                }
            ex = exercises[label]
            ex['total_sessions'] += 1
            ex['total_duration'] += s.duration
            ex['best_score'] = max(ex['best_score'], s.accuracy)
            ex['scores'].append(s.accuracy)

        for ex in exercises.values():
            scores = ex.pop('scores')
            ex['average_score'] = round(sum(scores) / len(scores), 1) if scores else 0.0
            ex['best_score'] = round(ex['best_score'], 1)
            ex['total_duration'] = round(ex['total_duration'], 1)

        return {
            'user_id': str(user_id),
            'exercises': exercises
        }

    @staticmethod
    def get_user_trends(user_id: Any) -> Dict[str, Any]:
        sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        scores = [s.accuracy for s in reversed(sessions[:10])] # chronological order

        direction = "INSUFFICIENT_DATA"
        pct_change = 0.0
        if len(scores) >= 3:
            first = scores[0]
            last = scores[-1]
            pct_change = ((last - first) / first * 100.0) if first > 0 else 0.0
            if pct_change > 2.0:
                direction = "IMPROVING"
            elif pct_change < -2.0:
                direction = "DECLINING"
            else:
                direction = "STABLE"

        return {
            'user_id': str(user_id),
            'overall_score_trend': {
                'metric_name': 'overall_score',
                'trend_direction': direction,
                'observation_count': len(scores),
                'percentage_change': round(pct_change, 2),
                'sample_values': scores
            }
        }

    @staticmethod
    def get_personal_records(user_id: Any) -> List[Dict[str, Any]]:
        sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        if not sessions:
            return []

        best_session = max(sessions, key=lambda s: s.accuracy)
        longest_session = max(sessions, key=lambda s: s.duration)

        return [
            {
                'record_type': 'Highest Score',
                'exercise_id': best_session.pose_label,
                'value': round(best_session.accuracy, 1),
                'unit': 'points'
            },
            {
                'record_type': 'Longest Hold / Duration',
                'exercise_id': longest_session.pose_label,
                'value': round(longest_session.duration, 1),
                'unit': 'seconds'
            }
        ]
