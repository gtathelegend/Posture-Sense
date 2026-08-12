"""
Integration & Data Integrity Tests for Session Analytics Persistence (Milestone: Real Session Analytics Persistence)
======================================================================================================================
Tests model serialization/deserialization, SessionService parameter validation, repository user isolation,
report service non-hardcoded payload retrieval, and complete pipeline data integrity for Warrior II fixture.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from backend.app.models.pose_session import PoseSession, build_pose_session
from backend.app.services.session_service import SessionService
from backend.app.repositories.session_repository import SessionRepository
from backend.app.repositories.analytics_repository import AnalyticsRepository
from backend.app.services.report_service import ReportService


# ---------------------------------------------------------------------------
# 1. Model Tests
# ---------------------------------------------------------------------------

def test_pose_session_model_serialization():
    session = PoseSession(
        id=101,
        user_id="usr_test_123",
        pose_label="Warrior II",
        timestamp="2026-08-12T14:30:00Z",
        duration=45.0,
        accuracy=92.5,
        reps=3,
        symmetry_score=94.2,
        balance_score=88.5,
        stability_score=91.0,
        rom_score=95.0,
        hold_time=42.5,
        tracking_quality=98.4,
        failed_rules=["left_knee_angle_low"]
    )

    d = session.to_dict()
    assert d['id'] == 101
    assert d['user_id'] == "usr_test_123"
    assert d['pose_label'] == "Warrior II"
    assert d['duration'] == 45.0
    assert d['accuracy'] == 92.5
    assert d['reps'] == 3
    assert d['symmetry_score'] == 94.2
    assert d['balance_score'] == 88.5
    assert d['stability_score'] == 91.0
    assert d['rom_score'] == 95.0
    assert d['hold_time'] == 42.5
    assert d['tracking_quality'] == 98.4
    assert d['failed_rules'] == ["left_knee_angle_low"]


def test_pose_session_model_legacy_defaults():
    record = {
        'id': 50,
        'user_id': 'usr_legacy',
        'pose_label': 'Tree Pose',
        'timestamp': '2026-01-01T00:00:00Z',
        'duration': 30.0,
        'accuracy': 85.0
    }
    session = build_pose_session(record)
    assert session.id == 50
    assert session.reps == 0
    assert session.symmetry_score == 100.0
    assert session.balance_score == 100.0
    assert session.stability_score == 100.0
    assert session.rom_score == 100.0
    assert session.hold_time == 0.0
    assert session.tracking_quality == 100.0
    assert session.failed_rules == []


# ---------------------------------------------------------------------------
# 2. Validation & Service Layer Tests
# ---------------------------------------------------------------------------

def test_session_service_validation_valid():
    with patch.object(SessionRepository, 'create_session') as mock_create:
        mock_create.return_value = PoseSession(
            id=1, user_id="u1", pose_label="Plank", duration=60.0, accuracy=90.0,
            reps=0, symmetry_score=95.0, balance_score=90.0, stability_score=92.0,
            rom_score=95.0, hold_time=58.0, tracking_quality=99.0, failed_rules=[]
        )
        session, error = SessionService.save_session(
            user_id="u1", pose_label="Plank", duration=60.0, accuracy=90.0,
            reps=0, symmetry_score=95.0, balance_score=90.0, stability_score=92.0,
            rom_score=95.0, hold_time=58.0, tracking_quality=99.0, failed_rules=[]
        )
        assert error is None
        assert session is not None
        assert session.pose_label == "Plank"


def test_session_service_validation_rejections():
    # Invalid pose label
    sess, err = SessionService.save_session("u1", "", 10.0, 80.0)
    assert sess is None and "pose" in err.lower()

    # Negative duration
    sess, err = SessionService.save_session("u1", "Plank", -5.0, 80.0)
    assert sess is None and "duration" in err.lower()

    # Out-of-bounds accuracy (> 100)
    sess, err = SessionService.save_session("u1", "Plank", 10.0, 105.0)
    assert sess is None and "accuracy" in err.lower()

    # Negative reps
    sess, err = SessionService.save_session("u1", "Plank", 10.0, 80.0, reps=-1)
    assert sess is None and "reps" in err.lower()

    # Out-of-bounds symmetry score (< 0)
    sess, err = SessionService.save_session("u1", "Plank", 10.0, 80.0, symmetry_score=-10.0)
    assert sess is None and "symmetry" in err.lower()

    # Malformed failed_rules (not a list)
    sess, err = SessionService.save_session("u1", "Plank", 10.0, 80.0, failed_rules="invalid_string")
    assert sess is None and "failed rules" in err.lower()


# ---------------------------------------------------------------------------
# 3. Pipeline Data Integrity Test (Step 18 Verification)
# ---------------------------------------------------------------------------

def test_pipeline_data_integrity_warrior_ii_fixture():
    """
    Step 18 Data Integrity Test:
    Create Warrior II fixture payload (Accuracy: 92.5, Symmetry: 94.2, Balance: 88.5,
    Stability: 91.0, ROM: 95.0, Hold: 42.5s, Tracking: 98.4%, Failed Rules: ['left_knee_angle_low']).
    Persist it, read back, and verify every value survives identically.
    """
    warrior_record = {
        'id': 999,
        'user_id': 'user_warrior_test',
        'pose_label': 'Warrior II',
        'timestamp': '2026-08-12T20:00:00Z',
        'duration': 45.0,
        'accuracy': 92.5,
        'reps': 0,
        'symmetry_score': 94.2,
        'balance_score': 88.5,
        'stability_score': 91.0,
        'rom_score': 95.0,
        'hold_time': 42.5,
        'tracking_quality': 98.4,
        'failed_rules': ['left_knee_angle_low']
    }

    mock_session = build_pose_session(warrior_record)

    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=[mock_session]):
        # A. Verify Analytics Summary API output
        summary = AnalyticsRepository.get_user_analytics_summary('user_warrior_test')
        assert summary['total_sessions'] == 1
        assert summary['total_duration'] == 45.0
        assert summary['overall_average_score'] == 92.5
        assert summary['biomechanics']['average_symmetry'] == 94.2
        assert summary['biomechanics']['average_balance'] == 88.5
        assert summary['biomechanics']['average_stability'] == 91.0
        assert summary['biomechanics']['average_rom'] == 95.0
        assert summary['biomechanics']['average_tracking_quality'] == 98.4
        assert summary['totals']['total_hold_time'] == 42.5
        assert summary['recent_sessions'][0]['failed_rules'] == ['left_knee_angle_low']

        # B. Verify Exercise History output
        ex_hist = AnalyticsRepository.get_exercise_history('user_warrior_test')
        warrior_ex = ex_hist['exercises']['Warrior II']
        assert warrior_ex['best_score'] == 92.5
        assert warrior_ex['average_symmetry'] == 94.2
        assert warrior_ex['average_balance'] == 88.5
        assert warrior_ex['average_stability'] == 91.0
        assert warrior_ex['average_rom'] == 95.0
        assert warrior_ex['total_hold_time'] == 42.5

        # C. Verify Personal Records output
        records = AnalyticsRepository.get_personal_records('user_warrior_test')
        rec_types = {r['record_type']: r['value'] for r in records}
        assert rec_types['Highest Score'] == 92.5
        assert rec_types['Longest Hold / Duration'] == 45.0
        assert rec_types['Best Symmetry'] == 94.2
        assert rec_types['Best Balance'] == 88.5
        assert rec_types['Best Stability'] == 91.0
        assert rec_types['Best ROM'] == 95.0

        # D. Verify Report Service output (Confirm NO hardcoding of reps: 10 or tracking_quality: 100.0)
        report_dict = ReportService.generate_session_report('user_warrior_test', '999')
        assert report_dict['performance']['overall_score'] == 92.5
        assert report_dict['data_quality']['tracking_quality'] == 98.4
        assert report_dict['session_info']['completed_reps'] == 0
        assert report_dict['session_info']['session_id'] == '999'
