# PostureSense Privacy & Data Minimization Specification

**Version:** 2.0.0  
**Status:** Completed (Milestone 10)  

---

## 1. Privacy Guarantees

PostureSense v2 is architected around **Zero Video Persistence** and **On-Device Computer Vision**:

1. **On-Device MediaPipe Inference**: Camera frames are processed strictly inside the user's browser via WebAssembly (`@mediapipe/tasks-vision`) and Web Workers.
2. **Zero Video Persistence**: Raw camera frames and video streams are **NEVER** recorded, uploaded, or transmitted to any server.
3. **Zero Raw Landmark Persistence**: 33-point raw landmark coordinate streams are processed in transient browser memory and are **NEVER** persisted to external databases.
4. **Data Minimization**: Only high-level, derived assessment metrics (`overall_score`, `rep_count`, `rom`, `stability`, `symmetry`, `duration`) are saved to the backend for longitudinal analytics.
5. **Camera Release**: Camera tracks are stopped immediately upon session completion, application pause, tab hide, or logout.
