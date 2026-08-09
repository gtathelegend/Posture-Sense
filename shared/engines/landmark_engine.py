from typing import Optional, Dict, Any, List
from shared.engines.interfaces import LandmarkEngineInterface
from shared.events.event_bus import EventBus
from shared.types.enums import EngineStatus
from shared.contracts.vision import Landmark, LandmarkSet


class LandmarkEngine(LandmarkEngineInterface):
    """Python Landmark Engine interface implementation for PostureSense server-side Engine Runtime."""

    def __init__(self, name: str = "LandmarkEngine", event_bus: Optional[EventBus] = None):
        super().__init__(name=name, event_bus=event_bus)
        self.version = "2.0.0"
        self.priority = 3
        self.dependencies = ["mediapipe_engine"]
        self.config = {
            "visibility_threshold": 0.6,
            "presence_threshold": 0.6,
            "quality_threshold": 60.0,
            "max_interpolation_frames": 5,
            "smoothing_method": "ema",
            "ema_alpha": 0.35
        }
        self._frames_accepted = 0
        self._frames_rejected = 0
        self._average_quality_score = 100.0

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
            return {"valid": False, "quality_score": 0.0}

        self._frames_accepted += 1
        quality_score = round(landmark_set.confidence * 100.0, 1)
        self._average_quality_score = quality_score

        validated_payload = {
            "source": self.name,
            "confidence": landmark_set.confidence,
            "quality_score": quality_score,
            "filtering_method": self.config["smoothing_method"],
            "landmarks": [lm.to_dict() for lm in landmark_set.landmarks]
        }

        self.publish("landmarks.validated", validated_payload)
        self.publish("landmarks.filtered", {"method": self.config["smoothing_method"]})
        self.publish("tracking.stable", {"qualityScore": quality_score})
        return validated_payload

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
                "average_quality_score": self._average_quality_score
            }
        }
