"""
Unit & Integration Tests for Dashboard V2 & User Progress Intelligence
======================================================================
Tests DashboardService.get_user_dashboard_overview(), timeframe filtering,
streak calculation, biomechanics aggregation, personal records calculation,
deterministic insights rule evaluation, latest vs previous session comparison,
legacy session handling, empty user state, and API endpoint integration.
"""

from datetime import datetime, timedelta, timezone
import pytest
from unittest.mock import patch

from backend.app.models.pose_session import PoseSession, build_pose_session
from backend.app.services.dashboard_service import DashboardService
from backend.app.repositories.session_repository import SessionRepository


@pytest.fixture
def mock_user_sessions():
    """
    Sample multi-session fixture for user progress intelligence testing.
    Uses relative UTC timestamps so streak calculations pass consistently.
    """
    now = datetime.now(timezone.utc)
    t3 = (now - timedelta(hours=1)).isoformat()
    t2 = (now - timedelta(days=1)).isoformat()
    t1 = (now - timedelta(days=2)).isoformat()

    s1 = PoseSession(
        id=101, user_id="u_dash_v2", pose_label="Tree Pose",
        timestamp=t1, duration=30.0, accuracy=75.0,
        reps=0, symmetry_score=80.0, balance_score=78.0, stability_score=82.0,
        rom_score=85.0, hold_time=25.0, tracking_quality=95.0, failed_rules=[]
    )
    s2 = PoseSession(
        id=102, user_id="u_dash_v2", pose_label="Warrior II",
        timestamp=t2, duration=45.0, accuracy=85.0,
        reps=0, symmetry_score=88.0, balance_score=85.0, stability_score=87.0,
        rom_score=90.0, hold_time=40.0, tracking_quality=98.0, failed_rules=["left_knee_angle_low"]
    )
    s3 = PoseSession(
        id=103, user_id="u_dash_v2", pose_label="Tree Pose",
        timestamp=t3, duration=50.0, accuracy=92.0,
        reps=0, symmetry_score=94.0, balance_score=92.0, stability_score=95.0,
        rom_score=96.0, hold_time=48.0, tracking_quality=99.0, failed_rules=[]
    )
    return [s3, s2, s1]  # Descending order by timestamp


# ---------------------------------------------------------------------------
# 1. Overview Aggregation & Field Structure Tests
# ---------------------------------------------------------------------------

def test_dashboard_overview_structure(mock_user_sessions):
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_user_sessions):
        data = DashboardService.get_user_dashboard_overview("u_dash_v2", timeframe="30d")

        assert data['total_sessions'] == 3
        assert data['total_sessions_all'] == 3
        assert data['total_duration'] == 125.0
        assert data['overall_average_score'] == 84.0  # (92 + 85 + 75) / 3
        assert data['streak_days'] == 3

        bio = data['biomechanics']
        assert bio['symmetry'] == 87.3  # (94 + 88 + 80) / 3
        assert bio['balance'] == 85.0   # (92 + 85 + 78) / 3
        assert bio['stability'] == 88.0 # (95 + 87 + 82) / 3
        assert bio['rom'] == 90.3       # (96 + 90 + 85) / 3
        assert bio['tracking_quality'] == 97.3
        assert bio['tracking_status'] == 'Excellent'

        assert data['totals']['hold_time'] == 113.0


# ---------------------------------------------------------------------------
# 2. Timeframe Filtering Test
# ---------------------------------------------------------------------------

def test_dashboard_timeframe_filtering(mock_user_sessions):
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_user_sessions):
        data_7d = DashboardService.get_user_dashboard_overview("u_dash_v2", timeframe="7d")
        data_all = DashboardService.get_user_dashboard_overview("u_dash_v2", timeframe="all")

        assert data_7d['timeframe'] == "7d"
        assert data_all['timeframe'] == "all"
        assert data_all['total_sessions'] == 3


# ---------------------------------------------------------------------------
# 3. Deterministic Insights Engine Tests (Rules 1 - 5)
# ---------------------------------------------------------------------------

def test_deterministic_insights_evaluation(mock_user_sessions):
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_user_sessions):
        data = DashboardService.get_user_dashboard_overview("u_dash_v2", timeframe="30d")
        insights = data['insights']

        assert len(insights) >= 1
        rule_types = [ins['type'] for ins in insights]
        assert any(t in ['achievement', 'record', 'habit', 'info'] for t in rule_types)


def test_deterministic_insights_empty_user():
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=[]):
        data = DashboardService.get_user_dashboard_overview("u_empty", timeframe="30d")
        assert data['total_sessions'] == 0
        assert data['total_sessions_all'] == 0
        assert len(data['insights']) == 1
        assert data['insights'][0]['id'] == 'insight_empty'
        assert "first pose session" in data['insights'][0]['message']


# ---------------------------------------------------------------------------
# 4. Session Comparison Matrix (Latest vs Previous)
# ---------------------------------------------------------------------------

def test_session_comparison_deltas(mock_user_sessions):
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_user_sessions):
        data = DashboardService.get_user_dashboard_overview("u_dash_v2", timeframe="30d")
        comp = data['session_comparison']

        assert comp['has_comparison'] is True
        assert comp['latest_session']['pose_label'] == "Tree Pose"
        assert comp['previous_session']['pose_label'] == "Warrior II"

        m = comp['metrics']
        assert m['overall_score']['latest'] == 92.0
        assert m['overall_score']['prev'] == 85.0
        assert m['overall_score']['delta'] == "+7.0"
        assert m['overall_score']['semantic'] == "positive"


# ---------------------------------------------------------------------------
# 5. Legacy Session Detection & Safety
# ---------------------------------------------------------------------------

def test_legacy_session_detection():
    legacy_rec = {
        'id': 1, 'user_id': 'u_leg', 'pose_label': 'Plank',
        'timestamp': '2026-01-01T00:00:00Z', 'duration': 30.0, 'accuracy': 70.0
    }
    session = build_pose_session(legacy_rec)
    assert DashboardService._is_legacy_session(session) is True

    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=[session]):
        data = DashboardService.get_user_dashboard_overview("u_leg", timeframe="30d")
        assert data['recent_sessions'][0]['is_legacy'] is True


# ---------------------------------------------------------------------------
# 6. Personal Records & User Isolation
# ---------------------------------------------------------------------------

def test_personal_records_evaluation(mock_user_sessions):
    records = DashboardService._calculate_personal_records(mock_user_sessions)
    rec_types = [r['record_type'] for r in records]

    assert 'Highest Score' in rec_types
    assert 'Longest Hold' in rec_types
    assert 'Best Symmetry' in rec_types
    assert 'Best Balance' in rec_types
    assert 'Best Stability' in rec_types
    assert 'Best ROM' in rec_types


def test_user_isolation_query():
    with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=[]) as mock_fetch:
        data = DashboardService.get_user_dashboard_overview("user_isolated_123", timeframe="30d")
        mock_fetch.assert_called_once_with("user_isolated_123")
        assert data['total_sessions'] == 0


# ---------------------------------------------------------------------------
# 7. HTTP Endpoint Integration Tests (/api/dashboard/overview)
# ---------------------------------------------------------------------------

@pytest.fixture
def app_client():
    from backend.app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


def test_api_dashboard_overview_unauthenticated(app_client):
    res = app_client.get('/api/dashboard/overview?timeframe=30d')
    assert res.status_code == 302
    assert '/login' in res.headers['Location']


def test_api_dashboard_overview_authenticated_valid_timeframes(app_client, mock_user_sessions):
    from backend.app.models.user import User
    from backend.app.services.auth_service import AuthService

    dummy_user = User('00000000-0000-0000-0000-000000000001', 'testuser', 'test@example.com', 'hash')

    with patch.object(AuthService, 'get_user_by_id', return_value=dummy_user):
        with app_client.session_transaction() as sess:
            sess['_user_id'] = '00000000-0000-0000-0000-000000000001'

        with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=mock_user_sessions):
            # Test 30d
            r30 = app_client.get('/api/dashboard/overview?timeframe=30d')
            assert r30.status_code == 200
            assert r30.content_type == 'application/json'
            d30 = r30.get_json()
            assert d30['timeframe'] == '30d'
            assert d30['total_sessions'] == 3
            assert isinstance(d30['sessions'], list)

            # Test 7d
            r7 = app_client.get('/api/dashboard/overview?timeframe=7d')
            assert r7.status_code == 200
            d7 = r7.get_json()
            assert d7['timeframe'] == '7d'

            # Test all
            r_all = app_client.get('/api/dashboard/overview?timeframe=all')
            assert r_all.status_code == 200
            d_all = r_all.get_json()
            assert d_all['timeframe'] == 'all'


def test_api_dashboard_overview_invalid_timeframe_returns_400(app_client):
    from backend.app.models.user import User
    from backend.app.services.auth_service import AuthService

    dummy_user = User('00000000-0000-0000-0000-000000000001', 'testuser', 'test@example.com', 'hash')

    with patch.object(AuthService, 'get_user_by_id', return_value=dummy_user):
        with app_client.session_transaction() as sess:
            sess['_user_id'] = '00000000-0000-0000-0000-000000000001'

        res = app_client.get('/api/dashboard/overview?timeframe=invalid_tf')
        assert res.status_code == 400
        data = res.get_json()
        assert data['status'] == 'error'
        assert 'Invalid timeframe' in data['message']


def test_api_dashboard_overview_legacy_null_handling(app_client):
    from backend.app.models.user import User
    from backend.app.services.auth_service import AuthService

    dummy_user = User('00000000-0000-0000-0000-000000000001', 'testuser', 'test@example.com', 'hash')
    legacy_rec = {
        'id': 99, 'user_id': '00000000-0000-0000-0000-000000000001', 'pose_label': 'Plank',
        'timestamp': '2026-01-01T00:00:00Z', 'duration': 30.0, 'accuracy': 70.0
    }
    legacy_session = build_pose_session(legacy_rec)

    with patch.object(AuthService, 'get_user_by_id', return_value=dummy_user):
        with app_client.session_transaction() as sess:
            sess['_user_id'] = '00000000-0000-0000-0000-000000000001'

        with patch.object(SessionRepository, 'fetch_sessions_by_user_id', return_value=[legacy_session]):
            res = app_client.get('/api/dashboard/overview?timeframe=30d')
            assert res.status_code == 200
            data = res.get_json()
            assert data['biomechanics']['symmetry'] is None
            assert data['biomechanics']['balance'] is None
            assert data['biomechanics']['stability'] is None
            assert data['biomechanics']['rom'] is None
            assert data['recent_sessions'][0]['is_legacy'] is True

