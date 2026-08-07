from typing import Dict, List, Optional, Any
from shared.core.base_engine import BaseEngine
from shared.core.runtime.lifecycle import LifecycleState


class EngineRecord:
    """Registry metadata container for an engine instance."""

    def __init__(
        self,
        engine: BaseEngine,
        engine_id: Optional[str] = None,
        name: Optional[str] = None,
        version: str = "2.0.0",
        dependencies: Optional[List[str]] = None,
        priority: int = 10
    ):
        self.instance = engine
        self.id = engine_id or getattr(engine, 'name', 'unnamed_engine')
        self.name = name or getattr(engine, 'name', self.id)
        self.version = version
        self.dependencies = dependencies or []
        self.priority = priority
        self.status = LifecycleState.REGISTERED
        self.health_score = 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "priority": self.priority,
            "health_score": self.health_score
        }


class EngineRegistry:
    """Central registration authority for all PostureSense system engines."""

    def __init__(self):
        self._records: Dict[str, EngineRecord] = {}

    def register(
        self,
        engine: BaseEngine,
        engine_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        priority: int = 10,
        version: str = "2.0.0"
    ) -> EngineRecord:
        eid = engine_id or getattr(engine, 'name', 'unnamed_engine')
        record = EngineRecord(
            engine=engine,
            engine_id=eid,
            name=getattr(engine, 'name', eid),
            version=version,
            dependencies=dependencies or [],
            priority=priority
        )
        self._records[eid] = record
        return record

    def unregister(self, engine_id: str) -> bool:
        if engine_id in self._records:
            record = self._records.pop(engine_id)
            record.status = LifecycleState.UNREGISTERED
            return True
        return False

    def get(self, engine_id: str) -> Optional[EngineRecord]:
        return self._records.get(engine_id)

    def get_instance(self, engine_id: str) -> Optional[BaseEngine]:
        record = self.get(engine_id)
        return record.instance if record else None

    def getAll(self) -> List[EngineRecord]:
        return list(self._records.values())

    def exists(self, engine_id: str) -> bool:
        return engine_id in self._records

    def list(self) -> List[str]:
        return list(self._records.keys())

    def get_dependencies_map(self) -> Dict[str, List[str]]:
        return {eid: rec.dependencies for eid, rec in self._records.items()}
