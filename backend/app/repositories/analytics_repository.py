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

        avg_symmetry = sum(s.symmetry_score for s in sessions) / total_sessions if total_sessions > 0 else 100.0
        avg_balance = sum(s.balance_score for s in sessions) / total_sessions if total_sessions > 0 else 100.0
        avg_stability = sum(s.stability_score for s in sessions) / total_sessions if total_sessions > 0 else 100.0
        avg_rom = sum(s.rom_score for s in sessions) / total_sessions if total_sessions > 0 else 100.0
        avg_tracking_quality = sum(s.tracking_quality for s in sessions) / total_sessions if total_sessions > 0 else 100.0

        total_reps = sum(s.reps for s in sessions)
        total_hold_time = sum(s.hold_time for s in sessions)

        # Exercise history breakdown
        exercise_counts = {}
        for session in sessions:
            label = session.pose_label
            exercise_counts[label] = exercise_counts.get(label, 0) + 1

        recent_sessions = []
        for session in sessions[:10]:
            recent_sessions.append(session.to_dict())

        return {
            'user_id': str(user_id),
            'total_sessions': total_sessions,
            'total_duration': round(total_duration, 1),
            'overall_average_score': round(avg_accuracy, 1),
            'biomechanics': {
                'average_symmetry': round(avg_symmetry, 1),
                'average_balance': round(avg_balance, 1),
                'average_stability': round(avg_stability, 1),
                'average_rom': round(avg_rom, 1),
                'average_tracking_quality': round(avg_tracking_quality, 1)
            },
            'totals': {
                'total_reps': total_reps,
                'total_hold_time': round(total_hold_time, 1)
            },
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

        latest = sessions[0] if sessions else None
        prev = sessions[1] if len(sessions) >= 2 else None

        session_comparison = {}
        if latest:
            session_comparison = {
                'latest_session': latest.to_dict(),
                'previous_session': prev.to_dict() if prev else None,
                'score_delta': round(latest.accuracy - prev.accuracy, 1) if prev else 0.0,
                'symmetry_delta': round(latest.symmetry_score - prev.symmetry_score, 1) if prev else 0.0,
                'balance_delta': round(latest.balance_score - prev.balance_score, 1) if prev else 0.0,
                'stability_delta': round(latest.stability_score - prev.stability_score, 1) if prev else 0.0,
                'rom_delta': round(latest.rom_score - prev.rom_score, 1) if prev else 0.0,
            }

        return {
            'user_id': str(user_id),
            'total_sessions': summary['total_sessions'],
            'latest_score': scores[0] if scores else 0.0,
            'overall_average': summary['overall_average_score'],
            'improvement_percentage': round(improvement_pct, 1),
            'biomechanics': summary['biomechanics'],
            'totals': summary['totals'],
            'session_comparison': session_comparison
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
                    'total_repetitions': 0,
                    'total_hold_time': 0.0,
                    'best_score': 0.0,
                    'scores': [],
                    'symmetry_scores': [],
                    'balance_scores': [],
                    'stability_scores': [],
                    'rom_scores': [],
                    'tracking_qualities': []
                }
            ex = exercises[label]
            ex['total_sessions'] += 1
            ex['total_duration'] += s.duration
            ex['total_repetitions'] += s.reps
            ex['total_hold_time'] += s.hold_time
            ex['best_score'] = max(ex['best_score'], s.accuracy)
            ex['scores'].append(s.accuracy)
            ex['symmetry_scores'].append(s.symmetry_score)
            ex['balance_scores'].append(s.balance_score)
            ex['stability_scores'].append(s.stability_score)
            ex['rom_scores'].append(s.rom_score)
            ex['tracking_qualities'].append(s.tracking_quality)

        for ex in exercises.values():
            scores = ex.pop('scores')
            symm = ex.pop('symmetry_scores')
            bal = ex.pop('balance_scores')
            stab = ex.pop('stability_scores')
            rom = ex.pop('rom_scores')
            tq = ex.pop('tracking_qualities')

            count = len(scores)
            ex['average_score'] = round(sum(scores) / count, 1) if count else 0.0
            ex['average_symmetry'] = round(sum(symm) / count, 1) if count else 100.0
            ex['average_balance'] = round(sum(bal) / count, 1) if count else 100.0
            ex['average_stability'] = round(sum(stab) / count, 1) if count else 100.0
            ex['average_rom'] = round(sum(rom) / count, 1) if count else 100.0
            ex['average_tracking_quality'] = round(sum(tq) / count, 1) if count else 100.0
            ex['best_score'] = round(ex['best_score'], 1)
            ex['total_duration'] = round(ex['total_duration'], 1)
            ex['total_hold_time'] = round(ex['total_hold_time'], 1)

        return {
            'user_id': str(user_id),
            'exercises': exercises
        }

    @staticmethod
    def get_user_trends(user_id: Any) -> Dict[str, Any]:
        sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        chronological_sessions = list(reversed(sessions[:10]))
        scores = [s.accuracy for s in chronological_sessions]
        symmetries = [s.symmetry_score for s in chronological_sessions]
        stabilities = [s.stability_score for s in chronological_sessions]
        roms = [s.rom_score for s in chronological_sessions]

        def compute_trend_dict(values, name):
            direction = "INSUFFICIENT_DATA"
            pct_change = 0.0
            if len(values) >= 3:
                first = values[0]
                last = values[-1]
                pct_change = ((last - first) / first * 100.0) if first > 0 else 0.0
                if pct_change > 2.0:
                    direction = "IMPROVING"
                elif pct_change < -2.0:
                    direction = "DECLINING"
                else:
                    direction = "STABLE"
            return {
                'metric_name': name,
                'trend_direction': direction,
                'observation_count': len(values),
                'percentage_change': round(pct_change, 2),
                'sample_values': values
            }

        return {
            'user_id': str(user_id),
            'overall_score_trend': compute_trend_dict(scores, 'overall_score'),
            'symmetry_trend': compute_trend_dict(symmetries, 'symmetry_score'),
            'stability_trend': compute_trend_dict(stabilities, 'stability_score'),
            'rom_trend': compute_trend_dict(roms, 'rom_score')
        }

    @staticmethod
    def get_personal_records(user_id: Any) -> List[Dict[str, Any]]:
        sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        if not sessions:
            return []

        best_score_sess = max(sessions, key=lambda s: s.accuracy)
        longest_sess = max(sessions, key=lambda s: s.duration)
        best_symm_sess = max(sessions, key=lambda s: s.symmetry_score)
        best_bal_sess = max(sessions, key=lambda s: s.balance_score)
        best_stab_sess = max(sessions, key=lambda s: s.stability_score)
        best_rom_sess = max(sessions, key=lambda s: s.rom_score)
        most_reps_sess = max(sessions, key=lambda s: s.reps)

        records = [
            {
                'record_type': 'Highest Score',
                'exercise_id': best_score_sess.pose_label,
                'value': round(best_score_sess.accuracy, 1),
                'unit': 'points'
            },
            {
                'record_type': 'Longest Hold / Duration',
                'exercise_id': longest_sess.pose_label,
                'value': round(longest_sess.duration, 1),
                'unit': 'seconds'
            },
            {
                'record_type': 'Best Symmetry',
                'exercise_id': best_symm_sess.pose_label,
                'value': round(best_symm_sess.symmetry_score, 1),
                'unit': '%'
            },
            {
                'record_type': 'Best Balance',
                'exercise_id': best_bal_sess.pose_label,
                'value': round(best_bal_sess.balance_score, 1),
                'unit': '%'
            },
            {
                'record_type': 'Best Stability',
                'exercise_id': best_stab_sess.pose_label,
                'value': round(best_stab_sess.stability_score, 1),
                'unit': '%'
            },
            {
                'record_type': 'Best ROM',
                'exercise_id': best_rom_sess.pose_label,
                'value': round(best_rom_sess.rom_score, 1),
                'unit': '%'
            }
        ]

        if most_reps_sess.reps > 0:
            records.append({
                'record_type': 'Most Repetitions',
                'exercise_id': most_reps_sess.pose_label,
                'value': float(most_reps_sess.reps),
                'unit': 'reps'
            })

        return records
