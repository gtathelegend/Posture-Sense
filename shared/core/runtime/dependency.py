from typing import Dict, List, Set, Any


class CircularDependencyError(ValueError):
    """Raised when a circular dependency is detected between engines."""
    pass


class MissingDependencyError(ValueError):
    """Raised when a required engine dependency is not registered."""
    pass


class DependencyResolver:
    """Resolves engine dependency ordering using Kahn's topological sorting algorithm."""

    @staticmethod
    def resolve_startup_order(engine_dependencies: Dict[str, List[str]]) -> List[str]:
        """
        Calculates startup order where dependencies precede dependent engines.
        `engine_dependencies`: Dict mapping engine_id -> list of dependency engine_ids.
        """
        all_engines = set(engine_dependencies.keys())
        in_degree: Dict[str, int] = {e: 0 for e in all_engines}
        graph: Dict[str, List[str]] = {e: [] for e in all_engines}

        for engine, deps in engine_dependencies.items():
            for dep in deps:
                if dep not in all_engines:
                    raise MissingDependencyError(f"Engine '{engine}' depends on unregistered engine '{dep}'.")
                graph[dep].append(engine)
                in_degree[engine] += 1

        queue = [e for e in all_engines if in_degree[e] == 0]
        # Sort queue for deterministic execution order
        queue.sort()
        startup_order: List[str] = []

        while queue:
            node = queue.pop(0)
            startup_order.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    queue.sort()

        if len(startup_order) != len(all_engines):
            unresolved = all_engines - set(startup_order)
            raise CircularDependencyError(f"Circular dependency detected involving engines: {unresolved}")

        return startup_order

    @staticmethod
    def resolve_shutdown_order(engine_dependencies: Dict[str, List[str]]) -> List[str]:
        """Calculates shutdown order (reverse of startup order)."""
        startup_order = DependencyResolver.resolve_startup_order(engine_dependencies)
        return list(reversed(startup_order))
