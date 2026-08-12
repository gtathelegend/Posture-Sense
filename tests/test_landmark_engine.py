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

        landmarks = [
            Landmark(index=0, name="nose", x=0.5, y=0.5, visibility=0.9, presence=0.9),
            Landmark(index=11, name="left_shoulder", x=0.4, y=0.4, visibility=0.9, presence=0.9),
            Landmark(index=12, name="right_shoulder", x=0.6, y=0.4, visibility=0.9, presence=0.9),
            Landmark(index=23, name="left_hip", x=0.4, y=0.6, visibility=0.9, presence=0.9),
            Landmark(index=24, name="right_hip", x=0.6, y=0.6, visibility=0.9, presence=0.9),
            Landmark(index=25, name="left_knee", x=0.4, y=0.8, visibility=0.9, presence=0.9),
            Landmark(index=26, name="right_knee", x=0.6, y=0.8, visibility=0.9, presence=0.9),
            Landmark(index=27, name="left_ankle", x=0.4, y=0.9, visibility=0.9, presence=0.9),
            Landmark(index=28, name="right_ankle", x=0.6, y=0.9, visibility=0.9, presence=0.9),
        ]
        lm_set = LandmarkSet(landmarks=landmarks, confidence=0.92)

        res = self.engine.validate_and_smooth(lm_set)
        self.assertEqual(res["quality_score"], 92.0)
        self.assertEqual(res["filtering_method"], "ema")
        self.assertEqual(res["tracking_state"], "FULL_BODY")
        self.assertEqual(res["body_coverage_pct"], 100.0)

        # Check event bus recording for landmarks.validated
        events = [e for e in self.event_bus.event_history if e["name"] == "landmarks.validated"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["data"]["quality_score"], 92.0)

    def test_partial_body_tracking_classification(self):
        self.engine.initialize()
        self.engine.start()

        # Head + shoulders only (3 / 9 = 33.3% coverage -> PARTIAL_BODY)
        upper_only = [
            Landmark(index=0, name="nose", x=0.5, y=0.5, visibility=0.9, presence=0.9),
            Landmark(index=11, name="left_shoulder", x=0.4, y=0.4, visibility=0.9, presence=0.9),
            Landmark(index=12, name="right_shoulder", x=0.6, y=0.4, visibility=0.9, presence=0.9),
        ]
        lm_set = LandmarkSet(landmarks=upper_only, confidence=0.85)

        res = self.engine.validate_and_smooth(lm_set)
        self.assertEqual(res["tracking_state"], "PARTIAL_BODY")
        self.assertLess(res["body_coverage_pct"], 70.0)

    def test_low_confidence_landmark_rejection(self):
        self.engine.initialize()
        self.engine.start()

        # Low visibility landmarks (< 0.6)
        low_vis = [
            Landmark(index=0, name="nose", x=0.5, y=0.5, visibility=0.2, presence=0.9),
            Landmark(index=11, name="left_shoulder", x=0.4, y=0.4, visibility=0.2, presence=0.9),
        ]
        lm_set = LandmarkSet(landmarks=low_vis, confidence=0.5)

        res = self.engine.validate_and_smooth(lm_set)
        self.assertFalse(res["valid"])
        self.assertEqual(res["tracking_state"], "NO_TRACKING")

    def test_no_false_skeleton_on_face_only(self):
        self.engine.initialize()
        self.engine.start()

        face_only = [
            Landmark(index=0, name="nose", x=0.5, y=0.5, visibility=0.9, presence=0.9),
        ]
        lm_set = LandmarkSet(landmarks=face_only, confidence=0.8)

        res = self.engine.validate_and_smooth(lm_set)
        self.assertFalse(res["valid"])
        self.assertEqual(res["tracking_state"], "NO_TRACKING")


if __name__ == '__main__':
    unittest.main()
