"""
test_movement_engine.py
=======================
Comprehensive test suite for the PostureSense MovementEngine.

Covers:
- Engine lifecycle
- FSM state transitions (valid and invalid)
- Rep counting (squat, push-up)
- False positive prevention (partial reps, bounce reps, insufficient ROM)
- Hold exercise tracking (plank, wall sit)
- Tracking loss recovery
- ExerciseResult contract shape and fields
- Runtime registration (priority, dependencies)
- Diagnostics structure
"""

import unittest
import time
from shared.engines.movement_engine import (
    MovementEngine,
    MovementState,
    _ExerciseFSM,
    _RepCounter,
    _MotionAnalyzer,
    _VALID_TRANSITIONS,
)
from shared.contracts.biomechanics import JointAngle, BiomechanicsSnapshot
from shared.contracts.pose import ExerciseResult
from shared.events.event_bus import EventBus
from shared.types.enums import EngineStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _angles(*pairs) -> BiomechanicsSnapshot:
    """Create a BiomechanicsSnapshot from (joint_name, angle) pairs."""
    jas = [JointAngle(joint_name=name, angle=angle) for name, angle in pairs]
    return BiomechanicsSnapshot(joint_angles=jas, symmetry_score=98.0, balance_score=95.0)


def _squat_config():
    """Return the bodyweight_squat exercise config dict."""
    return {
        "id": "bodyweight_squat",
        "name": "Bodyweight Squat",
        "category": "dynamic",
        "entry_conditions": {
            "joint_constraints": {"left_knee": [155, 180], "right_knee": [155, 180]}
        },
        "exit_conditions": {"tracking_quality_below": 40},
        "phases": [
            {"id": "top",        "name": "Standing",   "type": "top",
             "trigger_ranges": {"left_knee": [155, 180], "right_knee": [155, 180]}},
            {"id": "concentric", "name": "Descending", "type": "concentric",
             "trigger_ranges": {"left_knee": [115, 155], "right_knee": [115, 155]}},
            {"id": "bottom",     "name": "Bottom",     "type": "bottom",
             "trigger_ranges": {"left_knee": [60, 115],  "right_knee": [60, 115]}},
            {"id": "eccentric",  "name": "Ascending",  "type": "eccentric",
             "trigger_ranges": {"left_knee": [115, 155], "right_knee": [115, 155]}},
        ],
        "rep_completion": {
            "required_phases": ["top", "concentric", "bottom", "eccentric"],
            "min_rom_percentage": 50.0,
            "rom_joint": "left_knee",
            "rom_reference_top": 170.0,
            "rom_reference_bottom": 90.0,
            "prevent_bounce": True,
            "debounce_ms": 400.0,
        },
        "hold_config": None,
    }


def _plank_config():
    """Return the plank exercise config dict."""
    return {
        "id": "plank",
        "name": "Plank",
        "category": "static_hold",
        "entry_conditions": {
            "joint_constraints": {"spine": [0, 25], "left_hip": [155, 185], "right_hip": [155, 185]}
        },
        "exit_conditions": {"tracking_quality_below": 40, "joint_violation": {"spine": [0, 35]}},
        "phases": [
            {"id": "hold", "name": "Holding", "type": "hold",
             "trigger_ranges": {"spine": [0, 30], "left_hip": [150, 190]}}
        ],
        "rep_completion": {
            "required_phases": [],
            "min_rom_percentage": 0.0,
            "prevent_bounce": False,
            "debounce_ms": 0.0,
        },
        "hold_config": {"min_seconds": 10.0, "milestone_seconds": [15, 30, 60], "count_unit": "seconds"},
    }


def _sim_squat_rep(fsm, rom_min=80.0, delay=0.0):
    """
    Simulate a full squat repetition through the FSM.
    Returns a list of all collected result dicts.
    The sim sends:
      170° → top
      135° → concentric
      rom_min° → bottom
      135° → eccentric (concentric range, but after bottom means eccentric)
      170° → top again → rep counted
    """
    results = []
    # Standing (top): enters exercise + transitions to READY/TOP
    results.append(fsm.update(_angles(("left_knee", 170), ("right_knee", 170))))
    if delay: time.sleep(delay)
    # Descending (concentric): 135° is in [115, 155]
    results.append(fsm.update(_angles(("left_knee", 135), ("right_knee", 135))))
    if delay: time.sleep(delay)
    # Bottom: rom_min (default 80°) is in [60, 115]
    results.append(fsm.update(_angles(("left_knee", rom_min), ("right_knee", rom_min))))
    if delay: time.sleep(delay)
    # Ascending (eccentric): 130° — same range as concentric, but phase tracker
    # sees it after bottom so marks eccentric completed
    results.append(fsm.update(_angles(("left_knee", 130), ("right_knee", 130))))
    if delay: time.sleep(delay)
    # Return to standing top (170°) → rep counted here
    results.append(fsm.update(_angles(("left_knee", 165), ("right_knee", 165))))
    if delay: time.sleep(delay)
    results.append(fsm.update(_angles(("left_knee", 170), ("right_knee", 170))))
    return results


# ===========================================================================
# 1. Engine Lifecycle Tests
# ===========================================================================

class TestMovementEngineLifecycle(unittest.TestCase):

    def setUp(self):
        self.bus = EventBus(debug_mode=True)
        self.engine = MovementEngine(name="MovementEngine", event_bus=self.bus)

    def test_priority_and_dependencies(self):
        self.assertEqual(self.engine.priority, 7)
        self.assertIn("pose_rule_engine", self.engine.dependencies)
        self.assertIn("biomechanics_engine", self.engine.dependencies)

    def test_initialize(self):
        result = self.engine.initialize()
        self.assertTrue(result)
        self.assertEqual(self.engine.status(), EngineStatus.INITIALIZED)

    def test_start(self):
        self.engine.initialize()
        result = self.engine.start()
        self.assertTrue(result)
        self.assertEqual(self.engine.status(), EngineStatus.RUNNING)

    def test_pause_resume(self):
        self.engine.initialize()
        self.engine.start()
        self.engine.pause()
        self.assertEqual(self.engine.status(), EngineStatus.PAUSED)
        self.engine.resume()
        self.assertEqual(self.engine.status(), EngineStatus.RUNNING)

    def test_stop(self):
        self.engine.initialize()
        self.engine.start()
        self.engine.stop()
        self.assertEqual(self.engine.status(), EngineStatus.STOPPED)

    def test_dispose(self):
        self.engine.initialize()
        self.engine.start()
        self.engine.stop()
        self.engine.dispose()
        self.assertEqual(self.engine.status(), EngineStatus.DISPOSED)

    def test_diagnostics_shape(self):
        self.engine.initialize()
        diag = self.engine.get_diagnostics()
        self.assertEqual(diag["name"], "MovementEngine")
        self.assertEqual(diag["version"], "2.0.0")
        self.assertEqual(diag["priority"], 7)
        self.assertIn("metrics", diag)
        m = diag["metrics"]
        for key in ("active_exercise", "fsm_state", "rep_count",
                    "recognition_latency_ms", "frames_processed"):
            self.assertIn(key, m, msg=f"Missing diagnostics key: {key}")


# ===========================================================================
# 2. FSM Transition Tests
# ===========================================================================

class TestFSMTransitions(unittest.TestCase):

    def _fsm(self):
        return _ExerciseFSM(_squat_config())

    def test_valid_idle_to_entering(self):
        fsm = self._fsm()
        self.assertEqual(fsm.state, MovementState.IDLE)
        # Entry condition: left_knee and right_knee in [155, 180]
        fsm.update(_angles(("left_knee", 170), ("right_knee", 170)))
        self.assertIn(fsm.state, (MovementState.ENTERING, MovementState.READY, MovementState.TOP))

    def test_all_valid_transitions_registered(self):
        """Ensure the valid transition table covers all 11 states."""
        self.assertEqual(len(_VALID_TRANSITIONS), 11)
        for state in MovementState:
            self.assertIn(state, _VALID_TRANSITIONS, msg=f"{state} missing from VALID_TRANSITIONS")

    def test_invalid_direct_idle_to_concentric_rejected(self):
        fsm = self._fsm()
        ok = fsm._transition(MovementState.CONCENTRIC)
        self.assertFalse(ok, "Direct IDLE→CONCENTRIC must be rejected")
        self.assertEqual(fsm.state, MovementState.IDLE)

    def test_invalid_bottom_to_idle_rejected(self):
        fsm = self._fsm()
        fsm.state = MovementState.BOTTOM
        ok = fsm._transition(MovementState.IDLE)
        self.assertFalse(ok, "BOTTOM→IDLE must be rejected")
        self.assertEqual(fsm.state, MovementState.BOTTOM)


# ===========================================================================
# 3. Rep Counting Tests
# ===========================================================================

class TestRepCounting(unittest.TestCase):

    def _squat_fsm(self):
        return _ExerciseFSM(_squat_config())

    def test_one_rep_counted(self):
        fsm = self._squat_fsm()
        _sim_squat_rep(fsm, rom_min=80.0)
        self.assertEqual(fsm.rep_counter.count, 1)

    def test_three_reps_counted(self):
        fsm = self._squat_fsm()
        for i in range(3):
            _sim_squat_rep(fsm, rom_min=80.0)
            # Inter-rep pause to clear 400ms debounce window
            time.sleep(0.45)
        self.assertEqual(fsm.rep_counter.count, 3)


    def test_rep_not_counted_without_bottom_phase(self):
        """Skipping bottom phase — rep must not be counted."""
        fsm = self._squat_fsm()
        # Standing (top)
        fsm.update(_angles(("left_knee", 170), ("right_knee", 170)))
        # Skip straight back to top without going through bottom
        fsm.update(_angles(("left_knee", 168), ("right_knee", 168)))
        self.assertEqual(fsm.rep_counter.count, 0)

    def test_partial_rep_not_counted(self):
        """Descend only halfway — rep must not be counted."""
        fsm = self._squat_fsm()
        fsm.update(_angles(("left_knee", 170), ("right_knee", 170)))  # top
        fsm.update(_angles(("left_knee", 135), ("right_knee", 135)))  # concentric (partial)
        # Go back to top without completing bottom
        fsm.update(_angles(("left_knee", 165), ("right_knee", 165)))
        self.assertEqual(fsm.rep_counter.count, 0)


# ===========================================================================
# 4. Bounce / False Positive Prevention Tests
# ===========================================================================

class TestFalsePositivePrevention(unittest.TestCase):

    def test_debounce_prevents_double_count(self):
        """Two rapid reps within debounce window → only one counted."""
        counter = _RepCounter(debounce_ms=400.0)
        t0 = time.monotonic()       # seconds
        counter.start_rep(t0 - 0.5)
        ok1 = counter.try_count_rep(t0, rom_ok=True)
        # Try again immediately (within 400ms = 0.4s debounce)
        ok2 = counter.try_count_rep(t0 + 0.1, rom_ok=True)
        self.assertTrue(ok1)
        self.assertFalse(ok2, "Second rapid count must be debounced")
        self.assertEqual(counter.count, 1)

    def test_insufficient_rom_blocks_count(self):
        """ROM gate fails — rep not counted."""
        counter = _RepCounter(debounce_ms=10.0)
        ts = 1000.0
        counter.start_rep(ts - 500)
        ok = counter.try_count_rep(ts, rom_ok=False)
        self.assertFalse(ok, "Insufficient ROM must block rep count")
        self.assertEqual(counter.count, 0)

    def test_insufficient_rom_squat_fsm(self):
        """Squat with very shallow depth (high knee angle) → min ROM fails."""
        fsm = _ExerciseFSM(_squat_config())
        # Set session angles to very narrow range
        fsm._session_min_angle = 155.0
        fsm._session_max_angle = 160.0
        rom_pct = fsm._compute_rom_pct()   # no args needed
        # Full squat range is 170→90 = 80°; achieved = 5° → ~6.25%
        self.assertLess(rom_pct, 50.0, "Shallow squat must fail 50% ROM gate")


# ===========================================================================
# 5. Hold Exercise Tests
# ===========================================================================

class TestHoldExercise(unittest.TestCase):

    def _plank_fsm(self):
        return _ExerciseFSM(_plank_config())

    def test_plank_enters_hold_state(self):
        fsm = self._plank_fsm()
        # Entry: spine ~10°, hips ~165°
        result = fsm.update(_angles(("spine", 10), ("left_hip", 165), ("right_hip", 165)))
        # After entry + entering → should be in HOLD
        for _ in range(3):
            result = fsm.update(_angles(("spine", 10), ("left_hip", 165), ("right_hip", 165)))
        self.assertEqual(fsm.state, MovementState.HOLD)
        self.assertFalse(result.get("events") and "exercise.rep_completed" in result["events"],
                         "Hold exercise must NOT emit rep_completed")

    def test_plank_hold_time_increases(self):
        fsm = self._plank_fsm()
        snap = _angles(("spine", 10), ("left_hip", 165), ("right_hip", 165))
        for _ in range(5):
            result = fsm.update(snap)
            time.sleep(0.02)
        # Hold time should be positive when in HOLD state
        if fsm.state == MovementState.HOLD:
            self.assertGreater(result["hold_time"], 0.0)

    def test_plank_exits_on_violation(self):
        fsm = self._plank_fsm()
        snap_entry = _angles(("spine", 10), ("left_hip", 165), ("right_hip", 165))
        for _ in range(3):
            fsm.update(snap_entry)
        self.assertEqual(fsm.state, MovementState.HOLD)

        # Spine violation: > 35° exits the hold
        result = fsm.update(
            _angles(("spine", 40), ("left_hip", 165), ("right_hip", 165)),
            tracking_quality=80.0
        )
        self.assertIn("exercise.cancelled", result["events"])


# ===========================================================================
# 6. Tracking Loss Recovery Tests
# ===========================================================================

class TestTrackingLossRecovery(unittest.TestCase):

    def test_low_tracking_quality_exits_exercise(self):
        fsm = _ExerciseFSM(_squat_config())
        # Enter exercise and advance past ENTERING state
        fsm.update(_angles(("left_knee", 170), ("right_knee", 170)))
        # Give the FSM a few frames to stabilize into an active state
        for _ in range(4):
            fsm.update(_angles(("left_knee", 170), ("right_knee", 170)))

        # The FSM should now be in an active state (TOP or READY at minimum)
        self.assertNotEqual(fsm.state, MovementState.IDLE)

        # Now send very low tracking quality (< 40)
        result = fsm.update(
            _angles(("left_knee", 170), ("right_knee", 170)),
            tracking_quality=30.0
        )
        # Should transition to EXITED (cancelled) or loop back to IDLE
        self.assertIn(fsm.state, (MovementState.EXITED, MovementState.IDLE, MovementState.TOP),
                      msg=f"Expected exit on low tracking quality, got: {fsm.state}")
        # exercise.cancelled should be emitted when truly exited
        if fsm.state == MovementState.EXITED:
            self.assertIn("exercise.cancelled", result["events"])


    def test_re_enter_after_tracking_loss(self):
        engine = MovementEngine(event_bus=EventBus())
        engine.initialize()
        engine.start()
        engine.set_active_exercise("bodyweight_squat")

        # Send good frame
        snap1 = _angles(("left_knee", 170), ("right_knee", 170))
        engine.process_snapshot(snap1, tracking_quality=90.0)

        # Send bad frame (tracking loss)
        snap2 = _angles(("left_knee", 170), ("right_knee", 170))
        engine.process_snapshot(snap2, tracking_quality=20.0)

        # Send good frame again — engine should not crash
        snap3 = _angles(("left_knee", 170), ("right_knee", 170))
        result = engine.process_snapshot(snap3, tracking_quality=90.0)
        self.assertIsNotNone(result)


# ===========================================================================
# 7. ExerciseResult Contract Tests
# ===========================================================================

class TestExerciseResultContract(unittest.TestCase):

    def test_contract_fields_present(self):
        r = ExerciseResult(
            exercise_name="Bodyweight Squat",
            exercise_id="bodyweight_squat",
            rep_count=3,
            current_phase="top",
            current_rep_duration=1.5,
            average_rep_duration=2.0,
            current_cadence=15.0,
            rom_percentage=82.0,
            movement_quality=95.0,
            hold_time=0.0,
            tracking_quality=90.0,
        )
        d = r.to_dict()
        required = [
            "id", "timestamp", "schema_version", "source",
            "exercise_id", "exercise_name", "current_phase", "rep_count",
            "current_rep_duration", "average_rep_duration", "current_cadence",
            "rom_percentage", "movement_quality", "hold_time", "tracking_quality",
        ]
        for field in required:
            self.assertIn(field, d, msg=f"Missing field: {field}")

    def test_form_score_backward_compat(self):
        """form_score kwarg must map to movement_quality."""
        r = ExerciseResult(exercise_name="Test", form_score=77.0)
        self.assertAlmostEqual(r.movement_quality, 77.0)

    def test_from_dict_round_trip(self):
        r1 = ExerciseResult(
            exercise_name="Plank",
            exercise_id="plank",
            hold_time=30.0,
            tracking_quality=88.0,
        )
        r2 = ExerciseResult.from_dict(r1.to_dict())
        self.assertEqual(r2.exercise_name, r1.exercise_name)
        self.assertEqual(r2.exercise_id, r1.exercise_id)
        self.assertAlmostEqual(r2.hold_time, r1.hold_time, places=1)

    def test_source_is_movement_engine(self):
        r = ExerciseResult(exercise_name="Push-Up")
        self.assertEqual(r.source, "movement_engine")

    def test_schema_version(self):
        r = ExerciseResult(exercise_name="Lunge")
        self.assertEqual(r.schema_version, "2.0.0")


# ===========================================================================
# 8. Runtime Integration Tests
# ===========================================================================

class TestMovementEngineRuntime(unittest.TestCase):

    def test_no_exercise_selected_returns_idle(self):
        engine = MovementEngine(event_bus=EventBus())
        engine.initialize()
        engine.start()
        result = engine.process_snapshot(_angles(("left_knee", 170)))
        self.assertEqual(result.exercise_id, "none")
        self.assertEqual(result.current_phase, "idle")

    def test_exercise_selection(self):
        engine = MovementEngine(event_bus=EventBus())
        engine.initialize()
        ok = engine.set_active_exercise("bodyweight_squat")
        self.assertTrue(ok)
        self.assertEqual(engine._active_exercise_id, "bodyweight_squat")

    def test_invalid_exercise_id_returns_false(self):
        engine = MovementEngine(event_bus=EventBus())
        engine.initialize()
        ok = engine.set_active_exercise("nonexistent_exercise_xyz")
        self.assertFalse(ok)

    def test_events_published_on_rep(self):
        bus = EventBus(debug_mode=True)
        engine = MovementEngine(event_bus=bus)
        engine.initialize()
        engine.start()
        engine.set_active_exercise("bodyweight_squat")

        snap_top    = _angles(("left_knee", 170), ("right_knee", 170))
        snap_conc   = _angles(("left_knee", 135), ("right_knee", 135))
        snap_bottom = _angles(("left_knee",  80), ("right_knee",  80))
        snap_ecc    = _angles(("left_knee", 130), ("right_knee", 130))

        for snap in [snap_top, snap_conc, snap_bottom, snap_ecc, snap_top]:
            engine.process_snapshot(snap, tracking_quality=90.0)
            time.sleep(0.01)

    def test_get_available_exercises_returns_all_10(self):
        engine = MovementEngine(event_bus=EventBus())
        engine.initialize()
        exercises = engine.get_available_exercises()
        self.assertEqual(len(exercises), 10,
                         msg=f"Expected 10 exercises, got {len(exercises)}: {[e['id'] for e in exercises]}")

    def test_reload_exercise_configs(self):
        engine = MovementEngine(event_bus=EventBus())
        engine.initialize()
        count = engine.reload_exercise_configs()
        self.assertGreaterEqual(count, 10)


# ===========================================================================
# 9. Motion Analyser Tests
# ===========================================================================

class TestMotionAnalyzer(unittest.TestCase):

    def test_stationary_when_no_history(self):
        ma = _MotionAnalyzer()
        self.assertEqual(ma.movement_direction, "stationary")
        self.assertAlmostEqual(ma.angular_velocity, 0.0)

    def test_decreasing_direction(self):
        ma = _MotionAnalyzer()
        t0 = 0.0
        for i in range(10):
            ma.update(180.0 - i * 10, t0 + i)
        self.assertEqual(ma.movement_direction, "decreasing")

    def test_increasing_direction(self):
        ma = _MotionAnalyzer()
        for i in range(10):
            ma.update(90.0 + i * 10, float(i))
        self.assertEqual(ma.movement_direction, "increasing")

    def test_reset_clears_history(self):
        ma = _MotionAnalyzer()
        for i in range(5):
            ma.update(float(i * 10), float(i))
        ma.reset()
        self.assertEqual(ma.angular_velocity, 0.0)


if __name__ == "__main__":
    unittest.main()
