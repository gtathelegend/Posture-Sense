from typing import Optional, Dict, Any
from shared.engines.interfaces import CameraEngineInterface
from shared.events.event_bus import EventBus
from shared.types.enums import EngineStatus


class CameraEngine(CameraEngineInterface):
    """Python Camera Engine interface implementation for PostureSense server-side Engine Runtime."""

    def __init__(self, name: str = "CameraEngine", event_bus: Optional[EventBus] = None):
        super().__init__(name=name, event_bus=event_bus)
        self.version = "2.0.0"
        self._fps = 0
        self._resolution = "1280x720"
        self._frame_count = 0

    def initialize(self, config: Optional[dict] = None) -> bool:
        self._status = EngineStatus.INITIALIZED
        self.publish("camera.initialized", self.get_diagnostics())
        return True

    def start(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("camera.started", self.get_diagnostics())
        return True

    def pause(self) -> bool:
        self._status = EngineStatus.PAUSED
        self.publish("camera.paused", self.get_diagnostics())
        return True

    def resume(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("camera.resumed", self.get_diagnostics())
        return True

    def stop(self) -> bool:
        self._status = EngineStatus.STOPPED
        self.publish("camera.stopped", self.get_diagnostics())
        return True

    def dispose(self) -> bool:
        self._status = EngineStatus.DISPOSED
        self.publish("camera.disposed", self.get_diagnostics())
        return True

    def record_frame(self, width: int = 1280, height: int = 720, fps: int = 30) -> Dict[str, Any]:
        self._frame_count += 1
        self._fps = fps
        self._resolution = f"{width}x{height}"
        payload = {
            "source": self.name,
            "frame_number": self._frame_count,
            "width": width,
            "height": height,
            "fps": fps
        }
        self.publish("frame.captured", payload)
        return payload

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "metrics": {
                "fps": self._fps,
                "resolution": self._resolution,
                "frame_count": self._frame_count
            }
        }
