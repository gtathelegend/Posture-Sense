"""
AnalyticsRepository
===================
Data access layer for user progress analytics, trends, exercise histories, and personal records.
Scoped strictly to user_id for strict user data isolation.
Only aggregates non-NULL metrics; returns None for unavailable metrics.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from backend.app.repositories.session_repository import SessionRepository


def filter_sessions_by_timeframe(sessions: List[Any], timeframe: str) -> List[Any]:
    """Helper function to filter sessions by timeframe ('7d', '30d', 'all')."""
    if timeframe == 'all' or not timeframe:
        return sessions

    days = 7 if timeframe == '7d' else (30 if timeframe == '30d' else None)
    if days is None:
        return sessions

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

    filtered = []
    for s in sessions:
        ts = getattr(s, 'timestamp', None)
        if ts is None:
            continue
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except ValueError:
                continue
        if hasattr(ts, 'tzinfo') and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= cutoff:
            filtered.append(s)
    return filtered


class AnalyticsRepository:
    """
    Data repository for user-level progress analytics.
    Enforces strict user isolation.
    """

    @staticmethod
    def get_user_analytics_summary(user_id: Any, timeframe: str = 'all') -> Dict[str, Any]:
        all_sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        sessions = filter_sessions_by_timeframe(all_sessions, timeframe)
        total_sessions = len(sessions)
        total_duration = sum(s.duration for s in sessions)
        avg_accuracy = sum(s.accuracy for s in sessions) / total_sessions if total_sessions > 0 else 0.0

        symm_vals = [s.symmetry_score for s in sessions if getattr(s, 'symmetry_score', None) is not None]
        bal_vals = [s.balance_score for s in sessions if getattr(s, 'balance_score', None) is not None]
        stab_vals = [s.stability_score for s in sessions if getattr(s, 'stability_score', None) is not None]
        rom_vals = [s.rom_score for s in sessions if getattr(s, 'rom_score', None) is not None]
        tq_vals = [s.tracking_quality for s in sessions if getattr(s, 'tracking_quality', None) is not None]

        avg_symmetry = round(sum(symm_vals) / len(symm_vals), 1) if symm_vals else None
        avg_balance = round(sum(bal_vals) / len(bal_vals), 1) if bal_vals else None
        avg_stability = round(sum(stab_vals) / len(stab_vals), 1) if stab_vals else None
        avg_rom = round(sum(rom_vals) / len(rom_vals), 1) if rom_vals else None
        avg_tracking_quality = round(sum(tq_vals) / len(tq_vals), 1) if tq_vals else None

        total_reps = sum(s.reps for s in sessions)
        total_hold_time = sum(s.hold_time for s in sessions)

        exercise_counts = {}
        for session in sessions:
            label = session.pose_label
            exercise_counts[label] = exercise_counts.get(label, 0) + 1

        recent_sessions = [s.to_dict() for s in sessions[:10]]

        return {
            'user_id': str(user_id),
            'timeframe': timeframe,
            'total_sessions': total_sessions,
            'total_duration': round(total_duration, 1),
            'overall_average_score': round(avg_accuracy, 1),
            'biomechanics': {
                'average_symmetry': avg_symmetry,
                'average_balance': avg_balance,
                'average_stability': avg_stability,
                'average_rom': avg_rom,
                'average_tracking_quality': avg_tracking_quality
            },
            'totals': {
                'total_reps': total_reps,
                'total_hold_time': round(total_hold_time, 1)
            },
            'exercise_counts': exercise_counts,
            'recent_sessions': recent_sessions
        }

    @staticmethod
    def get_user_progress(user_id: Any, timeframe: str = 'all') -> Dict[str, Any]:
        summary = AnalyticsRepository.get_user_analytics_summary(user_id, timeframe=timeframe)
        all_sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        sessions = filter_sessions_by_timeframe(all_sessions, timeframe)

        scores = [s.accuracy for s in sessions]
        improvement_pct = 0.0
        if len(scores) >= 2 and scores[-1] > 0:
            first_score = scores[-1]
            latest_score = scores[0]
            improvement_pct = ((latest_score - first_score) / first_score) * 100.0

        latest = sessions[0] if sessions else None
        prev = sessions[1] if len(sessions) >= 2 else None

        def safe_delta(curr, previous):
            if curr is None or previous is None:
                return None
            return round(curr - previous, 1)

        session_comparison = {}
        if latest:
            session_comparison = {
                'latest_session': latest.to_dict(),
                'previous_session': prev.to_dict() if prev else None,
                'score_delta': round(latest.accuracy - prev.accuracy, 1) if prev else 0.0,
                'symmetry_delta': safe_delta(latest.symmetry_score, prev.symmetry_score) if prev else None,
                'balance_delta': safe_delta(latest.balance_score, prev.balance_score) if prev else None,
                'stability_delta': safe_delta(latest.stability_score, prev.stability_score) if prev else None,
                'rom_delta': safe_delta(latest.rom_score, prev.rom_score) if prev else None,
            }

        return {
            'user_id': str(user_id),
            'timeframe': timeframe,
            'total_sessions': summary['total_sessions'],
            'latest_score': scores[0] if scores else 0.0,
            'overall_average': summary['overall_average_score'],
            'improvement_percentage': round(improvement_pct, 1),
            'biomechanics': summary['biomechanics'],
            'totals': summary['totals'],
            'session_comparison': session_comparison
        }

    @staticmethod
    def get_exercise_history(user_id: Any, timeframe: str = 'all') -> Dict[str, Any]:
        all_sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        sessions = filter_sessions_by_timeframe(all_sessions, timeframe)
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
            if s.symmetry_score is not None:
                ex['symmetry_scores'].append(s.symmetry_score)
            if s.balance_score is not None:
                ex['balance_scores'].append(s.balance_score)
            if s.stability_score is not None:
                ex['stability_scores'].append(s.stability_score)
            if s.rom_score is not None:
                ex['rom_scores'].append(s.rom_score)
            if s.tracking_quality is not None:
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
            ex['average_symmetry'] = round(sum(symm) / len(symm), 1) if symm else None
            ex['average_balance'] = round(sum(bal) / len(bal), 1) if bal else None
            ex['average_stability'] = round(sum(stab) / len(stab), 1) if stab else None
            ex['average_rom'] = round(sum(rom) / len(rom), 1) if rom else None
            ex['average_tracking_quality'] = round(sum(tq) / len(tq), 1) if tq else None
            ex['best_score'] = round(ex['best_score'], 1)
            ex['total_duration'] = round(ex['total_duration'], 1)
            ex['total_hold_time'] = round(ex['total_hold_time'], 1)

        return {
            'user_id': str(user_id),
            'timeframe': timeframe,
            'exercises': exercises
        }

    @staticmethod
    def get_user_trends(user_id: Any, timeframe: str = 'all') -> Dict[str, Any]:
        all_sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        sessions = filter_sessions_by_timeframe(all_sessions, timeframe)
        chronological = list(reversed(sessions[:10]))

        scores = [s.accuracy for s in chronological if getattr(s, 'accuracy', None) is not None]
        symmetries = [s.symmetry_score for s in chronological if getattr(s, 'symmetry_score', None) is not None]
        stabilities = [s.stability_score for s in chronological if getattr(s, 'stability_score', None) is not None]
        roms = [s.rom_score for s in chronological if getattr(s, 'rom_score', None) is not None]

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
            'timeframe': timeframe,
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

        def format_date(s):
            ts = getattr(s, 'timestamp', '')
            if hasattr(ts, 'strftime'):
                return ts.strftime('%b %d, %Y')
            return str(ts)[:10] if ts else 'Recent'

        records = []

        # 1. Highest Score
        score_sessions = [s for s in sessions if getattr(s, 'accuracy', None) is not None]
        if score_sessions:
            best_score = max(score_sessions, key=lambda s: s.accuracy)
            records.append({
                'record_type': 'Highest Score',
                'exercise_id': best_score.pose_label,
                'value': round(best_score.accuracy, 1),
                'unit': 'points'
            })

        # 2. Longest Hold / Duration
        hold_sessions = [s for s in sessions if getattr(s, 'duration', 0.0) > 0]
        if hold_sessions:
            longest = max(hold_sessions, key=lambda s: s.duration)
            records.append({
                'record_type': 'Longest Hold / Duration',
                'exercise_id': longest.pose_label,
                'value': round(longest.duration, 1),
                'unit': 'seconds'
            })


        # 3. Best Symmetry
        symm_sessions = [s for s in sessions if getattr(s, 'symmetry_score', None) is not None]
        if symm_sessions:
            best_symm = max(symm_sessions, key=lambda s: s.symmetry_score)
            records.append({
                'record_type': 'Best Symmetry',
                'exercise_id': best_symm.pose_label,
                'value': round(best_symm.symmetry_score, 1),
                'unit': '%'
            })

        # 4. Best Balance
        bal_sessions = [s for s in sessions if getattr(s, 'balance_score', None) is not None]
        if bal_sessions:
            best_bal = max(bal_sessions, key=lambda s: s.balance_score)
            records.append({
                'record_type': 'Best Balance',
                'exercise_id': best_bal.pose_label,
                'value': round(best_bal.balance_score, 1),
                'unit': '%'
            })

        # 5. Best Stability
        stab_sessions = [s for s in sessions if getattr(s, 'stability_score', None) is not None]
        if stab_sessions:
            best_stab = max(stab_sessions, key=lambda s: s.stability_score)
            records.append({
                'record_type': 'Best Stability',
                'exercise_id': best_stab.pose_label,
                'value': round(best_stab.stability_score, 1),
                'unit': '%'
            })

        # 6. Best ROM
        rom_sessions = [s for s in sessions if getattr(s, 'rom_score', None) is not None]
        if rom_sessions:
            best_rom = max(rom_sessions, key=lambda s: s.rom_score)
            records.append({
                'record_type': 'Best ROM',
                'exercise_id': best_rom.pose_label,
                'value': round(best_rom.rom_score, 1),
                'unit': '%'
            })

        # 7. Most Repetitions
        rep_sessions = [s for s in sessions if getattr(s, 'reps', 0) > 0]
        if rep_sessions:
            most_reps = max(rep_sessions, key=lambda s: s.reps)
            records.append({
                'record_type': 'Most Repetitions',
                'exercise_id': most_reps.pose_label,
                'value': float(most_reps.reps),
                'unit': 'reps'
            })

        return records
