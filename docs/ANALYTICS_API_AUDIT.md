# PostureSense v2 — Analytics API Audit

## Overview

This document provides a comprehensive audit of all backend REST API endpoints related to analytics, dashboard statistics, session persistence, and report generation in PostureSense v2.

---

# 1. Dashboard & Core Session Endpoints

### `GET /api/dashboard_stats`
- **Blueprint / Service:** `dashboard_bp` (`backend/app/blueprints/dashboard/routes.py`) $\to$ `DashboardService`
- **Authentication:** Required (`@login_required`)
- **Request Parameters:** None
- **Response Format:** JSON
```json
{
  "total_sessions": 12,
  "total_duration": 485.5,
  "avg_accuracy": 87.4,
  "pose_counts": {
    "Tree Pose": 5,
    "Warrior II": 4,
    "Plank": 3
  },
  "recent_sessions": [
    {
      "timestamp": "2026-08-12 14:30:00",
      "pose_label": "Tree Pose",
      "duration": 45.0,
      "accuracy": 92.5
    }
  ]
}
```
- **Available Metrics:** Total session count, accumulated practice duration (seconds), overall mean accuracy score, session counts grouped by pose label, 20 most recent sessions.
- **Missing Metrics:** Streak days, score trends, biomechanics metrics (symmetry, balance, stability, ROM), rep counts, hold durations, personal record notifications.

---

### `POST /save_pose_session`
- **Blueprint / Service:** `api_bp` (`backend/app/blueprints/api/routes.py`) $\to$ `SessionService` $\to$ `SessionRepository`
- **Authentication:** Required (`@login_required`)
- **Request Parameters (JSON Body):**
```json
{
  "pose_label": "Tree Pose",
  "duration": 45.0,
  "accuracy": 92.5
}
```
- **Response Format:** JSON
```json
{
  "status": "success",
  "message": "Pose session saved"
}
```
- **Available Metrics:** Saves `pose_label`, `duration`, `accuracy` into Supabase `pose_sessions` table.
- **Missing Metrics:** Does not accept or save reps, symmetry_score, balance_score, stability_score, rom_score, hold_time, tracking_quality, or raw landmark JSON.

---

# 2. Analytics Endpoints

### `GET /api/analytics/summary`
- **Blueprint / Service:** `api_bp` $\to$ `AnalyticsRepository.get_user_analytics_summary()`
- **Authentication:** Required (`@login_required`)
- **Request Parameters:** None
- **Response Format:** JSON
```json
{
  "user_id": "uuid-string",
  "total_sessions": 12,
  "total_duration": 485.5,
  "overall_average_score": 87.4,
  "exercise_counts": {
    "Tree Pose": 5,
    "Warrior II": 4
  },
  "recent_sessions": [
    {
      "session_id": 101,
      "timestamp": "2026-08-12 14:30:00",
      "pose_label": "Tree Pose",
      "duration": 45.0,
      "accuracy": 92.5
    }
  ]
}
```
- **Available Metrics:** Total sessions, total duration, overall mean score, breakdown of session count by pose, 10 most recent sessions.
- **Missing Metrics:** `streak_days` (hardcoded to 0 in repo unless updated), active trends dict, personal records array, biomechanics breakdown.

---

### `GET /api/analytics/progress`
- **Blueprint / Service:** `api_bp` $\to$ `AnalyticsRepository.get_user_progress()`
- **Authentication:** Required (`@login_required`)
- **Request Parameters:** None
- **Response Format:** JSON
```json
{
  "user_id": "uuid-string",
  "total_sessions": 12,
  "latest_score": 92.5,
  "overall_average": 87.4,
  "improvement_percentage": 5.2
}
```
- **Available Metrics:** Total sessions, latest session score, overall mean score, simple percentage change from oldest to newest session.
- **Missing Metrics:** Timeframe-specific progress (7-day vs 30-day), dimensional progress (symmetry improvement, ROM improvement).

---

### `GET /api/analytics/exercises`
- **Blueprint / Service:** `api_bp` $\to$ `AnalyticsRepository.get_exercise_history()`
- **Authentication:** Required (`@login_required`)
- **Request Parameters:** None
- **Response Format:** JSON
```json
{
  "user_id": "uuid-string",
  "exercises": {
    "Tree Pose": {
      "exercise_id": "Tree Pose",
      "total_sessions": 5,
      "total_duration": 225.0,
      "best_score": 95.0,
      "average_score": 89.2
    }
  }
}
```
- **Available Metrics:** Grouped history per exercise/pose including total sessions, total duration, best score, average score.
- **Missing Metrics:** `best_rom`, `average_rom`, `average_stability`, `average_symmetry`, `total_repetitions`, `last_performed` timestamp. (These fields exist in `ExerciseAnalytics` contract but cannot be populated from the database because DB lacks component columns).

---

### `GET /api/analytics/trends`
- **Blueprint / Service:** `api_bp` $\to$ `AnalyticsRepository.get_user_trends()`
- **Authentication:** Required (`@login_required`)
- **Request Parameters:** None
- **Response Format:** JSON
```json
{
  "user_id": "uuid-string",
  "overall_score_trend": {
    "metric_name": "overall_score",
    "trend_direction": "IMPROVING",
    "observation_count": 10,
    "percentage_change": 8.5,
    "sample_values": [80.0, 82.5, 85.0, 84.0, 88.0, 92.5]
  }
}
```
- **Available Metrics:** `trend_direction` (`IMPROVING`, `DECLINING`, `STABLE`, `INSUFFICIENT_DATA`), observation count, percentage change over last 10 sessions, sample values array.
- **Missing Metrics:** Slope value, timeframe parameters (e.g. `?timeframe=7d`), biomechanics dimension trends (symmetry trend, ROM trend).

---

### `GET /api/analytics/records`
- **Blueprint / Service:** `api_bp` $\to$ `AnalyticsRepository.get_personal_records()`
- **Authentication:** Required (`@login_required`)
- **Request Parameters:** None
- **Response Format:** JSON
```json
{
  "user_id": "uuid-string",
  "records": [
    {
      "record_type": "Highest Score",
      "exercise_id": "Tree Pose",
      "value": 95.0,
      "unit": "points"
    },
    {
      "record_type": "Longest Hold / Duration",
      "exercise_id": "Plank",
      "value": 120.0,
      "unit": "seconds"
    }
  ]
}
```
- **Available Metrics:** All-time Highest Score and Longest Hold duration based on `pose_sessions` table.
- **Missing Metrics:** Best Symmetry record, Best Balance record, Best ROM record, Most Repetitions record, `achieved_at` timestamp, `previous_value`.

---

# 3. Reports & Export Endpoints

### `GET /reports/session/<session_id>`
- **Blueprint / Service:** `api_bp` $\to$ `ReportService.generate_session_report()` $\to$ `ReportEngine`
- **Authentication:** Required (`@login_required`)
- **Response Format:** JSON (`SessionReport.to_dict()`)
- **Available Metrics:** `metadata`, `session_info`, `performance`, `assessment`, `data_quality`.
- **Limitation / Missing Field Note:** Because `pose_sessions` does not store reps or tracking quality, `ReportService` fallbacks to hardcoded values (`completed_reps: 10`, `tracking_quality: 100.0`).

### `GET /reports/exercise/<exercise_id>`
- **Blueprint / Service:** `api_bp` $\to$ `ReportService.generate_exercise_report()`
- **Authentication:** Required (`@login_required`)
- **Response Format:** JSON (`ExerciseReport.to_dict()`)

### `GET /reports/progress`
- **Blueprint / Service:** `api_bp` $\to$ `ReportService.generate_progress_report()`
- **Authentication:** Required (`@login_required`)
- **Response Format:** JSON (`ProgressReport.to_dict()`)

### `GET /reports/comprehensive`
- **Blueprint / Service:** `api_bp` $\to$ `ReportService.generate_comprehensive_report()`
- **Authentication:** Required (`@login_required`)
- **Response Format:** JSON (`ComprehensiveReport.to_dict()`)

### `GET /reports/session/<session_id>/pdf`
- **Blueprint / Service:** `api_bp` $\to$ `ReportService.export_session_pdf()`
- **Response Format:** Inline HTML rendering PDF report template.

### `GET /reports/session/<session_id>/json`
- **Blueprint / Service:** `api_bp` $\to$ `ReportService.export_session_json()`
- **Response Format:** JSON attachment download.

### `GET /reports/progress.csv`
- **Blueprint / Service:** `api_bp` $\to$ `ReportService.export_progress_csv()`
- **Response Format:** CSV attachment download.
