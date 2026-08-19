# PostureSense v2 Test & Quality Assurance Guide

**Version:** 2.0.0  
**Test Suite Status:** 154 Passed / 0 Failed
**Test Framework:** Pytest 8.x + Pytest-Asyncio  

---

## 1. Executive Testing Strategy

PostureSense v2 employs a multi-layered quality assurance strategy designed to ensure correctness, reliability, security, and performance across all 11 core engines and API endpoints.

```
┌────────────────────────────────────────────────────────┐
│                   SECURITY & AUDIT                     │
│         IDOR Guards · Secret Fail-Fast Guards         │
├────────────────────────────────────────────────────────┤
│                   INTEGRATION TESTS                    │
│      Flask API Endpoints · Session Persistence DB      │
├────────────────────────────────────────────────────────┤
│                     ENGINE TESTS                       │
│    11 Core Engine Unit Tests · Event Bus Contracts     │
└────────────────────────────────────────────────────────┘
```

---

## 2. Test Suite Composition

The test suite located under `tests/` contains **154 automated test cases**:

| Test Module | Coverage Area | Test Count | Status |
|---|---|---|---|
| [test_shared_core.py](file:///d:/Github/Posture-Sense/tests/test_shared_core.py) | EventBus, Event model, BaseEngine lifecycle, DependencyResolver | 7 | PASSING |
| [test_camera_engine.py](file:///d:/Github/Posture-Sense/tests/test_camera_engine.py) | Camera configuration, frame rate control, resolution scaling | 3 | PASSING |
| [test_mediapipe_engine.py](file:///d:/Github/Posture-Sense/tests/test_mediapipe_engine.py) | WASM landmarker interface, keypoint parsing | 7 | PASSING |
| [test_landmark_engine.py](file:///d:/Github/Posture-Sense/tests/test_landmark_engine.py) | EMA smoothing, NaN validation, tracking loss recovery | 5 | PASSING |
| [test_biomechanics_engine.py](file:///d:/Github/Posture-Sense/tests/test_biomechanics_engine.py) | 3D joint angle math, ROM tracking, symmetry, CoM stability | 3 | PASSING |
| [test_pose_rule_engine.py](file:///d:/Github/Posture-Sense/tests/test_pose_rule_engine.py) | Pose rule classification, hold timer state machines | 3 | PASSING |
| [test_movement_engine.py](file:///d:/Github/Posture-Sense/tests/test_movement_engine.py) | 11-state exercise FSM, rep counter, ROM depth gate, tempo | 38 | PASSING |
| [test_scoring_engine.py](file:///d:/Github/Posture-Sense/tests/test_scoring_engine.py) | 8-dimension weighted scoring, quality gates, score bands | 12 | PASSING |
| [test_feedback_engine.py](file:///d:/Github/Posture-Sense/tests/test_feedback_engine.py) | Evidence-based rule evaluation, deduplication, cooldowns | 8 | PASSING |
| [test_analytics_engine.py](file:///d:/Github/Posture-Sense/tests/test_analytics_engine.py) | Statistical trend indicators, heatmaps, PR tracking | 7 | PASSING |
| [test_report_engine.py](file:///d:/Github/Posture-Sense/tests/test_report_engine.py) | Document composition, PDF rendering, CSV/JSON serializers | 8 | PASSING |
| [test_reports_v2.py](file:///d:/Github/Posture-Sense/tests/test_reports_v2.py) | Report schemas, legacy NULL semantics, route rendering | 14 | PASSING |
| [test_dashboard_v2.py](file:///d:/Github/Posture-Sense/tests/test_dashboard_v2.py) | Dashboard V2 analytics, trend indicators, overview endpoints | 12 | PASSING |
| [test_visualization_engine.py](file:///d:/Github/Posture-Sense/tests/test_visualization_engine.py) | Canvas render overlay configuration and High-DPI scaling | 7 | PASSING |
| [test_engine_runtime.py](file:///d:/Github/Posture-Sense/tests/test_engine_runtime.py) | Runtime lifecycle, engine startup/shutdown ordering | 5 | PASSING |
| [test_security.py](file:///d:/Github/Posture-Sense/tests/test_security.py) | Auth guards, IDOR protection, CSRF headers, secret validation | 4 | PASSING |
| [test_session_persistence.py](file:///d:/Github/Posture-Sense/tests/test_session_persistence.py) | Supabase persistence, session service validation, user isolation | 7 | PASSING |
| [test_pose_false_positives.py](file:///d:/Github/Posture-Sense/tests/test_pose_false_positives.py) | Pose rule false positive rejection boundaries | 4 | PASSING |

---

## 3. How to Run Tests

### Run Full Test Suite

Execute pytest via Python module runner from the repository root:

```bash
python -m pytest
```

### Run Specific Test Category

To run only security tests:
```bash
python -m pytest tests/test_security.py
```

To run Movement Engine FSM tests:
```bash
python -m pytest tests/test_movement_engine.py
```

### Run with Verbose Output

```bash
python -m pytest -v
```

---

## 4. Browser Validation Procedure

In addition to automated Python tests, client-side WASM perception logic is validated manually across major browsers:

1. **Chrome / Edge (Blink WASM Engine)**: Verified WASM PoseLandmarker execution at 60 FPS, $<15\text{ms}$ worker latency.
2. **Firefox (Gecko WASM Engine)**: Verified WebAssembly memory allocation and Canvas rendering.
3. **Safari (WebKit WASM Engine)**: Verified camera permission lifecycle and orientation scaling.

---

## 5. Security & Isolation Testing

Security tests in `tests/test_security.py` verify:
- **IDOR Protection**: Requests attempting to access session IDs belonging to other users are rejected with `403 Forbidden` or `404 Not Found`.
- **Production Secret Guard**: Startup fails fast with `ValueError` if `FLASK_ENV=production` is launched without configuring a secure `SECRET_KEY`.
- **Report Download Isolation**: PDF report generation verifies user ownership prior to streaming file bytes.
