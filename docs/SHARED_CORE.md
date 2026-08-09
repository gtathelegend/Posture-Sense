# PostureSense Shared Core Infrastructure

**Version:** 2.0.0  
**Status:** Completed (Milestone 2)  

---

## 1. Overview

The `shared/` package provides the foundational layer for PostureSense v2, establishing typed data contracts, an event-driven pub/sub Event Bus, a versioned configuration loader, a extensible plugin framework, abstract engine interfaces, utility libraries, and contract schema validation.

---

## 2. Core Components

### 2.1 Typed Data Contracts (`shared/contracts/`)

Every contract inherits from `BaseContract` and includes four mandatory metadata fields:
- `id`: Unique UUID string
- `timestamp`: ISO 8601 UTC timestamp string
- `schema_version`: Contract schema version (default `2.0.0`)
- `source`: Originating engine / component identifier

#### Contract Specifications

1. `Frame`: Camera frame metadata (`frame_number`, `width`, `height`, `fps`).
2. `Landmark`: Single 3D landmark (`index`, `name`, `x`, `y`, `z`, `visibility`).
3. `LandmarkSet`: Array of landmarks with overall detection `confidence`.
4. `JointAngle`: Calculated joint angle (`joint_name`, `angle`, `expected_min`, `expected_max`).
5. `BiomechanicsSnapshot`: Collection of joint angles, `symmetry_score`, and `balance_score`.
6. `PoseResult`: Recognized static pose (`pose_name`, `confidence`, `is_recognized`).
7. `ExerciseResult`: Dynamic exercise tracking (`exercise_name`, `rep_count`, `current_phase`, `form_score`).
8. `ScoreReport`: Multi-component explainable evaluation (`overall_score`, `score_confidence`, `category`, `components`, `exercise_id`, `rep_scores`, `hold_score`, `session_summary`, `missing_metrics`, `quality_gate_passed`, `quality_warning`).
9. `FeedbackMessage`: Corrective advice (`message`, `severity`, `target_joint`, `correction_angle`).
10. `AnalyticsSnapshot`: Session interval statistics (`session_id`, `current_score`, `frame_rate`, `elapsed_seconds`).
11. `SessionSummary`: Completed session metrics (`session_id`, `user_id`, `pose_label`, `duration`, `avg_accuracy`, `total_reps`).
12. `UserProfile`: User settings and preference payload (`user_id`, `username`, `email`, `preferred_mode`).

---

### 2.2 Event Bus Architecture (`shared/events/`)

The `EventBus` provides typed event-driven communication:
- `publish(event_name, data)`: Dispatches events to all registered handlers.
- `subscribe(event_name, handler)`: Registers persistent event handlers.
- `unsubscribe(event_name, handler)`: Removes event handlers.
- `once(event_name, handler)`: Registers single-use event handlers.
- `clear(event_name=None)`: Resets handlers and clears event history.
- `event_history`: Tracks published events for debugging when `debug_mode=True`.

---

### 2.3 Versioned Configuration System (`shared/config/`)

Supports versioned configuration loading for YAML and JSON configuration files:
- Directory structure: `shared/config/{version}/{category}/{file}`
- Default current version: `current/`
- Supported categories: `poses/`, `exercises/`, `feedback/`, `weights/`, `thresholds/`, `system/`
- Loader API: `ConfigLoader.load(relative_path, version="current")`

---

### 2.4 Plugin Framework (`shared/plugins/`)

Provides abstract interfaces and a registry for domain plugins:
- Abstract categories: `ExercisePlugin`, `YogaPlugin`, `ErgonomicsPlugin`, `RehabilitationPlugin`.
- Mandatory properties: `plugin_id`, `name`, `mode`, `metadata()`, `configuration()`, `recognition_rules()`, `feedback_rules()`, `visualization_hooks()`.
- Central Registry: `PluginRegistry` handles registration, unregistration, lookup, and category filtering.

---

### 2.5 Abstract Engine Interfaces (`shared/core/` & `shared/engines/`)

All 12 PostureSense engines inherit from `BaseEngine` and expose:
- `initialize(config)`
- `start()`
- `stop()`
- `dispose()`
- `status()`
- `publish(event_name, data)`
- `subscribe(event_name, handler)`

Interfaces implemented: `CameraEngineInterface`, `MediaPipeEngineInterface`, `LandmarkEngineInterface`, `BiomechanicsEngineInterface`, `PoseRuleEngineInterface`, `MovementEngineInterface`, `ScoringEngineInterface`, `FeedbackEngineInterface`, `AnalyticsEngineInterface`, `PersistenceEngineInterface`, `NotificationEngineInterface`, `ReportEngineInterface`.

---

### 2.6 Validation & Utilities (`shared/utils/`)

- `ContractValidator`: Ensures contract metadata schema integrity before events enter the EventBus.
- `math_utils`: 3-point interior angle calculation (`calculate_angle_3p`) and Euclidean distance (`calculate_distance`).
- `time_utils`: ISO timestamps (`current_iso_timestamp`) and duration formatting (`format_duration`).
