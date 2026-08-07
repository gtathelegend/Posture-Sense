from abc import ABC, abstractmethod
from typing import Dict, Any, List
from shared.types.enums import PluginMode


class BasePlugin(ABC):
    """Abstract base class for all PostureSense plugins."""

    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """Unique identifier for the plugin (e.g. 'plugin_squat')."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human readable plugin name."""
        pass

    @property
    @abstractmethod
    def mode(self) -> PluginMode:
        """Plugin operating mode category."""
        pass

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Plugin metadata summary."""
        pass

    @abstractmethod
    def configuration(self) -> Dict[str, Any]:
        """Plugin threshold and rule configuration."""
        pass

    @abstractmethod
    def recognition_rules(self) -> List[Dict[str, Any]]:
        """Pose or movement recognition rules."""
        pass

    @abstractmethod
    def feedback_rules(self) -> List[Dict[str, Any]]:
        """Corrective feedback rules."""
        pass

    @abstractmethod
    def visualization_hooks(self) -> Dict[str, Any]:
        """Custom UI canvas rendering hooks."""
        pass
