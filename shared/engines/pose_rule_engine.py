from typing import Optional, Dict, Any, List
from shared.engines.interfaces import PoseRuleEngineInterface
from shared.events.event_bus import EventBus
from shared.types.enums import EngineStatus
from shared.contracts.pose import PoseResult
from shared.contracts.biomechanics import BiomechanicsSnapshot


class PoseRuleEngine(PoseRuleEngineInterface):
    """Python Pose Rule Engine interface implementation for PostureSense server-side Engine Runtime."""

    def __init__(self, name: str = "PoseRuleEngine", event_bus: Optional[EventBus] = None):
        super().__init__(name=name, event_bus=event_bus)
        self.version = "2.0.0"
        self.priority = 5
        self.dependencies = ["biomechanics_engine"]
        self.config = {
            "min_confidence": 60.0,
            "hold_threshold_seconds": 3.0
        }
        self._evaluations_count = 0
        self._current_pose = "Standing Neutral"
        self._confidence = 100.0

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
        result = PoseResult(
            pose_name=self._current_pose,
            confidence=self._confidence,
            is_recognized=True,
            source=self.name
        )

        self.publish("pose.detected", result.to_dict())
        self.publish("pose.entered", {"pose_name": self._current_pose})
        self.publish("pose.hold_started", {"pose_name": self._current_pose})
        return result

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "priority": self.priority,
            "dependencies": self.dependencies,
            "config": self.config,
            "metrics": {
                "evaluations_count": self._evaluations_count,
                "current_pose_name": self._current_pose,
                "confidence_score": self._confidence
            }
        }
