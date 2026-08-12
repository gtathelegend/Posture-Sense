"""
Unit & Integration Tests for ReportEngine (Milestone 8)
======================================================
Tests report composition, JSON export, CSV formatting, PDF generation,
deterministic numerical fixtures, data quality notices, user isolation,
and EngineRuntime registration.
"""

import json
import pytest
from shared.events.event_bus import EventBus
from shared.engines.report_engine import ReportEngine
from shared.contracts.report import SessionReport, ExerciseReport, ProgressReport, ComprehensiveReport, ExportResult
from shared.core.runtime.runtime import EngineRuntime
from shared.types.enums import EngineStatus
from backend.app.services.report_service import ReportService


@pytest.fixture
def event_bus():
    return EventBus(debug_mode=True)


@pytest.fixture
def report_engine(event_bus):
    engine = ReportEngine(event_bus=event_bus)
    engine.initialize()
    engine.start()
    return engine


# 1. Lifecycle & Runtime Registration Test
def test_report_engine_lifecycle(event_bus):
    engine = ReportEngine(event_bus=event_bus)
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


def test_report_runtime_registration(event_bus):
    runtime = EngineRuntime(event_bus=event_bus)
    engine = ReportEngine(event_bus=event_bus)
    record = runtime.register(
        engine,
        priority=11,
        dependencies=["analytics_engine", "feedback_engine", "scoring_engine", "movement_engine", "pose_rule_engine", "biomechanics_engine"]
    )
    assert record.id == "ReportEngine"
    assert record.priority == 11


# 2. Session Report Composition Test
def test_generate_session_report(report_engine):
    session_data = {
        "session_id": "sess_101",
        "user_id": "usr_alpha",
        "exercise_id": "bodyweight_squat",
        "duration": 45.0,
        "average_score": 88.5,
        "completed_reps": 12,
        "valid_reps": 10,
        "invalid_reps": 2,
        "tracking_quality": 98.0
    }
    score_report = {
        "components": {"form": {"score": 90.0}, "rom": {"score": 85.0}},
        "quality_gate_passed": True,
        "score_confidence": 0.95
    }
    feedback_items = [
        {"message": "Keep knees tracking over toes", "severity": "medium"}
    ]

    report = report_engine.generate_session_report(session_data, score_report, feedback_items)
    assert isinstance(report, SessionReport)
    rep_dict = report.to_dict()

    assert rep_dict["metadata"]["report_type"] == "session"
    assert rep_dict["session_info"]["session_id"] == "sess_101"
    assert rep_dict["performance"]["overall_score"] == 88.5
    assert rep_dict["data_quality"]["tracking_quality"] == 98.0
    assert len(rep_dict["assessment"]["feedback_messages"]) == 1


# 3. JSON Export Test
def test_export_json(report_engine):
    session_data = {"session_id": "sess_json_1", "average_score": 80.0}
    report = report_engine.generate_session_report(session_data)

    export_res = report_engine.export_json(report.to_dict())
    assert isinstance(export_res, ExportResult)
    assert export_res.format == "json"
    assert export_res.content_type == "application/json"

    parsed = json.loads(export_res.content)
    assert parsed["metadata"]["report_type"] == "session"
    assert parsed["performance"]["overall_score"] == 80.0


# 4. CSV Export Test
def test_export_csv(report_engine):
    sessions = [
        {"timestamp": "2026-08-09T10:00:00Z", "exercise_id": "squat", "average_score": 85.0, "completed_reps": 10, "duration": 30.0, "tracking_quality": 100.0},
        {"timestamp": "2026-08-09T11:00:00Z", "exercise_id": "squat", "average_score": 90.0, "completed_reps": 12, "duration": 35.0, "tracking_quality": 95.0}
    ]

    export_res = report_engine.export_csv(sessions)
    assert isinstance(export_res, ExportResult)
    assert export_res.format == "csv"
    assert "Date,Exercise,Score,ROM,Stability,Symmetry,Cadence,Repetitions,Duration,Tracking Quality" in export_res.content
    assert "2026-08-09T10:00:00Z,squat,85.0" in export_res.content


# 5. PDF HTML Generation Test
def test_export_pdf(report_engine):
    session_data = {"session_id": "sess_pdf_1", "average_score": 92.5}
    report = report_engine.generate_session_report(session_data)

    export_res = report_engine.export_pdf(report.to_dict())
    assert isinstance(export_res, ExportResult)
    assert export_res.format == "pdf"
    assert "PostureSense AI Performance Report" in export_res.content
    assert "92.5 / 100" in export_res.content
    assert "DATA QUALITY NOTICE:" in export_res.content


# 6. Deterministic Numerical Fixture Test (70, 75, 80, 85, 90)
def test_deterministic_numerical_fixture(report_engine):
    summary_data = {
        "user_id": "test_user",
        "total_sessions": 5,
        "overall_average_score": 80.0,
        "active_trends": {
            "overall_score": {"trend_direction": "IMPROVING", "percentage_change": 28.57}
        },
        "personal_records": [
            {"record_type": "Highest Score", "value": 90.0}
        ],
        "recent_sessions": [
            {"session_id": "s1", "average_score": 70.0},
            {"session_id": "s5", "average_score": 90.0}
        ]
    }

    prog_report = report_engine.generate_progress_report(summary_data)
    assert prog_report.overall_summary["overall_average_score"] == 80.0
    assert prog_report.trends["overall_score"]["percentage_change"] == 28.57
    assert prog_report.personal_records[0]["value"] == 90.0


# 7. User Data Isolation Test
def test_user_isolation(report_engine):
    report_engine.set_active_user("user_a")
    rep_a = report_engine.generate_session_report({"session_id": "sa_1", "user_id": "user_a", "average_score": 95.0})

    report_engine.set_active_user("user_b")
    rep_b = report_engine.generate_session_report({"session_id": "sb_1", "user_id": "user_b", "average_score": 50.0})

    assert rep_a.metadata.user_id == "user_a"
    assert rep_b.metadata.user_id == "user_b"
    assert rep_a.performance["overall_score"] == 95.0
    assert rep_b.performance["overall_score"] == 50.0
