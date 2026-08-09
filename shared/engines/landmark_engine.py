from typing import Optional, Dict, Any, List
from shared.engines.interfaces import LandmarkEngineInterface
from shared.events.event_bus import EventBus
from shared.types.enums import EngineStatus
from shared.contracts.vision import Landmark, LandmarkSet

REQUIRED_BODY_LANDMARKS = [
    {"name": "nose", "index": 0},
    {"name": "left_shoulder", "index": 11},
    {"name": "right_shoulder", "index": 12},
    {"name": "left_hip", "index": 23},
    {"name": "right_hip", "index": 24},
    {"name": "left_knee", "index": 25},
    {"name": "right_knee", "index": 26},
    {"name": "left_ankle", "index": 27},
    {"name": "right_ankle", "index": 28}
]


class LandmarkEngine(LandmarkEngineInterface):
    """Python Landmark Engine implementation for PostureSense server-side Engine Runtime."""

    def __init__(self, name: str = "LandmarkEngine", event_bus: Optional[EventBus] = None):
        super().__init__(name=name, event_bus=event_bus)
        self.version = "2.0.0"
        self.priority = 3
        self.dependencies = ["mediapipe_engine"]
        self.config = {
            "visibility_threshold": 0.6,
            "presence_threshold": 0.6,
            "quality_threshold": 60.0,
            "full_body_threshold": 0.70,
            "partial_body_threshold": 0.30,
            "max_interpolation_frames": 5,
            "smoothing_method": "ema",
            "ema_alpha": 0.35
        }
        self._frames_accepted = 0
        self._frames_rejected = 0
        self._average_quality_score = 100.0
        self._tracking_state = "NO_TRACKING"
        self._body_coverage_pct = 0.0
        self._visible_landmarks_list = []
        self._missing_landmarks_list = []

    def initialize(self, config: Optional[dict] = None) -> bool:
        if config:
            self.config.update(config)
        self._status = EngineStatus.INITIALIZED
        self.publish("landmark.initialized", self.get_diagnostics())
        return True

    def start(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("landmark.started", self.get_diagnostics())
        return True

    def pause(self) -> bool:
        self._status = EngineStatus.PAUSED
        self.publish("landmark.paused", self.get_diagnostics())
        return True

    def resume(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("landmark.resumed", self.get_diagnostics())
        return True

    def stop(self) -> bool:
        self._status = EngineStatus.STOPPED
        self.publish("landmark.stopped", self.get_diagnostics())
        return True

    def dispose(self) -> bool:
        self._status = EngineStatus.DISPOSED
        self.publish("landmark.disposed", self.get_diagnostics())
        return True

    def validate_and_smooth(self, landmark_set: LandmarkSet) -> Dict[str, Any]:
        if not landmark_set or not landmark_set.landmarks:
            self._frames_rejected += 1
            self.publish("landmarks.invalid", {"reason": "Empty landmark set"})
            return {"valid": False, "quality_score": 0.0, "tracking_state": "NO_TRACKING"}

        raw_landmarks = [lm.to_dict() if hasattr(lm, "to_dict") else lm for lm in landmark_set.landmarks]
        annotated_landmarks = self._annotate_landmarks(raw_landmarks)
        coverage_res = self._analyze_body_coverage(annotated_landmarks)

        self._body_coverage_pct = coverage_res["coverage_pct"]
        self._tracking_state = coverage_res["tracking_state"]
        self._visible_landmarks_list = coverage_res["visible_list"]
        self._missing_landmarks_list = coverage_res["missing_list"]

        if self._tracking_state == "NO_TRACKING":
            self._frames_rejected += 1
            self.publish("landmarks.invalid", {"reason": "Insufficient body visibility (<30%)"})
            return {"valid": False, "quality_score": 0.0, "tracking_state": "NO_TRACKING"}

        self._frames_accepted += 1
        quality_score = round(landmark_set.confidence * 100.0, 1)
        self._average_quality_score = quality_score

        validated_payload = {
            "source": self.name,
            "confidence": landmark_set.confidence,
            "quality_score": quality_score,
            "filtering_method": self.config["smoothing_method"],
            "tracking_state": self._tracking_state,
            "body_coverage_pct": self._body_coverage_pct,
            "visible_landmarks": self._visible_landmarks_list,
            "missing_landmarks": self._missing_landmarks_list,
            "landmarks": annotated_landmarks
        }

        self.publish("landmarks.validated", validated_payload)
        self.publish("landmarks.filtered", {"method": self.config["smoothing_method"], "trackingState": self._tracking_state})
        self.publish("tracking.stable", {"qualityScore": quality_score})
        return validated_payload

    def _annotate_landmarks(self, landmarks: list) -> list:
        annotated = []
        for i, lm in enumerate(landmarks):
            if isinstance(lm, dict):
                vis = lm.get("visibility", 1.0)
                pres = lm.get("presence", 1.0)
                x = lm.get("x", 0.0)
                y = lm.get("y", 0.0)
                name = lm.get("name", f"landmark_{i}")
                idx = lm.get("index", i)
            else:
                vis = getattr(lm, "visibility", 1.0)
                pres = getattr(lm, "presence", 1.0)
                x = getattr(lm, "x", 0.0)
                y = getattr(lm, "y", 0.0)
                name = getattr(lm, "name", f"landmark_{i}")
                idx = getattr(lm, "index", i)

            is_vis = vis >= self.config["visibility_threshold"]
            is_pres = pres >= self.config["presence_threshold"]
            is_valid = is_vis and is_pres

            annotated.append({
                "id": i,
                "index": idx,
                "name": name,
                "x": x,
                "y": y,
                "visibility": vis,
                "presence": pres,
                "visible": is_valid,
                "reason": "valid" if is_valid else ("low_visibility" if not is_vis else "low_presence")
            })
        return annotated

    def _analyze_body_coverage(self, landmarks: list) -> dict:
        lm_map = {}
        for lm in landmarks:
            if lm.get("name"):
                lm_map[lm["name"].lower()] = lm
            if lm.get("index") is not None:
                lm_map[lm["index"]] = lm

        visible_list = []
        missing_list = []

        for req in REQUIRED_BODY_LANDMARKS:
            lm = lm_map.get(req["name"].lower()) or lm_map.get(req["index"])
            if lm and lm.get("visible", False):
                visible_list.append(req["name"])
            else:
                missing_list.append(req["name"])

        coverage = len(visible_list) / float(len(REQUIRED_BODY_LANDMARKS))
        coverage_pct = round(coverage * 100.0, 1)

        if coverage >= self.config["full_body_threshold"]:
            tracking_state = "FULL_BODY"
        elif coverage >= self.config["partial_body_threshold"]:
            tracking_state = "PARTIAL_BODY"
        else:
            tracking_state = "NO_TRACKING"

        return {
            "coverage_pct": coverage_pct,
            "tracking_state": tracking_state,
            "visible_list": visible_list,
            "missing_list": missing_list
        }

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "priority": self.priority,
            "dependencies": self.dependencies,
            "config": self.config,
            "metrics": {
                "frames_accepted": self._frames_accepted,
                "frames_rejected": self._frames_rejected,
                "average_quality_score": self._average_quality_score,
                "tracking_state": self._tracking_state,
                "body_coverage_pct": self._body_coverage_pct,
                "visible_landmarks_count": len(self._visible_landmarks_list),
                "missing_landmarks_count": len(self._missing_landmarks_list),
                "visible_landmarks": self._visible_landmarks_list,
                "missing_landmarks": self._missing_landmarks_list
            }
        }
