import unittest
from shared.engines.pose_rule_engine import PoseRuleEngine
from shared.contracts.biomechanics import JointAngle, BiomechanicsSnapshot
from shared.events import EventBus
from shared.types.enums import EngineStatus


class TestPoseRuleEngine(unittest.TestCase):

    def setUp(self):
        self.event_bus = EventBus(debug_mode=True)
        self.engine = PoseRuleEngine(name="PoseRuleEngine", event_bus=self.event_bus)

    def test_pose_rule_lifecycle_and_registration(self):
        self.assertEqual(self.engine.priority, 5)
        self.assertIn("biomechanics_engine", self.engine.dependencies)

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

    def test_pose_rule_evaluation(self):
        self.engine.initialize()
        self.engine.start()

        joint_angles = [JointAngle(joint_name="left_knee", angle=175.0)]
        snapshot = BiomechanicsSnapshot(joint_angles=joint_angles, symmetry_score=98.0)

        result = self.engine.evaluate_rules(snapshot)
        self.assertEqual(result.pose_name, "Standing Neutral")
        self.assertEqual(result.confidence, 100.0)
        self.assertTrue(result.is_recognized)

        # Check event bus recording for pose.detected
        events = [e for e in self.event_bus.event_history if e["name"] == "pose.detected"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["data"]["pose_name"], "Standing Neutral")

    def test_pose_rule_diagnostics(self):
        self.engine.initialize()
        self.engine.start()
        self.engine.evaluate_rules(BiomechanicsSnapshot(joint_angles=[], symmetry_score=98.0))

        diag = self.engine.get_diagnostics()
        self.assertEqual(diag["name"], "PoseRuleEngine")
        self.assertEqual(diag["metrics"]["evaluations_count"], 1)
        self.assertEqual(diag["metrics"]["current_pose_name"], "Standing Neutral")


if __name__ == '__main__':
    unittest.main()
