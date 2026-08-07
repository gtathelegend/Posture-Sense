from typing import Dict, List, Optional
from shared.plugins.base import BasePlugin
from shared.types.enums import PluginMode
from shared.constants.errors import ErrorCodes


class PluginRegistry:
    """Central registry for discovering, registering, and retrieving plugins."""

    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}

    def register(self, plugin: BasePlugin) -> None:
        if not isinstance(plugin, BasePlugin):
            raise TypeError(f"[{ErrorCodes.PLUGIN_REGISTRATION_FAILED}] Expected BasePlugin instance.")
        pid = plugin.plugin_id
        if pid in self._plugins:
            print(f"Warning: Overwriting registered plugin '{pid}'.")
        self._plugins[pid] = plugin

    def unregister(self, plugin_id: str) -> bool:
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            return True
        return False

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        return self._plugins.get(plugin_id)

    def get_by_mode(self, mode: PluginMode) -> List[BasePlugin]:
        return [p for p in self._plugins.values() if p.mode == mode]

    def list_plugins(self) -> List[str]:
        return list(self._plugins.keys())
