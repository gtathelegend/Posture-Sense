# PostureSense Pose Rule Engine Specification

**Version:** 2.0.0  
**Status:** Completed (Milestone 9)  

---

## 1. Overview

The `PoseRuleEngine` (`static/assets/js/engines/pose_rule_engine.js` & `shared/engines/pose_rule_engine.py`) provides static posture classification and hold time tracking using rule-based constraint evaluation.

It subscribes to `biomechanics.updated` (`BiomechanicsSnapshot`) contracts emitted by `BiomechanicsEngine`, evaluates joint angle ranges and orientation metrics against 12 configuration-driven poses (Mountain, Tree, Warrior I, Warrior II, Triangle, Chair, Downward Dog, Cobra, Bridge, Child's Pose, Standing Neutral, Seated Neutral), calculates rule match confidence, tracks pose hold durations (Entered, Stable, Exited), and dispatches `PoseResult` contracts over the `EventBus` without using machine learning or neural networks.

---

## 2. Component Architecture

```
Biomechanics Engine (Priority 4)             EventBus                     Pose Rule Engine (Priority 5)
┌─────────────────────────┐               ┌────────────┐               ┌───────────────────────────┐
│ Emits 33 Keypoint Vector├──────────────►│biomechanics│──────────────►│ 1. Rule Config Loader     │
│ Measurements & Angles   │               │.updated    │               │ 2. Angle Range Evaluation │
└─────────────────────────┘               └────────────┘               │ 3. Confidence Calculation │
                                                                       │ 4. Hold Duration Timer    │
                                                                       └─────────────┬─────────────┘
                                                                                     │
                                          ┌────────────┐                             ▼
                                          │pose.       │◄────────────────────────────┘
                                          │detected    │    Emits PoseResult Contracts
                                          └────────────┘
```

---

## 3. Configuration & Rule Format

Pose definitions are loaded from versioned JSON/YAML configurations (`shared/config/current/poses/yoga_poses.json`):

Example Pose Rule Structure:
```json
{
  "warrior_ii": {
    "id": "warrior_ii",
    "name": "Warrior II",
    "minHoldTime": 3.0,
    "constraints": {
      "left_knee": [80, 110],
      "right_knee": [160, 180],
      "left_shoulder": [80, 105],
      "right_shoulder": [80, 105]
    }
  }
}
```

### 3.1 Supported 12 Poses
1. Mountain Pose (`mountain_pose`)
2. Tree Pose (`tree_pose`)
3. Warrior I (`warrior_i`)
4. Warrior II (`warrior_ii`)
5. Triangle Pose (`triangle_pose`)
6. Chair Pose (`chair_pose`)
7. Downward Dog (`downward_dog`)
8. Cobra Pose (`cobra`)
9. Bridge Pose (`bridge`)
10. Child's Pose (`child_pose`)
11. Standing Neutral (`standing_neutral`)
12. Seated Neutral (`seated_neutral`)

---

## 4. Rule Evaluation & Hold Detection

- **Rule Match Confidence**: Derived percentage calculated as \(\frac{\text{Matched Constraints}}{\text{Total Constraints}} \times 100\).
- **Hold Timer State Machine**:
  - `entered`: Initial entry when pose confidence \(\ge 60\%\).
  - `holding`: Active hold after 1.0 second elapsed.
  - `completed`: Successfully held for `minHoldTime` (e.g. 3.0s).
  - `exited`: Dispatched when user changes posture or breaks constraints.

---

## 5. Event Flow

Dispatches events over `EventBus`:
- `pose.initialized`: Published when engine initializes.
- `pose.started`: Published when rule evaluation loop begins.
- `pose.paused` / `pose.resumed`: Published on pause/resume.
- `pose.stopped`: Published on termination.
- `pose.detected`: Published per frame with `PoseResult` contract (`pose_id`, `pose_name`, `confidence`, `matched_rules`, `hold_time`).
- `pose.changed`: Published when active pose transitions.
- `pose.entered`: Published on pose entry.
- `pose.exited`: Published on pose exit.
- `pose.hold_started`: Published after 1.0s of continuous hold.
- `pose.hold_completed`: Published when `minHoldTime` is satisfied.
