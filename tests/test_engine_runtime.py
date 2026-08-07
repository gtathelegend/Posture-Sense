import unittest
from typing import Optional
from shared.core.base_engine import BaseEngine
from shared.core.runtime import (
    EngineRuntime, LifecycleState, InvalidStateTransitionError,
    CircularDependencyError, MissingDependencyError
)
from shared.events import EventBus, Event


class DummyTestEngine(BaseEngine):
    def __init__(self, name: str, event_bus: Optional[EventBus] = None):
        super().__init__(name=name, event_bus=event_bus)
        self.init_called = False
        self.start_called = False
        self.stop_called = False

    def initialize(self, config=None) -> bool:
        self.init_called = True
        return True

    def start(self) -> bool:
        self.start_called = True
        return True

    def stop(self) -> bool:
        self.stop_called = True
        return True

    def dispose(self) -> bool:
        return True


class TestEngineRuntimeSystem(unittest.TestCase):

    def setUp(self):
        self.event_bus = EventBus(debug_mode=True)
        self.runtime = EngineRuntime(event_bus=self.event_bus)

    def test_engine_registration(self):
        eng = DummyTestEngine("CameraEngine", self.event_bus)
        rec = self.runtime.register(eng, engine_id="camera_engine", priority=1)

        self.assertTrue(self.runtime.registry.exists("camera_engine"))
        self.assertEqual(rec.status, LifecycleState.REGISTERED)
        self.assertEqual(len(self.event_bus.event_history), 1)
        self.assertEqual(self.event_bus.event_history[0]["name"], "engine.registered")

    def test_lifecycle_and_dependency_resolution(self):
        cam = DummyTestEngine("CameraEngine", self.event_bus)
        mp = DummyTestEngine("MediaPipeEngine", self.event_bus)
        bio = DummyTestEngine("BiomechanicsEngine", self.event_bus)

        self.runtime.register(cam, engine_id="camera_engine", priority=1)
        self.runtime.register(mp, engine_id="mediapipe_engine", dependencies=["camera_engine"], priority=2)
        self.runtime.register(bio, engine_id="biomechanics_engine", dependencies=["mediapipe_engine"], priority=3)

        self.assertTrue(self.runtime.initializeAll())
        self.assertTrue(self.runtime.startAll())

        self.assertEqual(self.runtime.registry.get("camera_engine").status, LifecycleState.RUNNING)
        self.assertEqual(self.runtime.registry.get("mediapipe_engine").status, LifecycleState.RUNNING)
        self.assertEqual(self.runtime.registry.get("biomechanics_engine").status, LifecycleState.RUNNING)

        self.assertTrue(cam.start_called)
        self.assertTrue(mp.start_called)

        self.assertTrue(self.runtime.stopAll())
        self.assertEqual(self.runtime.registry.get("camera_engine").status, LifecycleState.STOPPED)

    def test_circular_dependency_detection(self):
        eng1 = DummyTestEngine("Engine1", self.event_bus)
        eng2 = DummyTestEngine("Engine2", self.event_bus)

        self.runtime.register(eng1, engine_id="engine1", dependencies=["engine2"])
        self.runtime.register(eng2, engine_id="engine2", dependencies=["engine1"])

        with self.assertRaises(CircularDependencyError):
            self.runtime.initializeAll()

    def test_missing_dependency_detection(self):
        eng1 = DummyTestEngine("Engine1", self.event_bus)
        self.runtime.register(eng1, engine_id="engine1", dependencies=["non_existent_engine"])

        with self.assertRaises(MissingDependencyError):
            self.runtime.initializeAll()

    def test_health_monitoring_and_diagnostics(self):
        eng = DummyTestEngine("AnalyticsEngine", self.event_bus)
        self.runtime.register(eng, engine_id="analytics_engine")

        self.runtime.monitor.record_heartbeat("analytics_engine", last_event="test_event")
        self.runtime.monitor.record_error("analytics_engine", "Test error log")

        health = self.runtime.monitor.get_or_create_health("analytics_engine")
        self.assertEqual(health.health_score, 85.0)
        self.assertEqual(len(health.errors), 1)

        diag = self.runtime.get_diagnostics()
        self.assertEqual(diag["engine_count"], 1)
        self.assertEqual(diag["runtime_version"], "2.0.0")


if __name__ == '__main__':
    unittest.main()
