# PostureSense v2 Architecture Overview

**Version:** 2.0.0  
**Status:** Production Release  
**Author:** Lead Architecture & Release Engineering  

---

## 1. Executive Architecture Summary

PostureSense v2 is architected as an **event-driven, decoupled, multi-engine perception platform**. 

Key architectural principles:
1. **Browser-Native Perception**: All computer vision pose inference runs on-device via WebAssembly (WASM) inside Web Workers, ensuring privacy and sub-50ms latency.
2. **Event-Driven Decoupling**: 11 specialized engines communicate exclusively through an asynchronous, publish-subscribe **Event Bus**.
3. **Configuration-Driven Rules**: Pose definitions, exercise state machines, and scoring weights are declared in version-controlled YAML configuration files rather than hardcoded logic.
4. **Unidirectional Data Flow**: Data flows predictably from camera acquisition $\rightarrow$ landmark extraction $\rightarrow$ biomechanics vector math $\rightarrow$ rule classification $\rightarrow$ movement FSM $\rightarrow$ scoring $\rightarrow$ feedback $\rightarrow$ analytics $\rightarrow$ report export.

---

## 2. High-Level System Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                 CLIENT BROWSER                                    |
|                                                                                   |
|  +------------------+     +-------------------+     +--------------------------+  |
|  |  CameraEngine    | --> | MediaPipeEngine   | --> |      LandmarkEngine      |  |
|  |  (Webcam API)    |     | (WASM WebWorker)  |     |  (EMA Jitter/Quality)    |  |
|  +------------------+     +-------------------+     +--------------------------+  |
|                                                                  |                |
|                                                                  v                |
|  +------------------+     +-------------------+     +--------------------------+  |
|  |  MovementEngine  | <-- |  PoseRuleEngine   | <-- |   BiomechanicsEngine     |  |
|  |  (11-State FSM)  |     | (12 Pose Rules)   |     |  (3D Joint Vector Math)  |  |
|  +------------------+     +-------------------+     +--------------------------+  |
|           |                                                                       |
|           v                                                                       |
|  +------------------+     +-------------------+     +--------------------------+  |
|  |  ScoringEngine   | --> |  FeedbackEngine   | --> |  VisualizationEngine     |  |
|  | (8-Dim Weighted) |     | (Coaching Rules)  |     | (Canvas Overlays 60FPS)  |  |
|  +------------------+     +-------------------+     +--------------------------+  |
|           |                                                                       |
|           +--------------------------+                                            |
|                                      v                                            |
|                          +-----------------------+                                |
|                          |    AnalyticsEngine    |                                |
|                          |   (Session Aggreg)    |                                |
|                          +-----------------------+                                |
+--------------------------------------|--------------------------------------------+
                                       | HTTPS REST API (Derived Metrics Only)
                                       v
+-----------------------------------------------------------------------------------+
|                                BACKEND CLOUD                                      |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                          Flask 3.x Application                              |  |
|  |                                                                             |  |
|  |  +--------------------+   +---------------------+   +--------------------+  |  |
|  |  |   API Blueprint    |   |  Analytics Service  |   |   Report Service   |  |  |
|  |  +--------------------+   +---------------------+   +--------------------+  |  |
|  |            |                         |                         |            |  |
|  |            +-------------------------+-------------------------+            |  |
|  |                                      v                                      |  |
|  |                           Supabase Repository Layer                         |  |
|  +--------------------------------------|--------------------------------------+  |
|                                         v                                         |
|                             Supabase PostgreSQL Database                          |  |
+-----------------------------------------------------------------------------------+
```

---

## 3. The 11 Core Engines

PostureSense v2 decomposes real-time perception and movement intelligence into 11 discrete, specialized engines:

| Engine | Primary Function | Primary Event Input | Primary Event Output |
|---|---|---|---|
| **1. CameraEngine** | Manages video capture, device selection, resolution scaling, and frame timing. | Hardware Video Stream | `FRAME_CAPTURED` |
| **2. MediaPipeEngine** | Executes WASM `PoseLandmarker` in Web Worker; outputs raw 3D keypoints. | `FRAME_CAPTURED` | `LANDMARKS_DETECTED` |
| **3. LandmarkEngine** | Quality filter: EMA smoothing, NaN validation, tracking loss recovery. | `LANDMARKS_DETECTED` | `LANDMARKS_FILTERED` |
| **4. BiomechanicsEngine** | Computes 3D joint angles, ROM, bilateral symmetry, CoM stability. | `LANDMARKS_FILTERED` | `BIOMECHANICS_COMPUTED` |
| **5. PoseRuleEngine** | Evaluates 12 configuration-driven posture and yoga pose rules with hold timers. | `BIOMECHANICS_COMPUTED` | `POSE_MATCHED` |
| **6. MovementEngine** | Executes 11-state FSM for exercise rep counting, phase tracking & tempo analysis. | `BIOMECHANICS_COMPUTED` | `REP_COMPLETED` / `PHASE_TRANSITION` |
| **7. ScoringEngine** | Calculates weighted 8-dimension performance quality score index (0-100). | `MOVEMENT_UPDATED` / `POSE_MATCHED` | `SCORE_EVALUATED` |
| **8. FeedbackEngine** | Rule evaluation engine producing prioritized, deduplicated coaching cues. | `SCORE_EVALUATED` / `BIOMECHANICS_COMPUTED` | `FEEDBACK_GENERATED` |
| **9. AnalyticsEngine** | Aggregates longitudinal statistics, 30-day heatmaps, and PR trends. | `SESSION_COMPLETED` | `ANALYTICS_SAVED` |
| **10. VisualizationEngine**| Canvas renderer drawing 11 configurable overlay layers at 60 FPS. | `LANDMARKS_FILTERED` / `BIOMECHANICS_COMPUTED` | Screen Frame Render |
| **11. ReportEngine** | Generates PDF, CSV, and JSON document exports with user isolation guards. | REST Request / Session Payload | Document File Stream |

---

## 4. Engine Pipeline & Event Flow

### Sequence Diagram: Perception Loop Execution

```
User Camera   MediaPipe WASM   Event Bus     Engines (Bio/Pose/Move)   Scoring & Feedback
    │               │              │                    │                       │
    ├─ Frame ─────> │              │                    │                       │
    │  (30 FPS)     ├─ Landmarks ─>│                    │                       │
    │               │  (12ms)      ├─ LANDMARKS_FILTER >│                       │
    │               │              │                    ├─ Vector Geometry ────>│
    │               │              │                    ├─ Pose Classification >│
    │               │              │                    ├─ Rep / Phase FSM ────>│
    │               │              │                    │                       ├─ Calculate 8D Score
    │               │              │                    │                       ├─ Emit Coaching Cue
```

---

## 5. Event Bus Contracts & Data Schemas

All event payloads strictly conform to versioned data contracts declared in `shared/contracts/`.

### 5.1 — `LANDMARKS_FILTERED` Event Schema

```json
{
  "event": "LANDMARKS_FILTERED",
  "timestamp": 1723236491203,
  "frame_id": 1402,
  "landmarks": [
    { "id": 0, "name": "nose", "x": 0.512, "y": 0.234, "z": -0.12, "visibility": 0.99 },
    { "id": 11, "name": "left_shoulder", "x": 0.421, "y": 0.380, "z": -0.05, "visibility": 0.97 },
    { "id": 12, "name": "right_shoulder", "x": 0.603, "y": 0.382, "z": -0.04, "visibility": 0.98 }
  ],
  "quality": {
    "tracking_confidence": 0.98,
    "jitter_index": 0.012,
    "is_valid": true
  }
}
```

### 5.2 — `BIOMECHANICS_COMPUTED` Event Schema

```json
{
  "event": "BIOMECHANICS_COMPUTED",
  "timestamp": 1723236491220,
  "joint_angles": {
    "neck_flexion": 14.2,
    "left_knee": 104.5,
    "right_knee": 103.8,
    "trunk_incline": 8.5
  },
  "symmetry": {
    "shoulder_asymmetry_deg": 1.8,
    "knee_asymmetry_deg": 0.7
  },
  "center_of_mass": {
    "x": 0.502,
    "y": 0.485,
    "stability_score": 92.4
  }
}
```

---

## 6. Frontend Architecture

The frontend application (`static/assets/js/engine/` and `templates/`) follows a clean modular component pattern:

- **UI Controller**: Handlers in Jinja2 templates interface with client JS engine instances via `EngineAdapter`.
- **Engine Runtime**: `EngineRuntime.js` manages engine initialization, state transitions (`UNINITIALIZED` $\rightarrow$ `INITIALIZING` $\rightarrow$ `RUNNING` $\rightarrow$ `PAUSED` $\rightarrow$ `STOPPED`), and dependency resolution.
- **Canvas Renderer**: `VisualizationEngine.js` renders skeleton overlays, joint angle arcs, posture bounding boxes, and real-time form indicators using High-DPI canvas scaling.

---

## 7. Backend Architecture

The backend application (`backend/app/`) implements the Flask application factory pattern (`create_app()`):

```
backend/app/
├── __init__.py          # create_app() factory & middleware setup
├── config.py            # Development & Production configuration classes
├── errors.py            # Centralized HTTP error handlers
├── extensions.py        # Shared extension instances (Flask-Login, Bcrypt, Supabase)
├── logging.py           # Structured application logging
├── blueprints/
│   ├── api/             # REST endpoints (/api/analytics, /api/reports, /api/auth)
│   └── views/           # Jinja2 template view routes
├── middleware/
│   └── security.py      # HTTP Security headers (CSP, HSTS, Frame Options)
├── repositories/        # Database query abstractions
└── services/            # Core business logic (auth, analytics, PDF generation)
```

---

## 8. Cloud Deployment Architecture

- **WSGI Application**: Hosted on Render.com / Railway running Gunicorn (`gunicorn app:app`).
- **Database**: Supabase PostgreSQL cloud instance accessed via HTTP API with service role authentication.
- **Static & Perceptual Assets**: WASM binaries and frontend JavaScript served over CDN with caching control headers.
