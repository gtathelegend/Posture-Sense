from typing import Optional, Dict, Any, List
from shared.engines.interfaces import MediaPipeEngineInterface
from shared.events.event_bus import EventBus
from shared.types.enums import EngineStatus
from shared.contracts.vision import Landmark, LandmarkSet


class MediaPipeEngine(MediaPipeEngineInterface):
    """Python MediaPipe Engine interface implementation for PostureSense server-side Engine Runtime."""

    def __init__(self, name: str = "MediaPipeEngine", event_bus: Optional[EventBus] = None):
        super().__init__(name=name, event_bus=event_bus)
        self.version = "2.0.0"
        self.priority = 2
        self.dependencies = ["camera_engine"]
        self._is_model_loaded = False
        self._is_tracking = False
        self._frames_processed = 0
        self._inference_latency_ms = 0.0

    def initialize(self, config: Optional[dict] = None) -> bool:
        self._status = EngineStatus.INITIALIZED
        self.publish("mediapipe.initialized", self.get_diagnostics())
        self.load_model()
        return True

    def load_model(self) -> bool:
        self._is_model_loaded = True
        self.publish("mediapipe.model_loaded", self.get_diagnostics())
        return True

    def start(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("mediapipe.started", self.get_diagnostics())
        return True

    def pause(self) -> bool:
        self._status = EngineStatus.PAUSED
        self.publish("mediapipe.paused", self.get_diagnostics())
        return True

    def resume(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("mediapipe.resumed", self.get_diagnostics())
        return True

    def stop(self) -> bool:
        self._status = EngineStatus.STOPPED
        self.publish("mediapipe.stopped", self.get_diagnostics())
        return True

    def dispose(self) -> bool:
        self._status = EngineStatus.DISPOSED
        self.publish("mediapipe.disposed", self.get_diagnostics())
        return True

    def process_raw_frame(self, frame_number: int = 1) -> LandmarkSet:
        self._frames_processed += 1
        self._inference_latency_ms = 12.5

        # 33 raw MediaPipe pose keypoints
        landmarks = [
            Landmark(index=i, name=f"KEYPOINT_{i}", x=0.5, y=0.5, z=0.0, visibility=0.99)
            for i in range(33)
        ]
        landmark_set = LandmarkSet(landmarks=landmarks, confidence=0.95, source=self.name)

        if not self._is_tracking:
            self._is_tracking = True
            self.publish("tracking.recovered", {"confidence": 0.95})

        self.publish("landmarks.detected", landmark_set.to_dict())
        return landmark_set

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "priority": self.priority,
            "dependencies": self.dependencies,
            "is_model_loaded": self._is_model_loaded,
            "is_tracking": self._is_tracking,
            "metrics": {
                "frames_processed": self._frames_processed,
                "inference_latency_ms": self._inference_latency_ms,
                "landmark_count": 33
            }
        }
