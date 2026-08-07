from abc import ABC
from shared.core.base_engine import BaseEngine


class CameraEngineInterface(BaseEngine, ABC):
    """Camera Engine: Manages webcam access and frame acquisition."""
    pass


class MediaPipeEngineInterface(BaseEngine, ABC):
    """MediaPipe Engine: Pose detection and 33 landmark extraction."""
    pass


class LandmarkEngineInterface(BaseEngine, ABC):
    """Landmark Engine: Landmark validation and filtering."""
    pass


class BiomechanicsEngineInterface(BaseEngine, ABC):
    """Biomechanics Engine: Joint angle, symmetry, and balance calculations."""
    pass


class PoseRuleEngineInterface(BaseEngine, ABC):
    """Pose Rule Engine: Static posture recognition."""
    pass


class MovementEngineInterface(BaseEngine, ABC):
    """Movement Engine: Dynamic repetition counting and movement phase tracking."""
    pass


class ScoringEngineInterface(BaseEngine, ABC):
    """Scoring Engine: Form quality and component score evaluation."""
    pass


class FeedbackEngineInterface(BaseEngine, ABC):
    """Feedback Engine: Corrective feedback generation."""
    pass


class AnalyticsEngineInterface(BaseEngine, ABC):
    """Analytics Engine: Real-time analytics aggregation."""
    pass


class PersistenceEngineInterface(BaseEngine, ABC):
    """Persistence Engine: Session saving and local/remote data storage."""
    pass


class NotificationEngineInterface(BaseEngine, ABC):
    """Notification Engine: Ergonomic alerts and milestone notifications."""
    pass


class ReportEngineInterface(BaseEngine, ABC):
    """Report Engine: Export and report generation."""
    pass
