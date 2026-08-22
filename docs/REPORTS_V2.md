# PostureSense v2 — Reports V2 & Rich Analytics Export Specification

## Overview

The Reports V2 & Rich Analytics Export subsystem standardizes all user-facing evaluation reports (Session Reports, Exercise Reports, Progress Reports, Comprehensive Reports) and downloadable exports (PDF, JSON, CSV).

All report types and export formats consume the finalized persisted session telemetry pipeline (`public.pose_sessions` $\to$ `SessionRepository` $\to$ `AnalyticsRepository` $\to$ `DashboardService` $\to$ `ReportService` $\to$ `ReportEngine`).

---

## Architectural Principles & Strict Constraints

1. **No Perception Processing**: Reports do NOT execute MediaPipe, process camera frames, or evaluate landmark coordinate arrays.
2. **No Score Recalculation**: Posture scores, biomechanics metrics, and tracking quality are read directly from database persistence.
3. **No LLM Generation**: Reports do NOT invoke LLM prompts or non-deterministic natural language engines. All insights are generated deterministically.
4. **Source of Truth**: Supabase `public.pose_sessions` and `SessionRepository` are the single source of truth.
5. **Privacy Guarantee**: Raw camera video streams and landmark coordinate arrays NEVER leave local device memory. Reports only consume derived numerical telemetry.

---

## Report Data Schemas (Schema Version 2.0.0)

### 1. Session Report (`SessionReport`)
- **Metadata**: `report_type="session"`, `user_id`, `generated_at`, `source_data_version="2.0.0"`, `application_version="2.0.0"`, `schema_version="2.0.0"`.
- **Session Info**: `session_id`, `pose_id`, `pose_name`, `exercise_id`, `exercise_name`, `started_at`, `completed_at`, `timestamp`, `duration`, `completed_reps`.
- **Performance**: `overall_score`, `score_confidence`, `score_category` (`Excellent` $\ge 90$, `Good` $\ge 75$, `Fair` $\ge 50$, `Needs Improvement` $< 50$).
- **Movement**: `reps`, `hold_time`, `average_rep_duration`, `average_cadence`, `rom_percentage`, `movement_quality`.
- **Biomechanics**: `symmetry_score`, `balance_score`, `stability_score`, `rom_score` (preserves `NULL` for unmeasured/legacy sessions).
- **Tracking**: `tracking_quality`, `quality_gate_passed`.
- **Pose Rules**: `matched_rules`, `failed_rules`.
- **Feedback**: `strengths`, `weak_areas`, `common_mistakes`.
- **Data Quality**: `tracking_quality`, `quality_gate_passed`, `unavailable_metrics`, `quality_notice`, `is_legacy`.

### 2. Progress Report (`ProgressReport`)
- **Reporting Period**: `7d`, `30d`, `all` (default `30d`).
- **Overall Summary**: `total_sessions`, `total_duration`, `average_score`, `average_symmetry`, `average_balance`, `average_stability`, `average_rom`, `average_tracking_quality`, `streak_days`, `seven_day_delta`.
- **Trends**: Direction and delta for score and biomechanics dimensions.
- **Personal Records**: 7 record categories (`Highest Score`, `Longest Hold`, `Best Symmetry`, `Best Balance`, `Best Stability`, `Best ROM`, `Most Reps`).
- **Comparison**: Latest vs Previous session comparison matrix.
- **Data Quality**: Summary tracking quality, tracking status, data quality notice.

### 3. Exercise Report (`ExerciseReport`)
- **Exercise Info**: `exercise_id`, `pose_name`, `total_sessions`, `total_repetitions`, `last_performed`.
- **Performance Summary**: `average_score`, `best_score`, `average_hold`, `longest_hold`, `average_reps`, `best_reps`, `average_symmetry`, `best_symmetry`, `average_balance`, `best_balance`, `average_stability`, `best_stability`, `average_rom`, `best_rom`.
- **Recent History**: Tabular array of recent pose session executions.

### 4. Comprehensive Report (`ComprehensiveReport`)
Integrates all 10 evaluation portfolio sections:
1. Executive Summary
2. Overall Progress
3. Score Trends
4. Biomechanics Trends
5. Personal Records
6. Pose/Exercise Performance
7. Recent Sessions
8. Session Comparison Matrix
9. Feedback Summary
10. Data Quality Notice

---

## Exporters & Downloads

### 1. JSON Export (`export_json()`)
Serializes canonical `v2.0.0` report contract objects to formatted JSON. Guarantees deterministic key ordering, ISO timestamps, and `NULL` preservation.

### 2. CSV Export (`export_csv()`)
Generates RFC-4180 spreadsheet-compatible CSV file containing columns:
`Date, Pose, Exercise, Score, Score Category, Duration, Repetitions, Hold Time, Cadence, Symmetry, Balance, Stability, ROM, Tracking Quality, Failed Rules`
- `NULL` values render as `"N/A"` (never defaulted to 0 or 100).
- Multiple failed pose rules formatted as compact semicolon-delimited lists.

### 3. PDF / HTML Export (`export_pdf()`)
Renders a styled assessment document featuring:
- PostureSense AI header and metadata.
- Overview performance cards.
- Biomechanics table (Symmetry, Balance, Stability, ROM).
- Movement quality and tracking quality breakdown.
- Form evaluation and pose rule corrections.
- Explicit Data Quality & Privacy Guarantee notice.

---

## Legacy Session & NULL Handling

Older pose sessions recorded prior to v2 lack rich biomechanics metrics.
- All `NULL` fields (`symmetry_score`, `balance_score`, `stability_score`, `rom_score`, `tracking_quality`) preserve `NULL`.
- In HTML/PDF reports, `NULL` values display as `"Not available"`.
- In CSV exports, `NULL` values display as `"N/A"`.
- In JSON exports, `NULL` values display as `null`.
- Legacy sessions flag `is_legacy = True` and emit the notice: `"Detailed biomechanics data was not available for this session."`

---

## Authorization & Privacy Isolation

- All API endpoints (`/api/reports/*`) and HTML views (`/reports/view/*`) require `@login_required`.
- Queries filter strictly by `current_user.id`.
- Attempts to query reports for unauthorized session IDs return default empty structures for the requesting user (IDOR protection).
