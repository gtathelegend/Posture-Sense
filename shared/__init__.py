"""
PostureSense v2 Shared Core Infrastructure Package
Provides contracts, event bus, config loading, plugin interfaces, constants, and utilities.
"""

from shared.constants import EventNames, PoseNames, ExerciseNames, ScoreCategories, ErrorCodes
from shared.contracts import (
    BaseContract, Frame, Landmark, LandmarkSet, JointAngle, BiomechanicsSnapshot,
    PoseResult, ExerciseResult, ScoreReport, FeedbackMessage, AnalyticsSnapshot,
    SessionSummary, UserProfile
)
from shared.events import Event, EventBus
from shared.config import ConfigLoader
from shared.plugins import BasePlugin, PluginRegistry
from shared.core import BaseEngine
from shared.utils import ContractValidator, calculate_angle_3p, format_duration

__version__ = "2.0.0"
