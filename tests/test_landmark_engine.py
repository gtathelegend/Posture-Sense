import unittest
from shared.engines.landmark_engine import LandmarkEngine
from shared.contracts.vision import Landmark, LandmarkSet
from shared.events import EventBus
from shared.types.enums import EngineStatus


class TestLandmarkEngine(unittest.TestCase):

    def setUp(self):
        self.event_bus = EventBus(debug_mode=True)
        self.engine = LandmarkEngine(name="LandmarkEngine", event_bus=self.event_bus)

    def test_landmark_lifecycle_and_registration(self):
        self.assertEqual(self.engine.priority, 3)
        self.assertIn("mediapipe_engine", self.engine.dependencies)

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

    def test_validation_and_quality_scoring(self):
        self.engine.initialize()
        self.engine.start()

        landmarks = [Landmark(index=i, name=f"KP_{i}", x=0.5, y=0.5) for i in range(33)]
        lm_set = LandmarkSet(landmarks=landmarks, confidence=0.92)

        res = self.engine.validate_and_smooth(lm_set)
        self.assertEqual(res["quality_score"], 92.0)
        self.assertEqual(res["filtering_method"], "ema")

        # Check event bus recording for landmarks.validated
        events = [e for e in self.event_bus.event_history if e["name"] == "landmarks.validated"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["data"]["quality_score"], 92.0)

    def test_landmark_diagnostics(self):
        self.engine.initialize()
        self.engine.start()
        landmarks = [Landmark(index=i, name=f"KP_{i}", x=0.5, y=0.5) for i in range(33)]
        self.engine.validate_and_smooth(LandmarkSet(landmarks=landmarks, confidence=0.90))

        diag = self.engine.get_diagnostics()
        self.assertEqual(diag["name"], "LandmarkEngine")
        self.assertEqual(diag["metrics"]["frames_accepted"], 1)
        self.assertEqual(diag["metrics"]["average_quality_score"], 90.0)


if __name__ == '__main__':
    unittest.main()
