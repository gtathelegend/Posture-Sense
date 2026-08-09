import pytest
from shared.engines.pose_rule_engine import PoseRuleEngine
from shared.contracts.biomechanics import BiomechanicsSnapshot, JointAngle
from shared.contracts.vision import Landmark, LandmarkSet


@pytest.fixture
def pose_engine():
    engine = PoseRuleEngine()
    engine.initialize()
    engine.start()
    return engine


def test_sitting_in_front_of_camera_does_not_classify_as_cobra(pose_engine):
    """
    User sitting at a desk with head, shoulders, hips visible and spine angle ~15.0 deg.
    Lower body (knees, ankles) is missing/cut off.
    Must NOT classify as Cobra Pose.
    """
    # Create snapshot for seated user (spine = 15, no lower body keypoints/joints)
    snapshot = BiomechanicsSnapshot(
        joint_angles=[
            JointAngle(joint_name="spine", angle=15.0),
            JointAngle(joint_name="left_shoulder", angle=20.0),
            JointAngle(joint_name="right_shoulder", angle=20.0),
            JointAngle(joint_name="left_elbow", angle=90.0),
            JointAngle(joint_name="right_elbow", angle=90.0),
        ],
        symmetry_score=95.0,
        balance_score=90.0,
        source="BiomechanicsEngine"
    )

    result = pose_engine.evaluate_rules(snapshot)
    assert result.pose_name != "Cobra Pose", f"Seated user incorrectly classified as Cobra Pose! Got: {result.pose_name}"
    assert result.pose_name in ["Unknown Pose", "Seated Neutral"]


def test_missing_legs_reduces_confidence_for_full_body_poses(pose_engine):
    """
    Full body poses like Cobra Pose must require lower body tracking.
    When legs are missing, confidence for Cobra Pose must be zero / below 60%.
    """
    snapshot = BiomechanicsSnapshot(
        joint_angles=[
            JointAngle(joint_name="spine", angle=20.0),
            JointAngle(joint_name="left_hip", angle=160.0),
        ],
        symmetry_score=90.0,
        balance_score=90.0,
        source="BiomechanicsEngine"
    )

    result = pose_engine.evaluate_rules(snapshot)
    assert result.confidence < 60.0
    assert result.pose_name != "Cobra Pose"


def test_low_tracking_quality_returns_unknown_pose(pose_engine):
    """
    If tracking quality is below threshold (< 50.0), evaluate_rules must return Unknown Pose immediately.
    """
    snapshot_dict = {
        "joint_angles": [
            {"joint_name": "spine", "angle": 20.0},
            {"joint_name": "left_hip", "angle": 165.0},
            {"joint_name": "right_hip", "angle": 165.0},
            {"joint_name": "left_knee", "angle": 170.0},
            {"joint_name": "right_knee", "angle": 170.0},
        ],
        "tracking_quality": 35.0,  # Below 50% gate
        "landmarks": []
    }

    result = pose_engine.evaluate_rules(snapshot_dict)
    assert result.pose_name == "Unknown Pose"
    assert result.confidence == 0.0
    assert not result.is_recognized


def test_valid_cobra_fixture_classifies_correctly(pose_engine):
    """
    Valid Cobra Pose fixture with full body keypoints and extended prone hips/knees/spine
    must classify as Cobra Pose correctly.
    """
    # 33 full body landmarks present
    full_landmarks = [
        {"index": i, "x": 0.5, "y": 0.5, "z": 0.0, "visibility": 0.95}
        for i in range(33)
    ]

    snapshot_dict = {
        "joint_angles": [
            {"joint_name": "spine", "angle": 20.0},
            {"joint_name": "left_hip", "angle": 165.0},
            {"joint_name": "right_hip", "angle": 165.0},
            {"joint_name": "left_knee", "angle": 170.0},
            {"joint_name": "right_knee", "angle": 170.0},
        ],
        "tracking_quality": 95.0,
        "landmarks": full_landmarks
    }

    result = pose_engine.evaluate_rules(snapshot_dict)
    assert result.pose_name == "Cobra Pose"
    assert result.confidence >= 60.0
    assert result.is_recognized
