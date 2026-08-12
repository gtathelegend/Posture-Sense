# PostureSense Reliability & Hardening Specification

**Version:** 2.0.0  
**Status:** Completed (Milestone 9)  

---

## 1. Fault Tolerance & Error Recovery

PostureSense v2 handles pipeline failures gracefully without uncaught browser exceptions or false state publications:

```
[Camera Failure / Permission Denied]  -->  camera.error event --> UI displays error badge
[MediaPipe Worker Crash]              -->  mediapipe.failed event --> Worker auto-restarted
[Tracking Loss (User leaves frame)]  -->  tracking.lost event --> State set to LOST/UNSTABLE
[Tracking Recovery (User returns)]   -->  tracking.recovered --> Resume normal evaluation
```

---

## 2. Structured Error Categories

All system errors are categorized and published over the EventBus:

1. `CAMERA_PERMISSION`: User denied camera access or HTTPS missing.
2. `CAMERA_UNAVAILABLE`: Webcam disconnected or in use by another application.
3. `MEDIAPIPE_MODEL`: Failed to download or initialize WASM / `.task` model file.
4. `MEDIAPIPE_WORKER`: Web Worker crash or postMessage serialization failure.
5. `LANDMARK_VALIDATION`: Insufficient visible keypoints or corrupted coordinates.
6. `BIOMECHANICS`: Geometric calculation anomaly or divide-by-zero prevention.
7. `TRACKING_LOSS`: User out of frame or partial body occlusion.

---

## 3. Free-Tier Infrastructure Audit

- **Frontend Hosting (Vercel)**: Static HTML, JS ES Modules, CSS, and WASM assets served with edge CDN caching. Zero server-side rendering cost.
- **Backend Hosting (Render)**: Flask REST APIs for analytics and report storage. Free-tier cold starts mitigated by client-side browser perception engine operating independently.
- **Data Minimization**: Zero upload of raw camera frames, video streams, or landmark streams. All real-time AI perception runs locally in the browser.
