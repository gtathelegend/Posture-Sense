# Movement Engine

## Overview

The **MovementEngine** (Priority 7) is a production-grade, configuration-driven engine for dynamic exercise phase detection, repetition counting, tempo analysis, and isometric hold tracking. It is the seventh tier in the PostureSense v2 engine pipeline.

It operates entirely through externalized YAML exercise definitions. There is **no hardcoded exercise logic** anywhere in the engine.

---

## Architecture Position

```
CameraEngine (1)
    └─► MediaPipeEngine (2)
            └─► LandmarkEngine (3)
                    └─► BiomechanicsEngine (4)
                            └─► PoseRuleEngine (5)
                                    └─► VisualizationEngine (6)
                                                └─► MovementEngine (7)  ◄── THIS ENGINE
```

| Property | Value |
|----------|-------|
| Priority | 7 |
| Dependencies | `pose_rule_engine`, `biomechanics_engine` |
| Subscribes | `biomechanics.updated`, `pose.detected` |
| Publishes | `exercise.*` (see Events) |
| Contract | `ExerciseResult` |
| Python module | `shared/engines/movement_engine.py` |
| JS module | `static/assets/js/engines/movement_engine.js` |

---

## Core Principle

> The Movement Engine must work **entirely through configurable exercise definitions**. No hardcoded exercise logic. No posture scoring. No coaching feedback. No ML classifiers.

---

## Finite State Machine

The FSM has **11 states** covering the full exercise lifecycle:

```
Idle → Entering → Ready → Concentric → Bottom → Eccentric → Top → Completed
                    └──────────────────────── Hold → Completed
                                      ↗ (tracking loss)
                                   Exited
                              ↗ (FSM violation)
                           Invalid
```

### Valid Transition Table

| From State | To States |
|-----------|-----------|
| `Idle` | `Entering` |
| `Entering` | `Ready`, `Idle` |
| `Ready` | `Concentric`, `Bottom`, `Top`, `Hold`, `Idle` |
| `Concentric` | `Bottom`, `Eccentric`, `Invalid` |
| `Bottom` | `Eccentric`, `Concentric` |
| `Eccentric` | `Top`, `Concentric` |
| `Top` | `Completed`, `Concentric`, `Idle` |
| `Hold` | `Completed`, `Idle` |
| `Completed` | `Idle` |
| `Exited` | `Idle` |
| `Invalid` | `Idle` |

---

## Exercise Configuration Schema

Exercise definitions live in `shared/config/current/exercises/*.yaml`.

```yaml
schema_version: "2.0.0"
id: exercise_id              # Unique slug
name: Human-Readable Name
category: dynamic | static_hold

entry_conditions:
  joint_constraints:         # All must be satisfied to enter
    joint_name: [min_deg, max_deg]
  min_tracking_quality: 60.0
  required_joints: []

exit_conditions:
  tracking_quality_below: 40.0    # Exits on tracking loss
  joint_violation:                # Exits if joint escapes range
    joint_name: [min_deg, max_deg]
  inactivity_timeout_ms: 5000

phases:
  - id: phase_id
    name: Human Name
    type: top | concentric | bottom | eccentric | hold
    trigger_joints: [joint_name]
    trigger_ranges:
      joint_name: [min_deg, max_deg]
    min_duration_ms: 0
    max_duration_ms: 0

rep_completion:
  required_phases: [phase_id]     # All must appear in order
  min_rom_percentage: 50.0        # Minimum ROM gate
  rom_joint: joint_name           # Joint used for ROM %
  rom_reference_top: 170.0        # Fully extended reference
  rom_reference_bottom: 90.0      # Fully flexed reference
  prevent_bounce: true
  debounce_ms: 400

hold_config:                      # For static_hold exercises only
  min_seconds: 10.0
  milestone_seconds: [15, 30, 60]
  count_unit: seconds

tempo_limits:
  min_cadence_rpm: 4
  max_cadence_rpm: 40
```

---

## Supported Exercises

| ID | Name | Category | Primary Joints |
|----|------|----------|---------------|
| `bodyweight_squat` | Bodyweight Squat | dynamic | knee |
| `push_up` | Push-Up | dynamic | elbow |
| `lunge` | Lunge | dynamic | knee |
| `jumping_jack` | Jumping Jack | dynamic | shoulder |
| `plank` | Plank | static_hold | spine, hip |
| `wall_sit` | Wall Sit | static_hold | knee, hip |
| `chair_pose_hold` | Chair Pose Hold | static_hold | knee, hip |
| `tree_pose_hold` | Tree Pose Hold | static_hold | knee |
| `warrior_ii_hold` | Warrior II Hold | static_hold | knee, shoulder |
| `bridge_hold` | Bridge Hold | static_hold | hip |

---

## Rep Counting Algorithm

```
1. Entry Gate: entry_conditions satisfied → FSM IDLE → ENTERING → READY
2. Phase Tracking: required_phases traversed in sequential order
3. ROM Gate: min_rom_percentage met at bottom (measured vs reference range)
4. Completion Gate: final phase (TOP) reached after ECCENTRIC
5. Debounce: min 400ms between reps (prevent bounce)
6. Partial Rep Guard: required_phases must all be in _phases_completed
7. Exit Detection: exit_conditions → EXITED
```

### Sequential Phase Ordering

The engine uses `_next_phase_idx` to enforce sequential phase scanning. This prevents ambiguous re-matching when multiple phases share overlapping angle ranges (e.g., concentric and eccentric at 130°). The FSM only considers phases forward from the last matched position.

---

## ExerciseResult Contract

Published on every `exercise.updated` event and on every `exercise.rep_completed`.

```python
ExerciseResult(
    exercise_id          str       # "bodyweight_squat"
    exercise_name        str       # "Bodyweight Squat"
    current_phase        str       # "bottom", "top", "hold", etc.
    rep_count            int       # 0, 1, 2, ...
    current_rep_duration float     # seconds for current rep
    average_rep_duration float     # rolling average of all reps
    current_cadence      float     # reps/minute
    rom_percentage       float     # 0–100%
    movement_quality     float     # 0–100% (tracking quality, NOT posture score)
    hold_time            float     # seconds held (for static holds)
    tracking_quality     float     # 0–100%
    schema_version       str       # "2.0.0"
    source               str       # "movement_engine"
)
```

> **`movement_quality` is NOT a posture score.** It is derived exclusively from MediaPipe landmark visibility scores. No biomechanical evaluation is performed.

---

## Published Events

| Event | Trigger |
|-------|---------|
| `exercise.started` | Entry conditions satisfied, FSM enters ENTERING |
| `exercise.phase_changed` | FSM transitions to a new state |
| `exercise.rep_started` | FSM enters CONCENTRIC from TOP/READY |
| `exercise.rep_completed` | Full cycle completed with ROM gate passed |
| `exercise.completed` | Target rep count reached (if configured) |
| `exercise.cancelled` | Exit conditions triggered mid-exercise |
| `exercise.invalid` | FSM enters INVALID state |
| `exercise.updated` | Per-frame ExerciseResult (always) |

---

## Lifecycle

```python
engine = MovementEngine(name="MovementEngine", event_bus=event_bus)
engine.initialize()
engine.start()

# Select exercise
engine.set_active_exercise("bodyweight_squat")

# Hot-reload configs from disk
engine.reload_exercise_configs()

# Get available exercises
exercises = engine.get_available_exercises()
# → [{"id": "bodyweight_squat", "name": "Bodyweight Squat", "category": "dynamic"}, ...]

engine.pause()
engine.resume()
engine.stop()
engine.dispose()
```

---

## Diagnostics

```python
diag = engine.get_diagnostics()
# {
#   "name": "MovementEngine",
#   "version": "2.0.0",
#   "status": "running",
#   "priority": 7,
#   "dependencies": ["pose_rule_engine", "biomechanics_engine"],
#   "metrics": {
#     "active_exercise": "bodyweight_squat",
#     "fsm_state": "bottom",
#     "rep_count": 3,
#     "current_phase": "bottom",
#     "average_rep_time_s": 2.15,
#     "movement_direction": "decreasing",
#     "recognition_latency_ms": 0.12,
#     "exercise_duration_s": 42.1,
#     "loaded_exercises": 10,
#     "frames_processed": 2520,
#     "false_positives_prevented": 0
#   }
# }
```

---

## Developer Playground

The `/playground` route exposes the full Priority 1–7 pipeline with a Movement Engine panel:

- **Exercise selector**: dropdown to choose any of the 10 supported exercises
- **Rep Counter**: large live counter (purple)
- **Current Phase + FSM State**: per-frame phase badges
- **ROM %**: percentage of range-of-motion achieved
- **Cadence**: reps per minute (rolling average)
- **Movement Direction**: `increasing` / `decreasing` / `stationary`
- **Hold Timer**: seconds held (for static exercises)
- **Exercise Timer**: total session time
- **Latency**: per-frame recognition time in ms

**Debug Overlay** (`CTRL+SHIFT+D`): Movement Engine section at Priority 7 shows: exercise, phase, FSM state, reps, cadence, direction, latency.

---

## Adding a New Exercise

1. Create `shared/config/current/exercises/my_exercise.yaml` following the schema above.
2. Add the same config as an entry in `_BUILTIN_EXERCISE_CONFIGS` in `movement_engine.js` (no YAML parser in browser).
3. Add the exercise `<option>` to the `#mv-exercise-select` dropdown in `playground.html`.
4. Run `engine.reload_exercise_configs()` (Python) or re-initialize the JS engine.

---

## Technical Notes

- **Phase ordering**: The engine uses a sequential `_next_phase_idx` pointer rather than scanning all phases every frame. This eliminates false triggers when concentric and eccentric share overlapping joint angle ranges.
- **Debounce**: All rep counts are gated by 400ms (default) between completions. This prevents bounce double-counting.
- **ROM gate**: By default, 50% of the configured joint ROM must be achieved at bottom for the rep to count.
- **Hold exercises**: Static holds (`category: static_hold`) skip the rep cycle entirely. The FSM goes directly READY→HOLD and tracks hold duration.
- **Tracking loss**: Any frame with `tracking_quality < exit_conditions.tracking_quality_below` terminates the exercise immediately.
