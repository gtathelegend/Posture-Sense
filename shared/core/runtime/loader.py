from typing import List, Type
from shared.core.base_engine import BaseEngine


class EngineLoader:
    """Discovers and instantiates engines adhering to BaseEngine interface."""

    def __init__(self):
        self.discovered_engines: List[Type[BaseEngine]] = []

    def discover_engines(self) -> List[Type[BaseEngine]]:
        """Returns list of registered engine classes available for instantiation."""
        return self.discovered_engines

    def register_engine_class(self, engine_cls: Type[BaseEngine]) -> None:
        if issubclass(engine_cls, BaseEngine) and engine_cls not in self.discovered_engines:
            self.discovered_engines.append(engine_cls)
