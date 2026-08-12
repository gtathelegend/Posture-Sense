# PostureSense Feedback Engine Specification

**Version:** 2.0.0  
**Status:** Completed (Milestone 6)  
**Priority:** 9  

---

## 1. Overview

The `FeedbackEngine` (`shared/engines/feedback_engine.py` & `static/assets/js/engines/feedback_engine.js`) converts explainable assessment data from upstream perception and evaluation engines (`ScoringEngine`, `MovementEngine`, `PoseRuleEngine`, `BiomechanicsEngine`) into actionable, evidence-based feedback messages, warnings, improvement suggestions, and session summaries.

### Key Architectural Constraints
- **NO Vision Processing**: Consumes high-level assessment events; never processes camera frames or raw landmarks.
- **NO Score Computation**: Does not compute posture or movement scores.
- **NO Upstream Mutations**: Upstream biomechanics, pose recognition, movement phase tracking, and scoring remain untouched.
- **NO ML / LLM Generation**: Uses deterministic, configuration-driven rule templates with structured localization readiness.
- **Measurable Evidence**: Every generated feedback item is attached to empirical, measurable evidence (raw metric values, thresholds, deltas).

---

## 2. Dependencies & Priority

- **Priority:** 9
- **Runtime Dependencies:** `scoring_engine`, `movement_engine`, `pose_rule_engine`, `biomechanics_engine`
- **Inputs Subscribed via EventBus:**
  - `score.updated` (`ScoreReport`)
  - `score.rep_completed` (`ScoreReport` / rep evaluation)
  - `score.exercise_completed` (`ScoreReport`)
  - `score.session_completed` (`ScoreReport` / session summary)
  - `pose.detected` (`PoseResult`)
  - `exercise.completed` (`ExerciseResult`)
- **Events Published to EventBus:**
  - `feedback.generated`: Dispatched whenever new actionable feedback passes cooldown/priority filters.
  - `feedback.updated`: Real-time active feedback queue update.
  - `feedback.dismissed`: Dispatched when feedback expires or is cleared.
  - `feedback.session_summary`: End-of-session aggregate assessment summary (`FeedbackSessionSummary`).

---

## 3. Feedback Types & Categories

### Supported Feedback Types
1. **Positive Feedback**: Reinforces correct technique (e.g., *"Excellent body posture and execution!"*).
2. **Correction Feedback**: Actionable guidance for form deviations (e.g., *"Increase your range of motion to reach recommended depth."*).
3. **Warning Feedback**: Alerts on low tracking confidence or data quality issues (e.g., *"Tracking confidence is low. Ensure clear camera view."*).
4. **Achievement Feedback**: Milestone notifications (e.g., *"Outstanding performance! Peak form achieved."*).

### Supported Feedback Categories
- `Form`
- `Range of Motion`
- `Stability`
- `Symmetry`
- `Tempo`
- `Control`
- `Consistency`
- `Tracking Quality`

---

## 4. Configuration-Driven Rules

Rules are loaded from `shared/config/current/feedback/feedback_rules.yaml`:

```yaml
version: "2.0.0"

settings:
  default_cooldown_seconds: 4.0
  high_severity_cooldown_seconds: 2.5
  critical_severity_cooldown_seconds: 1.0
  max_active_feedback_queue: 5

rules:
  - id: rule_form_quality_low
    category: Form
    type: correction
    severity: high
    metric: form
    condition: below
    threshold: 60.0
    message: "Maintain upright torso and proper alignment."
    template_key: "feedback.form.low_quality"
    cooldown_seconds: 4.0
```

---

## 5. Prioritization & Deduplication

### Severity Ranking Queue
Feedback candidates are ranked by severity level (`critical` > `high` > `medium` > `low` > `info`) and score confidence:

$$\text{Priority Rank} = f(\text{Severity Weight}, \text{Confidence})$$

### Cooldown & Suppression
- **Same-Message Suppression**: Prevents repeating identical advice every frame.
- **Rule Cooldowns**: Enforces rule-specific cooldown periods before re-triggering.
- **Queue Limits**: Limits maximum concurrent active feedback items (default: 5).

---

## 6. Measurable Evidence & Multi-Language Readiness

Every `FeedbackResult` payload embeds:
- `evidence`: `{"raw_value": 55.0, "threshold": 60.0, "difference": 5.0, "unit": "points", "metric_source": "form"}`
- `template_key`: `"feedback.form.low_quality"`
- `variables`: `{"raw_value": 55.0, "threshold": 60.0, "metric_name": "form", "exercise_name": "Bodyweight Squat"}`

---

## 7. Session Feedback Summaries

At session completion, `FeedbackSessionSummary` synthesizes:
- **Strengths**: High-performing dimensions (scores $\ge 80$).
- **Weak Areas**: Low-performing dimensions (scores $< 60$).
- **Common Mistakes**: Repetitive form degradation patterns.
- **Improvement Areas**: Practical technique suggestions (without medical advice).
