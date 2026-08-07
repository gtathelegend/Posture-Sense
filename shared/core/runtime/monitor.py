from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


class EngineHealth:
    def __init__(self, engine_id: str, version: str = "2.0.0"):
        self.engine_id = engine_id
        self.version = version
        self.status = "registered"
        self.uptime_seconds = 0.0
        self.start_timestamp: Optional[datetime] = None
        self.last_heartbeat: Optional[str] = None
        self.last_event: Optional[str] = None
        self.memory_bytes = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.health_score = 100.0

    def record_heartbeat(self, last_event: Optional[str] = None) -> None:
        self.last_heartbeat = datetime.now(timezone.utc).isoformat()
        if last_event:
            self.last_event = last_event
        if self.start_timestamp:
            self.uptime_seconds = (datetime.now(timezone.utc) - self.start_timestamp).total_seconds()

    def record_error(self, error_message: str) -> None:
        self.errors.append(error_message)
        self.health_score = max(0.0, self.health_score - 15.0)

    def record_warning(self, warning_message: str) -> None:
        self.warnings.append(warning_message)
        self.health_score = max(0.0, self.health_score - 5.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "version": self.version,
            "status": self.status,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "last_heartbeat": self.last_heartbeat,
            "last_event": self.last_event,
            "memory_bytes": self.memory_bytes,
            "errors": self.errors,
            "warnings": self.warnings,
            "health_score": self.health_score
        }


class EngineMonitor:
    """Monitors health reports across all system engines."""

    def __init__(self):
        self._health_reports: Dict[str, EngineHealth] = {}

    def get_or_create_health(self, engine_id: str, version: str = "2.0.0") -> EngineHealth:
        if engine_id not in self._health_reports:
            self._health_reports[engine_id] = EngineHealth(engine_id=engine_id, version=version)
        return self._health_reports[engine_id]

    def record_heartbeat(self, engine_id: str, last_event: Optional[str] = None) -> None:
        health = self.get_or_create_health(engine_id)
        health.record_heartbeat(last_event)

    def record_error(self, engine_id: str, error_message: str) -> None:
        health = self.get_or_create_health(engine_id)
        health.record_error(error_message)

    def record_warning(self, engine_id: str, warning_message: str) -> None:
        health = self.get_or_create_health(engine_id)
        health.record_warning(warning_message)

    def get_health_summary(self) -> Dict[str, Any]:
        reports = self.get_all_reports()
        total = len(reports)
        avg_score = sum(r["health_score"] for r in reports.values()) / total if total > 0 else 100.0
        return {
            "total_monitored": total,
            "average_health_score": round(avg_score, 1),
            "reports": reports
        }

    def get_all_reports(self) -> Dict[str, Dict[str, Any]]:
        return {eid: h.to_dict() for eid, h in self._health_reports.items()}
