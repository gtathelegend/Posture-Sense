"""
Unit & Integration Tests for ScoringEngine (Milestone 5)
=========================================================
Tests metric normalization, weight validation, score aggregation, score bands,
missing data handling, quality gates, score confidence, rep/hold/session scoring,
event publication, engine lifecycle, and EngineRuntime registration.
"""

import pytest
from unittest.mock import MagicMock
from shared.events.event_bus import EventBus
from shared.events.event_types import Event
from shared.engines.scoring_engine import ScoringEngine
from shared.contracts.scoring import ScoreReport
from shared.contracts.biomechanics import BiomechanicsSnapshot, JointAngle
from shared.contracts.pose import PoseResult, ExerciseResult
from shared.core.runtime.runtime import EngineRuntime
from shared.types.enums import EngineStatus


@pytest.fixture
def event_bus():
    return EventBus(debug_mode=True)


@pytest.fixture
def scoring_engine(event_bus):
    engine = ScoringEngine(event_bus=event_bus)
    engine.initialize()
    engine.start()
    return engine


# 1. Engine Lifecycle & Diagnostics Tests
def test_engine_lifecycle(event_bus):
    engine = ScoringEngine(event_bus=event_bus)
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


def test_runtime_registration(event_bus):
    runtime = EngineRuntime(event_bus=event_bus)
    engine = ScoringEngine(event_bus=event_bus)
    record = runtime.register(engine, priority=8, dependencies=["movement_engine", "biomechanics_engine", "pose_rule_engine"])
    
    assert record.id == "ScoringEngine"
    assert record.priority == 8
    assert record.dependencies == ["movement_engine", "biomechanics_engine", "pose_rule_engine"]


# 2. Config Validation Tests
def test_weight_validation_valid(scoring_engine):
    valid_cfg = {
        "default_weights": {
            "form": 0.40,
            "rom": 0.30,
            "stability": 0.30
        }
    }
    val_ok, err = scoring_engine._validate_config(valid_cfg)
    assert val_ok is True
    assert err is None


def test_weight_validation_invalid_sum(scoring_engine):
    invalid_cfg = {
        "default_weights": {
            "form": 0.50,
            "rom": 0.50,
            "stability": 0.50  # Sum = 1.5
        }
    }
    val_ok, err = scoring_engine._validate_config(invalid_cfg)
    assert val_ok is False
    assert "must sum to 1.0" in err


def test_weight_validation_negative(scoring_engine):
    invalid_cfg = {
        "default_weights": {
            "form": 1.20,
            "rom": -0.20  # Negative weight
        }
    }
    val_ok, err = scoring_engine._validate_config(invalid_cfg)
    assert val_ok is False
    assert "cannot be negative" in err


# 3. Exact Numerical Score Aggregation Test
def test_deterministic_score_aggregation(scoring_engine):
    """
    Given:
    Form = 80.0
    ROM = 90.0
    Stability = 70.0
    Symmetry = 100.0

    and weights:
    Form = 0.30
    ROM = 0.30
    Stability = 0.20
    Symmetry = 0.20

    Expected Overall Score = (80 * 0.30) + (90 * 0.30) + (70 * 0.20) + (100 * 0.20)
                          = 24 + 27 + 14 + 20 = 85.0
    """
    scoring_engine.config["categories"]["dynamic"] = {
        "form": 0.30,
        "rom": 0.30,
        "stability": 0.20,
        "symmetry": 0.20
    }

    # Inject mock inputs
    scoring_engine._last_exercise = ExerciseResult(
        exercise_name="bodyweight_squat",
        movement_quality=80.0,
        rom_percentage=90.0,
        tracking_quality=100.0
    )
    scoring_engine._last_biomechanics = BiomechanicsSnapshot(
        joint_angles=[],
        balance_score=70.0,
        symmetry_score=100.0
    )
    scoring_engine._last_pose = PoseResult(pose_name="Squat", confidence=1.0)

    report = scoring_engine.evaluate_score()
    
    assert report.components["form"]["score"] == 80.0
    assert report.components["rom"]["score"] == 90.0
    assert report.components["stability"]["score"] == 70.0
    assert report.components["symmetry"]["score"] == 100.0

    assert report.components["form"]["contribution"] == 24.0
    assert report.components["rom"]["contribution"] == 27.0
    assert report.components["stability"]["contribution"] == 14.0
    assert report.components["symmetry"]["contribution"] == 20.0

    assert report.overall_score == 85.0
    assert report.category == "Good"


# 4. Score Bands Mapping Tests
def test_score_bands_mapping(scoring_engine):
    assert scoring_engine._map_score_band(95.0) == "Excellent"
    assert scoring_engine._map_score_band(90.0) == "Excellent"
    assert scoring_engine._map_score_band(85.0) == "Good"
    assert scoring_engine._map_score_band(75.0) == "Good"
    assert scoring_engine._map_score_band(70.0) == "Needs Improvement"
    assert scoring_engine._map_score_band(60.0) == "Needs Improvement"
    assert scoring_engine._map_score_band(45.0) == "Poor"
    assert scoring_engine._map_score_band(0.0) == "Poor"


# 5. Missing Data & Dynamic Re-weighting Test
def test_missing_data_reweighting(scoring_engine):
    """
    When ROM and Control are unavailable (None), active weights (Form: 0.30, Stability: 0.15, Symmetry: 0.15)
    should be re-scaled dynamically (sum active = 0.60 -> scaling factor = 1/0.60).
    """
    scoring_engine.config["categories"]["dynamic"] = {
        "form": 0.30,
        "stability": 0.15,
        "symmetry": 0.15
    }
    scoring_engine._last_exercise = ExerciseResult(
        exercise_name="test",
        movement_quality=100.0,
        tracking_quality=100.0
    )
    scoring_engine._last_biomechanics = BiomechanicsSnapshot(
        joint_angles=[],
        balance_score=80.0,
        symmetry_score=60.0
    )

    report = scoring_engine.evaluate_score()

    # Active weights: form (0.30 / 0.60 = 0.5), stability (0.15 / 0.60 = 0.25), symmetry (0.15 / 0.60 = 0.25)
    # Expected overall = (100 * 0.5) + (80 * 0.25) + (60 * 0.25) = 50 + 20 + 15 = 85.0
    assert report.overall_score == 85.0
    assert report.components["form"]["status"] == "GOOD"
    assert report.components["stability"]["status"] == "GOOD"
    assert report.components["symmetry"]["status"] == "WARNING"


# 6. Quality Gate & Low Confidence Test
def test_quality_gate_failure(scoring_engine):
    scoring_engine._last_exercise = ExerciseResult(
        exercise_name="test",
        movement_quality=90.0,
        tracking_quality=30.0  # Below min threshold 50.0
    )
    report = scoring_engine.evaluate_score()

    assert report.quality_gate_passed is False
    assert "Tracking quality too low" in report.quality_warning
    assert report.score_confidence < 0.6


# 7. Rep-Level & Session Scoring Test
def test_rep_and_session_scoring(event_bus, scoring_engine):
    published_events = []
    event_bus.subscribe("score.rep_completed", lambda e: published_events.append(e))

    # Rep 1
    scoring_engine._last_exercise = ExerciseResult(
        exercise_name="bodyweight_squat",
        rep_count=1,
        movement_quality=90.0,
        rom_percentage=85.0,
        current_rep_duration=2.0,
        average_rep_duration=2.0,
        tracking_quality=100.0
    )
    event_bus.publish("exercise.rep_completed", scoring_engine._last_exercise.to_dict())

    # Rep 2
    scoring_engine._last_exercise = ExerciseResult(
        exercise_name="bodyweight_squat",
        rep_count=2,
        movement_quality=70.0,
        rom_percentage=75.0,
        current_rep_duration=2.2,
        average_rep_duration=2.1,
        tracking_quality=100.0
    )
    event_bus.publish("exercise.rep_completed", scoring_engine._last_exercise.to_dict())

    assert len(scoring_engine._rep_scores) == 2
    assert len(published_events) == 2

    final_report = scoring_engine.evaluate_score()
    summary = final_report.session_summary

    assert summary["completed_reps"] == 2
    assert summary["best_rep_score"] >= summary["worst_rep_score"]
    assert "consistency_score" in summary
    assert "score_variance" in summary


# 8. Hold Scoring Test
def test_hold_scoring(scoring_engine):
    scoring_engine._exercise_category = "static_hold"
    scoring_engine._active_exercise_id = "plank"
    scoring_engine._last_exercise = ExerciseResult(
        exercise_name="plank",
        exercise_id="plank",
        hold_time=45.0,
        movement_quality=95.0,
        tracking_quality=90.0
    )
    scoring_engine._last_biomechanics = BiomechanicsSnapshot(
        joint_angles=[],
        balance_score=92.0,
        symmetry_score=94.0
    )

    report = scoring_engine.evaluate_score()
    assert report.hold_score is not None
    assert report.hold_score["duration"] == 45.0
    assert report.hold_score["balance"] == 92.0
    assert report.hold_score["alignment"] == 94.0


# 9. Event Publication Verification
def test_event_publication(event_bus, scoring_engine):
    reports = []
    event_bus.subscribe("score.updated", lambda e: reports.append(e))

    scoring_engine._on_biomechanics_updated(BiomechanicsSnapshot(joint_angles=[], symmetry_score=90.0))
    assert len(reports) == 1
    assert "overall_score" in reports[0].data
    assert "components" in reports[0].data
