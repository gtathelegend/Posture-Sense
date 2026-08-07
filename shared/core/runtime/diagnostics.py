from typing import Dict, Any, List
from shared.core.runtime.registry import EngineRegistry
from shared.core.runtime.lifecycle import LifecycleState


class EngineDiagnostics:
    """Generates runtime system summary diagnostics."""

    @staticmethod
    def generate_report(registry: EngineRegistry, runtime_version: str = "2.0.0", startup_time_ms: float = 0.0) -> Dict[str, Any]:
        records = registry.getAll()
        total_engines = len(records)
        
        status_counts: Dict[str, int] = {}
        for rec in records:
            st = rec.status.value if isinstance(rec.status, LifecycleState) else str(rec.status)
            status_counts[st] = status_counts.get(st, 0) + 1

        running_count = status_counts.get(LifecycleState.RUNNING.value, 0)
        stopped_count = status_counts.get(LifecycleState.STOPPED.value, 0)
        failed_count = status_counts.get(LifecycleState.FAILED.value, 0)

        dep_graph = registry.get_dependencies_map()

        return {
            "runtime_version": runtime_version,
            "engine_count": total_engines,
            "running_count": running_count,
            "stopped_count": stopped_count,
            "failed_count": failed_count,
            "startup_time_ms": round(startup_time_ms, 2),
            "status_breakdown": status_counts,
            "dependency_graph": dep_graph,
            "engines": [rec.to_dict() for rec in records]
        }
