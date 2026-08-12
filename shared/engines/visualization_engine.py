from typing import Optional, Dict, Any
from shared.engines.interfaces import BiomechanicsEngineInterface  # reuse closest interface; Visualization is server-side metadata only
from shared.events.event_bus import EventBus
from shared.types.enums import EngineStatus


class VisualizationEngineInterface:
    """Server-side Visualization Engine metadata interface for PostureSense Engine Runtime registration."""

    def __init__(self, name: str = "VisualizationEngine", event_bus: Optional[EventBus] = None):
        self.name = name
        self.version = "2.0.0"
        self.priority = 6
        self.dependencies = ["landmark_engine", "pose_rule_engine"]
        self.event_bus = event_bus or EventBus()
        self._status = EngineStatus.UNINITIALIZED
        self.config = {
            "mirror_mode": True,
            "target_fps": 60,
            "show_skeleton": True,
            "show_joint_labels": False,
            "show_joint_angles": True,
            "show_confidence_colors": True,
            "show_center_of_mass": True,
            "show_balance": True,
            "show_rule_evaluation": True,
            "show_pose_label": True,
            "show_orientation_axes": False,
            "show_symmetry": False,
            "confidence_good_threshold": 0.7,
            "confidence_warn_threshold": 0.4,
            "joint_radius": 5,
            "bone_line_width": 2.5,
            "com_radius": 10
        }
        self._frames_rendered = 0
        self._average_render_fps = 0.0

    def initialize(self, config: Optional[dict] = None) -> bool:
        if config:
            self.config.update(config)
        self._status = EngineStatus.INITIALIZED
        self.publish("visualization.initialized", self.get_diagnostics())
        return True

    def start(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("visualization.started", self.get_diagnostics())
        return True

    def pause(self) -> bool:
        self._status = EngineStatus.PAUSED
        self.publish("visualization.paused", self.get_diagnostics())
        return True

    def resume(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("visualization.resumed", self.get_diagnostics())
        return True

    def stop(self) -> bool:
        self._status = EngineStatus.STOPPED
        self.publish("visualization.stopped", self.get_diagnostics())
        return True

    def dispose(self) -> bool:
        self._status = EngineStatus.DISPOSED
        self.publish("visualization.disposed", self.get_diagnostics())
        return True

    def status(self) -> EngineStatus:
        return self._status

    def publish(self, event_name: str, data: Any = None):
        return self.event_bus.publish(event_name, data)

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "priority": self.priority,
            "dependencies": self.dependencies,
            "config": self.config,
            "metrics": {
                "frames_rendered": self._frames_rendered,
                "average_render_fps": self._average_render_fps,
            }
        }
