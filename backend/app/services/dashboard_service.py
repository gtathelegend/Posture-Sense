"""
DashboardService
================
Service layer for compiling Dashboard V2 analytics, timeframe trends, biomechanics aggregates,
deterministic insights, pose performance metrics, personal records, and session comparisons.
Enforces strict user isolation.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from backend.app.repositories.session_repository import SessionRepository


class DashboardService:
    @staticmethod
    def get_user_dashboard_data(user_id: Any) -> Dict[str, Any]:
        """
        Backwards-compatible dashboard stats loader.
        """
        return DashboardService.get_user_dashboard_overview(user_id, timeframe='all')

    @staticmethod
    def get_user_dashboard_overview(user_id: Any, timeframe: str = '30d') -> Dict[str, Any]:
        """
        Full Dashboard V2 overview aggregator with timeframe filtering and deterministic insights.
        """
        all_sessions = SessionRepository.fetch_sessions_by_user_id(user_id)
        total_sessions_all = len(all_sessions)

        # 1. Date / Timeframe Filtering
        filtered_sessions = DashboardService._filter_by_timeframe(all_sessions, timeframe)
        total_sessions = len(filtered_sessions)
        total_duration = sum(s.duration for s in filtered_sessions)
        avg_accuracy = sum(s.accuracy for s in filtered_sessions) / total_sessions if total_sessions > 0 else 0.0

        # 2. Practice Streak (Consecutive calendar days)
        streak_days = DashboardService._calculate_streak_days(all_sessions)

        # 3. 7-Day Score Delta
        seven_day_delta = DashboardService._calculate_seven_day_delta(all_sessions)

        # 4. Biomechanics Aggregation (Filter out None / NULL metrics)
        symm_vals = [s.symmetry_score for s in filtered_sessions if getattr(s, 'symmetry_score', None) is not None]
        bal_vals = [s.balance_score for s in filtered_sessions if getattr(s, 'balance_score', None) is not None]
        stab_vals = [s.stability_score for s in filtered_sessions if getattr(s, 'stability_score', None) is not None]
        rom_vals = [s.rom_score for s in filtered_sessions if getattr(s, 'rom_score', None) is not None]
        tq_vals = [s.tracking_quality for s in filtered_sessions if getattr(s, 'tracking_quality', None) is not None]

        avg_symmetry = round(sum(symm_vals) / len(symm_vals), 1) if symm_vals else None
        avg_balance = round(sum(bal_vals) / len(bal_vals), 1) if bal_vals else None
        avg_stability = round(sum(stab_vals) / len(stab_vals), 1) if stab_vals else None
        avg_rom = round(sum(rom_vals) / len(rom_vals), 1) if rom_vals else None
        avg_tracking_quality = round(sum(tq_vals) / len(tq_vals), 1) if tq_vals else None

        total_reps = sum(s.reps for s in filtered_sessions)
        total_hold_time = sum(s.hold_time for s in filtered_sessions)

        tracking_quality_status = DashboardService._get_tracking_quality_status(avg_tracking_quality) if avg_tracking_quality is not None else 'Not Available'


        # 5. Score Trend Line & Points (Chronological)
        chronological = list(reversed(filtered_sessions))
        trend_points = []
        for s in chronological:
            ts_str = s.timestamp.strftime('%Y-%m-%d') if hasattr(s.timestamp, 'strftime') else str(s.timestamp)[:10]
            trend_points.append({
                'session_id': getattr(s, 'id', 'sess_unknown'),
                'date': ts_str,
                'score': round(s.accuracy, 1),
                'duration': round(s.duration, 1),
                'pose_label': s.pose_label
            })

        slope, trend_direction = DashboardService._calculate_trend_slope(chronological)

        # 6. Pose Performance Cards & Strongest/Weakest Pose
        pose_counts = {}
        pose_groups = {}
        for s in filtered_sessions:
            label = s.pose_label
            pose_counts[label] = pose_counts.get(label, 0) + 1
            if label not in pose_groups:
                pose_groups[label] = []
            pose_groups[label].append(s)

        pose_cards = []
        for label, p_sessions in pose_groups.items():
            count = len(p_sessions)
            avg_score = sum(s.accuracy for s in p_sessions) / count
            best_score = max(s.accuracy for s in p_sessions)
            avg_hold = sum(s.hold_time for s in p_sessions) / count
            best_hold = max(s.hold_time for s in p_sessions)

            p_symms = [s.symmetry_score for s in p_sessions if getattr(s, 'symmetry_score', None) is not None]
            best_symm = max(p_symms) if p_symms else None

            p_roms = [s.rom_score for s in p_sessions if getattr(s, 'rom_score', None) is not None]
            best_rom = max(p_roms) if p_roms else None

            pose_cards.append({
                'pose_label': label,
                'sessions': count,
                'avg_score': round(avg_score, 1),
                'best_score': round(best_score, 1),
                'avg_hold': round(avg_hold, 1),
                'best_hold': round(best_hold, 1),
                'best_symmetry': round(best_symm, 1) if best_symm is not None else None,
                'best_rom': round(best_rom, 1) if best_rom is not None else None
            })


        pose_cards.sort(key=lambda p: p['avg_score'], reverse=True)
        strongest_pose = pose_cards[0] if len(pose_cards) >= 2 else None
        weakest_pose = pose_cards[-1] if len(pose_cards) >= 2 else None

        # 7. Personal Records Grid
        personal_records = DashboardService._calculate_personal_records(all_sessions)

        # 8. Deterministic Insights Engine (Rules 1 - 5)
        insights = DashboardService._evaluate_deterministic_insights(
            all_sessions=all_sessions,
            filtered_sessions=filtered_sessions,
            streak_days=streak_days,
            pose_groups=pose_groups
        )

        # 9. Session Comparison (Latest vs Previous)
        session_comparison = DashboardService._build_session_comparison(all_sessions)

        # 10. Recent Sessions List (Up to 20)
        recent_sessions = []
        for s in all_sessions[:20]:
            is_legacy = DashboardService._is_legacy_session(s)
            ts_str = s.timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(s.timestamp, 'strftime') else str(s.timestamp)
            recent_sessions.append({
                'session_id': getattr(s, 'id', 'sess_unknown'),
                'timestamp': ts_str,
                'pose_label': s.pose_label,
                'duration': round(s.duration, 1),
                'accuracy': round(s.accuracy, 1),
                'reps': s.reps,
                'symmetry_score': round(s.symmetry_score, 1) if s.symmetry_score is not None else None,
                'balance_score': round(s.balance_score, 1) if s.balance_score is not None else None,
                'stability_score': round(s.stability_score, 1) if s.stability_score is not None else None,
                'rom_score': round(s.rom_score, 1) if s.rom_score is not None else None,
                'hold_time': round(s.hold_time, 1),
                'tracking_quality': round(s.tracking_quality, 1) if s.tracking_quality is not None else None,
                'failed_rules': s.failed_rules,
                'is_legacy': is_legacy
            })

        return {
            'timeframe': timeframe,
            'sessions': all_sessions,
            'total_sessions': total_sessions,
            'total_sessions_all': total_sessions_all,
            'total_duration': round(total_duration, 1),
            'avg_accuracy': round(avg_accuracy, 1),
            'overall_average_score': round(avg_accuracy, 1),
            'streak_days': streak_days,
            'seven_day_delta': round(seven_day_delta, 1) if seven_day_delta is not None else None,
            'biomechanics': {
                'symmetry': round(avg_symmetry, 1) if avg_symmetry is not None else None,
                'balance': round(avg_balance, 1) if avg_balance is not None else None,
                'stability': round(avg_stability, 1) if avg_stability is not None else None,
                'rom': round(avg_rom, 1) if avg_rom is not None else None,
                'tracking_quality': round(avg_tracking_quality, 1) if avg_tracking_quality is not None else None,
                'tracking_status': tracking_quality_status
            },

            'totals': {
                'reps': total_reps,
                'hold_time': round(total_hold_time, 1)
            },
            'trend': {
                'points': trend_points,
                'slope': slope,
                'direction': trend_direction,
                'observation_count': len(trend_points)
            },
            'pose_counts': pose_counts,
            'pose_cards': pose_cards,
            'strongest_pose': strongest_pose,
            'weakest_pose': weakest_pose,
            'personal_records': personal_records,
            'insights': insights,
            'session_comparison': session_comparison,
            'recent_sessions': recent_sessions
        }

    # ---------------------------------------------------------------------------
    # Private Helper Calculations
    # ---------------------------------------------------------------------------

    @staticmethod
    def _is_legacy_session(session: Any) -> bool:
        """
        A session is legacy if analytics metrics are None/NULL or default fallbacks without real telemetry.
        """
        symm = getattr(session, 'symmetry_score', None)
        bal = getattr(session, 'balance_score', None)
        stab = getattr(session, 'stability_score', None)
        reps = getattr(session, 'reps', 0)
        failed = getattr(session, 'failed_rules', [])

        if symm is None or bal is None or stab is None:
            return True
        return (symm == 100.0 and bal == 100.0 and stab == 100.0 and reps == 0 and not failed)


    @staticmethod
    def _filter_by_timeframe(sessions: List[Any], timeframe: str) -> List[Any]:
        if timeframe not in ['7d', '30d'] or not sessions:
            return sessions

        days = 7 if timeframe == '7d' else 30
        now = datetime.now(timezone.utc)

        filtered = []
        for s in sessions:
            ts = s.timestamp
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                except ValueError:
                    filtered.append(s)
                    continue

            if hasattr(ts, 'tzinfo') and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            if now - ts <= timedelta(days=days):
                filtered.append(s)

        return filtered if filtered else sessions

    @staticmethod
    def _calculate_streak_days(sessions: List[Any]) -> int:
        if not sessions:
            return 0

        unique_dates = set()
        for s in sessions:
            ts = s.timestamp
            if isinstance(ts, str):
                d_str = ts[:10]
            elif hasattr(ts, 'strftime'):
                d_str = ts.strftime('%Y-%m-%d')
            else:
                d_str = str(ts)[:10]
            unique_dates.add(d_str)

        sorted_dates = sorted(list(unique_dates), reverse=True)
        if not sorted_dates:
            return 0

        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)
        latest_date = datetime.strptime(sorted_dates[0], '%Y-%m-%d').date()

        if latest_date not in [today, yesterday]:
            return 0

        streak = 1
        curr = latest_date
        for next_date_str in sorted_dates[1:]:
            next_date = datetime.strptime(next_date_str, '%Y-%m-%d').date()
            if curr - next_date == timedelta(days=1):
                streak += 1
                curr = next_date
            elif curr == next_date:
                continue
            else:
                break
        return streak

    @staticmethod
    def _calculate_seven_day_delta(sessions: List[Any]) -> Optional[float]:
        if not sessions:
            return None

        now = datetime.now(timezone.utc)
        curr_7d = []
        prev_7d = []

        for s in sessions:
            ts = s.timestamp
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                except ValueError:
                    continue
            if hasattr(ts, 'tzinfo') and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            age = now - ts
            if age <= timedelta(days=7):
                curr_7d.append(s.accuracy)
            elif timedelta(days=7) < age <= timedelta(days=14):
                prev_7d.append(s.accuracy)

        if curr_7d and prev_7d:
            avg_curr = sum(curr_7d) / len(curr_7d)
            avg_prev = sum(prev_7d) / len(prev_7d)
            return avg_curr - avg_prev
        return None

    @staticmethod
    def _get_tracking_quality_status(score: float) -> str:
        if score >= 90.0:
            return 'Excellent'
        if score >= 75.0:
            return 'Good'
        if score >= 50.0:
            return 'Fair'
        return 'Low'

    @staticmethod
    def _calculate_trend_slope(chronological_sessions: List[Any]) -> tuple[Optional[float], str]:
        n = len(chronological_sessions)
        if n < 3:
            return None, 'INSUFFICIENT_DATA'

        first_score = chronological_sessions[0].accuracy
        last_score = chronological_sessions[-1].accuracy
        pct_change = ((last_score - first_score) / first_score * 100.0) if first_score > 0 else 0.0

        if pct_change > 2.0:
            direction = 'IMPROVING'
        elif pct_change < -2.0:
            direction = 'DECLINING'
        else:
            direction = 'STABLE'

        return round(pct_change, 1), direction

    @staticmethod
    def _calculate_personal_records(sessions: List[Any]) -> List[Dict[str, Any]]:
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
                'id': 'rec_score',
                'record_type': 'Highest Score',
                'pose_label': best_score.pose_label,
                'value': round(best_score.accuracy, 1),
                'unit': 'pts',
                'date': format_date(best_score)
            })

        # 2. Longest Hold
        hold_sessions = [s for s in sessions if getattr(s, 'hold_time', 0.0) > 0 or getattr(s, 'duration', 0.0) > 0]
        if hold_sessions:
            longest_hold = max(hold_sessions, key=lambda s: s.hold_time if s.hold_time > 0 else s.duration)
            records.append({
                'id': 'rec_hold',
                'record_type': 'Longest Hold',
                'pose_label': longest_hold.pose_label,
                'value': round(longest_hold.hold_time if longest_hold.hold_time > 0 else longest_hold.duration, 1),
                'unit': 's',
                'date': format_date(longest_hold)
            })

        # 3. Best Symmetry
        symm_sessions = [s for s in sessions if getattr(s, 'symmetry_score', None) is not None]
        if symm_sessions:
            best_symm = max(symm_sessions, key=lambda s: s.symmetry_score)
            records.append({
                'id': 'rec_symm',
                'record_type': 'Best Symmetry',
                'pose_label': best_symm.pose_label,
                'value': round(best_symm.symmetry_score, 1),
                'unit': '%',
                'date': format_date(best_symm)
            })

        # 4. Best Balance
        bal_sessions = [s for s in sessions if getattr(s, 'balance_score', None) is not None]
        if bal_sessions:
            best_bal = max(bal_sessions, key=lambda s: s.balance_score)
            records.append({
                'id': 'rec_bal',
                'record_type': 'Best Balance',
                'pose_label': best_bal.pose_label,
                'value': round(best_bal.balance_score, 1),
                'unit': '%',
                'date': format_date(best_bal)
            })

        # 5. Best ROM
        rom_sessions = [s for s in sessions if getattr(s, 'rom_score', None) is not None]
        if rom_sessions:
            best_rom = max(rom_sessions, key=lambda s: s.rom_score)
            records.append({
                'id': 'rec_rom',
                'record_type': 'Best ROM',
                'pose_label': best_rom.pose_label,
                'value': round(best_rom.rom_score, 1),
                'unit': '%',
                'date': format_date(best_rom)
            })

        # 6. Most Repetitions
        rep_sessions = [s for s in sessions if getattr(s, 'reps', 0) > 0]
        if rep_sessions:
            most_reps = max(rep_sessions, key=lambda s: s.reps)
            records.append({
                'id': 'rec_reps',
                'record_type': 'Most Repetitions',
                'pose_label': most_reps.pose_label,
                'value': int(most_reps.reps),
                'unit': 'reps',
                'date': format_date(most_reps)
            })

        return records


    @staticmethod
    def _evaluate_deterministic_insights(
        all_sessions: List[Any],
        filtered_sessions: List[Any],
        streak_days: int,
        pose_groups: Dict[str, List[Any]]
    ) -> List[Dict[str, Any]]:
        insights = []

        if len(all_sessions) < 2:
            insights.append({
                'id': 'insight_empty',
                'title': 'Building Baseline',
                'message': 'Complete 2 more sessions to establish a progress trend.',
                'type': 'info',
                'icon': '💡'
            })
            return insights

        # Rule 1: Score Improvement >= 10% for a pose with >= 3 sessions
        for pose, p_sessions in pose_groups.items():
            if len(p_sessions) >= 3:
                sorted_p = sorted(p_sessions, key=lambda s: getattr(s, 'timestamp', ''))
                oldest_score = sorted_p[0].accuracy
                newest_score = sorted_p[-1].accuracy
                if oldest_score > 0:
                    pct_imp = ((newest_score - oldest_score) / oldest_score) * 100.0
                    if pct_imp >= 10.0:
                        insights.append({
                            'id': f'insight_score_imp_{pose}',
                            'title': 'Pose Mastered',
                            'message': f'Your {pose} score improved {round(pct_imp, 1)}% over your last {len(p_sessions)} sessions.',
                            'type': 'achievement',
                            'icon': '📈'
                        })
                        break

        # Rule 2: Symmetry Improvement >= 5%
        non_legacy = [s for s in filtered_sessions if not DashboardService._is_legacy_session(s)]
        if len(non_legacy) >= 4:
            half = len(non_legacy) // 2
            prev_symm = sum(s.symmetry_score for s in non_legacy[:half]) / half
            curr_symm = sum(s.symmetry_score for s in non_legacy[half:]) / (len(non_legacy) - half)
            if prev_symm > 0 and (curr_symm - prev_symm) >= 5.0:
                insights.append({
                    'id': 'insight_symm_imp',
                    'title': 'Symmetry Gains',
                    'message': f'Your postural symmetry improved {round(curr_symm - prev_symm, 1)}%.',
                    'type': 'achievement',
                    'icon': '⚖️'
                })

        # Rule 3: Hold PR (Latest session hold time > previous best hold for pose)
        latest = all_sessions[0]
        if latest.hold_time > 0 and len(all_sessions) >= 2:
            prev_holds = [s.hold_time for s in all_sessions[1:] if s.pose_label == latest.pose_label]
            if prev_holds and latest.hold_time > max(prev_holds):
                insights.append({
                    'id': 'insight_hold_pr',
                    'title': 'New Hold PR',
                    'message': f'New record: {latest.pose_label} hold for {round(latest.hold_time, 1)}s.',
                    'type': 'record',
                    'icon': '⏱️'
                })

        # Rule 4: Consistency Benchmark (>= 7 of last 10 sessions score >= 80)
        recent_10 = all_sessions[:10]
        high_count = sum(1 for s in recent_10 if s.accuracy >= 80.0)
        if len(recent_10) >= 5 and high_count >= 7:
            insights.append({
                'id': 'insight_consistency',
                'title': 'Great Consistency',
                'message': f'Great consistency — {high_count} of your last {len(recent_10)} sessions scored 80+.',
                'type': 'habit',
                'icon': '🎯'
            })

        # Rule 5: Streak Milestone
        if streak_days in [3, 7, 14, 30, 60, 100]:
            insights.append({
                'id': f'insight_streak_{streak_days}',
                'title': 'Streak Milestone',
                'message': f"You're on a {streak_days}-day practice streak!",
                'type': 'habit',
                'icon': '🔥'
            })

        return insights

    @staticmethod
    def _build_session_comparison(sessions: List[Any]) -> Dict[str, Any]:
        if not sessions:
            return {'has_comparison': False}

        latest = sessions[0]
        prev = sessions[1] if len(sessions) >= 2 else None

        if not prev:
            return {
                'has_comparison': False,
                'latest_session': latest.to_dict(),
                'message': 'First recorded session — no comparison available yet.'
            }

        def comp_metric(curr_val, prev_val, higher_is_better=True):
            if curr_val is None or prev_val is None:
                return {
                    'prev': round(prev_val, 1) if prev_val is not None else None,
                    'latest': round(curr_val, 1) if curr_val is not None else None,
                    'delta': 'N/A',
                    'semantic': 'neutral'
                }
            delta = round(curr_val - prev_val, 1)
            if delta > 0:
                semantic = 'positive' if higher_is_better else 'negative'
            elif delta < 0:
                semantic = 'negative' if higher_is_better else 'positive'
            else:
                semantic = 'neutral'
            return {
                'prev': round(prev_val, 1),
                'latest': round(curr_val, 1),
                'delta': f'+{delta}' if delta > 0 else str(delta),
                'semantic': semantic
            }


        return {
            'has_comparison': True,
            'latest_session': latest.to_dict(),
            'previous_session': prev.to_dict(),
            'metrics': {
                'overall_score': comp_metric(latest.accuracy, prev.accuracy),
                'symmetry': comp_metric(latest.symmetry_score, prev.symmetry_score),
                'balance': comp_metric(latest.balance_score, prev.balance_score),
                'stability': comp_metric(latest.stability_score, prev.stability_score),
                'rom': comp_metric(latest.rom_score, prev.rom_score),
                'hold_time': comp_metric(latest.hold_time, prev.hold_time),
                'reps': comp_metric(float(latest.reps), float(prev.reps)),
                'tracking_quality': comp_metric(latest.tracking_quality, prev.tracking_quality)
            }
        }
