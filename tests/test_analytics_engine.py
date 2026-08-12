"""
Unit & Integration Tests for AnalyticsEngine (Milestone 7)
==========================================================
Tests session aggregation, exercise history tracking, deterministic trend calculations,
personal record updates, streak & consistency calculation, session comparisons,
user data isolation, data quality filtering, and EngineRuntime registration.
"""

import pytest
from shared.events.event_bus import EventBus
from shared.engines.analytics_engine import AnalyticsEngine
from shared.contracts.scoring import ScoreReport
from shared.contracts.analytics import SessionAnalytics, ExerciseAnalytics, PersonalRecord
from shared.core.runtime.runtime import EngineRuntime
from shared.types.enums import EngineStatus
from backend.app.repositories.analytics_repository import AnalyticsRepository


@pytest.fixture
def event_bus():
    return EventBus(debug_mode=True)


@pytest.fixture
def analytics_engine(event_bus):
    engine = AnalyticsEngine(event_bus=event_bus)
    engine.initialize()
    engine.start()
    return engine


# 1. Lifecycle & Runtime Registration Test
def test_analytics_engine_lifecycle(event_bus):
    engine = AnalyticsEngine(event_bus=event_bus)
    assert engine.status() == EngineStatus.UNINITIALIZED

    assert engine.initialize() is True
    assert engine.status() == EngineStatus.INITIALIZED

    assert engine.start() is True
    assert engine.status() == EngineStatus.RUNNING

    assert engine.pause() is True
    assert engine.status() == EngineStatus.PAUSED

    assert engine.resume() is True
    assert engine.status() == EngineStatus.RUNNING

    assert engine.stop() is True
    assert engine.status() == EngineStatus.STOPPED

    assert engine.dispose() is True
    assert engine.status() == EngineStatus.DISPOSED


def test_analytics_runtime_registration(event_bus):
    runtime = EngineRuntime(event_bus=event_bus)
    engine = AnalyticsEngine(event_bus=event_bus)
    record = runtime.register(
        engine,
        priority=10,
        dependencies=["feedback_engine", "scoring_engine", "movement_engine", "pose_rule_engine", "biomechanics_engine"]
    )
    assert record.id == "AnalyticsEngine"
    assert record.priority == 10


# 2. MANDATORY NUMERICAL TEST (Exact Fixutre Scores: 70, 75, 80, 85, 90)
def test_deterministic_numerical_fixture(analytics_engine):
    """
    Fixture Scores: 70, 75, 80, 85, 90
    Verify:
    - Average: 80.0
    - Trend: IMPROVING
    - Improvement percentage: +28.57% ( (90-70)/70 * 100 = 28.5714... )
    - Personal best: 90.0
    """
    scores = [70.0, 75.0, 80.0, 85.0, 90.0]
    for idx, score in enumerate(scores):
        report = ScoreReport(
            overall_score=score,
            exercise_id="bodyweight_squat",
            score_confidence=0.9,
            quality_gate_passed=True
        )
        analytics_engine._last_score_report = report
        analytics_engine._process_completed_session({
            "session_id": f"sess_{idx+1}",
            "exercise_id": "bodyweight_squat",
            "average_score": score,
            "duration": 30.0,
            "completed_reps": 10
        })

    summary = analytics_engine.get_summary()

    # 1. Average
    assert summary.overall_average_score == 80.0

    # 2. Trend
    tr = summary.active_trends["overall_score"]
    assert tr["trend_direction"] == "IMPROVING"
    assert round(tr["percentage_change"], 2) == 28.57

    # 3. Personal best
    records = {r["record_type"]: r["value"] for r in summary.personal_records}
    assert records["Highest Score"] == 90.0

    # 4. Exercise History improvement percentage
    ex_hist = summary.exercise_history["bodyweight_squat"]
    assert ex_hist["best_score"] == 90.0
    assert ex_hist["average_score"] == 80.0


# 3. Trend Classification Test (IMPROVING, STABLE, DECLINING, INSUFFICIENT_DATA)
def test_trend_classification(analytics_engine):
    # Test INSUFFICIENT_DATA (<3 sessions)
    analytics_engine._user_sessions.clear()
    analytics_engine._process_completed_session({"session_id": "s1", "average_score": 70.0})
    analytics_engine._process_completed_session({"session_id": "s2", "average_score": 72.0})

    tr1 = analytics_engine.compute_trends("anonymous")["overall_score"]
    assert tr1.trend_direction == "INSUFFICIENT_DATA"

    # Test DECLINING trend
    analytics_engine._process_completed_session({"session_id": "s3", "average_score": 50.0})
    tr2 = analytics_engine.compute_trends("anonymous")["overall_score"]
    assert tr2.trend_direction == "DECLINING"

    # Test STABLE trend
    analytics_engine._user_sessions.clear()
    for i, sc in enumerate([80.0, 80.5, 80.2]):
        analytics_engine._process_completed_session({"session_id": f"st_{i}", "average_score": sc})
    tr3 = analytics_engine.compute_trends("anonymous")["overall_score"]
    assert tr3.trend_direction == "STABLE"


# 4. Personal Record Events Test
def test_personal_record_event_publishing(event_bus, analytics_engine):
    records_broken = []
    event_bus.subscribe("analytics.record_broken", lambda e: records_broken.append(e))

    # First session establishes baseline records
    analytics_engine._process_completed_session({"session_id": "s1", "average_score": 80.0, "completed_reps": 10})

    # Second session breaks Highest Score record
    analytics_engine._process_completed_session({"session_id": "s2", "average_score": 95.0, "completed_reps": 10})

    assert len(records_broken) >= 1
    broken_record = records_broken[0].data
    assert broken_record["record_type"] == "Highest Score"
    assert broken_record["value"] == 95.0
    assert broken_record["previous_value"] == 80.0


# 5. User Data Isolation Test
def test_user_data_isolation(analytics_engine):
    # Record for User A
    analytics_engine.set_active_user("user_a")
    analytics_engine._process_completed_session({"session_id": "sa1", "average_score": 90.0})

    # Record for User B
    analytics_engine.set_active_user("user_b")
    analytics_engine._process_completed_session({"session_id": "sb1", "average_score": 60.0})

    summary_a = analytics_engine.get_summary("user_a")
    summary_b = analytics_engine.get_summary("user_b")

    assert summary_a.overall_average_score == 90.0
    assert summary_b.overall_average_score == 60.0
    assert len(summary_a.recent_sessions) == 1
    assert len(summary_b.recent_sessions) == 1


# 6. Data Quality Gate Exclusions Test
def test_quality_gate_exclusion(analytics_engine):
    report_bad = ScoreReport(
        overall_score=99.0, # High score but invalid quality gate
        score_confidence=0.2, # Below 0.4 threshold
        quality_gate_passed=False,
        quality_warning="Tracking lost"
    )

    analytics_engine._last_score_report = report_bad
    result = analytics_engine._process_completed_session({"session_id": "bad_sess", "average_score": 99.0})

    # Bad session should be excluded (result is None)
    assert result is None
    assert analytics_engine.get_summary().total_sessions == 0
