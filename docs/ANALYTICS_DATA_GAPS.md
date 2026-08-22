# PostureSense v2 — Analytics Data Gaps & Infrastructure Requirements

## Overview

This document specifies the exact data gaps identified during the audit of the PostureSense v2 perception pipeline, persistence layer, API endpoints, and dashboard. It outlines the schema, API, and persistence changes required to unlock advanced analytics and user progress tracking.

---

# 1. Comprehensive Data Gap Inventory

| Data Gap | Why Needed | Source Engine | Persistence Status | API Change | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Repetitions Count** (`reps`) | Track exercise volume, dynamic rep counts, and rep-based personal records. | `MovementEngine` | ✅ **RESOLVED** (`reps` integer DEFAULT 0). | Updated `POST /save_pose_session` body & analytics responses. | **P0 (Resolved)** |
| **Symmetry Score** (`symmetry_score`) | Track bilateral posture balance, left/right shoulder/hip alignment trends over time. | `BiomechanicsEngine` | ✅ **RESOLVED** (`symmetry_score` float NULL). | Exposed `symmetry_score` in `/api/analytics/*` & `/api/dashboard/overview`. | **P0 (Resolved)** |
| **Balance Score** (`balance_score`) | Measure postural stability and center-of-mass alignment over base of support. | `BiomechanicsEngine` | ✅ **RESOLVED** (`balance_score` float NULL). | Exposed `balance_score` in `/api/analytics/*` & `/api/dashboard/overview`. | **P0 (Resolved)** |
| **Stability Score** (`stability_score`) | Measure body sway and posture hold steadiness during static poses. | `ScoringEngine` / `BiomechanicsEngine` | ✅ **RESOLVED** (`stability_score` float NULL). | Exposed `stability_score` in `/api/analytics/*` & `/api/dashboard/overview`. | **P0 (Resolved)** |
| **Range of Motion** (`rom_score`) | Measure flexibility, joint movement depth, and ROM progression per exercise. | `MovementEngine` | ✅ **RESOLVED** (`rom_score` float NULL). | Exposed `rom_score` in `/api/analytics/*` & `/api/dashboard/overview`. | **P0 (Resolved)** |
| **Hold Duration** (`hold_time`) | Measure static pose hold endurance (distinct from total camera session duration). | `MovementEngine` | ✅ **RESOLVED** (`hold_time` float DEFAULT 0.0). | Exposed `hold_time` in `/api/analytics/*` & `/api/dashboard/overview`. | **P0 (Resolved)** |
| **Tracking Quality** (`tracking_quality`) | Filter low-confidence frames, prevent corrupted landmark data from affecting trends. | `LandmarkEngine` | ✅ **RESOLVED** (`tracking_quality` float NULL). | Included `tracking_quality` in session summaries & reports. | **P0 (Resolved)** |
| **Failed Rules JSON** (`failed_rules`) | Generate targeted coaching insights, common mistakes history, and posture flaw trends. | `PoseRuleEngine` / `FeedbackEngine` | ✅ **RESOLVED** (`failed_rules` jsonb DEFAULT '[]'). | Included `failed_rules` in session reports & analytics API. | **P1 (Resolved)** |
| **Streak Tracking** (`streak_days`) | Drive user engagement and habit building via daily practice streaks. | `AnalyticsEngine` | Derived from `pose_sessions.timestamp`. | Included calculated `streak_days` in `/api/dashboard/overview`. | **P1 (Resolved)** |
| **Personal Records Persistence** | Track historical achievements (best hold, best score, highest reps) across restarts. | `AnalyticsEngine` | Derived dynamically from indexed `pose_sessions`. | Enhanced `/api/analytics/records` response. | **P1 (Resolved)** |


---

# 2. Database Schema Migration

To resolve these data gaps cleanly with `NULL` indicating unmeasured metrics, `public.pose_sessions` has been migrated:

```sql
-- Migration 001: Rich Session Persistence & Analytics Pipeline
ALTER TABLE public.pose_sessions
    ADD COLUMN IF NOT EXISTS reps integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS symmetry_score double precision NULL,
    ADD COLUMN IF NOT EXISTS balance_score double precision NULL,
    ADD COLUMN IF NOT EXISTS stability_score double precision NULL,
    ADD COLUMN IF NOT EXISTS rom_score double precision NULL,
    ADD COLUMN IF NOT EXISTS hold_time double precision NOT NULL DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS tracking_quality double precision NULL,
    ADD COLUMN IF NOT EXISTS failed_rules jsonb NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE public.pose_sessions
    ALTER COLUMN symmetry_score DROP DEFAULT,
    ALTER COLUMN balance_score DROP DEFAULT,
    ALTER COLUMN stability_score DROP DEFAULT,
    ALTER COLUMN rom_score DROP DEFAULT,
    ALTER COLUMN tracking_quality DROP DEFAULT;
```


---

# 3. Required API Pipeline Enhancements

1. **`POST /save_pose_session` Request Body Expansion:**
```json
{
  "pose_label": "Tree Pose",
  "duration": 45.0,
  "accuracy": 92.5,
  "reps": 0,
  "symmetry_score": 94.2,
  "balance_score": 88.5,
  "stability_score": 91.0,
  "rom_score": 95.0,
  "hold_time": 42.5,
  "tracking_quality": 98.4,
  "failed_rules": ["left_knee_angle_low"]
}
```

2. **Backend Repository Mapping Updates:**
   - Update `PoseSession` model in `backend/app/models/pose_session.py` to parse new fields.
   - Update `SessionRepository.create_session()` to pass expanded payload to Supabase.
   - Update `AnalyticsRepository` to aggregate symmetry, balance, stability, ROM, and hold time trends.
