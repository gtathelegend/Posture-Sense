import unittest
from shared.events import EventBus, Event
from shared.contracts import Landmark, LandmarkSet, JointAngle, BiomechanicsSnapshot, ScoreReport
from shared.config import ConfigLoader
from shared.plugins import PluginRegistry, ExercisePlugin
from shared.utils import ContractValidator, calculate_angle_3p, format_duration
from shared.types import PluginMode


class DummyExercisePlugin(ExercisePlugin):
    @property
    def plugin_id(self) -> str:
        return "test_squat_plugin"

    @property
    def name(self) -> str:
        return "Test Squat Plugin"

    def metadata(self):
        return {"category": "test"}

    def configuration(self):
        return {"threshold": 90}

    def recognition_rules(self):
        return []

    def feedback_rules(self):
        return []

    def visualization_hooks(self):
        return {}


class TestSharedCoreInfrastructure(unittest.TestCase):

    def test_event_bus_pub_sub(self):
        bus = EventBus(debug_mode=True)
        received = []

        def handler(event: Event):
            received.append(event.data)

        bus.subscribe("test.event", handler)
        bus.publish("test.event", "payload_data")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], "payload_data")
        self.assertEqual(len(bus.event_history), 1)

    def test_event_bus_once(self):
        bus = EventBus()
        counts = [0]

        def handler(event: Event):
            counts[0] += 1

        bus.once("test.once", handler)
        bus.publish("test.once", 1)
        bus.publish("test.once", 2)

        self.assertEqual(counts[0], 1)

    def test_contract_metadata_and_serialization(self):
        lm1 = Landmark(index=0, name="NOSE", x=0.5, y=0.5)
        lm_set = LandmarkSet(landmarks=[lm1], confidence=0.95)
        
        self.assertIsNotNone(lm_set.id)
        self.assertIsNotNone(lm_set.timestamp)
        self.assertEqual(lm_set.schema_version, "2.0.0")

        d = lm_set.to_dict()
        reconstructed = LandmarkSet.from_dict(d)
        self.assertEqual(reconstructed.confidence, 0.95)
        self.assertEqual(len(reconstructed.landmarks), 1)

    def test_contract_validation(self):
        score = ScoreReport(overall_score=92.5)
        self.assertTrue(ContractValidator.validate_contract(score))

        invalid_dict = {"overall_score": 90.0}
        with self.assertRaises(ValueError):
            ContractValidator.validate_contract(invalid_dict)

    def test_config_loader(self):
        loader = ConfigLoader()
        poses_config = loader.load("poses/yoga_poses.json", version="current")
        self.assertEqual(poses_config.get("version"), "2.0.0")
        self.assertIn("warrior_ii", poses_config.get("poses", {}))

    def test_plugin_registry(self):
        registry = PluginRegistry()
        plugin = DummyExercisePlugin()
        registry.register(plugin)

        retrieved = registry.get_plugin("test_squat_plugin")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Squat Plugin")

        exercise_plugins = registry.get_by_mode(PluginMode.EXERCISE)
        self.assertEqual(len(exercise_plugins), 1)

    def test_math_and_time_utils(self):
        angle = calculate_angle_3p((0, 1, 0), (0, 0, 0), (1, 0, 0))
        self.assertEqual(angle, 90.0)

        formatted = format_duration(125.0)
        self.assertEqual(formatted, "02:05")


if __name__ == '__main__':
    unittest.main()
