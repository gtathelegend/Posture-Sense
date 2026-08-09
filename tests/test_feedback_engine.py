"""
Unit & Integration Tests for FeedbackEngine (Milestone 6)
==========================================================
Tests rule evaluation, measurable evidence attachment, priority ordering,
deduplication/cooldown suppression, missing metric handling, session summary generation,
event publishing, engine lifecycle, and EngineRuntime registration.
"""

import time
import pytest
from shared.events.event_bus import EventBus
from shared.engines.feedback_engine import FeedbackEngine
from shared.contracts.scoring import ScoreReport
from shared.contracts.feedback import FeedbackResult, FeedbackSessionSummary
from shared.contracts.pose import PoseResult, ExerciseResult
from shared.core.runtime.runtime import EngineRuntime
from shared.types.enums import EngineStatus


@pytest.fixture
def event_bus():
    return EventBus(debug_mode=True)


@pytest.fixture
def feedback_engine(event_bus):
    engine = FeedbackEngine(event_bus=event_bus)
    engine.initialize()
    engine.start()
    return engine


# 1. Engine Lifecycle & Diagnostics Tests
def test_feedback_engine_lifecycle(event_bus):
    engine = FeedbackEngine(event_bus=event_bus)
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


def test_feedback_runtime_registration(event_bus):
    runtime = EngineRuntime(event_bus=event_bus)
    engine = FeedbackEngine(event_bus=event_bus)
    record = runtime.register(
        engine,
        priority=9,
        dependencies=["scoring_engine", "movement_engine", "pose_rule_engine", "biomechanics_engine"]
    )
    assert record.id == "FeedbackEngine"
    assert record.priority == 9
    assert record.dependencies == ["scoring_engine", "movement_engine", "pose_rule_engine", "biomechanics_engine"]


# 2. Rule Evaluation & Evidence Attachment Test
def test_rule_evaluation_and_evidence(feedback_engine):
    report = ScoreReport(
        overall_score=75.0,
        score_confidence=0.9,
        category="Good",
        components={
            "form": {"score": 55.0, "status": "POOR"},  # Below threshold 60.0 -> triggers rule_form_quality_low
            "rom": {"score": 65.0, "status": "WARNING"}, # Below threshold 70.0 -> triggers rule_rom_shallow
            "stability": {"score": 95.0, "status": "GOOD"}
        },
        exercise_id="bodyweight_squat",
        exercise_name="Bodyweight Squat"
    )

    feedback_engine._on_score_updated(report)
    active_fb = feedback_engine._active_feedback
    assert len(active_fb) >= 1

    # High severity form rule should be ranked first
    top = active_fb[0]
    assert top.category == "Form"
    assert top.severity == "high"
    assert "upright torso" in top.message.lower()

    # Evidence verification
    evidence = top.evidence
    assert evidence["raw_value"] == 55.0
    assert evidence["threshold"] == 60.0
    assert evidence["difference"] == 5.0
    assert evidence["metric_source"] == "form"


# 3. Priority Ordering Test
def test_priority_ordering(feedback_engine):
    """
    Critical severity rules (e.g. low tracking quality) should be ranked higher
    than medium/low severity rules regardless of insertion order.
    """
    report = ScoreReport(
        overall_score=50.0,
        score_confidence=0.5,
        category="Poor",
        components={
            "rom": {"score": 50.0, "status": "POOR"},  # Medium severity rule
            "form": {"score": 40.0, "status": "POOR"}, # High severity rule
            "tracking_quality": {"score": 40.0, "status": "POOR"} # Critical severity rule
        },
        exercise_id="squat"
    )

    feedback_engine._on_score_updated(report)
    active_fb = feedback_engine._active_feedback
    assert len(active_fb) >= 2

    # First feedback item must be critical severity
    assert active_fb[0].severity == "critical"
    # Second feedback item must be high severity
    assert active_fb[1].severity == "high"


# 4. Deduplication & Cooldown Test
def test_deduplication_and_cooldown(feedback_engine):
    report = ScoreReport(
        overall_score=75.0,
        components={
            "form": {"score": 50.0, "status": "POOR"}
        }
    )

    feedback_engine._on_score_updated(report)

    # First evaluation generates feedback
    fb1 = feedback_engine._active_feedback
    assert len(fb1) == 1

    # Immediate second evaluation should suppress duplicate due to cooldown
    fb2 = feedback_engine.evaluate_feedback_rules()
    assert len(fb2) == 0


# 5. Missing Metric Handling Test
def test_missing_metric_handling(feedback_engine):
    report = ScoreReport(
        overall_score=80.0,
        components={
            "form": {"score": None, "status": "UNAVAILABLE"},
            "rom": {"score": None, "status": "UNAVAILABLE"}
        },
        missing_metrics=["form", "rom"]
    )

    feedback_engine._on_score_updated(report)
    # Rules targeting unavailable metrics must not be triggered
    assert len(feedback_engine._active_feedback) == 0


# 6. Session Summary Generation Test
def test_session_summary_generation(event_bus, feedback_engine):
    summaries = []
    event_bus.subscribe("feedback.session_summary", lambda e: summaries.append(e))

    report = ScoreReport(
        overall_score=85.0,
        components={
            "form": {"score": 90.0, "status": "GOOD"},
            "rom": {"score": 55.0, "status": "POOR"},
            "stability": {"score": 95.0, "status": "GOOD"}
        },
        rep_scores=[
            {"rep_number": 1, "overall_score": 90.0},
            {"rep_number": 2, "overall_score": 50.0} # Low rep
        ],
        exercise_id="bodyweight_squat"
    )
    feedback_engine._last_score_report = report

    feedback_engine._on_score_session_completed({"session_id": "sess_123"})
    assert len(summaries) == 1

    s_data = summaries[0].data
    assert s_data["session_id"] == "sess_123"
    assert len(s_data["strengths"]) >= 1
    assert len(s_data["weak_areas"]) >= 1
    assert len(s_data["common_mistakes"]) >= 1
    assert len(s_data["improvement_areas"]) >= 1


# 7. Event Publication Verification
def test_event_publication(event_bus, feedback_engine):
    generated = []
    updated = []
    event_bus.subscribe("feedback.generated", lambda e: generated.append(e))
    event_bus.subscribe("feedback.updated", lambda e: updated.append(e))

    report = ScoreReport(
        overall_score=60.0,
        components={
            "form": {"score": 40.0, "status": "POOR"}
        }
    )
    feedback_engine._on_score_updated(report)

    assert len(generated) >= 1
    assert len(updated) >= 1
    assert "message" in generated[0].data
    assert "evidence" in generated[0].data
