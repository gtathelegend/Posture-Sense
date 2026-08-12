import unittest
from shared.engines.mediapipe_engine import MediaPipeEngine
from shared.events import EventBus
from shared.types.enums import EngineStatus


class TestMediaPipeEngine(unittest.TestCase):

    def setUp(self):
        self.event_bus = EventBus(debug_mode=True)
        self.engine = MediaPipeEngine(name="MediaPipeEngine", event_bus=self.event_bus)

    def test_mediapipe_lifecycle_and_registration(self):
        self.assertEqual(self.engine.priority, 2)
        self.assertIn("camera_engine", self.engine.dependencies)

        self.assertTrue(self.engine.initialize())
        self.assertTrue(self.engine._is_model_loaded)
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

    def test_landmark_detection_publishing(self):
        self.engine.initialize()
        self.engine.start()

        landmark_set = self.engine.process_raw_frame(frame_number=1)
        self.assertEqual(len(landmark_set.landmarks), 33)
        self.assertEqual(landmark_set.confidence, 0.95)

        # Check event bus recording for landmarks.detected
        events = [e for e in self.event_bus.event_history if e["name"] == "landmarks.detected"]
        self.assertEqual(len(events), 1)
        self.assertEqual(len(events[0]["data"]["landmarks"]), 33)

    def test_mediapipe_diagnostics(self):
        self.engine.initialize()
        self.engine.start()
        self.engine.process_raw_frame(frame_number=1)

        diag = self.engine.get_diagnostics()
        self.assertEqual(diag["name"], "MediaPipeEngine")
        self.assertTrue(diag["is_model_loaded"])
        self.assertTrue(diag["is_tracking"])
        self.assertEqual(diag["metrics"]["landmark_count"], 33)


    def test_mediapipe_worker_local_asset_paths_and_no_cdn(self):
        worker_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', 'js', 'workers', 'mediapipe_worker.js'))
        with open(worker_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('/static/vendor/mediapipe/v0.10.0', content)
        self.assertIn('vision_bundle.js', content)
        self.assertIn('wasm', content)
        self.assertIn('pose_landmarker_lite.task', content)

        # Confirm no production CDN URLs remain
        self.assertNotIn('cdn.jsdelivr.net', content)
        self.assertNotIn('unpkg.com', content)
        self.assertNotIn('storage.googleapis.com', content)

    def test_mediapipe_engine_js_no_cdn(self):
        engine_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', 'js', 'engines', 'mediapipe_engine.js'))
        with open(engine_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertNotIn('cdn.jsdelivr.net', content)
        self.assertNotIn('unpkg.com', content)

    def test_flask_serves_mediapipe_local_static_assets(self):
        from backend.app import create_app
        from backend.app.config import Config

        app = create_app(Config)
        app.config['TESTING'] = True
        client = app.test_client()

        res_bundle = client.get('/static/vendor/mediapipe/v0.10.0/vision_bundle.js')
        self.assertEqual(res_bundle.status_code, 200)

        res_task = client.get('/static/vendor/mediapipe/v0.10.0/pose_landmarker_lite.task')
        self.assertEqual(res_task.status_code, 200)

        res_wasm_js = client.get('/static/vendor/mediapipe/v0.10.0/wasm/vision_wasm_internal.js')
        self.assertEqual(res_wasm_js.status_code, 200)

        res_wasm_bin = client.get('/static/vendor/mediapipe/v0.10.0/wasm/vision_wasm_internal.wasm')
        self.assertEqual(res_wasm_bin.status_code, 200)

    def test_pipeline_controller_degraded_state(self):
        ctrl_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', 'js', 'controllers', 'pose_pipeline_controller.js'))
        with open(ctrl_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('[PostureSense][Pipeline] MediaPipe ready.', content)
        self.assertIn('[PostureSense][Pipeline] MediaPipe failed.', content)
        self.assertIn('DEGRADED', content)


import os

if __name__ == '__main__':
    unittest.main()

