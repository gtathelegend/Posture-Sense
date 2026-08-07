import time
from typing import Dict, List, Optional, Any
from shared.events.event_bus import EventBus
from shared.core.base_engine import BaseEngine
from shared.core.runtime.lifecycle import LifecycleState, validate_transition
from shared.core.runtime.registry import EngineRegistry, EngineRecord
from shared.core.runtime.dependency import DependencyResolver
from shared.core.runtime.monitor import EngineMonitor
from shared.core.runtime.metrics import EngineMetrics
from shared.core.runtime.diagnostics import EngineDiagnostics


class EngineRuntime:
    """Production-ready Engine Runtime orchestrator for PostureSense v2."""

    def __init__(self, event_bus: Optional[EventBus] = None, version: str = "2.0.0"):
        self.version = version
        self.event_bus = event_bus or EventBus()
        self.registry = EngineRegistry()
        self.monitor = EngineMonitor()
        self.metrics = EngineMetrics()
        self._start_time: Optional[float] = None

    def register(
        self,
        engine: BaseEngine,
        engine_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        priority: int = 10,
        version: str = "2.0.0"
    ) -> EngineRecord:
        record = self.registry.register(engine, engine_id, dependencies, priority, version)
        validate_transition(LifecycleState.UNREGISTERED, LifecycleState.REGISTERED)
        record.status = LifecycleState.REGISTERED
        self.monitor.get_or_create_health(record.id, record.version)
        self.event_bus.publish("engine.registered", record.to_dict())
        return record

    def unregister(self, engine_id: str) -> bool:
        record = self.registry.get(engine_id)
        if record:
            self.event_bus.publish("engine.disposed", record.to_dict())
            return self.registry.unregister(engine_id)
        return False

    def initializeAll(self) -> bool:
        init_start = time.time()
        startup_order = DependencyResolver.resolve_startup_order(self.registry.get_dependencies_map())
        success = True

        for eid in startup_order:
            record = self.registry.get(eid)
            if not record:
                continue
            try:
                validate_transition(record.status, LifecycleState.INITIALIZED)
                res = record.instance.initialize()
                record.status = LifecycleState.INITIALIZED
                self.event_bus.publish("engine.initialized", record.to_dict())
            except Exception as e:
                record.status = LifecycleState.FAILED
                self.monitor.record_error(eid, f"Initialization error: {e}")
                self.event_bus.publish("engine.failed", {"id": eid, "error": str(e)})
                success = False

        self.metrics.initialization_time_ms = (time.time() - init_start) * 1000
        return success

    def startAll(self) -> bool:
        self._start_time = time.time()
        startup_order = DependencyResolver.resolve_startup_order(self.registry.get_dependencies_map())
        all_started = True

        for eid in startup_order:
            record = self.registry.get(eid)
            if not record:
                continue
            try:
                validate_transition(record.status, LifecycleState.STARTING)
                record.status = LifecycleState.STARTING
                res = record.instance.start()
                validate_transition(record.status, LifecycleState.RUNNING)
                record.status = LifecycleState.RUNNING
                self.monitor.record_heartbeat(eid, last_event="started")
                self.event_bus.publish("engine.started", record.to_dict())
            except Exception as e:
                record.status = LifecycleState.FAILED
                self.monitor.record_error(eid, f"Startup error: {e}")
                self.event_bus.publish("engine.failed", {"id": eid, "error": str(e)})
                all_started = False

        self.metrics.startup_time_ms = (time.time() - self._start_time) * 1000
        return all_started

    def pauseAll(self) -> bool:
        records = self.registry.getAll()
        for record in records:
            if record.status == LifecycleState.RUNNING:
                try:
                    validate_transition(record.status, LifecycleState.PAUSED)
                    record.status = LifecycleState.PAUSED
                    self.event_bus.publish("engine.paused", record.to_dict())
                except Exception as e:
                    record.status = LifecycleState.FAILED
                    self.event_bus.publish("engine.failed", {"id": record.id, "error": str(e)})
        return True

    def resumeAll(self) -> bool:
        records = self.registry.getAll()
        for record in records:
            if record.status == LifecycleState.PAUSED:
                try:
                    validate_transition(record.status, LifecycleState.RUNNING)
                    record.status = LifecycleState.RUNNING
                    self.event_bus.publish("engine.resumed", record.to_dict())
                except Exception as e:
                    record.status = LifecycleState.FAILED
                    self.event_bus.publish("engine.failed", {"id": record.id, "error": str(e)})
        return True

    def stopAll(self) -> bool:
        shutdown_order = DependencyResolver.resolve_shutdown_order(self.registry.get_dependencies_map())
        for eid in shutdown_order:
            record = self.registry.get(eid)
            if not record:
                continue
            try:
                validate_transition(record.status, LifecycleState.STOPPING)
                record.status = LifecycleState.STOPPING
                record.instance.stop()
                validate_transition(record.status, LifecycleState.STOPPED)
                record.status = LifecycleState.STOPPED
                self.event_bus.publish("engine.stopped", record.to_dict())
            except Exception as e:
                record.status = LifecycleState.FAILED
                self.event_bus.publish("engine.failed", {"id": eid, "error": str(e)})
        return True

    def disposeAll(self) -> bool:
        records = self.registry.getAll()
        for record in records:
            try:
                record.instance.dispose()
                validate_transition(record.status, LifecycleState.DISPOSED)
                record.status = LifecycleState.DISPOSED
                self.event_bus.publish("engine.disposed", record.to_dict())
            except Exception as e:
                self.event_bus.publish("engine.failed", {"id": record.id, "error": str(e)})
        return True

    def get_diagnostics(self) -> Dict[str, Any]:
        return EngineDiagnostics.generate_report(
            registry=self.registry,
            runtime_version=self.version,
            startup_time_ms=self.metrics.startup_time_ms
        )
