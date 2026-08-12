import unittest
from shared.engines.camera_engine import CameraEngine
from shared.events import EventBus
from shared.types.enums import EngineStatus


class TestCameraEngine(unittest.TestCase):

    def setUp(self):
        self.event_bus = EventBus(debug_mode=True)
        self.engine = CameraEngine(name="CameraEngine", event_bus=self.event_bus)

    def test_camera_lifecycle(self):
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

    def test_frame_publishing(self):
        self.engine.initialize()
        self.engine.start()

        payload = self.engine.record_frame(width=1280, height=720, fps=30)
        self.assertEqual(payload["width"], 1280)
        self.assertEqual(payload["height"], 720)
        self.assertEqual(payload["frame_number"], 1)

        # Check event bus recording
        events = [e for e in self.event_bus.event_history if e["name"] == "frame.captured"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["data"]["frame_number"], 1)

    def test_camera_diagnostics(self):
        self.engine.initialize()
        self.engine.start()
        self.engine.record_frame(width=1920, height=1080, fps=60)

        diag = self.engine.get_diagnostics()
        self.assertEqual(diag["name"], "CameraEngine")
        self.assertEqual(diag["metrics"]["resolution"], "1920x1080")
        self.assertEqual(diag["metrics"]["fps"], 60)


if __name__ == '__main__':
    unittest.main()
