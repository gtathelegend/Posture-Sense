from typing import Optional, Dict, Any, List
from shared.engines.interfaces import PoseRuleEngineInterface
from shared.events.event_bus import EventBus
from shared.types.enums import EngineStatus
from shared.contracts.pose import PoseResult
from shared.contracts.biomechanics import BiomechanicsSnapshot

LANDMARK_NAME_TO_INDEX = {
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
    "nose": 0
}


class PoseRuleEngine(PoseRuleEngineInterface):
    """Python Pose Rule Engine implementation for PostureSense server-side Engine Runtime."""

    def __init__(self, name: str = "PoseRuleEngine", event_bus: Optional[EventBus] = None):
        super().__init__(name=name, event_bus=event_bus)
        self.version = "2.0.0"
        self.priority = 5
        self.dependencies = ["biomechanics_engine"]
        self.config = {
            "min_confidence": 60.0,
            "min_tracking_quality": 50.0,
            "min_valid_landmarks": 10,
            "min_body_coverage_threshold": 0.70,
            "hold_threshold_seconds": 3.0
        }
        self._evaluations_count = 0
        self._current_pose = "Unknown Pose"
        self._confidence = 0.0
        self._matched_rules_count = 0
        self._failed_rules_count = 0
        self._required_landmarks_count = 0
        self._visible_landmarks_list = []
        self._missing_landmarks_list = []
        self._body_coverage_pct = 0.0
        self._pose_rejection_reason = "None"

        # Supported Pose Definitions & Rule Constraints
        self.pose_rules = {
            "standing_neutral": {
                "id": "standing_neutral",
                "name": "Standing Neutral",
                "min_hold_time": 2.0,
                "required_landmarks": [
                    "left_shoulder", "right_shoulder", "left_hip", "right_hip",
                    "left_knee", "right_knee", "left_ankle", "right_ankle"
                ],
                "constraints": {
                    "left_knee": [160, 180],
                    "right_knee": [160, 180],
                    "spine": [0, 15]
                }
            },
            "tree_pose": {
                "id": "tree_pose",
                "name": "Tree Pose",
                "min_hold_time": 3.0,
                "required_landmarks": [
                    "left_shoulder", "right_shoulder", "left_hip", "right_hip",
                    "left_knee", "right_knee", "left_ankle", "right_ankle"
                ],
                "constraints": {
                    "left_knee": [160, 180],
                    "right_knee": [30, 90]
                }
            },
            "warrior_ii": {
                "id": "warrior_ii",
                "name": "Warrior II",
                "min_hold_time": 3.0,
                "required_landmarks": [
                    "left_shoulder", "right_shoulder", "left_hip", "right_hip",
                    "left_knee", "right_knee", "left_ankle", "right_ankle"
                ],
                "constraints": {
                    "left_knee": [80, 110],
                    "right_knee": [160, 180],
                    "left_shoulder": [80, 105],
                    "right_shoulder": [80, 105]
                }
            },
            "cobra": {
                "id": "cobra",
                "name": "Cobra Pose",
                "min_hold_time": 3.0,
                "required_landmarks": [
                    "left_shoulder", "right_shoulder", "left_hip", "right_hip",
                    "left_knee", "right_knee", "left_ankle", "right_ankle"
                ],
                "constraints": {
                    "spine": [10, 45],
                    "left_hip": [150, 180],
                    "right_hip": [150, 180],
                    "left_knee": [160, 180],
                    "right_knee": [160, 180]
                }
            },
            "seated_neutral": {
                "id": "seated_neutral",
                "name": "Seated Neutral",
                "min_hold_time": 2.0,
                "required_landmarks": [
                    "left_shoulder", "right_shoulder", "left_hip", "right_hip",
                    "left_knee", "right_knee"
                ],
                "constraints": {
                    "spine": [0, 25]
                }
            }
        }

    def initialize(self, config: Optional[dict] = None) -> bool:
        if config:
            self.config.update(config)
        self._status = EngineStatus.INITIALIZED
        self.publish("pose.initialized", self.get_diagnostics())
        return True

    def start(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("pose.started", self.get_diagnostics())
        return True

    def pause(self) -> bool:
        self._status = EngineStatus.PAUSED
        self.publish("pose.paused", self.get_diagnostics())
        return True

    def resume(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("pose.resumed", self.get_diagnostics())
        return True

    def stop(self) -> bool:
        self._status = EngineStatus.STOPPED
        self.publish("pose.stopped", self.get_diagnostics())
        return True

    def dispose(self) -> bool:
        self._status = EngineStatus.DISPOSED
        self.publish("pose.disposed", self.get_diagnostics())
        return True

    def evaluate_rules(self, snapshot: BiomechanicsSnapshot) -> PoseResult:
        self._evaluations_count += 1
        snapshot_dict = snapshot.to_dict() if hasattr(snapshot, "to_dict") else snapshot

        tracking_quality = snapshot_dict.get("tracking_quality", 100.0)
        joint_angles = snapshot_dict.get("joint_angles", [])
        landmarks = snapshot_dict.get("landmarks", [])

        # Quality Gate 1: Tracking Quality Check (< 50%)
        if tracking_quality < self.config.get("min_tracking_quality", 50.0):
            return self._return_unknown_state("Low Tracking Quality (< 50%)")

        angles_map = {}
        for ja in joint_angles:
            if isinstance(ja, dict):
                jname = ja.get("joint_name")
                jangle = ja.get("angle")
            else:
                jname = getattr(ja, "joint_name", None)
                jangle = getattr(ja, "angle", None)
            if jname and jangle is not None:
                angles_map[jname] = jangle

        best_match = None
        highest_confidence = 0.0
        last_rejection_reason = "No pose matched confidence threshold"

        for pid, rule in self.pose_rules.items():
            eval_res = self._evaluate_pose_rule(rule, angles_map, landmarks, joint_angles)
            if eval_res["rejected"]:
                last_rejection_reason = eval_res["rejection_reason"]
                continue

            if eval_res["confidence"] > highest_confidence and eval_res["confidence"] >= self.config.get("min_confidence", 60.0):
                highest_confidence = eval_res["confidence"]
                best_match = {"id": pid, "rule": rule, **eval_res}

        if best_match:
            self._current_pose = best_match["rule"]["name"]
            self._confidence = round(best_match["confidence"], 1)
            self._matched_rules_count = best_match["matched_rules"]
            self._failed_rules_count = best_match["failed_rules"]
            self._required_landmarks_count = best_match["total_required_landmarks"]
            self._visible_landmarks_list = best_match["visible_landmarks"]
            self._missing_landmarks_list = best_match["missing_landmarks"]
            self._body_coverage_pct = best_match["coverage_pct"]
            self._pose_rejection_reason = "None"

            result = PoseResult(
                pose_name=self._current_pose,
                confidence=self._confidence,
                is_recognized=True,
                source=self.name
            )
            self.publish("pose.detected", result.to_dict())
            return result
        else:
            return self._return_unknown_state(last_rejection_reason)

    def _evaluate_pose_rule(self, rule: dict, angles_map: dict, landmarks: list, joint_angles: list) -> dict:
        required_landmarks = rule.get("required_landmarks", [])
        constraints = rule.get("constraints", {})

        total_required_landmarks = len(required_landmarks)
        total_joint_constraints = len(constraints)
        total_required = total_joint_constraints + total_required_landmarks

        visible_landmarks = []
        missing_landmarks = []

        if landmarks:
            lm_map = {}
            for lm in landmarks:
                if isinstance(lm, dict):
                    name = lm.get("name")
                    idx = lm.get("index")
                    vis = lm.get("visibility", 1.0)
                    pres = lm.get("presence", 1.0)
                else:
                    name = getattr(lm, "name", None)
                    idx = getattr(lm, "index", None)
                    vis = getattr(lm, "visibility", 1.0)
                    pres = getattr(lm, "presence", 1.0)

                if vis >= 0.6 and pres >= 0.6:
                    if name:
                        lm_map[name.lower()] = True
                    if idx is not None:
                        for req_n, req_i in LANDMARK_NAME_TO_INDEX.items():
                            if req_i == idx:
                                lm_map[req_n.lower()] = True

            for req_n in required_landmarks:
                if lm_map.get(req_n.lower(), False):
                    visible_landmarks.append(req_n)
                else:
                    missing_landmarks.append(req_n)
        else:
            available_joints = set()
            for ja in joint_angles:
                jname = ja.get("joint_name") if isinstance(ja, dict) else getattr(ja, "joint_name", None)
                if jname:
                    available_joints.add(jname)

            for req_n in required_landmarks:
                if "knee" in req_n and ("left_knee" in available_joints or "right_knee" in available_joints):
                    visible_landmarks.append(req_n)
                elif "shoulder" in req_n and ("left_shoulder" in available_joints or "right_shoulder" in available_joints):
                    visible_landmarks.append(req_n)
                elif "hip" in req_n and ("left_hip" in available_joints or "right_hip" in available_joints):
                    visible_landmarks.append(req_n)
                elif "ankle" in req_n and ("left_knee" in available_joints or "right_knee" in available_joints):
                    # Ankle inferable if knee present
                    visible_landmarks.append(req_n)
                else:
                    missing_landmarks.append(req_n)

        visible_count = len(visible_landmarks)
        coverage = (visible_count / total_required_landmarks) if total_required_landmarks > 0 else 1.0
        coverage_pct = round(coverage * 100.0, 1)

        # BODY COVERAGE VALIDATION: If coverage < 70%, return UNKNOWN / Insufficient body visibility
        if coverage < self.config.get("min_body_coverage_threshold", 0.70):
            return {
                "rejected": True,
                "confidence": 0.0,
                "coverage_pct": coverage_pct,
                "visible_landmarks": visible_landmarks,
                "missing_landmarks": missing_landmarks,
                "total_required_landmarks": total_required_landmarks,
                "rejection_reason": "Insufficient body visibility"
            }

        matched_joints = 0
        for joint, (min_a, max_a) in constraints.items():
            angle = angles_map.get(joint)
            if angle is not None and min_a <= angle <= max_a:
                matched_joints += 1

        total_matched = matched_joints + visible_count
        confidence = (total_matched / total_required * 100.0) if total_required > 0 else 0.0

        return {
            "rejected": False,
            "confidence": round(confidence, 1),
            "matched_rules": total_matched,
            "failed_rules": total_required - total_matched,
            "total_required": total_required,
            "total_required_landmarks": total_required_landmarks,
            "visible_landmarks": visible_landmarks,
            "missing_landmarks": missing_landmarks,
            "coverage_pct": coverage_pct,
            "rejection_reason": "None"
        }

    def _return_unknown_state(self, reason: str) -> PoseResult:
        self._current_pose = "Unknown Pose"
        self._confidence = 0.0
        self._matched_rules_count = 0
        self._failed_rules_count = 0
        self._pose_rejection_reason = reason

        result = PoseResult(
            pose_name="Unknown Pose",
            confidence=0.0,
            is_recognized=False,
            source=self.name
        )
        self.publish("pose.detected", result.to_dict())
        return result

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "status": self._status.value if hasattr(self._status, "value") else str(self._status),
            "priority": self.priority,
            "dependencies": self.dependencies,
            "config": self.config,
            "metrics": {
                "evaluations_count": self._evaluations_count,
                "current_pose_name": self._current_pose,
                "confidence_score": self._confidence,
                "required_landmarks_count": self._required_landmarks_count,
                "visible_landmarks_count": len(self._visible_landmarks_list),
                "missing_landmarks_count": len(self._missing_landmarks_list),
                "visible_landmarks": self._visible_landmarks_list,
                "missing_landmarks": self._missing_landmarks_list,
                "body_coverage_pct": self._body_coverage_pct,
                "pose_rejection_reason": self._pose_rejection_reason
            }
        }
