# PostureSense Engine Runtime Specification

**Version:** 2.0.0  
**Status:** Completed (Milestone 4)  

---

## 1. Overview

The `EngineRuntime` system (`shared/core/runtime/`) manages the registration, lifecycle state machine, topological dependency resolution, startup/shutdown ordering, health monitoring, metrics collection, and diagnostics for all 12 PostureSense engines without requiring AI models or pose detection algorithms to be present.

---

## 2. Directory & Component Architecture

```
shared/core/runtime/
├── lifecycle.py            # LifecycleState enum & state transition validator
├── registry.py             # EngineRecord & EngineRegistry
├── dependency.py           # DependencyResolver (topological sort & graph validation)
├── monitor.py              # EngineHealth & EngineMonitor
├── metrics.py              # EngineMetrics (startup time, event count, processing time)
├── diagnostics.py          # EngineDiagnostics (dependency graph & system summary)
├── loader.py               # EngineLoader (automatic engine discovery)
└── runtime.py              # EngineRuntime (main manager orchestrating all engine lifecycles)
```

---

## 3. Lifecycle State Machine

Engines transition through 10 strictly validated lifecycle states:

```
UNREGISTERED ➔ REGISTERED ➔ INITIALIZED ➔ STARTING ➔ RUNNING
                                                         │
                                              ┌──────────┴──────────┐
                                              ▼                     ▼
                                           PAUSED                FAILED
                                              │                     │
                                              ▼                     ▼
                                           STOPPING ➔ STOPPED ➔ DISPOSED
```

- Invalid transitions raise `InvalidStateTransitionError`.

---

## 4. Dependency Resolution

Startup order is computed dynamically using Kahn's topological sorting algorithm (`DependencyResolver.resolve_startup_order`).

Example topology:
```
CameraEngine ➔ MediaPipeEngine ➔ LandmarkEngine ➔ BiomechanicsEngine ➔ PoseRuleEngine ➔ MovementEngine ➔ ScoringEngine ➔ FeedbackEngine ➔ AnalyticsEngine
```

- Engines will not start until all prerequisite dependencies are running.
- Circular dependencies raise `CircularDependencyError`.
- Unregistered missing dependencies raise `MissingDependencyError`.
- Shutdown ordering executes in reverse topological order (`DependencyResolver.resolve_shutdown_order`).

---

## 5. Health Monitoring & Metrics

- `EngineHealth`: Tracks uptime, heartbeat timestamp, last event, error logs, warning logs, and dynamic `health_score` (0.0 to 100.0).
- `EngineMetrics`: Measures initialization time, startup time, event count, error count, and average processing latency per engine.

---

## 6. Runtime Events

Published via `EventBus`:
- `engine.registered`: Dispatched when an engine is registered.
- `engine.initialized`: Dispatched when initialization succeeds.
- `engine.started`: Dispatched when engine starts running.
- `engine.paused` / `engine.resumed`: Dispatched on pause/resume actions.
- `engine.stopped`: Dispatched on graceful shutdown.
- `engine.failed`: Dispatched on runtime exception.
- `engine.disposed`: Dispatched on resource disposal.
