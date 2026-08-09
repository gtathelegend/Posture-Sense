# PostureSense v2 — MediaPipe Local Vendor Assets & Failure Handling

## Overview
PostureSense v2 relies on MediaPipe Tasks Vision (`PoseLandmarker`) for client-side pose landmark perception. To ensure production resilience when third-party CDNs (jsDelivr, Google Cloud Storage) are blocked, offline, or experiencing network latency, all required MediaPipe runtime assets are hosted locally under `/static/vendor/mediapipe/`.

---

## 1. Local Asset Directory Structure

```
static/vendor/mediapipe/
├── vision_bundle.js                       (MediaPipe Tasks Vision bundle JS)
├── pose_landmarker_lite.task              (5.7 MB Float16 Lite Pose Landmarker model)
└── wasm/
    ├── vision_wasm_internal.js            (WASM loader script - SIMD)
    ├── vision_wasm_internal.wasm          (9.0 MB WebAssembly binary - SIMD)
    ├── vision_wasm_nosimd_internal.js     (WASM loader script - Non-SIMD fallback)
    └── vision_wasm_nosimd_internal.wasm   (8.1 MB WebAssembly binary - Non-SIMD)
```

---

## 2. Asset Loading Strategy & Fallback Hierarchy

`static/assets/js/workers/mediapipe_worker.js` uses a resilient two-tier loading protocol:

1. **Tier 1 (Local Primary)**:
   - Worker imports `/static/vendor/mediapipe/vision_bundle.js`.
   - `FilesetResolver.forVisionTasks` points to `/static/vendor/mediapipe/wasm`.
   - Model task file points to `/static/vendor/mediapipe/pose_landmarker_lite.task`.

2. **Tier 2 (CDN Fallback)**:
   - If local files are missing, HTTP 404, or fail to load, worker automatically catches the exception and falls back to:
     - Bundle: `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/vision_bundle.js`
     - WASM: `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm`
     - Model: `https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task`

---

## 3. Production Failure Recovery & UI Reset

When MediaPipe worker initialization or frame inference fails:

1. `MediaPipeEngine` publishes `tracking.lost` and `mediapipe.failed` with details (`reason`, `error`, `timestamp`).
2. `VisualizationEngine` receives `tracking.lost`:
   - Immediately clears canvas `ctx.clearRect(0, 0, W, H)`.
   - Flushes cached landmarks, skeleton, joint angles, and pose overlays (`this._latestLandmarks = null`, `this._latestPose = null`).
   - Displays warning overlay banner: `🚫 Pose tracking unavailable`.
3. `PosePipelineController` sets pipeline health to `DEGRADED` and suppresses false healthy status reports.
