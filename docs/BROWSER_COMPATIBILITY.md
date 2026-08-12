# PostureSense Browser & OS Compatibility Matrix

**Version:** 2.0.0  
**Status:** Completed (Milestone 9)  

---

## 1. Supported Browser Matrix

| Browser | Version | WebAssembly (WASM) | Web Worker | `getUserMedia()` | GPU Delegate | Overall Compatibility |
|---|---|---|---|---|---|---|
| **Google Chrome** | $\ge 100$ | ✅ Supported | ✅ Supported | ✅ Supported | ✅ WebGL / WebGPU | **FULL SUPPORT** |
| **Microsoft Edge** | $\ge 100$ | ✅ Supported | ✅ Supported | ✅ Supported | ✅ WebGL / WebGPU | **FULL SUPPORT** |
| **Mozilla Firefox** | $\ge 102$ | ✅ Supported | ✅ Supported | ✅ Supported | ✅ WebGL | **FULL SUPPORT** |
| **Apple Safari (macOS)** | $\ge 16.0$ | ✅ Supported | ✅ Supported | ✅ Supported | ✅ WebGL | **FULL SUPPORT** |
| **Safari Mobile (iOS)** | $\ge 16.0$ | ✅ Supported | ✅ Supported | ✅ Supported | ✅ WebGL | **FULL SUPPORT** (Portrait/Landscape) |
| **Chrome Mobile (Android)** | $\ge 100$ | ✅ Supported | ✅ Supported | ✅ Supported | ✅ WebGL | **FULL SUPPORT** |

---

## 2. Feature & Requirement Matrix

- **Camera Permissions**: Requires HTTPS in production (localhost exempt during development). Handles `NotAllowedError` and permission denial via explicit `camera.error` event.
- **Off-Main-Thread Inference**: MediaPipe Tasks Vision (`pose_landmarker_lite.task`) executes inside Web Worker with CPU/WebGL delegate fallbacks.
- **Offline Capability**: Client-side perception pipeline (Camera, MediaPipe, Landmarks, Biomechanics, Pose Rules, Movement, Scoring, Feedback, Analytics, Reports) functions 100% offline once static WASM assets and model files are cached.
