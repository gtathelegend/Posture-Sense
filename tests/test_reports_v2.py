"""
tests/test_reports_v2.py
========================
Comprehensive Unit & Integration Tests for Reports V2 & Rich Analytics Export Subsystem.
Tests Session, Progress, Exercise, and Comprehensive Report generation, JSON, CSV, PDF exporters,
legacy session NULL preservation, data quality notices, and strict user isolation.
"""

from datetime import datetime, timedelta, timezone
import json
import pytest
from unittest.mock import patch

from backend.app.models.pose_session import PoseSession
from backend.app.services.report_service import ReportService
from backend.app.repositories.session_repository import SessionRepository
from shared.engines.report_engine import ReportEngine


@pytest.fixture
def mock_rich_sessions():
    """Fixture providing a list of rich, fully-measured pose sessions."""
    now = datetime.now(timezone.utc)
    t3 = (now - timedelta(hours=2)).isoformat()
    t2 = (now - timedelta(days=1)).isoformat()
    t1 = (now - timedelta(days=3)).isoformat()

    s1 = PoseSession(
        id=201, user_id="u_report_test", pose_label="Tree Pose",
        timestamp=t1, duration=35.0, accuracy=82.0,
        reps=0, symmetry_score=85.0, balance_score=80.0, stability_score=84.0,
        rom_score=88.0, hold_time=30.0, tracking_quality=96.0, failed_rules=["arm_extension_low"]
    )
    s2 = PoseSession(
        id=202, user_id="u_report_test", pose_label="Warrior II",
        timestamp=t2, duration=60.0, accuracy=90.0,
        reps=0, symmetry_score=92.0, balance_score=89.0, stability_score=91.0,
        rom_score=94.0, hold_time=55.0, tracking_quality=99.0, failed_rules=[]
    )
    s3 = PoseSession(
        id=203, user_id="u_report_test", pose_label="Tree Pose",
        timestamp=t3, duration=45.0, accuracy=95.0,
        reps=0, symmetry_score=96.0, balance_score=94.0, stability_score=97.0,
        rom_score=98.0, hold_time=42.0, tracking_quality=100.0, failed_rules=[]
    )
    return [s3, s2, s1]


@pytest.fixture
def mock_legacy_session():
    """Fixture providing a legacy session with NULL biomechanics fields."""
    now = datetime.now(timezone.utc)
    t_legacy = (now - timedelta(days=30)).isoformat()

    return PoseSession(
        id=999, user_id="u_report_test", pose_label="Plank",
        timestamp=t_legacy, duration=20.0, accuracy=70.0,
        reps=0, symmetry_score=None, balance_score=None, stability_score=None,
        rom_score=None, hold_time=18.0, tracking_quality=None, failed_rules=["hip_sag"]
    )


# ---------------------------------------------------------------------------
# 1. Session Report Tests
# ---------------------------------------------------------------------------

def test_session_report_complete(mock_rich_sessions):
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_rich_sessions):
        report = ReportService.generate_session_report("u_report_test", "203")

        assert report['metadata']['report_type'] == 'session'
        assert report['metadata']['user_id'] == 'u_report_test'
        assert report['metadata']['schema_version'] == '2.0.0'

        assert report['performance']['overall_score'] == 95.0
        assert report['performance']['score_category'] == 'Excellent'

        assert report['biomechanics']['symmetry_score'] == 96.0
        assert report['biomechanics']['balance_score'] == 94.0
        assert report['biomechanics']['stability_score'] == 97.0
        assert report['biomechanics']['rom_score'] == 98.0

        assert report['tracking']['tracking_quality'] == 100.0
        assert report['tracking']['quality_gate_passed'] is True
        assert report['data_quality']['is_legacy'] is False
        assert "captured successfully" in report['data_quality']['quality_notice']


def test_session_report_legacy_null_safety(mock_legacy_session):
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=[mock_legacy_session]):
        report = ReportService.generate_session_report("u_report_test", "999")

        assert report['metadata']['report_type'] == 'session'
        # Crucial test: NULL fields MUST remain None, never converted to 0 or 100
        assert report['biomechanics']['symmetry_score'] is None
        assert report['biomechanics']['balance_score'] is None
        assert report['biomechanics']['stability_score'] is None
        assert report['biomechanics']['rom_score'] is None
        assert report['tracking']['tracking_quality'] is None

        assert report['data_quality']['is_legacy'] is True
        assert "Detailed biomechanics data was not available" in report['data_quality']['quality_notice']
        assert "symmetry_score" in report['data_quality']['unavailable_metrics']


# ---------------------------------------------------------------------------
# 2. Progress & Exercise Report Tests
# ---------------------------------------------------------------------------

def test_progress_report_timeframe(mock_rich_sessions):
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_rich_sessions):
        rep_30d = ReportService.generate_progress_report("u_report_test", timeframe="30d")

        assert rep_30d['metadata']['report_type'] == 'progress'
        assert rep_30d['reporting_period'] == '30d'
        assert rep_30d['overall_summary']['total_sessions'] == 3
        assert rep_30d['overall_summary']['average_score'] > 80.0
        assert len(rep_30d['personal_records']) >= 1
        assert 'tracking_quality' in rep_30d['data_quality']


def test_exercise_report_aggregation(mock_rich_sessions):
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_rich_sessions):
        rep_ex = ReportService.generate_exercise_report("u_report_test", "tree_pose")

        assert rep_ex['metadata']['report_type'] == 'exercise'
        assert rep_ex['exercise_info']['exercise_id'] == 'tree_pose'
        assert rep_ex['exercise_info']['total_sessions'] == 2
        assert rep_ex['performance_summary']['best_score'] == 95.0
        assert len(rep_ex['recent_history']) == 2


def test_comprehensive_report_10_sections(mock_rich_sessions):
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_rich_sessions):
        comp = ReportService.generate_comprehensive_report("u_report_test")

        assert comp['metadata']['report_type'] == 'comprehensive'
        assert 'executive_summary' in comp
        assert 'overall_progress' in comp
        assert 'score_trends' in comp
        assert 'biomechanics_trends' in comp
        assert 'personal_records' in comp
        assert 'pose_performance' in comp
        assert 'recent_sessions' in comp
        assert 'session_comparison' in comp
        assert 'feedback_summary' in comp
        assert 'data_quality_notice' in comp


# ---------------------------------------------------------------------------
# 3. Export Tests (JSON, CSV, PDF)
# ---------------------------------------------------------------------------

def test_export_json(mock_rich_sessions):
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_rich_sessions):
        exp = ReportService.export_session_json("u_report_test", "203")

        assert exp['format'] == 'json'
        assert exp['content_type'] == 'application/json'
        
        parsed = json.loads(exp['content'])
        assert parsed['metadata']['schema_version'] == '2.0.0'
        assert parsed['session_info']['session_id'] == '203'


def test_export_csv_rfc4180(mock_rich_sessions):
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_rich_sessions):
        exp = ReportService.export_progress_csv("u_report_test", timeframe="30d")

        assert exp['format'] == 'csv'
        assert exp['content_type'] == 'text/csv'

        lines = exp['content'].strip().split('\n')
        assert len(lines) == 4  # 1 header + 3 sessions
        header = lines[0]
        assert "Date,Pose,Exercise,Score,Score Category" in header
        assert "Failed Rules" in header


def test_export_pdf_html_rendering(mock_rich_sessions):
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_rich_sessions):
        exp = ReportService.export_session_pdf("u_report_test", "203")

        assert exp['format'] == 'pdf'
        assert exp['content_type'] == 'application/pdf'
        assert "POSTURESENSE AI" in exp['content']
        assert "SESSION REPORT" in exp['content']
        assert "DATA QUALITY &amp; PRIVACY NOTICE" in exp['content']


# ---------------------------------------------------------------------------
# 4. User Isolation & Security Tests
# ---------------------------------------------------------------------------

def test_report_service_user_isolation(mock_rich_sessions):
    """Verify User A data is isolated from User B."""
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_rich_sessions):
        # Generate for User A
        rep_a = ReportService.generate_session_report("user_A", "203")
        assert rep_a['metadata']['user_id'] == "user_A"

    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=[]):
        # Query for User B who has no sessions
        rep_b = ReportService.generate_session_report("user_B", "203")
        assert rep_b['metadata']['user_id'] == "user_B"
        assert rep_b['performance']['overall_score'] == 0.0


# ---------------------------------------------------------------------------
# 5. Route Integration & HTML Template Rendering Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def app_client():
    from backend.app import create_app
    from backend.app.config import Config
    app = create_app(Config)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app.test_client()


def test_comprehensive_report_route_renders_200(app_client, mock_rich_sessions):
    from backend.app.models.user import User
    from backend.app.services.auth_service import AuthService

    dummy_user = User('00000000-0000-0000-0000-000000000001', 'testuser', 'test@example.com', 'hash')

    with patch.object(AuthService, 'get_user_by_id', return_value=dummy_user):
        with app_client.session_transaction() as sess:
            sess['_user_id'] = '00000000-0000-0000-0000-000000000001'

        with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_rich_sessions):
            res = app_client.get('/reports/view/comprehensive')
            assert res.status_code == 200
            html = res.get_data(as_text=True)
            assert 'PostureSense AI Report' in html
            assert 'comprehensive' in html
            assert 'Tracking Quality' in html


def test_comprehensive_report_route_legacy_session_no_crash(app_client, mock_legacy_session):
    from backend.app.models.user import User
    from backend.app.services.auth_service import AuthService

    dummy_user = User('00000000-0000-0000-0000-000000000001', 'testuser', 'test@example.com', 'hash')

    with patch.object(AuthService, 'get_user_by_id', return_value=dummy_user):
        with app_client.session_transaction() as sess:
            sess['_user_id'] = '00000000-0000-0000-0000-000000000001'

        with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=[mock_legacy_session]):
            res = app_client.get('/reports/view/comprehensive')
            assert res.status_code == 200
            html = res.get_data(as_text=True)
            assert 'Not available' in html or 'N/A' in html


def test_progress_report_route_renders_200(app_client, mock_rich_sessions):
    from backend.app.models.user import User
    from backend.app.services.auth_service import AuthService

    dummy_user = User('00000000-0000-0000-0000-000000000001', 'testuser', 'test@example.com', 'hash')

    with patch.object(AuthService, 'get_user_by_id', return_value=dummy_user):
        with app_client.session_transaction() as sess:
            sess['_user_id'] = '00000000-0000-0000-0000-000000000001'

        with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_rich_sessions):
            res = app_client.get('/reports/view/progress?timeframe=30d')
            assert res.status_code == 200
            html = res.get_data(as_text=True)
            assert 'progress' in html


def test_session_report_route_renders_200(app_client, mock_rich_sessions):
    from backend.app.models.user import User
    from backend.app.services.auth_service import AuthService

    dummy_user = User('00000000-0000-0000-0000-000000000001', 'testuser', 'test@example.com', 'hash')

    with patch.object(AuthService, 'get_user_by_id', return_value=dummy_user):
        with app_client.session_transaction() as sess:
            sess['_user_id'] = '00000000-0000-0000-0000-000000000001'

        with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_rich_sessions):
            res = app_client.get('/reports/view/session/203')
            assert res.status_code == 200
            html = res.get_data(as_text=True)
            assert 'session' in html


def test_exercise_report_route_renders_200(app_client, mock_rich_sessions):
    from backend.app.models.user import User
    from backend.app.services.auth_service import AuthService

    dummy_user = User('00000000-0000-0000-0000-000000000001', 'testuser', 'test@example.com', 'hash')

    with patch.object(AuthService, 'get_user_by_id', return_value=dummy_user):
        with app_client.session_transaction() as sess:
            sess['_user_id'] = '00000000-0000-0000-0000-000000000001'

        with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_rich_sessions):
            res = app_client.get('/reports/view/exercise/tree_pose')
            assert res.status_code == 200
            html = res.get_data(as_text=True)
            assert 'exercise' in html
