# PostureSense v2 — Real Session Analytics Persistence Specification

## 1. Overview

This specification documents the implementation of the P0 analytics persistence layer in PostureSense v2. It defines how real-time biomechanics, posture scoring, repetitions, hold times, tracking quality, and failed pose rules computed by the browser perception pipeline are validated, transmitted, and persisted in Supabase.

---

## 2. Session Lifecycle & Authoritative Completion Event

1. **Session Initialization:** When a user starts posture detection on `templates/app.html`, `PosePipelineController` initializes and starts all 9 browser JS engines (`CameraEngine`, `MediaPipeEngine`, `LandmarkEngine`, `BiomechanicsEngine`, `PoseRuleEngine`, `VisualizationEngine`, `MovementEngine`, `ScoringEngine`, `FeedbackEngine`).
2. **Real-Time Telemetry Harvesting:** As the user performs exercises, the pipeline fires EventBus events:
   - `landmarks.validated` $\to$ tracking quality (`latestTelemetry.tracking_quality`).
   - `biomechanics.updated` $\to$ symmetry score (`symmetry_score`), balance score (`balance_score`).
   - `score.updated` $\to$ overall posture score, stability score (`components.stability`), ROM score (`components.rom`).
   - `exercise.rep_completed` $\to$ completed reps (`reps`), accumulated hold time (`hold_time`).
   - `feedback.generated` $\to$ triggered pose rule IDs (`failed_rules`).
3. **Authoritative Session Completion:** A session is finalized ONCE when:
   - The user transitions to a different pose (`pose.detected`).
   - The user pauses or closes the camera (`stopCamera` / `closeCamera`).
4. **Idempotency Guarantee:** Duplicate frame-by-frame saves are prevented using a client-side set (`savedSessionKeys`) keyed by `${poseLabel}_${poseStartTime}_${durationSec}`.

---

## 3. Data Contract

The JSON payload posted to `POST /save_pose_session` complies with the following contract:

```json
{
  "pose_label": "Warrior II",
  "duration": 45.0,
  "accuracy": 92.5,
  "reps": 0,
  "symmetry_score": 94.2,
  "balance_score": 88.5,
  "stability_score": 91.0,
  "rom_score": 95.0,
  "hold_time": 42.5,
  "tracking_quality": 98.4,
  "failed_rules": [
    "left_knee_angle_low"
  ]
}
```

---

## 4. Server-Side Validation Rules

`SessionService.save_session()` enforces strict business validation rules before persisting:

- `pose_label`: Must be a non-empty string, excluding `'Unknown'` and `'Scanning...'`.
- `duration`: Numeric, $\ge 0.0$ seconds.
- `accuracy`: Numeric, $\in [0.0, 100.0]$.
- `reps`: Integer, $\ge 0$.
- `symmetry_score`: Numeric, $\in [0.0, 100.0]$.
- `balance_score`: Numeric, $\in [0.0, 100.0]$.
- `stability_score`: Numeric, $\in [0.0, 100.0]$.
- `rom_score`: Numeric, $\in [0.0, 100.0]$.
- `tracking_quality`: Numeric, $\in [0.0, 100.0]$.
- `hold_time`: Numeric, $\ge 0.0$ seconds.
- `failed_rules`: Must be a JSON array containing string rule identifiers.

If any parameter violates these constraints, `SessionService` rejects the submission and returns HTTP 400 Bad Request with an explicit validation error message.

---

## 5. Database Schema & Migration

Database table: `public.pose_sessions` in Supabase PostgreSQL:

```sql
ALTER TABLE public.pose_sessions
    ADD COLUMN IF NOT EXISTS reps integer NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS symmetry_score double precision NOT NULL DEFAULT 100.0,
    ADD COLUMN IF NOT EXISTS balance_score double precision NOT NULL DEFAULT 100.0,
    ADD COLUMN IF NOT EXISTS stability_score double precision NOT NULL DEFAULT 100.0,
    ADD COLUMN IF NOT EXISTS rom_score double precision NOT NULL DEFAULT 100.0,
    ADD COLUMN IF NOT EXISTS hold_time double precision NOT NULL DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS tracking_quality double precision NOT NULL DEFAULT 100.0,
    ADD COLUMN IF NOT EXISTS failed_rules jsonb NOT NULL DEFAULT '[]'::jsonb;
```

---

## 6. Legacy Sessions & Backward Compatibility

- **Database Reading:** Legacy rows stored prior to this migration automatically receive safe schema defaults (`reps=0`, `symmetry_score=100.0`, `failed_rules=[]`).
- **Client Fallbacks:** Optional parameters default safely if omitted by legacy API clients, while new v2 frontend code passes actual computed telemetry.
- **Report Generation:** `ReportService` consumes actual `target.reps`, `target.tracking_quality`, `target.symmetry_score`, and `target.failed_rules` from database models, eliminating hardcoded fallbacks (`completed_reps: 10`, `tracking_quality: 100.0`).

---

## 7. Security & Privacy Boundaries

- **Local Devices:** Video feeds, canvas renders, and 33 MediaPipe 3D landmark coordinate arrays remain strictly browser-local.
- **Server Persistence:** Only aggregated session performance metrics are sent to Flask and stored in Supabase.
- **User Data Isolation:** All database reads and writes are strictly scoped to `current_user.id` using Flask-Login and Supabase `.eq('user_id', str(user_id))`.
