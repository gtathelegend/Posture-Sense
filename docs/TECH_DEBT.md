# PostureSense Technical Debt Registry

**Version:** 2.0.0  
**Status:** Completed & Audited for v2.0.0 Public Release  

---

## 1. Resolved Technical Debt (Completed in v2.0.0)

| Item ID | Description | Resolution Summary |
|---|---|---|
| **TD-01** | Monolithic `app.py` (>900 lines) | Split into `backend/app/` blueprints, services, repositories, and domain models. |
| **TD-02** | Direct database queries in HTTP route handlers | Moved database queries into `UserRepository` and `SessionRepository`. |
| **TD-03** | Ad-hoc environment variable parsing | Centralized configuration in `backend/app/config.py`. |
| **TD-04** | Global extension state & lack of application factory | Implemented `create_app()` and `backend/app/extensions.py`. |
| **TD-05** | Unstructured `print()` debugging statements | Replaced with standard Flask logging in `backend/app/logging.py`. |
| **TD-06** | Unhandled HTTP exceptions returning generic 500s | Added centralized error handlers in `backend/app/errors.py`. |
| **TD-07** | Missing HTTP security response headers | Implemented security middleware (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`). |
| **TD-08** | Direct HTTP fetch calls embedded in inline HTML scripts | Extracted clean frontend service layer (`AuthService`, `DashboardService`, `SessionService`). |
| **TD-09** | Tight coupling between UI and lower event handlers | Introduced `EngineAdapter` and `EngineContext` state architecture. |
| **TD-10** | Lack of runtime lifecycle state machine | Implemented `EngineRuntime`, `EngineRegistry`, `LifecycleState`, and `DependencyResolver`. |
| **TD-11** | Server-side webcam streaming dependency | Implemented browser-native `CameraEngine` with resolution scaling and FPS counter. |
| **TD-12** | Main-thread blocking CV inference | Implemented `MediaPipeEngine` with WebAssembly (`PoseLandmarker`) running inside a Web Worker. |
| **TD-13** | Keypoint jitter & unvalidated landmarks | Implemented `LandmarkEngine` quality gate with EMA filtering, NaN validation, and interpolation. |
| **TD-14** | Heuristic 2D joint angle approximations | Implemented `BiomechanicsEngine` 3D vector geometry, CoM estimation, symmetry analysis, and ROM tracking. |
| **TD-15** | Hardcoded pose classification thresholds | Implemented configuration-driven `PoseRuleEngine` matching 12 poses with hold timers. |
| **TD-16** | Lack of real-time skeleton / biomechanics rendering | Implemented `VisualizationEngine` Canvas renderer with 11 configurable overlays, 60 FPS target, and High-DPI support. |
| **TD-17** | Lack of rep counting, phase tracking & ROM gates | Implemented `MovementEngine` with 11-state FSM, sequential phase ordering, debounced rep counter, ROM gate, and tempo analyzer. |
| **TD-21** | Lack of multi-dimensional performance scoring | Implemented `ScoringEngine` with 8 configurable scoring dimensions, versioned weights, score confidence, and score bands. |
| **TD-22** | Hardcoded text strings & coaching feedback | Implemented `FeedbackEngine` with rule-based evaluation, empirical evidence models, severity ranking, deduplication, and cooldown timers. |
| **TD-23** | Lack of longitudinal trend analytics & PR tracking | Implemented `AnalyticsEngine` with deterministic statistical trend classification, exercise performance history, personal records, calendar streaks, and REST APIs. |
| **TD-24** | Lack of exportable performance reports | Implemented `ReportEngine` with session, exercise, progress, and comprehensive report composition, PDF rendering, CSV/JSON serializers, and REST APIs. |
| **TD-25** | Unvalidated end-to-end browser pipeline latency | Validated complete 11-engine pipeline, added worker backpressure (`isInferenceBusy` gate), verified $< 50$ms inference latency, tracking loss recovery, 107+ unit tests passed. |
| **TD-26** | Lack of production security hardening | Added production secret validation guard, CORS restriction, secure cookies, security headers, zero raw video/landmark persistence, and 111 unit & security tests passed. |
| **TD-31** | Legacy `/video_feed` server-side streaming on Live Demo | Integrated browser-native `CameraEngine` (`getUserMedia`) and `PosePipelineController` into `templates/app.html`, eliminating server-side OpenCV dependencies. |


---

## 2. Accepted Technical Debt (Accepted Architecture & Design Decisions)

| Item ID | Description | Justification & Impact |
|---|---|---|
| **TD-27** | Single-user local perception scoping per camera | **Accepted Design Choice**: PostureSense v2 is optimized for individual ergonomic desk monitoring, home workout evaluation, and physical therapy sessions. Single-person tracking maximizes inference framerate (60 FPS) and browser WASM responsiveness without multi-person tracking overhead. |
| **TD-28** | Dynamic WASM Asset Loading via CDN Fallback | **Accepted Design Choice**: Serving `@mediapipe/tasks-vision` WASM binaries via CDN reduces initial repository clone size while guaranteeing browser caching across user sessions. |

---

## 3. Future Work (Planned for Phase 3+)

| Item ID | Planned Enhancement | Scope & Target Phase |
|---|---|---|
| **TD-29** | WebGPU Perception Acceleration | Upgrade WebWorker WASM delegate to WebGPU backend for higher landmark precision on supported hardware (Phase 3). |
| **TD-30** | Multi-Sensor Hybrid Perception | Integrate wearable IMU Bluetooth sensor telemetry (e.g., smart watch accelerometer) with vision keypoints for combined biomechanics (Phase 4). |
