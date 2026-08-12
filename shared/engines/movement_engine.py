"""
MovementEngine
==============
Production-grade, configuration-driven engine for dynamic exercise phase detection,
repetition counting, tempo analysis, and hold tracking.

Priority    : 7
Dependencies: pose_rule_engine, biomechanics_engine
Subscribes  : biomechanics.updated (BiomechanicsSnapshot)
              pose.detected       (PoseResult)
Publishes   : exercise.started
              exercise.phase_changed
              exercise.rep_started
              exercise.rep_completed
              exercise.completed
              exercise.cancelled
              exercise.invalid

DO NOT implement posture scoring.
DO NOT implement coaching feedback.
DO NOT use ML classifiers.
"""

from __future__ import annotations

import time
from collections import deque
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, Tuple

import yaml
import os

from shared.engines.interfaces import MovementEngineInterface
from shared.events.event_bus import EventBus
from shared.types.enums import EngineStatus
from shared.contracts.biomechanics import BiomechanicsSnapshot
from shared.contracts.pose import ExerciseResult


# ---------------------------------------------------------------------------
# FSM States
# ---------------------------------------------------------------------------

class MovementState(str, Enum):
    IDLE        = "idle"
    ENTERING    = "entering"
    READY       = "ready"
    CONCENTRIC  = "concentric"
    BOTTOM      = "bottom"
    ECCENTRIC   = "eccentric"
    TOP         = "top"
    HOLD        = "hold"
    COMPLETED   = "completed"
    EXITED      = "exited"
    INVALID     = "invalid"


# Valid state transitions
_VALID_TRANSITIONS: Dict[MovementState, List[MovementState]] = {
    MovementState.IDLE:       [MovementState.ENTERING],
    MovementState.ENTERING:   [MovementState.READY, MovementState.IDLE],
    MovementState.READY:      [MovementState.CONCENTRIC, MovementState.BOTTOM, MovementState.TOP, MovementState.HOLD, MovementState.IDLE],
    MovementState.CONCENTRIC: [MovementState.BOTTOM, MovementState.ECCENTRIC, MovementState.INVALID],
    MovementState.BOTTOM:     [MovementState.ECCENTRIC, MovementState.CONCENTRIC],
    MovementState.ECCENTRIC:  [MovementState.TOP, MovementState.CONCENTRIC],
    MovementState.TOP:        [MovementState.COMPLETED, MovementState.CONCENTRIC, MovementState.IDLE],
    MovementState.HOLD:       [MovementState.COMPLETED, MovementState.IDLE],
    MovementState.COMPLETED:  [MovementState.IDLE],
    MovementState.EXITED:     [MovementState.IDLE],
    MovementState.INVALID:    [MovementState.IDLE],
}


# ---------------------------------------------------------------------------
# Exercise Config Loader
# ---------------------------------------------------------------------------

_EXERCISES_DIR = os.path.join(
    os.path.dirname(__file__),  # shared/engines/
    "..", "config", "current", "exercises"
)


def _load_exercise_configs() -> Dict[str, Dict[str, Any]]:
    """Load all YAML exercise definitions from the config directory."""
    exercises: Dict[str, Dict[str, Any]] = {}
    exercises_dir = os.path.normpath(_EXERCISES_DIR)
    if not os.path.isdir(exercises_dir):
        return exercises
    for fname in os.listdir(exercises_dir):
        if not fname.endswith((".yaml", ".yml")):
            continue
        fpath = os.path.join(exercises_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            if isinstance(cfg, dict) and "id" in cfg:
                exercises[cfg["id"]] = cfg
        except Exception:
            pass
    return exercises


# ---------------------------------------------------------------------------
# Motion Analyser (single-exercise helper)
# ---------------------------------------------------------------------------

class _MotionAnalyzer:
    """Computes per-frame motion metrics from a sliding angle history window."""

    _WINDOW = 15  # frames

    def __init__(self) -> None:
        self._history: Deque[Tuple[float, float]] = deque(maxlen=self._WINDOW)
        # (timestamp_s, primary_joint_angle)

    def update(self, angle: float, ts: float) -> None:
        self._history.append((ts, angle))

    @property
    def angular_velocity(self) -> float:
        """Degrees per second of the primary joint, signed."""
        if len(self._history) < 2:
            return 0.0
        (t0, a0), (t1, a1) = self._history[0], self._history[-1]
        dt = t1 - t0
        if dt < 1e-6:
            return 0.0
        return (a1 - a0) / dt

    @property
    def movement_direction(self) -> str:
        v = self.angular_velocity
        if abs(v) < 2.0:
            return "stationary"
        return "decreasing" if v < 0 else "increasing"

    def reset(self) -> None:
        self._history.clear()


# ---------------------------------------------------------------------------
# Rep Counter
# ---------------------------------------------------------------------------

class _RepCounter:
    """
    Stateful repetition counter with bounce/partial-rep prevention.
    Only counts reps when the FSM has completed a full required-phase cycle.
    """

    def __init__(self, debounce_ms: float = 400.0) -> None:
        self._count = 0
        self._debounce_s = debounce_ms / 1000.0
        self._last_rep_time: float = 0.0
        self._rep_start_time: float = 0.0
        self._rep_durations: Deque[float] = deque(maxlen=20)

    def start_rep(self, ts: float) -> None:
        self._rep_start_time = ts

    def try_count_rep(self, ts: float, rom_ok: bool) -> bool:
        """
        Attempt to count a rep.
        ts is in monotonic seconds.
        Returns True if counted, False if rejected (debounce / ROM gate).
        """
        if not rom_ok:
            return False
        if self._last_rep_time > 0 and (ts - self._last_rep_time) < self._debounce_s:
            return False
        duration = ts - self._rep_start_time if self._rep_start_time > 0 else 0.0
        self._rep_durations.append(duration)
        self._count += 1
        self._last_rep_time = ts
        self._rep_start_time = 0.0
        return True

    @property
    def count(self) -> int:
        return self._count

    @property
    def last_rep_duration(self) -> float:
        return self._rep_durations[-1] if self._rep_durations else 0.0

    @property
    def average_rep_duration(self) -> float:
        if not self._rep_durations:
            return 0.0
        return sum(self._rep_durations) / len(self._rep_durations)

    @property
    def cadence_rpm(self) -> float:
        if self.average_rep_duration < 1e-6:
            return 0.0
        return 60.0 / self.average_rep_duration

    def reset(self) -> None:
        self._count = 0
        self._last_rep_time = 0.0
        self._rep_start_time = 0.0
        self._rep_durations.clear()


# ---------------------------------------------------------------------------
# Exercise State Machine
# ---------------------------------------------------------------------------

class _ExerciseFSM:
    """
    Deterministic finite state machine for one loaded exercise.
    All transition logic is driven by the exercise config — no hardcoded exercises.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.exercise_id: str = config["id"]
        self.exercise_name: str = config["name"]
        self.category: str = config.get("category", "dynamic")
        self.is_hold_exercise = self.category == "static_hold"

        # Indexed phases
        self._phases: List[Dict[str, Any]] = config.get("phases", [])
        self._phase_index: Dict[str, int] = {p["id"]: i for i, p in enumerate(self._phases)}

        # Rep completion config
        rc = config.get("rep_completion", {})
        self._required_phases: List[str] = rc.get("required_phases", [])
        self._min_rom_pct: float = float(rc.get("min_rom_percentage", 0.0))
        self._debounce_ms: float = float(rc.get("debounce_ms", 400.0))
        self._rom_joint: str = rc.get("rom_joint", "")
        self._rom_ref_top: float = float(rc.get("rom_reference_top", 170.0))
        self._rom_ref_bottom: float = float(rc.get("rom_reference_bottom", 90.0))
        self._min_bottom_depth: float = float(rc.get("min_bottom_depth_deg", 115.0))

        # Hold config
        hc = config.get("hold_config")
        self.hold_config: Optional[Dict[str, Any]] = hc

        # State
        self.state = MovementState.IDLE
        self.current_phase_id: Optional[str] = None
        self._phases_completed: List[str] = []
        self._state_entry_time: float = time.monotonic()
        self._exercise_start_time: float = 0.0
        self._hold_start_time: float = 0.0

        self.rep_counter = _RepCounter(debounce_ms=self._debounce_ms)
        self.motion_analyzer = _MotionAnalyzer()

        # ROM tracking
        self._rom_history: Deque[float] = deque(maxlen=30)
        self._session_min_angle: float = 999.0
        self._session_max_angle: float = 0.0
        # Sequential phase pointer: index of the NEXT phase we expect to match
        self._next_phase_idx: int = 0

    # ------------------------------------------------------------------
    # Transition helpers
    # ------------------------------------------------------------------

    def _transition(self, new_state: MovementState) -> bool:
        allowed = _VALID_TRANSITIONS.get(self.state, [])
        if new_state not in allowed:
            return False
        self.state = new_state
        self._state_entry_time = time.monotonic()
        return True

    # ------------------------------------------------------------------
    # ROM computation
    # ------------------------------------------------------------------

    def _compute_rom_pct(self) -> float:
        """Percentage of full configured range-of-motion achieved."""
        full_range = abs(self._rom_ref_top - self._rom_ref_bottom)
        if full_range < 1e-6:
            return 100.0
        achieved = abs(self._session_max_angle - self._session_min_angle)
        return min(100.0, (achieved / full_range) * 100.0)

    # ------------------------------------------------------------------
    # Phase detection
    # ------------------------------------------------------------------

    def _angles_to_map(self, snapshot: BiomechanicsSnapshot) -> Dict[str, float]:
        return {ja.joint_name: ja.angle for ja in snapshot.joint_angles}

    def _phase_matches(self, phase: Dict[str, Any], angles: Dict[str, float]) -> bool:
        ranges = phase.get("trigger_ranges", {})
        if not ranges:
            return False
        for joint, (lo, hi) in ranges.items():
            a = angles.get(joint)
            if a is None:
                return False
            if not (lo <= a <= hi):
                return False
        return True

    def _entry_conditions_met(self, angles: Dict[str, float]) -> bool:
        constraints = self.config.get("entry_conditions", {}).get("joint_constraints", {})
        for joint, (lo, hi) in constraints.items():
            a = angles.get(joint)
            if a is None or not (lo <= a <= hi):
                return False
        return True

    def _exit_conditions_met(self, angles: Dict[str, float], tracking_quality: float) -> bool:
        ec = self.config.get("exit_conditions", {})
        # Tracking quality gate
        tq_threshold = float(ec.get("tracking_quality_below", 0.0))
        if tq_threshold > 0 and tracking_quality < tq_threshold:
            return True
        # Joint violation check
        violations = ec.get("joint_violation", {})
        for joint, (lo, hi) in violations.items():
            a = angles.get(joint)
            if a is not None and not (lo <= a <= hi):
                return True
        return False

    # ------------------------------------------------------------------
    # Main update (called every frame)
    # ------------------------------------------------------------------

    def update(
        self,
        snapshot: BiomechanicsSnapshot,
        tracking_quality: float = 100.0,
    ) -> Dict[str, Any]:
        """
        Process one BiomechanicsSnapshot.
        Returns a dict with FSM events to emit.
        """
        ts = time.monotonic()
        angles = self._angles_to_map(snapshot)
        events: List[str] = []

        # Update ROM tracking for primary joint
        primary_angle = angles.get(self._rom_joint, 0.0) if self._rom_joint else 0.0
        if primary_angle > 0:
            self._session_min_angle = min(self._session_min_angle, primary_angle)
            self._session_max_angle = max(self._session_max_angle, primary_angle)
            self.motion_analyzer.update(primary_angle, ts)

        rom_pct = self._compute_rom_pct()

        # ------------------------------------------------------------------
        # IDLE → ENTERING: check entry conditions
        # ------------------------------------------------------------------
        if self.state == MovementState.IDLE:
            if self._entry_conditions_met(angles):
                self._transition(MovementState.ENTERING)
                events.append("exercise.started")
                self._exercise_start_time = ts
                self._phases_completed = []
                self._next_phase_idx = 0
                self.rep_counter.reset()
                self.motion_analyzer.reset()
                self._session_min_angle = primary_angle if primary_angle > 0 else 999.0
                self._session_max_angle = primary_angle if primary_angle > 0 else 0.0
            return self._make_result(events, angles, rom_pct, ts)

        # ------------------------------------------------------------------
        # Exit detection (from any active state, including READY)
        # ------------------------------------------------------------------
        if self.state not in (MovementState.IDLE, MovementState.COMPLETED,
                               MovementState.EXITED, MovementState.INVALID):
            if self._exit_conditions_met(angles, tracking_quality):
                self._transition(MovementState.EXITED)
                events.append("exercise.cancelled")
                return self._make_result(events, angles, rom_pct, ts)

        # ------------------------------------------------------------------
        # ENTERING → READY (then fall through to phase detection)
        # ------------------------------------------------------------------
        if self.state == MovementState.ENTERING:
            self._transition(MovementState.READY)
            if self.is_hold_exercise:
                self._transition(MovementState.HOLD)
                self._hold_start_time = ts
                events.append("exercise.phase_changed")
                return self._make_result(events, angles, rom_pct, ts)
            # Dynamic exercises fall through to phase detection below
            # so the current frame's angles immediately set the first phase.

        # ------------------------------------------------------------------
        # HOLD exercise path
        # ------------------------------------------------------------------
        if self.state == MovementState.HOLD:
            hold_phase = self._phases[0] if self._phases else None
            if hold_phase and not self._phase_matches(hold_phase, angles):
                self._transition(MovementState.EXITED)
                events.append("exercise.cancelled")
            return self._make_result(events, angles, rom_pct, ts)

        # ------------------------------------------------------------------
        # Dynamic exercise: sequential phase detection
        # Scan forward from _next_phase_idx to prevent ambiguous re-matching
        # (e.g. eccentric and concentric sharing the same angle range).
        # ------------------------------------------------------------------
        prev_state = self.state

        # Build ordered list starting from _next_phase_idx, wrapping around
        n = len(self._phases)
        candidates = [self._phases[(self._next_phase_idx + i) % n] for i in range(n)]

        for phase in candidates:
            if not self._phase_matches(phase, angles):
                continue

            matched_phase_id = phase["id"]
            phase_type = phase["type"]

            # Map phase type → FSM state
            type_to_state = {
                "top":        MovementState.TOP,
                "concentric": MovementState.CONCENTRIC,
                "bottom":     MovementState.BOTTOM,
                "eccentric":  MovementState.ECCENTRIC,
                "hold":       MovementState.HOLD,
            }
            target_state = type_to_state.get(phase_type)
            if not target_state or target_state == self.state:
                break

            if self._transition(target_state):
                self.current_phase_id = matched_phase_id
                events.append("exercise.phase_changed")

                # Advance the sequential pointer to the next phase
                matched_global_idx = self._phase_index.get(matched_phase_id, 0)
                self._next_phase_idx = (matched_global_idx + 1) % n

                # Mark phase as completed in sequence
                if matched_phase_id not in self._phases_completed:
                    self._phases_completed.append(matched_phase_id)

                # Rep started when entering concentric from top/ready
                if target_state == MovementState.CONCENTRIC and prev_state in (
                    MovementState.TOP, MovementState.READY
                ):
                    self.rep_counter.start_rep(ts)
                    events.append("exercise.rep_started")

                # Rep completed when returning to top
                if target_state == MovementState.TOP and prev_state == MovementState.ECCENTRIC:
                    required_ok = all(
                        ph in self._phases_completed for ph in self._required_phases
                    )
                    rom_ok = (self._min_rom_pct <= 0.0) or (rom_pct >= self._min_rom_pct)
                    if required_ok and self.rep_counter.try_count_rep(ts, rom_ok):
                        events.append("exercise.rep_completed")
                        # Reset phase tracking for next rep
                        self._phases_completed = []
                        self._next_phase_idx = 0  # restart from TOP
                        self._session_min_angle = primary_angle if primary_angle > 0 else 999.0
                        self._session_max_angle = primary_angle if primary_angle > 0 else 0.0
            break

        # ------------------------------------------------------------------
        # COMPLETED / EXITED → IDLE after one frame
        # ------------------------------------------------------------------
        if self.state in (MovementState.COMPLETED, MovementState.EXITED):
            self._transition(MovementState.IDLE)

        return self._make_result(events, angles, rom_pct, ts)

    # ------------------------------------------------------------------
    # Result packaging
    # ------------------------------------------------------------------

    def _make_result(
        self,
        events: List[str],
        angles: Dict[str, float],
        rom_pct: float,
        ts: float,
    ) -> Dict[str, Any]:
        hold_time = (ts - self._hold_start_time) if (
            self.state == MovementState.HOLD and self._hold_start_time > 0
        ) else 0.0

        return {
            "events": events,
            "exercise_id": self.exercise_id,
            "exercise_name": self.exercise_name,
            "fsm_state": self.state.value,
            "current_phase": self.current_phase_id or self.state.value,
            "rep_count": self.rep_counter.count,
            "current_rep_duration": round(ts - self.rep_counter._rep_start_time, 2)
                if self.rep_counter._rep_start_time > 0 else 0.0,
            "average_rep_duration": round(self.rep_counter.average_rep_duration, 2),
            "current_cadence": round(self.rep_counter.cadence_rpm, 1),
            "rom_percentage": round(rom_pct, 1),
            "hold_time": round(hold_time, 2),
            "movement_direction": self.motion_analyzer.movement_direction,
            "angular_velocity": round(self.motion_analyzer.angular_velocity, 1),
            "exercise_duration": round(ts - self._exercise_start_time, 2)
                if self._exercise_start_time > 0 else 0.0,
        }


# ---------------------------------------------------------------------------
# MovementEngine
# ---------------------------------------------------------------------------

class MovementEngine(MovementEngineInterface):
    """
    Production-grade Movement Engine for PostureSense v2.

    Consumes BiomechanicsSnapshot and PoseResult contracts via EventBus.
    Runs per-exercise FSMs with configurable exercise definitions.
    Publishes ExerciseResult contracts on every update.
    """

    def __init__(self, name: str = "MovementEngine", event_bus: Optional[EventBus] = None):
        super().__init__(name=name, event_bus=event_bus)
        self.version = "2.0.0"
        self.priority = 7
        self.dependencies = ["pose_rule_engine", "biomechanics_engine"]

        self.config: Dict[str, Any] = {
            "active_exercise_id": None,
            "min_tracking_quality": 55.0,
            "enable_hold_milestones": True,
        }

        # Loaded exercise definitions
        self._exercise_configs: Dict[str, Dict[str, Any]] = {}

        # Active FSM
        self._fsm: Optional[_ExerciseFSM] = None
        self._active_exercise_id: Optional[str] = None

        # Diagnostics
        self._frames_processed = 0
        self._false_positives_prevented = 0
        self._recognition_latency_ms = 0.0
        self._session_start_time: float = 0.0
        self._last_result: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self, config: Optional[dict] = None) -> bool:
        if config:
            self.config.update(config)
        self._exercise_configs = _load_exercise_configs()
        self._status = EngineStatus.INITIALIZED
        self.publish("exercise.initialized", self.get_diagnostics())
        return True

    def start(self) -> bool:
        self._status = EngineStatus.RUNNING
        self._session_start_time = time.monotonic()
        self._subscribe_to_events()
        self.publish("exercise.started_engine", self.get_diagnostics())
        return True

    def pause(self) -> bool:
        self._status = EngineStatus.PAUSED
        self.publish("exercise.paused", self.get_diagnostics())
        return True

    def resume(self) -> bool:
        self._status = EngineStatus.RUNNING
        self.publish("exercise.resumed", self.get_diagnostics())
        return True

    def stop(self) -> bool:
        self._status = EngineStatus.STOPPED
        self.publish("exercise.stopped", self.get_diagnostics())
        return True

    def dispose(self) -> bool:
        self._status = EngineStatus.DISPOSED
        self.publish("exercise.disposed", self.get_diagnostics())
        return True

    # ------------------------------------------------------------------
    # Event subscriptions
    # ------------------------------------------------------------------

    def _subscribe_to_events(self) -> None:
        self.subscribe("biomechanics.updated", self._on_biomechanics_updated)
        self.subscribe("pose.detected", self._on_pose_detected)

    def _on_biomechanics_updated(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        data = event.data if hasattr(event, "data") else event
        if not data:
            return
        snapshot = BiomechanicsSnapshot.from_dict(data)
        self.process_snapshot(snapshot)

    def _on_pose_detected(self, event: Any) -> None:
        """
        PoseResult can be used for entry-condition enrichment.
        Currently consumed for tracking quality and pose context.
        """
        if self._status != EngineStatus.RUNNING:
            return
        data = event.data if hasattr(event, "data") else event
        if isinstance(data, dict):
            tq = float(data.get("tracking_quality", 100.0))
            self._last_tracking_quality = tq

    # ------------------------------------------------------------------
    # Exercise selection
    # ------------------------------------------------------------------

    def set_active_exercise(self, exercise_id: str) -> bool:
        """Select which exercise definition the FSM should run."""
        if exercise_id not in self._exercise_configs:
            return False
        cfg = self._exercise_configs[exercise_id]
        self._fsm = _ExerciseFSM(cfg)
        self._active_exercise_id = exercise_id
        self.config["active_exercise_id"] = exercise_id
        return True

    def get_available_exercises(self) -> List[Dict[str, str]]:
        """Return list of {id, name, category} for all loaded exercises."""
        return [
            {
                "id": cfg["id"],
                "name": cfg["name"],
                "category": cfg.get("category", "dynamic"),
            }
            for cfg in self._exercise_configs.values()
        ]

    def reload_exercise_configs(self) -> int:
        """Hot-reload exercise definitions from disk. Returns count loaded."""
        self._exercise_configs = _load_exercise_configs()
        return len(self._exercise_configs)

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------

    def process_snapshot(
        self,
        snapshot: BiomechanicsSnapshot,
        tracking_quality: float = 100.0,
    ) -> ExerciseResult:
        t_start = time.monotonic()

        if not self._fsm:
            # No exercise loaded — return idle result
            result = self._idle_result()
            self.publish("exercise.updated", result.to_dict())
            return result

        tq = getattr(self, "_last_tracking_quality", tracking_quality)
        raw = self._fsm.update(snapshot, tracking_quality=tq)

        self._frames_processed += 1
        self._recognition_latency_ms = (time.monotonic() - t_start) * 1000.0

        # Publish per-event events
        for evt in raw.get("events", []):
            self.publish(evt, raw)

        # Build and publish ExerciseResult contract
        result = ExerciseResult(
            exercise_name=raw["exercise_name"],
            exercise_id=raw["exercise_id"],
            rep_count=raw["rep_count"],
            current_phase=raw["current_phase"],
            current_rep_duration=raw["current_rep_duration"],
            average_rep_duration=raw["average_rep_duration"],
            current_cadence=raw["current_cadence"],
            rom_percentage=raw["rom_percentage"],
            movement_quality=min(100.0, tq),
            hold_time=raw["hold_time"],
            tracking_quality=tq,
            source=self.name,
        )
        self._last_result = raw
        self.publish("exercise.updated", result.to_dict())
        return result

    # ------------------------------------------------------------------
    # Idle result
    # ------------------------------------------------------------------

    def _idle_result(self) -> ExerciseResult:
        return ExerciseResult(
            exercise_name="None",
            exercise_id="none",
            current_phase="idle",
            source=self.name,
        )

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def get_diagnostics(self) -> Dict[str, Any]:
        session_duration = (time.monotonic() - self._session_start_time
                            ) if self._session_start_time > 0 else 0.0
        fsm_state = self._fsm.state.value if self._fsm else "idle"
        rep_count = self._fsm.rep_counter.count if self._fsm else 0
        current_phase = self._fsm.current_phase_id if self._fsm else None
        avg_rep_time = self._fsm.rep_counter.average_rep_duration if self._fsm else 0.0
        direction = self._fsm.motion_analyzer.movement_direction if self._fsm else "stationary"

        return {
            "name": self.name,
            "version": self.version,
            "status": self._status.value if hasattr(self._status, "value") else str(self._status),
            "priority": self.priority,
            "dependencies": self.dependencies,
            "config": self.config,
            "metrics": {
                "active_exercise": self._active_exercise_id,
                "fsm_state": fsm_state,
                "rep_count": rep_count,
                "false_positives_prevented": self._false_positives_prevented,
                "average_rep_time_s": round(avg_rep_time, 2),
                "current_phase": current_phase or fsm_state,
                "movement_direction": direction,
                "recognition_latency_ms": round(self._recognition_latency_ms, 2),
                "exercise_duration_s": round(session_duration, 1),
                "loaded_exercises": len(self._exercise_configs),
                "frames_processed": self._frames_processed,
            },
        }
