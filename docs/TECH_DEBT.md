# PostureSense Technical Debt Registry

## Closed Technical Debt (Resolved in Phase 1)

| Item ID | Description | Resolution |
|---|---|---|
| **TD-01** | Monolithic `app.py` (>900 lines) | Split into `backend/app/` blueprints, services, repositories, and models. |
| **TD-02** | Direct database queries in HTTP route handlers | Moved database queries into `UserRepository` and `SessionRepository`. |
| **TD-03** | Ad-hoc environment variable parsing scattered in code | Centralized configuration in `backend/app/config.py`. |
| **TD-04** | Global extension state and lack of application factory | Implemented `create_app()` and `backend/app/extensions.py`. |
| **TD-05** | Unstructured `print()` statements for debugging | Replaced with standard Flask logging in `backend/app/logging.py`. |
| **TD-06** | Unhandled HTTP exceptions returning generic 500 errors | Added centralized error handlers in `backend/app/errors.py`. |
| **TD-07** | Missing security HTTP response headers | Added security middleware (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`). |
| **TD-08** | Direct HTTP fetch calls embedded in HTML inline scripts | Extracted frontend service layer (`AuthService`, `DashboardService`, `SessionService`, `ContactService`). |
| **TD-09** | Tight coupling between UI elements and lower event handlers | Introduced `EngineAdapter` and `EngineContext` state architecture. |
| **TD-10** | Lack of runtime lifecycle state machine & dependency resolution | Implemented `EngineRuntime`, `EngineRegistry`, `LifecycleState`, and `DependencyResolver`. |
| **TD-11** | Server-side webcam streaming dependency | Implemented browser-native `CameraEngine` with device selection, resolution options, and FPS meter. |
| **TD-12** | Main-thread blocking computer vision inference | Implemented `MediaPipeEngine` with WebAssembly (`PoseLandmarker`) running inside a Web Worker. |
| **TD-13** | Raw keypoint jitter and unvalidated landmarks | Implemented `LandmarkEngine` quality gate with EMA filtering, NaN validation, and interpolation. |
| **TD-14** | Heuristic 2D joint angle approximations | Implemented `BiomechanicsEngine` 3D vector geometry, CoM estimation, symmetry analysis, and ROM tracking. |
| **TD-15** | Hardcoded pose classification thresholds | Implemented configuration-driven `PoseRuleEngine` matching 12 poses with hold timers. |
| **TD-16** | No real-time skeleton or biomechanics visualization | Implemented `VisualizationEngine` Canvas renderer with 11 configurable overlays, 60 FPS target, High-DPI support, and mirror mode. |
| **TD-17** | No dynamic rep counting, phase detection, or exercise hold tracking | Implemented `MovementEngine` (Priority 7) with 11-state FSM, sequential phase ordering, debounced rep counter, ROM gate, tempo analyzer, and 10 YAML exercise configs. |
| **TD-21** | No explainable or multi-dimension performance scoring | Implemented `ScoringEngine` (Priority 8) with 8 configurable scoring dimensions, versioned weights, score confidence, score bands, quality gates, rep/hold/session scoring, and explainability breakdown. |
| **TD-22** | Hardcoded text strings & lack of evidence-based coaching guidance | Implemented `FeedbackEngine` (Priority 9) with rule-based evaluation, empirical evidence models, severity ranking, deduplication, cooldown timers, and multi-language template keys. |
| **TD-23** | Lack of longitudinal trend analytics and personal record tracking | Implemented `AnalyticsEngine` (Priority 10) with deterministic statistical trend classification, exercise performance history, personal records, calendar streaks, session comparisons, user isolation, and REST APIs. |




---

## Remaining Technical Debt (Deferred to Phase 3+)

| Item ID | Description | Planned Phase |
|---|---|---|
| **TD-18** | Server-side OpenCV / MediaPipe video streaming (`/video_feed`) causing high CPU usage | Phase 3 (Browser MediaPipe WASM Engine) |
| **TD-19** | Monolithic Jinja2 HTML templates without modern component framework | Phase 4 (Next.js + React Frontend Migration) |
| **TD-20** | Heavy server-side dependencies (`opencv-contrib-python`, `mediapipe`, `protobuf`) | Phase 3 (Backend dependency cleanup) |

