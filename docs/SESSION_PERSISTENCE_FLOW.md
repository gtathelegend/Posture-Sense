# PostureSense v2 — Session Persistence Flow Specification

## 1. End-to-End Data Pipeline Architecture

```text
  [CameraEngine]
        │ (raw video frames)
        ▼
  [MediaPipeEngine]
        │ (33 3D landmarks array)
        ▼
  [LandmarkEngine]
        │ (validated LandmarkSet + tracking_quality)
        ▼
  [BiomechanicsEngine]
        │ (JointAngles + symmetry_score + balance_score)
        ▼
  [PoseRuleEngine]
        │ (PoseResult + matched_rules + failed_rules)
        ▼
  [MovementEngine]
        │ (ExerciseResult + reps + hold_time + rom_percentage)
        ▼
  [ScoringEngine]
        │ (ScoreReport + overall_score + stability_score + category)
        ▼
  [FeedbackEngine]
        │ (FeedbackResult + session summary + flaw corrections)
        ▼
  [Browser Session Controller (templates/app.html)]
        │ (Harvests telemetry snapshot on pose change or camera stop)
        ▼
  [POST /save_pose_session (Flask API)]
        │ (Authenticates current_user.id + validates parameters 0-100 & nulls)
        ▼
  [SessionRepository.create_session()]
        │ (Performs Supabase SQL INSERT into public.pose_sessions)
        ▼
  [Supabase PostgreSQL Database]
```

---

## 2. Telemetry Harvesting & Session Finalization

1. **Active Session Telemetry Harvesting:** As the user performs exercises on `templates/app.html`, event listeners maintain a transient `latestTelemetry` state:
   - `landmarks.validated` $\to$ `tracking_quality`
   - `biomechanics.updated` $\to$ `symmetry_score`, `balance_score`
   - `score.updated` $\to$ `overall_score` (accuracy), `stability_score`, `rom_score`
   - `exercise.rep_completed` $\to$ `reps`, `hold_time`
   - `feedback.generated` $\to$ `failed_rules`
2. **Authoritative Session Finalization:** When the user switches poses or stops the camera, `saveSession()` triggers ONCE per session.
3. **Idempotency Guarantee:** Duplicate writes are prevented by tracking a unique session key (`${poseLabel}_${poseStartTime}_${durationSec}`) in a client-side `Set`.
4. **User Isolation Guarantee:** The client payload does **not** specify `user_id`. The server strictly binds all database writes to `current_user.id` derived from the authenticated Flask-Login session.
