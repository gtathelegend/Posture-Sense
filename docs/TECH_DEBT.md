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

---

## Remaining Technical Debt (Deferred to Phase 2+)

| Item ID | Description | Planned Phase |
|---|---|---|
| **TD-08** | Server-side OpenCV / MediaPipe video streaming (`/video_feed`) causing high CPU usage | Phase 2 (Browser MediaPipe WASM Engine) |
| **TD-09** | Hardcoded pose classification if-statements in `classifyPose()` | Phase 2 (Configuration-driven Pose Rule Engine) |
| **TD-10** | Monolithic Jinja2 HTML templates without modern component framework | Phase 3 (Next.js + React Frontend Migration) |
| **TD-11** | Heavy server-side dependencies (`opencv-contrib-python`, `mediapipe`, `protobuf`) | Phase 2 (Backend dependency cleanup) |
