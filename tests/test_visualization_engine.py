import unittest
from shared.engines.visualization_engine import VisualizationEngineInterface
from shared.events import EventBus
from shared.types.enums import EngineStatus


class TestVisualizationEngine(unittest.TestCase):

    def setUp(self):
        self.event_bus = EventBus(debug_mode=True)
        self.engine = VisualizationEngineInterface(
            name="VisualizationEngine",
            event_bus=self.event_bus
        )

    # ── Priority & dependency registration ───────────────────────────────────

    def test_priority_and_dependencies(self):
        self.assertEqual(self.engine.priority, 6)
        self.assertIn("landmark_engine", self.engine.dependencies)
        self.assertIn("pose_rule_engine", self.engine.dependencies)

    # ── Full lifecycle ────────────────────────────────────────────────────────

    def test_full_lifecycle(self):
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

    # ── Runtime events published ──────────────────────────────────────────────

    def test_lifecycle_events_published(self):
        self.engine.initialize()
        self.engine.start()
        self.engine.pause()
        self.engine.resume()
        self.engine.stop()

        names = [e["name"] for e in self.event_bus.event_history]
        self.assertIn("visualization.initialized", names)
        self.assertIn("visualization.started",     names)
        self.assertIn("visualization.paused",      names)
        self.assertIn("visualization.resumed",     names)
        self.assertIn("visualization.stopped",     names)

    # ── Config overrides via initialize ──────────────────────────────────────

    def test_config_override(self):
        self.engine.initialize(config={"target_fps": 30, "mirror_mode": False})
        self.assertEqual(self.engine.config["target_fps"], 30)
        self.assertFalse(self.engine.config["mirror_mode"])

    # ── Diagnostics shape ────────────────────────────────────────────────────

    def test_diagnostics_shape(self):
        self.engine.initialize()
        diag = self.engine.get_diagnostics()
        self.assertEqual(diag["name"], "VisualizationEngine")
        self.assertEqual(diag["version"], "2.0.0")
        self.assertIn("config",  diag)
        self.assertIn("metrics", diag)
        self.assertIn("frames_rendered",     diag["metrics"])
        self.assertIn("average_render_fps",  diag["metrics"])

    # ── Config keys present (no hardcoding check) ────────────────────────────

    def test_config_keys_all_present(self):
        expected_keys = [
            "mirror_mode", "target_fps", "show_skeleton", "show_joint_labels",
            "show_joint_angles", "show_confidence_colors", "show_center_of_mass",
            "show_balance", "show_rule_evaluation", "show_pose_label",
            "show_orientation_axes", "show_symmetry",
            "confidence_good_threshold", "confidence_warn_threshold",
            "joint_radius", "bone_line_width", "com_radius"
        ]
        for k in expected_keys:
            self.assertIn(k, self.engine.config, f"Missing config key: {k}")

    # ── Default config values are reasonable (not zero / nonsensical) ─────────

    def test_default_config_values(self):
        self.assertGreater(self.engine.config["target_fps"], 0)
        self.assertGreater(self.engine.config["joint_radius"], 0)
        self.assertGreater(self.engine.config["bone_line_width"], 0)
        self.assertGreater(self.engine.config["com_radius"], 0)
        self.assertTrue(0 < self.engine.config["confidence_good_threshold"] <= 1)
        self.assertTrue(0 < self.engine.config["confidence_warn_threshold"] < self.engine.config["confidence_good_threshold"])


if __name__ == '__main__':
    unittest.main()
