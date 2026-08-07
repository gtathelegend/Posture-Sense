# PostureSense Visualization Engine Specification

**Version:** 2.0.0  
**Status:** Completed (Milestone 10)  
**Priority:** 6  
**Dependencies:** `landmark_engine`, `pose_rule_engine`

---

## 1. Overview

The `VisualizationEngine` (`static/assets/js/engines/visualization_engine.js` & `shared/engines/visualization_engine.py`) provides real-time Canvas-based rendering of the complete PostureSense AI pipeline output.

It subscribes to three EventBus channels:
- `landmarks.validated` → `ValidatedLandmarkSet` (33 normalized keypoints + visibility)
- `biomechanics.updated` → `BiomechanicsSnapshot` (joint angles, CoM, balance, symmetry, orientation)
- `pose.detected` → `PoseResult` (pose name, confidence, matched/failed rules, hold time)

It publishes:
- `visualization.initialized / started / updated / paused / resumed / stopped / disposed`

**There is no AI logic in this engine.** It is a pure rendering component for debugging, demonstration, and explainability.

---

## 2. Architecture

```
landmarks.validated   ──┐
                        │
biomechanics.updated  ──┼──► VisualizationEngine (Priority 6) ──► Canvas 2D / OffscreenCanvas
                        │         │
pose.detected         ──┘         └──► visualization.updated  ──► Debug Overlay
```

### Rendering layers (bottom → top)

| Layer | Content | Toggle |
|-------|---------|--------|
| 0 | `<video>` element (live camera stream) | always on |
| 1 | Bone connections (33 skeleton edges) | `showSkeleton` |
| 2 | Joint circles (colour-coded by visibility) | `showSkeleton` |
| 3 | Joint angle labels at vertex keypoints | `showJointAngles` |
| 4 | Joint name labels | `showJointLabels` |
| 5 | Centre-of-Mass marker | `showCenterOfMass` |
| 6 | Left/Right balance bar | `showBalance` |
| 7 | Symmetry indicator | `showSymmetry` |
| 8 | Orientation axes | `showOrientationAxes` |
| 9 | Pose name / confidence / hold HUD (top-left) | `showPoseLabel` |
| 10 | Rule evaluation panel (top-right) | `showRuleEvaluation` |

---

## 3. Skeleton Rendering

### Keypoints
All 33 MediaPipe keypoints are rendered as filled circles with a white border.  
Colour is mapped from visibility using the configurable threshold pair `confidenceGoodThreshold` / `confidenceWarnThreshold`:

| Visibility | Colour | Key |
|------------|--------|-----|
| ≥ good threshold | `colors.good` | green |
| ≥ warn threshold | `colors.warning` | yellow |
| < warn threshold | `colors.poor` | red |
| < 0.1 (hidden) | skip | — |

### Bone Connections
All 33 standard MediaPipe pose skeleton edges are drawn. Alpha is blended from visibility: `α = clamp(0.3 + vis × 0.7, 0, 1)`.

---

## 4. Joint Angle Display

Joint angles from `BiomechanicsSnapshot.joint_angles` are rendered as floating label boxes anchored to the vertex keypoint of each joint.

```
ANGLE_ANCHORS = {
  left_knee: 25,  right_knee: 26,
  left_hip: 23,   right_hip: 24,
  left_elbow: 13, right_elbow: 14,
  left_shoulder: 11, right_shoulder: 12,
  neck: 0,        spine: 23
}
```

Colour: green if angle is within `[expected_min, expected_max]`, yellow otherwise.

---

## 5. Biomechanics Overlays

### Centre of Mass (CoM)
Rendered as a concentric ring + dot using `colors.comMarker` (orange), labelled `CoM`.  
Position: `(com.x × W, com.y × H)`.

### Balance Bar
Horizontal progress bar spanning 35 % of canvas width, centred at bottom.  
Left fill = `leftRightRatio / 100`. Purple fill, white centre divider, percentage labels.

### Symmetry Indicator
Text overlay (top-right) showing overall symmetry percentage, colour-coded:
- > 85 % → green, > 60 % → yellow, ≤ 60 % → red.

### Orientation Axes
Two short vectors (forward lean and side lean) rendered from a fixed anchor point (bottom-right), useful for diagnosing torso lean.

---

## 6. Pose HUD

A semi-transparent rounded rectangle (top-left) shows:
- **Pose name** (large, white)
- **Confidence** (colour-coded: green ≥ 80 %, yellow ≥ 50 %, red < 50 %)
- **Hold timer** in seconds

---

## 7. Rule Evaluation Panel

A compact panel (top-right) shows matched and failed rule counts drawn from the `PoseResult` contract.

---

## 8. Rendering Configuration

All values are configurable via `initialize(config)` or `setOption(key, value)` at runtime. **No hardcoded values.**

| Key | Default | Description |
|-----|---------|-------------|
| `mirrorMode` | `true` | Flip canvas horizontally |
| `targetFps` | `60` | Target animation frame rate |
| `showSkeleton` | `true` | Render bones + joint circles |
| `showJointAngles` | `true` | Angle labels at each vertex |
| `showJointLabels` | `false` | Keypoint name labels |
| `showConfidenceColors` | `true` | Colour-code joints by visibility |
| `showCenterOfMass` | `true` | CoM marker |
| `showBalance` | `true` | Balance progress bar |
| `showRuleEvaluation` | `true` | Matched/failed rule panel |
| `showPoseLabel` | `true` | Pose name HUD |
| `showOrientationAxes` | `false` | Torso lean axis lines |
| `showSymmetry` | `false` | Symmetry % text |
| `confidenceGoodThreshold` | `0.7` | Visibility → green |
| `confidenceWarnThreshold` | `0.4` | Visibility → yellow |
| `jointRadius` | `5` | Joint circle radius (px) |
| `boneLineWidth` | `2.5` | Bone stroke width (px) |
| `comRadius` | `10` | CoM marker radius (px) |

---

## 9. Color System

All colours are configurable via `initialize(colorOverrides)` or `setColor(key, value)`. **No hardcoded hex values in render paths.**

| Key | Default | Semantic |
|-----|---------|----------|
| `good` | `#22c55e` | High confidence / in-range |
| `warning` | `#eab308` | Moderate confidence / borderline |
| `poor` | `#ef4444` | Low confidence / out-of-range |
| `tracking` | `#3b82f6` | Neutral tracking marker |
| `missing` | `#6b7280` | Invisible / missing keypoint |
| `bone` | `rgba(255,255,255,0.55)` | Skeleton edge |
| `comMarker` | `#f97316` | Centre-of-Mass ring |
| `balanceLine` | `#a855f7` | Balance bar fill |
| `poseLabel` | `#ffffff` | Pose name text |
| `overlay` | `rgba(0,0,0,0.55)` | HUD background |
| `labelBg` | `rgba(15,23,42,0.80)` | Angle label background |

---

## 10. High-DPI & Responsive Rendering

`_configureHighDpi()` reads `window.devicePixelRatio` and scales the canvas buffer accordingly while keeping CSS dimensions stable.  
`resize(width, height)` can be called at any time to adapt to container size changes.  
`requestFullscreen()` delegates to the native browser Fullscreen API.

---

## 11. Mirror Mode

When `mirrorMode = true`:
- The CSS `transform: scaleX(-1)` on the `<video>` element flips the live feed.
- The Canvas context is mirrored for skeleton/angle rendering.
- Biomechanics world-space overlays (CoM, balance bar, HUD) are rendered in an unmirrored context to avoid coordinate confusion.

---

## 12. Event Flow

```
landmarks.validated  ──────────────────────────────────┐
biomechanics.updated ──── VisualizationEngine._render() ──► visualization.updated
pose.detected        ──────────────────────────────────┘
```

`visualization.updated` carries `{ fps, latencyMs }` for downstream diagnostics.

---

## 13. Diagnostics

| Metric | Description |
|--------|-------------|
| `renderFps` | Measured frames rendered per second |
| `canvasFps` | Alias of renderFps (Canvas 2D context) |
| `visualizationLatencyMs` | Time to complete one full `_render()` call |
| `droppedFrames` | Frames where rendering was skipped |
| `totalFrames` | Cumulative frame count since `start()` |

---

## 14. Runtime Integration

```
EngineRuntime
  Priority 1 → CameraEngine
  Priority 2 → MediaPipeEngine
  Priority 3 → LandmarkEngine
  Priority 4 → BiomechanicsEngine
  Priority 5 → PoseRuleEngine
  Priority 6 → VisualizationEngine   ← this engine
```

VisualizationEngine depends on `landmark_engine` (for keypoint data) and `pose_rule_engine` (for pose overlay data). It does **not** depend on BiomechanicsEngine directly — biomechanics data flows in via the shared EventBus.

---

## 15. Developer Playground (`/playground`)

The `/playground` route hosts a full-pipeline test harness with:
- Live `<video>` + transparent `<canvas>` overlay stack (canvas positioned absolutely over the video)
- Six live metric boxes (render FPS, latency, confidence, hold timer, pose name, matched/failed rules)
- Biomechanics panel (L/R balance, symmetry %, CoM coordinates, forward lean)
- Eleven real-time toggle buttons wired to `vizEngine.setOption()`
- Fullscreen canvas button

---

## 16. Debug Overlay (`CTRL + SHIFT + D`)

The global debug overlay panel now includes a **Visualization Engine** section showing:
- Render FPS and latency
- Dropped frames and total frame count

Plus pre-existing sections for Camera, MediaPipe, Landmark, Biomechanics, and Pose Rule engines.
