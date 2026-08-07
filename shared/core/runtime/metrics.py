import time
from typing import Dict, Any


class EngineMetrics:
    """Collects runtime performance metrics (startup time, initialization time, event count, processing time)."""

    def __init__(self):
        self.startup_time_ms: float = 0.0
        self.initialization_time_ms: float = 0.0
        self.event_count: int = 0
        self.error_count: int = 0
        self.total_processing_time_ms: float = 0.0
        self.processing_samples: int = 0

    def record_event(self, processing_time_ms: float = 0.0) -> None:
        self.event_count += 1
        if processing_time_ms > 0:
            self.total_processing_time_ms += processing_time_ms
            self.processing_samples += 1

    def record_error(self) -> None:
        self.error_count += 1

    @property
    def avg_processing_time_ms(self) -> float:
        if self.processing_samples == 0:
            return 0.0
        return round(self.total_processing_time_ms / self.processing_samples, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "startup_time_ms": round(self.startup_time_ms, 2),
            "initialization_time_ms": round(self.initialization_time_ms, 2),
            "event_count": self.event_count,
            "error_count": self.error_count,
            "avg_processing_time_ms": self.avg_processing_time_ms
        }
