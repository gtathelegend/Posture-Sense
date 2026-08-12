"""
AnalyticsEngine
===============
Production-grade Analytics & User Progress Engine for PostureSense v2.

Priority    : 10
Dependencies: feedback_engine, scoring_engine, movement_engine, pose_rule_engine, biomechanics_engine
Subscribes  : score.session_completed  (ScoreReport / session summary)
              score.exercise_completed (ScoreReport)
              score.rep_completed       (ScoreReport / rep data)
              feedback.session_summary (FeedbackSessionSummary)
              exercise.completed       (ExerciseResult)
Publishes   : analytics.session_completed
              analytics.updated
              analytics.trend_detected
              analytics.record_broken
              analytics.progress_updated

DO NOT process camera frames or raw landmarks.
DO NOT generate coaching advice or feedback.
DO NOT calculate or alter scores.
DO NOT use ML for trend classification.
DO NOT persist raw video or landmark streams.
"""

from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from shared.engines.interfaces import AnalyticsEngineInterface
from shared.events.event_bus import EventBus
from shared.types.enums import EngineStatus
from shared.contracts.scoring import ScoreReport
from shared.contracts.analytics import (
    AnalyticsSnapshot,
    SessionAnalytics,
    ExerciseAnalytics,
    TrendMetric,
    PersonalRecord,
    AnalyticsSummary,
)


class AnalyticsEngine(AnalyticsEngineInterface):
    """
    Analytics & User Progress Engine transforms completed posture and exercise assessments
    into longitudinal progress data, trends, personal records, consistency stats, and comparisons.
    """

    def __init__(self, name: str = "AnalyticsEngine", event_bus: Optional[EventBus] = None):
        super().__init__(name=name, event_bus=event_bus)
        self.version = "2.0.0"
        self.priority = 10
        self.dependencies = [
            "feedback_engine",
            "scoring_engine",
            "movement_engine",
            "pose_rule_engine",
            "biomechanics_engine"
        ]

        self.config: Dict[str, Any] = {
            "version": "2.0.0",
            "settings": {
                "min_trend_observations": 3,
                "improvement_threshold_pct": 2.0,
                "decline_threshold_pct": -2.0,
                "min_quality_confidence": 0.4
            }
        }

        # Internal state store (scoped by user_id)
        # user_id -> List[SessionAnalytics]
        self._user_sessions: Dict[str, List[SessionAnalytics]] = {}
        # user_id -> Dict[exercise_id, ExerciseAnalytics]
        self._user_exercises: Dict[str, Dict[str, ExerciseAnalytics]] = {}
        # user_id -> Dict[record_type, PersonalRecord]
        self._user_records: Dict[str, Dict[str, PersonalRecord]] = {}

        self._active_user_id: str = "anonymous"
        self._sessions_processed_count: int = 0
        self._records_broken_count: int = 0
        self._processing_time_ms: float = 0.0
        self._last_score_report: Optional[ScoreReport] = None

    def initialize(self, config: Optional[dict] = None) -> bool:
        if config:
            self.config.update(config)

        # Subscribe to high-level completed assessment events
        self.subscribe("score.session_completed", self._on_score_session_completed)
        self.subscribe("score.exercise_completed", self._on_score_exercise_completed)
        self.subscribe("score.rep_completed", self._on_score_rep_completed)
        self.subscribe("feedback.session_summary", self._on_feedback_session_summary)
        self.subscribe("exercise.completed", self._on_exercise_completed)

        self._status = EngineStatus.INITIALIZED
        self.publish("analytics.initialized", self.get_diagnostics())
        return True

    def start(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("analytics.started", self.get_diagnostics())
        return True

    def pause(self) -> bool:
        self._status = EngineStatus.PAUSED
        self.publish("analytics.paused", self.get_diagnostics())
        return True

    def resume(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("analytics.resumed", self.get_diagnostics())
        return True

    def stop(self) -> bool:
        self._status = EngineStatus.STOPPED
        self.publish("analytics.stopped", self.get_diagnostics())
        return True

    def dispose(self) -> bool:
        self._status = EngineStatus.DISPOSED
        self._user_sessions.clear()
        self._user_exercises.clear()
        self._user_records.clear()
        self._last_score_report = None
        self.publish("analytics.disposed", self.get_diagnostics())
        return True

    def set_active_user(self, user_id: str) -> None:
        """Sets active user scope for user data isolation."""
        self._active_user_id = str(user_id) if user_id else "anonymous"

    # ---------------------------------------------------------------------------
    # Event Handlers
    # ---------------------------------------------------------------------------

    def _on_score_session_completed(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        data = event.data if hasattr(event, "data") else event
        self._process_completed_session(data)

    def _on_score_exercise_completed(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        data = event.data if hasattr(event, "data") else event
        if isinstance(data, dict):
            self._last_score_report = ScoreReport.from_dict(data)
        elif isinstance(data, ScoreReport):
            self._last_score_report = data

    def _on_score_rep_completed(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        # Store rep-level scoring telemetry if needed

    def _on_feedback_session_summary(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return

    def _on_exercise_completed(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        data = event.data if hasattr(event, "data") else event
        self._process_completed_session(data)

    # ---------------------------------------------------------------------------
    # Core Processing & Aggregation
    # ---------------------------------------------------------------------------

    def _process_completed_session(self, payload: Any) -> Optional[SessionAnalytics]:
        t0 = time.time()
        user_id = self._active_user_id

        # Extract or build SessionAnalytics
        report = self._last_score_report
        session_id = f"sess_{int(time.time()*1000)}"
        exercise_id = "unknown"
        duration = 0.0
        avg_score = 0.0
        best_score = 0.0
        worst_score = 0.0
        reps = 0
        valid_reps = 0
        invalid_reps = 0
        tracking_quality = 100.0

        if isinstance(payload, dict):
            session_id = str(payload.get("session_id", session_id))
            user_id = str(payload.get("user_id", user_id))
            exercise_id = str(payload.get("exercise_id", exercise_id))
            duration = float(payload.get("duration", duration))
            avg_score = float(payload.get("average_score", payload.get("overall_score", avg_score)))
            reps = int(payload.get("completed_reps", payload.get("total_reps", reps)))

        if report:
            exercise_id = report.exercise_id or exercise_id
            avg_score = report.overall_score if avg_score == 0.0 else avg_score
            best_score = avg_score
            worst_score = avg_score
            if report.rep_scores:
                reps = len(report.rep_scores)
                scores = [r.get("overall_score", 0.0) for r in report.rep_scores]
                if scores:
                    best_score = max(scores)
                    worst_score = min(scores)
                    valid_reps = len([s for s in scores if s >= 60.0])
                    invalid_reps = reps - valid_reps

            comp_tq = report.components.get("tracking_quality", {}).get("score")
            if comp_tq is not None:
                tracking_quality = float(comp_tq)

        # Quality Gate Check (exclude unusable or low-confidence data)
        min_conf = float(self.config.get("settings", {}).get("min_quality_confidence", 0.4))
        if report and (not report.quality_gate_passed or report.score_confidence < min_conf):
            print(f"[AnalyticsEngine] Session {session_id} excluded due to quality gate failure.")
            return None

        # Build SessionAnalytics instance
        session = SessionAnalytics(
            session_id=session_id,
            user_id=user_id,
            duration=duration,
            exercise_id=exercise_id,
            completed_reps=reps,
            valid_reps=valid_reps,
            invalid_reps=invalid_reps,
            average_score=avg_score,
            best_score=best_score,
            worst_score=worst_score,
            tracking_quality=tracking_quality,
            source=self.name
        )

        # Record session in user isolation store
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session)
        self._sessions_processed_count += 1

        # Update Exercise History
        self._update_exercise_analytics(user_id, session, report)

        # Evaluate Personal Records
        self._evaluate_personal_records(user_id, session, report)

        # Calculate Trends & Session Comparisons
        trends = self.compute_trends(user_id)

        self._processing_time_ms = (time.time() - t0) * 1000.0

        # Publish Events
        self.publish("analytics.session_completed", session.to_dict())
        self.publish("analytics.updated", self.get_summary(user_id).to_dict())
        self.publish("analytics.progress_updated", {
            "user_id": user_id,
            "session_id": session_id,
            "overall_score": avg_score,
            "trends_count": len(trends)
        })

        return session

    def _update_exercise_analytics(self, user_id: str, session: SessionAnalytics, report: Optional[ScoreReport]) -> None:
        if user_id not in self._user_exercises:
            self._user_exercises[user_id] = {}

        ex_id = session.exercise_id
        user_exs = self._user_exercises[user_id]

        prev_ex = user_exs.get(ex_id)
        total_sessions = (prev_ex.total_sessions + 1) if prev_ex else 1
        total_reps = (prev_ex.total_repetitions + session.completed_reps) if prev_ex else session.completed_reps

        best_score = max(prev_ex.best_score if prev_ex else 0.0, session.average_score)
        prev_avg_score = prev_ex.average_score if prev_ex else session.average_score
        avg_score = (prev_avg_score * (total_sessions - 1) + session.average_score) / total_sessions

        # Extract ROM, form, stability, symmetry from report components
        comp_rom = float(report.components.get("rom", {}).get("score", 0.0)) if report and "rom" in report.components else 0.0
        comp_form = float(report.components.get("form", {}).get("score", 0.0)) if report and "form" in report.components else 0.0
        comp_stab = float(report.components.get("stability", {}).get("score", 0.0)) if report and "stability" in report.components else 0.0
        comp_symm = float(report.components.get("symmetry", {}).get("score", 0.0)) if report and "symmetry" in report.components else 0.0

        best_rom = max(prev_ex.best_rom if prev_ex else 0.0, comp_rom)
        avg_rom = ( (prev_ex.average_rom * (total_sessions - 1) + comp_rom) / total_sessions ) if prev_ex else comp_rom
        avg_form = ( (prev_ex.average_form * (total_sessions - 1) + comp_form) / total_sessions ) if prev_ex else comp_form
        avg_stab = ( (prev_ex.average_stability * (total_sessions - 1) + comp_stab) / total_sessions ) if prev_ex else comp_stab
        avg_symm = ( (prev_ex.average_symmetry * (total_sessions - 1) + comp_symm) / total_sessions ) if prev_ex else comp_symm

        # Improvement percentage
        improvement_pct = 0.0
        if prev_ex and prev_ex.average_score > 0:
            improvement_pct = ((avg_score - prev_ex.average_score) / prev_ex.average_score) * 100.0

        ex_analytics = ExerciseAnalytics(
            exercise_id=ex_id,
            total_sessions=total_sessions,
            total_repetitions=total_reps,
            best_score=best_score,
            average_score=avg_score,
            best_rom=best_rom,
            average_rom=avg_rom,
            average_stability=avg_stab,
            average_symmetry=avg_symm,
            average_form=avg_form,
            improvement_percentage=improvement_pct,
            source=self.name
        )

        user_exs[ex_id] = ex_analytics

    def _evaluate_personal_records(self, user_id: str, session: SessionAnalytics, report: Optional[ScoreReport]) -> None:
        if user_id not in self._user_records:
            self._user_records[user_id] = {}

        records_map = self._user_records[user_id]

        candidates = [
            ("Highest Score", session.average_score, "points"),
            ("Most Reps", float(session.completed_reps), "reps")
        ]

        if report and "rom" in report.components and report.components["rom"].get("score") is not None:
            candidates.append(("Best ROM", float(report.components["rom"]["score"]), "%"))
        if report and "stability" in report.components and report.components["stability"].get("score") is not None:
            candidates.append(("Best Stability", float(report.components["stability"]["score"]), "%"))
        if report and "symmetry" in report.components and report.components["symmetry"].get("score") is not None:
            candidates.append(("Best Symmetry", float(report.components["symmetry"]["score"]), "%"))

        for r_type, val, unit in candidates:
            prev_rec = records_map.get(r_type)
            prev_val = prev_rec.value if prev_rec else None

            if prev_val is None or val > prev_val:
                new_rec = PersonalRecord(
                    record_type=r_type,
                    exercise_id=session.exercise_id,
                    value=val,
                    unit=unit,
                    previous_value=prev_val,
                    source=self.name
                )
                records_map[r_type] = new_rec
                if prev_val is not None:
                    self._records_broken_count += 1
                    self.publish("analytics.record_broken", new_rec.to_dict())

    # ---------------------------------------------------------------------------
    # Statistical Trend Calculations (Deterministic, No ML)
    # ---------------------------------------------------------------------------

    def compute_trends(self, user_id: str) -> Dict[str, TrendMetric]:
        """
        Calculates deterministic statistical trend direction (IMPROVING, STABLE, DECLINING, INSUFFICIENT_DATA)
        for overall score and key dimensions over user's session history.
        """
        sessions = self._user_sessions.get(user_id, [])
        min_obs = int(self.config.get("settings", {}).get("min_trend_observations", 3))

        trends: Dict[str, TrendMetric] = {}
        scores = [s.average_score for s in sessions]

        trend_dir, slope, pct_change = self._calculate_statistical_trend(scores, min_obs)

        trends["overall_score"] = TrendMetric(
            metric_name="overall_score",
            timeframe="session",
            trend_direction=trend_dir,
            observation_count=len(scores),
            slope=slope,
            percentage_change=pct_change,
            sample_values=scores,
            source=self.name
        )

        if trend_dir != "INSUFFICIENT_DATA":
            self.publish("analytics.trend_detected", trends["overall_score"].to_dict())

        return trends

    def _calculate_statistical_trend(self, values: List[float], min_obs: int) -> Tuple[str, float, float]:
        n = len(values)
        if n < min_obs:
            return ("INSUFFICIENT_DATA", 0.0, 0.0)

        # Baseline & percentage change calculation
        first_val = values[0]
        last_val = values[-1]
        pct_change = ((last_val - first_val) / first_val * 100.0) if first_val > 0 else 0.0

        # Linear regression slope calculation: slope = cov(x,y) / var(x)
        x_mean = (n - 1) / 2.0
        y_mean = sum(values) / float(n)

        num = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(values))
        den = sum((i - x_mean) ** 2 for i in range(n))
        slope = (num / den) if den != 0 else 0.0

        up_thresh = float(self.config.get("settings", {}).get("improvement_threshold_pct", 2.0))
        down_thresh = float(self.config.get("settings", {}).get("decline_threshold_pct", -2.0))

        if pct_change > up_thresh or slope > 0.2:
            direction = "IMPROVING"
        elif pct_change < down_thresh or slope < -0.2:
            direction = "DECLINING"
        else:
            direction = "STABLE"

        return (direction, slope, pct_change)

    # ---------------------------------------------------------------------------
    # Consistency & Streak Calculation
    # ---------------------------------------------------------------------------

    def calculate_consistency_and_streak(self, user_id: str) -> Tuple[int, float]:
        """
        Calculates calendar-safe day streak and score consistency for a user.
        """
        sessions = self._user_sessions.get(user_id, [])
        if not sessions:
            return (0, 100.0)

        # Sort timestamps
        timestamps = sorted([s.timestamp for s in sessions])
        dates = []
        for ts in timestamps:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
                dates.append(dt)
            except Exception:
                pass

        unique_dates = sorted(list(set(dates)))
        if not unique_dates:
            return (len(sessions), 100.0)

        # Calculate streak from most recent date backwards
        streak = 1
        for i in range(len(unique_dates) - 1, 0, -1):
            delta = (unique_dates[i] - unique_dates[i - 1]).days
            if delta == 1:
                streak += 1
            else:
                break

        # Calculate score variance / consistency
        scores = [s.average_score for s in sessions]
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        std_dev = math.sqrt(variance)
        consistency = max(0.0, 100.0 - std_dev)

        return (streak, round(consistency, 1))

    # ---------------------------------------------------------------------------
    # Session Comparisons
    # ---------------------------------------------------------------------------

    def compare_session(self, user_id: str, session: SessionAnalytics) -> Dict[str, Any]:
        sessions = self._user_sessions.get(user_id, [])
        if len(sessions) <= 1:
            return {
                "vs_previous": 0.0,
                "vs_recent_avg": 0.0,
                "vs_personal_best": 0.0,
                "improvement_pct": 0.0
            }

        prev = sessions[-2] if len(sessions) >= 2 else None
        recent_5 = [s.average_score for s in sessions[-6:-1]] if len(sessions) >= 2 else [session.average_score]
        recent_avg = sum(recent_5) / len(recent_5) if recent_5 else session.average_score
        personal_best = max([s.average_score for s in sessions])

        vs_prev = (session.average_score - prev.average_score) if prev else 0.0
        vs_recent = session.average_score - recent_avg
        vs_best = session.average_score - personal_best
        imp_pct = ((vs_prev / prev.average_score) * 100.0) if prev and prev.average_score > 0 else 0.0

        return {
            "vs_previous": round(vs_prev, 1),
            "vs_recent_avg": round(vs_recent, 1),
            "vs_personal_best": round(vs_best, 1),
            "improvement_pct": round(imp_pct, 1)
        }

    # ---------------------------------------------------------------------------
    # Summary & Telemetry
    # ---------------------------------------------------------------------------

    def get_summary(self, user_id: Optional[str] = None) -> AnalyticsSummary:
        target_uid = user_id or self._active_user_id
        sessions = self._user_sessions.get(target_uid, [])

        total_sessions = len(sessions)
        total_duration = sum(s.duration for s in sessions)
        overall_avg = (sum(s.average_score for s in sessions) / total_sessions) if total_sessions > 0 else 0.0

        streak, consistency = self.calculate_consistency_and_streak(target_uid)
        trends = self.compute_trends(target_uid)

        ex_history = {
            k: v.to_dict() for k, v in self._user_exercises.get(target_uid, {}).items()
        }
        records = [
            r.to_dict() for r in self._user_records.get(target_uid, {}).values()
        ]

        last_sess = sessions[-1] if sessions else None
        comparison = self.compare_session(target_uid, last_sess) if last_sess else {}

        recent = [s.to_dict() for s in sessions[-10:]]

        return AnalyticsSummary(
            user_id=target_uid,
            total_sessions=total_sessions,
            total_duration=total_duration,
            overall_average_score=overall_avg,
            streak_days=streak,
            recent_sessions=recent,
            exercise_history=ex_history,
            active_trends={k: v.to_dict() for k, v in trends.items()},
            personal_records=records,
            comparison=comparison,
            source=self.name
        )

    def get_diagnostics(self) -> Dict[str, Any]:
        sessions = self._user_sessions.get(self._active_user_id, [])
        latest_score = sessions[-1].average_score if sessions else 0.0
        trends = self.compute_trends(self._active_user_id)

        return {
            "name": self.name,
            "version": self.version,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "priority": self.priority,
            "dependencies": self.dependencies,
            "metrics": {
                "activeUserId": self._active_user_id,
                "sessionsProcessedCount": self._sessions_processed_count,
                "exercisesTrackedCount": len(self._user_exercises.get(self._active_user_id, {})),
                "personalRecordsCount": len(self._user_records.get(self._active_user_id, {})),
                "recordsBrokenCount": self._records_broken_count,
                "trendCount": len(trends),
                "latestScore": round(latest_score, 1),
                "analyticsLatencyMs": round(self._processing_time_ms, 2)
            }
        }
