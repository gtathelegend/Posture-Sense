import unittest
from shared.engines.biomechanics_engine import BiomechanicsEngine
from shared.contracts.vision import Landmark, LandmarkSet
from shared.events import EventBus
from shared.types.enums import EngineStatus


class TestBiomechanicsEngine(unittest.TestCase):

    def setUp(self):
        self.event_bus = EventBus(debug_mode=True)
        self.engine = BiomechanicsEngine(name="BiomechanicsEngine", event_bus=self.event_bus)

    def test_biomechanics_lifecycle_and_registration(self):
        self.assertEqual(self.engine.priority, 4)
        self.assertIn("landmark_engine", self.engine.dependencies)

        self.assertTrue(self.engine.initialize())
        self.assertEqual(self.engine.status(), EngineStatus.INITIALIZED)

        self.assertTrue(self.engine.start())
        self.assertEqual(self.engine.status(), EngineStatus.RUNNING)

        self.assertTrue(self.engine.pause())
        self.assertEqual(self.engine.status(), EngineStatus.PAUSED)

        self.assertTrue(self.engine.resume())
        self.assertEqual(self.engine.status(), EngineStatus.RUNNING)

        self.assertTrue(self.engine.stop())
        self.assertEqual(self.engine.status(), EngineStatus.STOPPED)

        self.assertTrue(self.engine.dispose())
        self.assertEqual(self.engine.status(), EngineStatus.DISPOSED)

    def test_biomechanics_snapshot_generation(self):
        self.engine.initialize()
        self.engine.start()

        landmarks = [Landmark(index=i, name=f"KP_{i}", x=0.5, y=0.5) for i in range(33)]
        lm_set = LandmarkSet(landmarks=landmarks, confidence=0.95)

        snapshot = self.engine.process_biomechanics(lm_set)
        self.assertEqual(len(snapshot.joint_angles), 5)
        self.assertEqual(snapshot.symmetry_score, 98.0)
        self.assertEqual(snapshot.balance_score, 95.0)

        # Check event bus recording for biomechanics.updated
        events = [e for e in self.event_bus.event_history if e["name"] == "biomechanics.updated"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["data"]["symmetry_score"], 98.0)

    def test_biomechanics_diagnostics(self):
        self.engine.initialize()
        self.engine.start()
        landmarks = [Landmark(index=i, name=f"KP_{i}", x=0.5, y=0.5) for i in range(33)]
        self.engine.process_biomechanics(LandmarkSet(landmarks=landmarks, confidence=0.95))

        diag = self.engine.get_diagnostics()
        self.assertEqual(diag["name"], "BiomechanicsEngine")
        self.assertEqual(diag["metrics"]["snapshots_generated"], 1)
        self.assertEqual(diag["metrics"]["tracked_joint_count"], 10)


if __name__ == '__main__':
    unittest.main()
