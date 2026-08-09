# PostureSense Scoring Engine Specification

**Version:** 2.0.0  
**Status:** Completed (Milestone 5)  
**Priority:** 8  

---

## 1. Overview

The `ScoringEngine` (`shared/engines/scoring_engine.py` & `static/assets/js/engines/scoring_engine.js`) converts objective output data from upstream perception and movement engines (`BiomechanicsEngine`, `PoseRuleEngine`, `MovementEngine`) into explainable, configuration-driven performance scores.

### Key Architectural Constraints
- **NO Coaching Advice**: The engine computes objective scores; feedback is handled downstream by the Feedback Engine.
- **NO Natural Language Recommendations**: All output values are structured numerical metrics, category bands, and explainability payloads.
- **NO Upstream Measurement Mutation**: Upstream biomechanics, pose recognition, and rep counters remain untouched.
- **NO Hidden Failed Metrics**: Failed or missing input metrics are explicitly flagged as `UNAVAILABLE` rather than defaulting silently to 100 or 0.
- **Full Traceability**: Every score component is traceable to raw input values, configured dimension weights, and dynamic re-weighting factors.

---

## 2. Dependencies & Priority

- **Priority:** 8
- **Runtime Dependencies:** `movement_engine`, `biomechanics_engine`, `pose_rule_engine`
- **Inputs Subscribed via EventBus:**
  - `biomechanics.updated` (`BiomechanicsSnapshot`)
  - `pose.detected` (`PoseResult`)
  - `exercise.started` (`ExerciseResult`)
  - `exercise.phase_changed` (`ExerciseResult`)
  - `exercise.rep_completed` (`ExerciseResult`)
  - `exercise.completed` (`ExerciseResult`)
- **Events Published to EventBus:**
  - `score.updated`: Real-time score report dispatch per frame / evaluation.
  - `score.rep_completed`: Performed rep evaluation breakdown.
  - `score.exercise_completed` / `score.session_completed`: End-of-exercise assessment.
  - `score.unavailable`: Dispatched when inputs are insufficient for valid scoring.
  - `score.quality_warning`: Dispatched on quality gate failure.

---

## 3. Configurable Scoring Dimensions

The engine evaluates 8 objective dimensions:

1. **Form Quality (`form`)**: Derived from Movement Engine quality / Pose confidence.
2. **Range of Motion (`rom`)**: Derived from exercise ROM percentage.
3. **Stability (`stability`)**: Derived from Biomechanics balance score and center of mass variance.
4. **Symmetry (`symmetry`)**: Derived from left-right joint angle symmetry.
5. **Movement Control (`control`)**: Derived from rep duration consistency and execution smoothness.
6. **Tempo / Cadence (`tempo`)**: Derived from repetition cadence vs target movement velocity bounds.
7. **Consistency (`consistency`)**: Derived from variance of rep scores across a set.
8. **Tracking Quality (`tracking_quality`)**: Derived from landmark visibility and detection stability.

---

## 4. Configuration-Driven Weights

Weights are loaded from versioned configuration files (`shared/config/current/weights/scoring_weights.yaml`):

```yaml
version: "2.0.0"

default_weights:
  form: 0.30
  rom: 0.20
  stability: 0.15
  symmetry: 0.15
  control: 0.10
  tempo: 0.10

categories:
  dynamic:
    form: 0.30
    rom: 0.20
    stability: 0.15
    symmetry: 0.15
    control: 0.10
    tempo: 0.10
  static_hold:
    form: 0.25
    stability: 0.30
    symmetry: 0.20
    control: 0.15
    tracking_quality: 0.10

score_bands:
  - min: 90.0
    max: 100.0
    label: "Excellent"
  - min: 75.0
    max: 89.99
    label: "Good"
  - min: 60.0
    max: 74.99
    label: "Needs Improvement"
  - min: 0.0
    max: 59.99
    label: "Poor"

quality_gates:
  min_tracking_quality: 50.0
  min_pose_confidence: 0.4
  min_landmark_visibility: 0.5
  min_samples: 3
```

All configured dimension weights are validated during initialization:
- Sum of weights must equal 1.0 (within `1e-4` tolerance).
- Weights must be non-negative.

---

## 5. Metric Normalization & Aggregation

Raw metric inputs are normalized internally to `[0.0, 100.0]`:

$$\text{Overall Score} = \sum_{i \in \text{Available}} \text{Score}_i \times \left( \frac{\text{Weight}_i}{\sum_{j \in \text{Available}} \text{Weight}_j} \right)$$

If an input metric is missing or low quality, it is marked with status `"UNAVAILABLE"` and recorded in `missing_metrics`. The engine dynamically re-scales active weights among available metrics so their sum equals `1.0`.

---

## 6. Score Confidence & Quality Gates

### Score Confidence Formula
$$\text{Confidence} = 0.4 \times \frac{\text{Tracking Quality}}{100} + 0.3 \times \text{Pose Confidence} + 0.3 \times \left( \frac{\text{Available Metrics}}{\text{Total Metrics}} \right)$$

### Quality Gates
If tracking quality or pose confidence falls below configured thresholds (`min_tracking_quality`, `min_pose_confidence`):
- `quality_gate_passed` is set to `False`.
- `quality_warning` description is attached.
- Event `score.quality_warning` is published.

---

## 7. Rep-Level, Hold, and Session Assessment

- **Rep Scoring**: Generates per-rep evaluation records containing `rep_number`, `overall_score`, `form_score`, `rom`, `stability`, `control`, `duration`, and `quality`.
- **Hold Scoring**: Evaluates time-based holds (Plank, Wall Sit, etc.) tracking `hold_stability`, `alignment`, `balance`, `duration`, and `tracking_quality`.
- **Session Scoring**: Aggregates running session statistics including `avg_score`, `best_rep_score`, `worst_rep_score`, `score_variance`, `consistency_score`, `completed_reps`, `invalid_reps`, and `duration_seconds`.
