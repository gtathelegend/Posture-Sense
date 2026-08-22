# PostureSense Reports & Export Engine Specification

**Version:** 2.0.0  
**Status:** Completed (Milestone 8)  
**Priority:** 11  

---

## 1. Overview

The `ReportEngine` (`shared/engines/report_engine.py` & `static/assets/js/engines/report_engine.js`) composes human-readable evaluation reports and downloadable exports (`PDF`, `JSON`, `CSV`) from finalized upstream assessment, feedback, and analytics outputs.

### Key Architectural Constraints
- **NO Recalculation**: Does not recalculate biomechanics, scores, pose rules, movement tracking, or analytics trends.
- **NO Feedback Generation**: Reuses existing `FeedbackResult` / `FeedbackSessionSummary` outputs; never invents new coaching advice.
- **NO Camera / Landmark Processing**: Operates downstream of completed assessment events.
- **NO Machine Learning**: Uses deterministic report composition algorithms.
- **Strict User Isolation**: Scopes all report queries and exports to authenticated `user_id`.
- **Data Quality Preservation**: Preserves upstream score confidence and quality gate warnings; never invents missing data.

---

## 2. Dependencies & Priority

- **Priority:** 11
- **Runtime Dependencies:** `analytics_engine`, `feedback_engine`, `scoring_engine`, `movement_engine`, `pose_rule_engine`, `biomechanics_engine`
- **Events Published to EventBus:**
  - `report.generated`: Dispatched when a report is composed (`SessionReport`, `ExerciseReport`, `ProgressReport`, `ComprehensiveReport`).
  - `report.exported`: Dispatched when an export file payload is rendered (`JSON`, `CSV`, `PDF`).

---

## 3. Report Contracts

1. **`ReportMetadata`**: Versioning and audit payload (`report_type`, `user_id`, `generated_at`, `source_data_version`, `application_version`, `schema_version`).
2. **`SessionReport`**: Single-session report (`metadata`, `session_info`, `performance`, `assessment`, `data_quality`).
3. **`ExerciseReport`**: Historical exercise performance report (`metadata`, `exercise_info`, `performance_summary`, `recent_history`).
4. **`ProgressReport`**: Longitudinal progress report (`metadata`, `overall_summary`, `trends`, `personal_records`, `comparison`).
5. **`ComprehensiveReport`**: Master all-in-one report container.
6. **`ExportResult`**: Download container (`report_type`, `format` [`json`, `csv`, `pdf`], `filename`, `content`, `content_type`).

---

## 4. Supported Export Formats

- **JSON Export**: Serializes versioned report contracts with `schema_version: "2.0.0"`.
- **CSV Export**: Formats session records into RFC-4180 spreadsheet CSV (`Date, Pose, Exercise, Score, Score Category, Duration, Repetitions, Hold Time, Cadence, Symmetry, Balance, Stability, ROM, Tracking Quality, Failed Rules`).
- **PDF Export**: Renders clean, styled HTML/PDF output with PostureSense branding, executive summary, performance cards, biomechanics table, feedback breakdown, personal records, and data quality & privacy notice.

See [REPORTS_V2.md](file:///d:/Github/Posture-Sense/docs/REPORTS_V2.md) for full technical documentation.

---

## 5. Security & Isolation

- All endpoints (`/api/reports/...`) enforce `@login_required` and query filters by `current_user.id`.
- User A cannot access or export User B's reports by guessing IDs or traversing paths.
- Exported reports are streamed directly as inline/download attachments and are never written to public static directories.
