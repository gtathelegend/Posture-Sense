# PostureSense v2 — Landmark Visibility & Partial Body Tracking Documentation

## Overview
This document specifies the landmark data flow, visibility metadata preservation, confidence filtering thresholds, body coverage calculation, and visualization overlay behaviors in PostureSense v2.

---

## 1. Landmark Data Flow & Metadata Preservation

Every keypoint output from the MediaPipe worker into `LandmarkEngine` and downstream engines preserves all 7 contract fields with safe defaults:

```json
{
  "id": 0,
  "index": 0,
  "name": "nose",
  "x": 0.5123,
  "y": 0.3412,
  "z": -0.012,
  "visibility": 0.98,
  "presence": 0.95
}
```

If MediaPipe does not return a value for `visibility` or `presence`, safe fallbacks (`0.0`) are applied automatically.

---

## 2. Landmark Confidence Filtering

`LandmarkEngine` enforces configurable confidence thresholds:
- `visibilityThreshold = 0.60`
- `presenceThreshold = 0.60`

A landmark is annotated as `visible: true` if and only if:
$$\text{visibility} \ge 0.60 \quad \text{AND} \quad \text{presence} \ge 0.60$$

If either score falls below $0.60$, the keypoint is marked `visible: false` with reason `low_visibility` or `low_presence`. Invalid keypoints are excluded from bone connection rendering and joint calculations.

---

## 3. Body Coverage Calculation & Tracking Quality States

Body coverage is evaluated across 9 core required keypoints:
- **Head**: `nose` (0)
- **Shoulders**: `left_shoulder` (11), `right_shoulder` (12)
- **Torso**: `left_hip` (23), `right_hip` (24)
- **Legs**: `left_knee` (25), `right_knee` (26), `left_ankle` (27), `right_ankle` (28)

$$\text{coverage} = \frac{\text{visible\_required\_landmarks}}{9.0}$$

### Tracking Quality States:

| State | Coverage Range | Canvas Overlay Behavior | Pose Engine Behavior |
| :--- | :--- | :--- | :--- |
| **`FULL_BODY`** | $\ge 70\%$ | Full skeleton, joint angles, & CoM HUD rendered | Normal pose classification active |
| **`PARTIAL_BODY`** | $30\% - 69\%$ | Only valid bones/joints rendered + `⚠️ Move farther away` banner | Pose evaluation returns `Unknown Pose` |
| **`NO_TRACKING`** | $< 30\%$ | Skeleton hidden completely + `🚫 No person detected` banner | Pose evaluation returns `Unknown Pose` |

---

## 4. UI Warning Overlay Specifications

When tracking is `PARTIAL_BODY` or `NO_TRACKING`, `VisualizationEngine` renders a top-center warning banner on the HUD canvas:

- **`PARTIAL_BODY` Banner**:
  - Icon & Header: `⚠️ Move farther away`
  - Subtitle: `Full body not visible — Body visibility: XX%`
  - Color: Amber (`rgba(217, 119, 6, 0.92)`)

- **`NO_TRACKING` Banner**:
  - Icon & Header: `🚫 No person detected`
  - Subtitle: `Step into frame or adjust camera angle`
  - Color: Red (`rgba(220, 38, 38, 0.92)`)
