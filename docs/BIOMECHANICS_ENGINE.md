# PostureSense Biomechanics Engine Specification

**Version:** 2.0.0  
**Status:** Completed (Milestone 8)  

---

## 1. Overview

The `BiomechanicsEngine` (`static/assets/js/engines/biomechanics_engine.js` & `shared/engines/biomechanics_engine.py`) provides 3D vector geometry calculations, body orientation vector parsing, Center of Mass (CoM) estimation, symmetry measurements, and Range of Motion (ROM) tracking.

It subscribes to `landmarks.validated` (`ValidatedLandmarkSet`) contracts emitted by `LandmarkEngine`, performs deterministic mathematical evaluations, and dispatches `biomechanics.updated` (`BiomechanicsSnapshot`) events over the `EventBus` without performing pose/exercise classification or posture quality scoring.

---

## 2. Component Architecture

```
Landmark Engine (Priority 3)                  EventBus                   Biomechanics Engine (Priority 4)
┌─────────────────────────┐               ┌────────────┐               ┌───────────────────────────┐
│ Emits Validated         ├──────────────►│landmarks.  ├──────────────►│ 1. 3D Joint Angle Vectors │
│ Keypoint Contracts      │               │validated   │               │ 2. Body Orientation       │
└─────────────────────────┘               └────────────┘               │ 3. Center of Mass & Bal.  │
                                                                       │ 4. Symmetry & ROM Tracking│
                                                                       └─────────────┬─────────────┘
                                                                                     │
                                          ┌────────────┐                             ▼
                                          │biomechanics│◄────────────────────────────┘
                                          │.updated    │    Emits BiomechanicsSnapshot
                                          └────────────┘
```

---

## 3. Mathematical Models & Joint Definitions

### 3.1 3D Joint Angle Calculation
Calculated as the interior angle between three 3D keypoint vectors at vertex \( P_2 \):
\[
\theta = \arccos\left( \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|} \right)
\]
where \( \vec{u} = P_1 - P_2 \) and \( \vec{v} = P_3 - P_2 \).

Tracked 10 Core Joints:
1. `left_knee`: HIP (23) \(\rightarrow\) KNEE (25) \(\rightarrow\) ANKLE (27)
2. `right_knee`: HIP (24) \(\rightarrow\) KNEE (26) \(\rightarrow\) ANKLE (28)
3. `left_hip`: SHOULDER (11) \(\rightarrow\) HIP (23) \(\rightarrow\) KNEE (25)
4. `right_hip`: SHOULDER (12) \(\rightarrow\) HIP (24) \(\rightarrow\) KNEE (26)
5. `left_elbow`: SHOULDER (11) \(\rightarrow\) ELBOW (13) \(\rightarrow\) WRIST (15)
6. `right_elbow`: SHOULDER (12) \(\rightarrow\) ELBOW (14) \(\rightarrow\) WRIST (16)
7. `left_shoulder`: HIP (23) \(\rightarrow\) SHOULDER (11) \(\rightarrow\) ELBOW (13)
8. `right_shoulder`: HIP (24) \(\rightarrow\) SHOULDER (12) \(\rightarrow\) ELBOW (14)
9. `neck`: SHOULDER_MID \(\rightarrow\) NOSE (0) \(\rightarrow\) VERTICAL
10. `spine`: SHOULDER_MID \(\rightarrow\) HIP_MID \(\rightarrow\) VERTICAL

---

### 3.2 Center of Mass (CoM) & Balance Approximation
- **Center of Mass (CoM)**: Weighted geometric mean of shoulder, hip, and knee keypoints:
  \[
  \text{CoM}_x = \frac{\sum x_i}{N}, \quad \text{CoM}_y = \frac{\sum y_i}{N}
  \]
- **Left/Right Balance Ratio**: Measures horizontal offset between CoM and hip center line.

---

### 3.3 Symmetry & ROM Tracking
- **Symmetry Scores**: Measures vertical height differentials between bilateral pairs (Shoulder height symmetry, Hip level symmetry, Knee angle symmetry).
- **Range of Motion (ROM)**: Tracks real-time minimum, maximum, and angular range across a sliding frame window (`romWindowSize = 30`).

---

## 4. Event Flow

Dispatches events over `EventBus`:
- `biomechanics.initialized`: Dispatched when engine initializes.
- `biomechanics.started`: Dispatched when processing loop begins.
- `biomechanics.paused` / `biomechanics.resumed`: Dispatched on pause/resume.
- `biomechanics.stopped`: Dispatched on termination.
- `biomechanics.updated`: Published per frame with `BiomechanicsSnapshot` contract payload (`joint_angles`, `orientation`, `center_of_mass`, `balance`, `symmetry`, `rom`).
