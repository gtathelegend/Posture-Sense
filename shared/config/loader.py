import json
import os
from typing import Any, Dict, Optional
from shared.constants.errors import ErrorCodes


class ConfigLoader:
    """Version-aware configuration loader for YAML and JSON configuration files."""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_dir = base_dir
        else:
            self.base_dir = os.path.dirname(__file__)

    def _resolve_path(self, relative_path: str, version: str = "current") -> str:
        # e.g., relative_path="poses/yoga_poses.json", version="current"
        return os.path.abspath(os.path.join(self.base_dir, version, relative_path))

    def load_json(self, relative_path: str, version: str = "current") -> Dict[str, Any]:
        path = self._resolve_path(relative_path, version)
        if not os.path.exists(path):
            raise FileNotFoundError(f"[{ErrorCodes.CONFIG_NOT_FOUND}] Config file not found: {path}")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"[{ErrorCodes.CONFIG_LOAD_FAILED}] Error parsing JSON config at {path}: {e}")

    def load_yaml(self, relative_path: str, version: str = "current") -> Dict[str, Any]:
        path = self._resolve_path(relative_path, version)
        if not os.path.exists(path):
            raise FileNotFoundError(f"[{ErrorCodes.CONFIG_NOT_FOUND}] Config file not found: {path}")
        try:
            import yaml
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            # Fallback to json parsing if yaml package is not installed and file is valid json
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"[{ErrorCodes.CONFIG_LOAD_FAILED}] Error parsing YAML config at {path}: {e}")

    def load(self, relative_path: str, version: str = "current") -> Dict[str, Any]:
        if relative_path.endswith('.yaml') or relative_path.endswith('.yml'):
            return self.load_yaml(relative_path, version)
        return self.load_json(relative_path, version)
