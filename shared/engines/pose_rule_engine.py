from typing import Optional, Dict, Any, List
from shared.engines.interfaces import PoseRuleEngineInterface
from shared.events.event_bus import EventBus
from shared.types.enums import EngineStatus
from shared.contracts.pose import PoseResult
from shared.contracts.biomechanics import BiomechanicsSnapshot


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
            "hold_threshold_seconds": 3.0
        }
        self._evaluations_count = 0
        self._current_pose = "Unknown Pose"
        self._confidence = 0.0
        self._matched_rules_count = 0
        self._failed_rules_count = 0
        self._required_landmarks_count = 0
        self._available_landmarks_count = 0
        self._body_coverage_pct = 0.0
        self._pose_rejection_reason = "None"

        # Supported Pose Definitions & Rule Constraints
        self.pose_rules = {
            "standing_neutral": {
                "id": "standing_neutral",
                "name": "Standing Neutral",
                "min_hold_time": 2.0,
                "requires_full_body": True,
                "required_regions": ["head", "shoulders", "hips", "knees", "ankles"],
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
                "requires_full_body": True,
                "required_regions": ["head", "shoulders", "hips", "knees", "ankles"],
                "constraints": {
                    "left_knee": [160, 180],
                    "right_knee": [30, 90]
                }
            },
            "warrior_ii": {
                "id": "warrior_ii",
                "name": "Warrior II",
                "min_hold_time": 3.0,
                "requires_full_body": True,
                "required_regions": ["head", "shoulders", "hips", "knees", "ankles"],
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
                "requires_full_body": True,
                "required_regions": ["head", "shoulders", "hips", "knees", "ankles"],
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
                "requires_full_body": False,
                "required_regions": ["head", "shoulders", "hips"],
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

        # Quality Gate 1: Minimum tracking quality check
        if tracking_quality < self.config.get("min_tracking_quality", 50.0):
            return self._return_unknown_state("Low Tracking Quality (< 50%)")

        # Body Coverage Analysis
        body_coverage = self._check_body_coverage(snapshot_dict)
        self._available_landmarks_count = body_coverage["valid_count"]
        self._body_coverage_pct = body_coverage["coverage_pct"]

        # Quality Gate 2: Insufficient valid keypoints check
        if body_coverage["valid_count"] < self.config.get("min_valid_landmarks", 10):
            return self._return_unknown_state("Insufficient Valid Landmarks (< 10)")

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

        for pid, rule in self.pose_rules.items():
            eval_res = self._evaluate_pose_rule(rule, angles_map, body_coverage)
            if eval_res["confidence"] > highest_confidence and eval_res["confidence"] >= self.config.get("min_confidence", 60.0):
                highest_confidence = eval_res["confidence"]
                best_match = {"id": pid, "rule": rule, **eval_res}

        if best_match:
            self._current_pose = best_match["rule"]["name"]
            self._confidence = round(best_match["confidence"], 1)
            self._matched_rules_count = best_match["matched_rules"]
            self._failed_rules_count = best_match["failed_rules"]
            self._required_landmarks_count = best_match["total_required"]
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
            return self._return_unknown_state(body_coverage.get("rejection_reason", "No pose matched confidence threshold"))

    def _evaluate_pose_rule(self, rule: dict, angles_map: dict, body_coverage: dict) -> dict:
        matched = 0
        constraints = rule.get("constraints", {})
        required_regions = rule.get("required_regions", [])

        total_joint_constraints = len(constraints)
        total_required_regions = len(required_regions)

        # FORMULA REQUIREMENT: total_required_rules = total_joint_constraints + total_required_landmarks
        total_required = total_joint_constraints + total_required_regions

        for joint, (min_a, max_a) in constraints.items():
            angle = angles_map.get(joint)
            if angle is not None and min_a <= angle <= max_a:
                matched += 1

        for region in required_regions:
            if region in body_coverage.get("available_regions", []):
                matched += 1

        if rule.get("requires_full_body", False) and not body_coverage.get("has_full_body", False):
            return {
                "confidence": 0.0,
                "matched_rules": matched,
                "failed_rules": total_required - matched,
                "total_required": total_required,
                "rejection_reason": "Requires full body tracking (lower body keypoints missing)"
            }

        confidence = (matched / total_required * 100.0) if total_required > 0 else 0.0
        return {
            "confidence": round(confidence, 1),
            "matched_rules": matched,
            "failed_rules": total_required - matched,
            "total_required": total_required,
            "rejection_reason": "None"
        }

    def _check_body_coverage(self, snapshot_dict: dict) -> dict:
        landmarks = snapshot_dict.get("landmarks", [])
        joint_angles = snapshot_dict.get("joint_angles", [])

        if not landmarks:
            available_joints = set()
            for ja in joint_angles:
                jname = ja.get("joint_name") if isinstance(ja, dict) else getattr(ja, "joint_name", None)
                if jname:
                    available_joints.add(jname)

            has_legs = "left_knee" in available_joints or "right_knee" in available_joints
            has_upper = "left_shoulder" in available_joints or "right_shoulder" in available_joints
            regions = []
            if has_upper:
                regions.extend(["head", "shoulders", "hips"])
            if has_legs:
                regions.extend(["knees", "ankles"])

            return {
                "valid_count": len(available_joints) * 2,
                "available_regions": regions,
                "coverage_pct": round((len(regions) / 5.0) * 100.0, 1),
                "has_full_body": has_legs and has_upper,
                "rejection_reason": "None" if has_legs else "Missing lower body keypoints"
            }

        valid_lms = [lm for lm in landmarks if isinstance(lm, dict) and lm.get("visibility", 1.0) >= 0.5]
        valid_indices = {lm.get("index") for lm in valid_lms if lm.get("index") is not None}

        regions = []
        if any(i in valid_indices for i in range(11)):
            regions.append("head")
        if 11 in valid_indices or 12 in valid_indices:
            regions.append("shoulders")
        if 23 in valid_indices or 24 in valid_indices:
            regions.append("hips")
        if 25 in valid_indices or 26 in valid_indices:
            regions.append("knees")
        if 27 in valid_indices or 28 in valid_indices:
            regions.append("ankles")

        has_full_body = all(r in regions for r in ["head", "shoulders", "hips", "knees", "ankles"])
        rejection_reason = "None" if ("knees" in regions and "ankles" in regions) else "Lower body missing (knees/ankles cut off)"

        return {
            "valid_count": len(valid_lms),
            "available_regions": regions,
            "coverage_pct": round((len(regions) / 5.0) * 100.0, 1),
            "has_full_body": has_full_body,
            "rejection_reason": rejection_reason
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
                "available_landmarks_count": self._available_landmarks_count,
                "body_coverage_pct": self._body_coverage_pct,
                "pose_rejection_reason": self._pose_rejection_reason
            }
        }
