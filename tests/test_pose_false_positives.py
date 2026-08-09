import pytest
from shared.engines.pose_rule_engine import PoseRuleEngine
from shared.contracts.biomechanics import BiomechanicsSnapshot, JointAngle


@pytest.fixture
def pose_engine():
    engine = PoseRuleEngine()
    engine.initialize()
    engine.start()
    return engine


def test_upper_body_only_returns_unknown(pose_engine):
    """
    User sitting close to camera with only upper body visible (head, shoulders visible; hips, knees, ankles missing).
    Coverage for Seated Neutral (2/6 required = 33%) is < 70%.
    Must return Unknown Pose with confidence = 0.
    """
    # Only shoulders present in landmark map
    upper_body_landmarks = [
        {"name": "left_shoulder", "index": 11, "visibility": 0.95, "presence": 0.95},
        {"name": "right_shoulder", "index": 12, "visibility": 0.95, "presence": 0.95},
        {"name": "nose", "index": 0, "visibility": 0.95, "presence": 0.95},
    ]

    snapshot = BiomechanicsSnapshot(
        joint_angles=[
            JointAngle(joint_name="spine", angle=15.0),
            JointAngle(joint_name="left_shoulder", angle=20.0),
            JointAngle(joint_name="right_shoulder", angle=20.0),
        ],
        landmarks=upper_body_landmarks,
        symmetry_score=95.0,
        balance_score=90.0,
        source="BiomechanicsEngine"
    )

    result = pose_engine.evaluate_rules(snapshot)
    assert result.pose_name == "Unknown Pose", f"Upper body only incorrectly classified! Got: {result.pose_name}"
    assert result.confidence == 0.0
    assert not result.is_recognized


def test_full_seated_pose_classifies_correctly(pose_engine):
    """
    Full seated pose with shoulders, hips, and knees visible (6/6 required landmarks present = 100% coverage >= 70%)
    should classify as Seated Neutral correctly.
    """
    full_seated_landmarks = [
        {"name": "left_shoulder", "index": 11, "visibility": 0.95, "presence": 0.95},
        {"name": "right_shoulder", "index": 12, "visibility": 0.95, "presence": 0.95},
        {"name": "left_hip", "index": 23, "visibility": 0.95, "presence": 0.95},
        {"name": "right_hip", "index": 24, "visibility": 0.95, "presence": 0.95},
        {"name": "left_knee", "index": 25, "visibility": 0.95, "presence": 0.95},
        {"name": "right_knee", "index": 26, "visibility": 0.95, "presence": 0.95},
    ]

    snapshot = BiomechanicsSnapshot(
        joint_angles=[
            JointAngle(joint_name="spine", angle=15.0),
            JointAngle(joint_name="left_knee", angle=90.0),
            JointAngle(joint_name="right_knee", angle=90.0),
            JointAngle(joint_name="left_hip", angle=90.0),
            JointAngle(joint_name="right_hip", angle=90.0),
        ],
        landmarks=full_seated_landmarks,
        symmetry_score=98.0,
        balance_score=95.0,
        source="BiomechanicsEngine"
    )

    result = pose_engine.evaluate_rules(snapshot)
    assert result.pose_name == "Seated Neutral"
    assert result.confidence >= 60.0
    assert result.is_recognized


def test_missing_legs_reduces_confidence_for_full_body_poses(pose_engine):
    """
    Full body poses (Cobra, Warrior, Standing Neutral) require 8 landmarks (shoulders, hips, knees, ankles).
    When legs are missing, coverage (4/8 = 50%) is < 70%, rejecting full-body pose classification.
    """
    upper_only_landmarks = [
        {"name": "left_shoulder", "index": 11, "visibility": 0.95, "presence": 0.95},
        {"name": "right_shoulder", "index": 12, "visibility": 0.95, "presence": 0.95},
        {"name": "left_hip", "index": 23, "visibility": 0.95, "presence": 0.95},
        {"name": "right_hip", "index": 24, "visibility": 0.95, "presence": 0.95},
    ]

    snapshot = BiomechanicsSnapshot(
        joint_angles=[
            JointAngle(joint_name="spine", angle=20.0),
            JointAngle(joint_name="left_hip", angle=160.0),
        ],
        landmarks=upper_only_landmarks,
        symmetry_score=90.0,
        balance_score=90.0,
        source="BiomechanicsEngine"
    )

    result = pose_engine.evaluate_rules(snapshot)
    assert result.confidence < 60.0
    assert result.pose_name != "Cobra Pose"
    assert result.pose_name != "Standing Neutral"


def test_low_visibility_prevents_classification(pose_engine):
    """
    Keypoints with visibility < 0.6 are ignored, preventing pose classification.
    """
    low_vis_landmarks = [
        {"name": "left_shoulder", "index": 11, "visibility": 0.3, "presence": 0.9},
        {"name": "right_shoulder", "index": 12, "visibility": 0.3, "presence": 0.9},
        {"name": "left_hip", "index": 23, "visibility": 0.3, "presence": 0.9},
        {"name": "right_hip", "index": 24, "visibility": 0.3, "presence": 0.9},
    ]

    snapshot = BiomechanicsSnapshot(
        joint_angles=[
            JointAngle(joint_name="spine", angle=20.0),
        ],
        landmarks=low_vis_landmarks,
        symmetry_score=50.0,
        balance_score=50.0,
        source="BiomechanicsEngine"
    )

    result = pose_engine.evaluate_rules(snapshot)
    assert result.pose_name == "Unknown Pose"
    assert result.confidence == 0.0
    assert not result.is_recognized
