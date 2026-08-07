# PostureSense Camera Engine Specification

**Version:** 2.0.0  
**Status:** Completed (Milestone 5)  

---

## 1. Overview

The `CameraEngine` (`static/assets/js/engines/camera_engine.js` & `shared/engines/camera_engine.py`) provides browser-native video acquisition, device enumeration, constraint management, camera switching, resolution scaling, frame rate monitoring, and event publication over the `EventBus` without performing AI model inference or pose landmark detection.

---

## 2. Component Architecture

```
Browser (JavaScript)                           Event Bus & Runtime
┌─────────────────────────┐                   ┌─────────────────────────┐
│  CameraViewport Component │                   │   EngineRuntime System  │
│  (HTML5 <video> Stream) │                   │   (Priority 1 Engine)   │
└───────────┬─────────────┘                   └────────────▲────────────┘
            │                                              │
            ▼                                              │
┌─────────────────────────┐    frame.captured              │
│      CameraEngine       ├────────────────────────────────┘
│ (getUserMedia, 30/60FPS)│    camera.started / camera.stopped
└─────────────────────────┘
```

---

## 3. Browser APIs & Configuration

- **Media Stream Acquisition**: Uses `navigator.mediaDevices.getUserMedia({ video: constraints, audio: false })`.
- **Device Enumeration**: Calls `navigator.mediaDevices.enumerateDevices()` filtering for `videoinput` devices. Remembers user choice in `localStorage`.
- **Supported Resolutions**: `640x480` (SD), `1280x720` (HD 720p), `1920x1080` (FHD 1080p).
- **Supported Frame Rates**: `15`, `24`, `30`, `60` FPS.

---

## 4. Diagnostics & Metrics

- **FPS Counter**: Calculates live frames per second window.
- **Captured Frames**: Tracks cumulative frames captured.
- **Resolution**: Live video track width and height settings.
- **Permission Status**: `granted`, `denied`, or `prompt`.
- **Device Name**: Media stream track label.

---

## 5. Event Flow

Dispatches events over `EventBus`:
- `camera.initialized`: Published when constraints and engine initialize.
- `camera.started`: Published when webcam stream starts playing.
- `camera.paused` / `camera.resumed`: Published on pause/resume toggle.
- `camera.stopped`: Published on stream termination.
- `camera.disposed`: Published on resource cleanup.
- `frame.captured`: Published per video frame with `Frame` contract metadata payload (`frame_number`, `width`, `height`, `fps`).
- `camera.error`: Published on permission denial or stream interruption.
