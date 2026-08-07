from enum import Enum
from typing import Set, Dict


class LifecycleState(str, Enum):
    UNREGISTERED = "unregistered"
    REGISTERED = "registered"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    DISPOSED = "disposed"


# Valid state transitions
VALID_TRANSITIONS: Dict[LifecycleState, Set[LifecycleState]] = {
    LifecycleState.UNREGISTERED: {LifecycleState.REGISTERED},
    LifecycleState.REGISTERED: {LifecycleState.INITIALIZED, LifecycleState.FAILED, LifecycleState.DISPOSED},
    LifecycleState.INITIALIZED: {LifecycleState.STARTING, LifecycleState.FAILED, LifecycleState.DISPOSED},
    LifecycleState.STARTING: {LifecycleState.RUNNING, LifecycleState.FAILED, LifecycleState.STOPPED},
    LifecycleState.RUNNING: {LifecycleState.PAUSED, LifecycleState.STOPPING, LifecycleState.FAILED, LifecycleState.STOPPED},
    LifecycleState.PAUSED: {LifecycleState.RUNNING, LifecycleState.STOPPING, LifecycleState.FAILED, LifecycleState.STOPPED},
    LifecycleState.STOPPING: {LifecycleState.STOPPED, LifecycleState.FAILED},
    LifecycleState.STOPPED: {LifecycleState.INITIALIZED, LifecycleState.STARTING, LifecycleState.DISPOSED, LifecycleState.FAILED},
    LifecycleState.FAILED: {LifecycleState.INITIALIZED, LifecycleState.STARTING, LifecycleState.DISPOSED, LifecycleState.STOPPED},
    LifecycleState.DISPOSED: {LifecycleState.UNREGISTERED, LifecycleState.REGISTERED}
}


class InvalidStateTransitionError(ValueError):
    """Raised when an engine attempts an invalid lifecycle transition."""
    pass


def validate_transition(current_state: LifecycleState, new_state: LifecycleState) -> bool:
    allowed = VALID_TRANSITIONS.get(current_state, set())
    if new_state not in allowed:
        raise InvalidStateTransitionError(
            f"Cannot transition engine lifecycle from {current_state.value} to {new_state.value}. Allowed: {[s.value for s in allowed]}"
        )
    return True
