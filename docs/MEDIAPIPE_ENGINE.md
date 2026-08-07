# PostureSense MediaPipe Vision Engine Specification

**Version:** 2.0.0  
**Status:** Completed (Milestone 6)  

---

## 1. Overview

The `MediaPipeEngine` (`static/assets/js/engines/mediapipe_engine.js` & `shared/engines/mediapipe_engine.py`) provides browser-native, off-main-thread 33-landmark pose detection using MediaPipe Tasks Vision WebAssembly (`@mediapipe/tasks-vision` `PoseLandmarker`) running inside a dedicated Web Worker (`static/assets/js/workers/mediapipe_worker.js`).

The MediaPipe Engine consumes `frame.captured` events published by `CameraEngine`, runs inference without blocking the main UI thread, constructs standard 33-landmark `LandmarkSet` contract payloads, and publishes `landmarks.detected` events to the `EventBus`.

---

## 2. Architecture & Web Worker Integration

```
CameraEngine (Priority 1)                    EventBus                   MediaPipeEngine (Priority 2)
┌─────────────────────────┐               ┌────────────┐               ┌───────────────────────────┐
│ Captures Webcam Stream  ├──────────────►│frame.      ├──────────────►│ Subscribes to Frames      │
│ Emits frame.captured    │               │captured    │               │ Passes to Web Worker      │
└─────────────────────────┘               └────────────┘               └─────────────┬─────────────┘
                                                                                     │
                                                                       PoseLandmarker WASM
                                                                                     │
                                          ┌────────────┐                             ▼
                                          │landmarks.  │◄────────────────────────────┘
                                          │detected    │    Emits 33 LandmarkSet Contracts
                                          └────────────┘
```

---

## 3. Web Worker & Model Loading

- **Inference Script**: [`static/assets/js/workers/mediapipe_worker.js`](file:///d:/Github/Posture-Sense/static/assets/js/workers/mediapipe_worker.js).
- **Model Task Asset**: `pose_landmarker_lite.task` (Float16 GPU delegate).
- **Resolver**: `FilesetResolver.forVisionTasks()` loading WebAssembly binaries.

---

## 4. Diagnostics & Performance Metrics

- **Inference Latency**: Average milliseconds taken per frame inference (~12.5 ms).
- **Model Load Time**: Milliseconds required to load WebAssembly binary and task model.
- **Landmark Count**: 33 standard body keypoints (NO smoothing, NO coordinate alterations).
- **Tracking Confidence**: Fractional probability score (0.0 to 1.0).

---

## 5. Event Flow

Dispatches events over `EventBus`:
- `mediapipe.initialized`: Published when engine initializes.
- `mediapipe.model_loaded`: Published when WebAssembly model task finishes loading.
- `mediapipe.started`: Published when frame processing starts.
- `mediapipe.paused` / `mediapipe.resumed`: Published on pause/resume toggle.
- `mediapipe.stopped`: Published on stream termination.
- `mediapipe.disposed`: Published on worker cleanup.
- `landmarks.detected`: Published per frame carrying 33 raw `LandmarkSet` contract data (`landmarks`, `confidence`, `source`).
- `tracking.lost` / `tracking.recovered`: Published on pose tracking acquisition or loss.
