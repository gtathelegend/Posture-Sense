# PostureSense Production Smoke Test Guide

**Version:** 2.0.0  
**Script:** `scripts/production_smoke_test.py`  
**Purpose:** Verify live deployment endpoint status, static asset MIME types, binary file integrity, and response latencies without modifying database state.

---

## 1. Quick Start

Run the smoke test script against a running local server or production URL:

### Local Environment
```bash
python scripts/production_smoke_test.py
```

### Production Deployment (e.g. Render)
```bash
BASE_URL=https://posture-sense-4b1i.onrender.com python scripts/production_smoke_test.py
```

---

## 2. Tested Endpoints & Assets

| Target | Endpoint Path | Expected HTTP Status | Expected Content-Type | Minimum Expected Size |
|---|---|:---:|---|:---:|
| **Health Check** | `/health` | 200 | `application/json` | — |
| **API Health Check** | `/api/health` | 200 | `application/json` | — |
| **Version Metadata** | `/version` | 200 | `application/json` | — |
| **Index Page** | `/` | 200 | `text/html` | — |
| **MediaPipe Vision Bundle** | `/static/vendor/mediapipe/v0.10.0/vision_bundle.js` | 200 | `application/javascript` | 100 KB |
| **Pose Landmarker Model** | `/static/vendor/mediapipe/v0.10.0/pose_landmarker_lite.task` | 200 | `application/octet-stream` | 1 MB |
| **WASM Runtime Binary** | `/static/vendor/mediapipe/v0.10.0/wasm/vision_wasm_internal.wasm` | 200 | `application/wasm` | 1 MB |
| **Worker Script** | `/static/assets/js/workers/mediapipe_worker.js` | 200 | `application/javascript` | 1 KB |
| **Engine Script** | `/static/assets/js/engines/mediapipe_engine.js` | 200 | `application/javascript` | 1 KB |

---

## 3. Failure Diagnostics

- **HTML Error Fallback Detection**: If Flask or a reverse proxy returns an HTML 404/500 page for static WASM/JS/.task assets, the script identifies this error immediately and fails the test.
- **MIME Type Mismatch**: Ensures `.wasm` is served as `application/wasm` and `.task` as `application/octet-stream` to prevent Web Worker execution failures in modern browsers.
- **Non-Destructive Execution**: The script makes only read-only `GET` requests; it does not persist fake sessions or mutate database records.
