# PostureSense Landmark Processing Engine Specification

**Version:** 2.0.0  
**Status:** Completed (Milestone 7)  

---

## 1. Overview

The `LandmarkEngine` (`static/assets/js/engines/landmark_engine.js` & `shared/engines/landmark_engine.py`) serves as the quality gate for all downstream biomechanical and pose rule engines.

It subscribes to raw `landmarks.detected` (`LandmarkSet`) contracts emitted by `MediaPipeEngine`, validates keypoint boundary bounds and visibility thresholds, computes a 0–100 Frame Quality Score, applies configurable temporal smoothing (Exponential Moving Average / OneEuro Filter), recovers missing keypoints via historical frame interpolation up to `max_interpolation_frames`, and publishes `landmarks.validated` (`ValidatedLandmarkSet`) events to the `EventBus`.

---

## 2. Component Architecture

```
MediaPipe Engine (Priority 2)                  EventBus                   Landmark Engine (Priority 3)
┌─────────────────────────┐               ┌────────────┐               ┌───────────────────────────┐
│ Emits Raw Keypoints     ├──────────────►│landmarks.  ├──────────────►│ 1. Keypoint Validation    │
│ (33 MediaPipe Keypoints)│               │detected    │               │ 2. Temporal Smoothing     │
└─────────────────────────┘               └────────────┘               │ 3. Missing Interpolation  │
                                                                       │ 4. Quality Scoring (0-100)│
                                                                       └─────────────┬─────────────┘
                                                                                     │
                                          ┌────────────┐                             ▼
                                          │landmarks.  │◄────────────────────────────┘
                                          │validated   │    Emits ValidatedLandmarkSet
                                          └────────────┘
```

---

## 3. Key Pipeline Steps

### 3.1 Validation Pipeline
- Rejects empty landmark sets or frames with fewer than 10 valid keypoints.
- Filters out NaN, infinite, and out-of-bounds (`x`, `y` outside `[-0.5, 1.5]`) coordinates.

### 3.2 Temporal Smoothing Pipeline
- **Exponential Moving Average (EMA)**: \( S_t = \alpha \cdot X_t + (1 - \alpha) \cdot S_{t-1} \) (default \(\alpha = 0.35\)).
- **OneEuro Filter**: Adaptive low-pass filter reducing high-frequency jitter while preserving fast movements.

### 3.3 Missing Keypoint Recovery
- Interpolates keypoints with visibility below `visibilityThreshold` (default `0.5`) using previous valid keypoint state up to `max_interpolation_frames` (default `5`).

### 3.4 Quality Assessment
- Frame Quality Score (0 to 100): Weighted calculation combining keypoint visibility and tracking confidence:
  \[
  \text{QualityScore} = (\text{AvgVisibility} \times 50) + (\text{Confidence} \times 50)
  \]

---

## 4. Configuration Parameters

Configurable options via `ConfigLoader`:
- `visibility_threshold`: Default `0.5`
- `presence_threshold`: Default `0.5`
- `quality_threshold`: Default `60.0`
- `max_interpolation_frames`: Default `5`
- `smoothing_method`: `'ema'`, `'one_euro'`, or `'none'`
- `ema_alpha`: Default `0.35`
- `one_euro_beta`: Default `0.007`

---

## 5. Event Flow

Dispatches events over `EventBus`:
- `landmark.initialized`: Dispatched when engine initializes.
- `landmark.started`: Dispatched when landmark processing loop starts.
- `landmark.paused` / `landmark.resumed`: Dispatched on pause/resume.
- `landmark.stopped`: Dispatched on termination.
- `landmarks.validated`: Published per frame with `ValidatedLandmarkSet` contract (`quality_score`, `filtering_method`, `tracking_state`, `landmarks`).
- `landmarks.filtered`: Dispatched when temporal smoothing is applied.
- `landmarks.interpolated`: Dispatched when missing keypoint interpolation occurs.
- `landmarks.invalid`: Dispatched when frame fails validation checks.
- `tracking.stable` / `tracking.unstable`: Dispatched based on quality score threshold.
