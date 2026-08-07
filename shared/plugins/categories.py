from abc import ABC
from shared.plugins.base import BasePlugin
from shared.types.enums import PluginMode


class ExercisePlugin(BasePlugin, ABC):
    """Abstract interface for Fitness & Exercise mode plugins."""
    @property
    def mode(self) -> PluginMode:
        return PluginMode.EXERCISE


class YogaPlugin(BasePlugin, ABC):
    """Abstract interface for Yoga Asana mode plugins."""
    @property
    def mode(self) -> PluginMode:
        return PluginMode.YOGA


class ErgonomicsPlugin(BasePlugin, ABC):
    """Abstract interface for Ergonomic Workplace Monitoring plugins."""
    @property
    def mode(self) -> PluginMode:
        return PluginMode.ERGONOMICS


class RehabilitationPlugin(BasePlugin, ABC):
    """Abstract interface for Physical Rehabilitation plugins."""
    @property
    def mode(self) -> PluginMode:
        return PluginMode.REHABILITATION
