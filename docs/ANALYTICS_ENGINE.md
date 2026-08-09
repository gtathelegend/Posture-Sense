# PostureSense Analytics & User Progress Engine Specification

**Version:** 2.0.0  
**Status:** Completed (Milestone 7)  
**Priority:** 10  

---

## 1. Overview

The `AnalyticsEngine` (`shared/engines/analytics_engine.py` & `static/assets/js/engines/analytics_engine.js`) transforms completed posture and exercise assessment outputs into longitudinal progress analytics, statistical trends, exercise histories, personal records, calendar streak calculations, and session comparisons.

### Key Architectural Constraints
- **NO Coaching / Feedback Generation**: Immediate feedback is owned exclusively by the Feedback Engine.
- **NO Score Computation**: Does not compute posture or movement scores.
- **NO Camera / Landmark Processing**: Operates strictly on completed high-level assessment events; never processes camera frames or raw landmark streams.
- **NO ML Trend Classification**: Uses deterministic statistical slope and percentage delta calculations over configurable observation windows ($N \ge 3$).
- **Strict User Data Isolation**: Enforces user-scoped query filters across memory stores and repositories (`user_id`).
- **Data Minimization & Privacy**: Never persists raw video, camera frames, or landmark streams. Persists only derived performance metrics required for progress tracking.

---

## 2. Dependencies & Priority

- **Priority:** 10
- **Runtime Dependencies:** `feedback_engine`, `scoring_engine`, `movement_engine`, `pose_rule_engine`, `biomechanics_engine`
- **Inputs Subscribed via EventBus:**
  - `score.session_completed` (`ScoreReport` / session summary)
  - `score.exercise_completed` (`ScoreReport`)
  - `score.rep_completed` (`ScoreReport` / rep data)
  - `feedback.session_summary` (`FeedbackSessionSummary`)
  - `exercise.completed` (`ExerciseResult`)
- **Events Published to EventBus:**
  - `analytics.session_completed`: Dispatched when a session is aggregated into analytics.
  - `analytics.updated`: Dispatched when user summary payload is updated (`AnalyticsSummary`).
  - `analytics.trend_detected`: Dispatched when a statistical trend direction is calculated (`TrendMetric`).
  - `analytics.record_broken`: Dispatched when a personal record is broken (`PersonalRecord`).
  - `analytics.progress_updated`: Dispatched on progress telemetry updates.

---

## 3. Analytics Contracts

1. **`SessionAnalytics`**: Single session analytics record (`session_id`, `user_id`, `start_time`, `end_time`, `duration`, `exercise_id`, `completed_reps`, `valid_reps`, `invalid_reps`, `average_score`, `best_score`, `worst_score`, `consistency`, `tracking_quality`).
2. **`ExerciseAnalytics`**: Historical exercise metrics (`exercise_id`, `total_sessions`, `total_repetitions`, `best_score`, `average_score`, `best_rom`, `average_rom`, `average_stability`, `average_symmetry`, `average_form`, `last_performed`, `improvement_percentage`).
3. **`TrendMetric`**: Statistical trend evaluation (`metric_name`, `timeframe`, `trend_direction` [`IMPROVING`, `STABLE`, `DECLINING`, `INSUFFICIENT_DATA`], `observation_count`, `slope`, `percentage_change`, `sample_values`).
4. **`PersonalRecord`**: Achievement record (`record_type` [`Highest Score`, `Best ROM`, `Best Stability`, `Best Symmetry`, `Longest Hold`, `Most Reps`, `Best Consistency`], `exercise_id`, `value`, `unit`, `achieved_at`, `previous_value`).
5. **`AnalyticsSummary`**: Master progress summary payload.

---

## 4. Deterministic Statistical Trend Classification

Trends are computed over minimum observation windows ($N \ge 3$):

$$\text{Percentage Change} = \frac{\text{Latest Value} - \text{First Value}}{\text{First Value}} \times 100\%$$

$$\text{Slope} = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sum (x_i - \bar{x})^2}$$

### Classification Criteria
- **`IMPROVING`**: $\text{Percentage Change} > +2.0\%$ OR $\text{Slope} > 0.2$
- **`DECLINING`**: $\text{Percentage Change} < -2.0\%$ OR $\text{Slope} < -0.2$
- **`STABLE`**: Otherwise
- **`INSUFFICIENT_DATA`**: $N < 3$

---

## 5. Persistence & Privacy

- Reuses existing `SessionRepository` and `AnalyticsRepository` (`backend/app/repositories/analytics_repository.py`).
- All queries and analytics endpoints (`GET /api/analytics/summary`, `GET /api/analytics/progress`, `GET /api/analytics/exercises`, `GET /api/analytics/trends`, `GET /api/analytics/records`) enforce `@login_required` and scope results strictly to `current_user.id`.
