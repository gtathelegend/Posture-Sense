/**
 * MovementEngine
 * ===============
 * Production-grade, configuration-driven browser-side engine for dynamic
 * exercise phase detection, repetition counting, tempo analysis, and hold tracking.
 *
 * Priority    : 7
 * Dependencies: biomechanics_engine, pose_rule_engine
 * Subscribes  : biomechanics.updated  (BiomechanicsSnapshot)
 *               pose.detected         (PoseResult)
 * Publishes   : exercise.started
 *               exercise.phase_changed
 *               exercise.rep_started
 *               exercise.rep_completed
 *               exercise.completed
 *               exercise.cancelled
 *               exercise.invalid
 *               exercise.updated      (ExerciseResult per-frame)
 *
 * DO NOT implement posture scoring.
 * DO NOT implement coaching feedback.
 * DO NOT use ML classifiers.
 */

// ---------------------------------------------------------------------------
// FSM States
// ---------------------------------------------------------------------------

export const MovementState = Object.freeze({
    IDLE:       'idle',
    ENTERING:   'entering',
    READY:      'ready',
    CONCENTRIC: 'concentric',
    BOTTOM:     'bottom',
    ECCENTRIC:  'eccentric',
    TOP:        'top',
    HOLD:       'hold',
    COMPLETED:  'completed',
    EXITED:     'exited',
    INVALID:    'invalid',
});

const VALID_TRANSITIONS = {
    [MovementState.IDLE]:       [MovementState.ENTERING],
    [MovementState.ENTERING]:   [MovementState.READY, MovementState.IDLE],
    [MovementState.READY]:      [MovementState.CONCENTRIC, MovementState.HOLD, MovementState.IDLE],
    [MovementState.CONCENTRIC]: [MovementState.BOTTOM, MovementState.ECCENTRIC, MovementState.INVALID],
    [MovementState.BOTTOM]:     [MovementState.ECCENTRIC, MovementState.CONCENTRIC],
    [MovementState.ECCENTRIC]:  [MovementState.TOP, MovementState.CONCENTRIC],
    [MovementState.TOP]:        [MovementState.COMPLETED, MovementState.CONCENTRIC, MovementState.IDLE],
    [MovementState.HOLD]:       [MovementState.COMPLETED, MovementState.IDLE],
    [MovementState.COMPLETED]:  [MovementState.IDLE],
    [MovementState.EXITED]:     [MovementState.IDLE],
    [MovementState.INVALID]:    [MovementState.IDLE],
};

// ---------------------------------------------------------------------------
// Motion Analyser
// ---------------------------------------------------------------------------

class MotionAnalyzer {
    constructor(windowSize = 15) {
        this._window = windowSize;
        this._history = []; // [{ts, angle}]
    }

    update(angle, ts) {
        this._history.push({ ts, angle });
        if (this._history.length > this._window) this._history.shift();
    }

    get angularVelocity() {
        if (this._history.length < 2) return 0.0;
        const first = this._history[0];
        const last  = this._history[this._history.length - 1];
        const dt = (last.ts - first.ts) / 1000.0; // ms → s
        if (dt < 1e-6) return 0.0;
        return (last.angle - first.angle) / dt;
    }

    get movementDirection() {
        const v = this.angularVelocity;
        if (Math.abs(v) < 2.0) return 'stationary';
        return v < 0 ? 'decreasing' : 'increasing';
    }

    reset() { this._history = []; }
}

// ---------------------------------------------------------------------------
// Rep Counter
// ---------------------------------------------------------------------------

class RepCounter {
    constructor(debounceMs = 400) {
        this._count = 0;
        this._debounceMs = debounceMs;
        this._lastRepTime = 0;
        this._repStartTime = 0;
        this._repDurations = [];
    }

    startRep(ts) { this._repStartTime = ts; }

    tryCountRep(ts, romOk) {
        if (!romOk) return false;
        if ((ts - this._lastRepTime) < this._debounceMs) return false;
        const duration = this._repStartTime > 0 ? (ts - this._repStartTime) / 1000.0 : 0;
        this._repDurations.push(duration);
        if (this._repDurations.length > 20) this._repDurations.shift();
        this._count++;
        this._lastRepTime = ts;
        this._repStartTime = 0;
        return true;
    }

    get count()              { return this._count; }
    get lastRepDuration()    { return this._repDurations.at(-1) ?? 0; }
    get averageRepDuration() {
        if (!this._repDurations.length) return 0;
        return this._repDurations.reduce((a, b) => a + b, 0) / this._repDurations.length;
    }
    get cadenceRpm()         {
        return this.averageRepDuration < 1e-6 ? 0 : 60.0 / this.averageRepDuration;
    }

    reset() {
        this._count = 0; this._lastRepTime = 0;
        this._repStartTime = 0; this._repDurations = [];
    }
}

// ---------------------------------------------------------------------------
// Exercise FSM
// ---------------------------------------------------------------------------

class ExerciseFSM {
    constructor(config) {
        this.config = config;
        this.exerciseId   = config.id;
        this.exerciseName = config.name;
        this.category     = config.category || 'dynamic';
        this.isHoldExercise = this.category === 'static_hold';

        this._phases     = config.phases || [];
        this._phaseIndex = Object.fromEntries(this._phases.map((p, i) => [p.id, i]));

        const rc = config.rep_completion || {};
        this._requiredPhases  = rc.required_phases || [];
        this._minRomPct       = parseFloat(rc.min_rom_percentage || 0);
        this._debounceMs      = parseFloat(rc.debounce_ms || 400);
        this._romJoint        = rc.rom_joint || '';
        this._romRefTop       = parseFloat(rc.rom_reference_top || 170);
        this._romRefBottom    = parseFloat(rc.rom_reference_bottom || 90);
        this._minBottomDepth  = parseFloat(rc.min_bottom_depth_deg || 115);

        this.holdConfig = config.hold_config || null;

        // State
        this.state            = MovementState.IDLE;
        this.currentPhaseId   = null;
        this._phasesCompleted = [];
        this._stateEntryTime  = performance.now();
        this._exerciseStartTime = 0;
        this._holdStartTime   = 0;

        this.repCounter    = new RepCounter(this._debounceMs);
        this.motionAnalyzer = new MotionAnalyzer();

        this._sessionMinAngle = 999;
        this._sessionMaxAngle = 0;
    }

    // ── Transition ──────────────────────────────────────────────────────────

    _transition(newState) {
        const allowed = VALID_TRANSITIONS[this.state] || [];
        if (!allowed.includes(newState)) return false;
        this.state = newState;
        this._stateEntryTime = performance.now();
        return true;
    }

    // ── Angle map ───────────────────────────────────────────────────────────

    _anglesMap(snapshot) {
        const map = {};
        (snapshot.joint_angles || []).forEach(ja => { map[ja.joint_name] = ja.angle; });
        return map;
    }

    // ── ROM ─────────────────────────────────────────────────────────────────

    _computeRomPct() {
        const fullRange = Math.abs(this._romRefTop - this._romRefBottom);
        if (fullRange < 1e-6) return 100;
        const achieved = Math.abs(this._sessionMaxAngle - this._sessionMinAngle);
        return Math.min(100, (achieved / fullRange) * 100);
    }

    // ── Condition checks ────────────────────────────────────────────────────

    _entryConditionsMet(angles) {
        const constraints = (this.config.entry_conditions || {}).joint_constraints || {};
        for (const [joint, [lo, hi]] of Object.entries(constraints)) {
            const a = angles[joint];
            if (a === undefined || a < lo || a > hi) return false;
        }
        return true;
    }

    _exitConditionsMet(angles, trackingQuality) {
        const ec = this.config.exit_conditions || {};
        const tqThreshold = parseFloat(ec.tracking_quality_below || 0);
        if (tqThreshold > 0 && trackingQuality < tqThreshold) return true;
        const violations = ec.joint_violation || {};
        for (const [joint, [lo, hi]] of Object.entries(violations)) {
            const a = angles[joint];
            if (a !== undefined && (a < lo || a > hi)) return true;
        }
        return false;
    }

    _phaseMatches(phase, angles) {
        const ranges = phase.trigger_ranges || {};
        if (!Object.keys(ranges).length) return false;
        for (const [joint, [lo, hi]] of Object.entries(ranges)) {
            const a = angles[joint];
            if (a === undefined || a < lo || a > hi) return false;
        }
        return true;
    }

    // ── Main update ─────────────────────────────────────────────────────────

    update(snapshot, trackingQuality = 100) {
        const ts = performance.now();
        const angles = this._anglesMap(snapshot);
        const events = [];

        // ROM + motion tracking
        const primaryAngle = this._romJoint ? (angles[this._romJoint] || 0) : 0;
        if (primaryAngle > 0) {
            this._sessionMinAngle = Math.min(this._sessionMinAngle, primaryAngle);
            this._sessionMaxAngle = Math.max(this._sessionMaxAngle, primaryAngle);
            this.motionAnalyzer.update(primaryAngle, ts);
        }
        const romPct = this._computeRomPct();

        // IDLE → ENTERING
        if (this.state === MovementState.IDLE) {
            if (this._entryConditionsMet(angles)) {
                this._transition(MovementState.ENTERING);
                events.push('exercise.started');
                this._exerciseStartTime = ts;
                this._phasesCompleted = [];
                this.repCounter.reset();
                this.motionAnalyzer.reset();
                this._sessionMinAngle = primaryAngle || 999;
                this._sessionMaxAngle = primaryAngle || 0;
            }
            return this._makeResult(events, romPct, ts);
        }

        // Exit detection
        const activeStates = [
            MovementState.ENTERING, MovementState.READY, MovementState.CONCENTRIC,
            MovementState.BOTTOM, MovementState.ECCENTRIC, MovementState.TOP, MovementState.HOLD
        ];
        if (activeStates.includes(this.state) && this._exitConditionsMet(angles, trackingQuality)) {
            this._transition(MovementState.EXITED);
            events.push('exercise.cancelled');
            return this._makeResult(events, romPct, ts);
        }

        // ENTERING → READY (or HOLD for static exercises)
        if (this.state === MovementState.ENTERING) {
            if (this.isHoldExercise) {
                this._transition(MovementState.READY);
                this._transition(MovementState.HOLD);
                this._holdStartTime = ts;
                events.push('exercise.phase_changed');
            } else {
                this._transition(MovementState.READY);
                events.push('exercise.phase_changed');
            }
            return this._makeResult(events, romPct, ts);
        }

        // HOLD path
        if (this.state === MovementState.HOLD) {
            const holdPhase = this._phases[0];
            if (holdPhase && !this._phaseMatches(holdPhase, angles)) {
                this._transition(MovementState.EXITED);
                events.push('exercise.cancelled');
            }
            return this._makeResult(events, romPct, ts);
        }

        // Dynamic exercise: phase detection
        const prevState = this.state;
        for (const phase of this._phases) {
            if (!this._phaseMatches(phase, angles)) continue;

            const typeToState = {
                top:        MovementState.TOP,
                concentric: MovementState.CONCENTRIC,
                bottom:     MovementState.BOTTOM,
                eccentric:  MovementState.ECCENTRIC,
                hold:       MovementState.HOLD,
            };
            const targetState = typeToState[phase.type];
            if (!targetState || targetState === this.state) break;

            if (this._transition(targetState)) {
                this.currentPhaseId = phase.id;
                events.push('exercise.phase_changed');

                if (!this._phasesCompleted.includes(phase.id)) {
                    this._phasesCompleted.push(phase.id);
                }

                // Rep started
                if (targetState === MovementState.CONCENTRIC &&
                    (prevState === MovementState.TOP || prevState === MovementState.READY)) {
                    this.repCounter.startRep(ts);
                    events.push('exercise.rep_started');
                }

                // Rep completed
                if (targetState === MovementState.TOP && prevState === MovementState.ECCENTRIC) {
                    const requiredOk = this._requiredPhases.every(ph => this._phasesCompleted.includes(ph));
                    const romOk      = this._minRomPct <= 0 || romPct >= this._minRomPct;
                    if (requiredOk && this.repCounter.tryCountRep(ts, romOk)) {
                        events.push('exercise.rep_completed');
                        this._phasesCompleted = [];
                        this._sessionMinAngle = primaryAngle || 999;
                        this._sessionMaxAngle = primaryAngle || 0;
                    }
                }
            }
            break;
        }

        // Completed / Exited → reset to IDLE
        if (this.state === MovementState.COMPLETED || this.state === MovementState.EXITED) {
            this._transition(MovementState.IDLE);
        }

        return this._makeResult(events, romPct, ts);
    }

    _makeResult(events, romPct, ts) {
        const holdTime = (this.state === MovementState.HOLD && this._holdStartTime > 0)
            ? (ts - this._holdStartTime) / 1000.0 : 0;
        const currentRepDuration = this.repCounter._repStartTime > 0
            ? (ts - this.repCounter._repStartTime) / 1000.0 : 0;

        return {
            events,
            exerciseId:           this.exerciseId,
            exerciseName:         this.exerciseName,
            fsmState:             this.state,
            currentPhase:         this.currentPhaseId || this.state,
            repCount:             this.repCounter.count,
            currentRepDuration:   round2(currentRepDuration),
            averageRepDuration:   round2(this.repCounter.averageRepDuration),
            currentCadence:       round1(this.repCounter.cadenceRpm),
            romPercentage:        round1(romPct),
            holdTime:             round2(holdTime),
            movementDirection:    this.motionAnalyzer.movementDirection,
            angularVelocity:      round1(this.motionAnalyzer.angularVelocity),
            exerciseDuration:     this._exerciseStartTime > 0
                ? round2((ts - this._exerciseStartTime) / 1000.0) : 0,
        };
    }
}

// ---------------------------------------------------------------------------
// MovementEngine
// ---------------------------------------------------------------------------

export class MovementEngine {
    constructor(eventBus = null) {
        this.name         = 'MovementEngine';
        this.version      = '2.0.0';
        this.eventBus     = eventBus;
        this.status       = 'uninitialized';
        this.priority     = 7;
        this.dependencies = ['pose_rule_engine', 'biomechanics_engine'];

        this.config = {
            activeExerciseId:    null,
            minTrackingQuality:  55.0,
            enableHoldMilestones: true,
        };

        // All loaded exercise definitions (fetched from YAML via a static registry below)
        this._exerciseConfigs = {};

        // Active FSM
        this._fsm = null;
        this._activeExerciseId = null;
        this._lastTrackingQuality = 100.0;

        // Diagnostics
        this._framesProcessed         = 0;
        this._falsePosPreventedCount  = 0;
        this._recognitionLatencyMs    = 0.0;
        this._sessionStartTime        = 0;
        this._lastResult              = null;

        this.metrics = {
            activeExercise:        null,
            fsmState:              MovementState.IDLE,
            repCount:              0,
            currentPhase:          'idle',
            currentRepDuration:    0,
            averageRepDuration:    0,
            currentCadence:        0,
            romPercentage:         0,
            holdTime:              0,
            movementDirection:     'stationary',
            angularVelocity:       0,
            exerciseDuration:      0,
            recognitionLatencyMs:  0,
            framesProcessed:       0,
        };
    }

    // ── Lifecycle ────────────────────────────────────────────────────────────

    async initialize(config = {}) {
        Object.assign(this.config, config);
        // Load built-in exercise definitions (inline — no fetch required)
        this._exerciseConfigs = _BUILTIN_EXERCISE_CONFIGS;
        this.status = 'initialized';
        this._publish('exercise.engine_initialized', this.getDiagnostics());
        return true;
    }

    async start() {
        this.status = 'running';
        this._sessionStartTime = performance.now();
        this._subscribeToEvents();
        this._publish('exercise.engine_started', this.getDiagnostics());
        return true;
    }

    pause() {
        if (this.status === 'running') {
            this.status = 'paused';
            this._publish('exercise.paused', this.getDiagnostics());
        }
    }

    resume() {
        if (this.status === 'paused') {
            this.status = 'running';
            this._publish('exercise.resumed', this.getDiagnostics());
        }
    }

    async stop() {
        this.status = 'stopped';
        this._publish('exercise.engine_stopped', this.getDiagnostics());
    }

    dispose() {
        this.stop();
        this.status = 'disposed';
        this._publish('exercise.engine_disposed', this.getDiagnostics());
    }

    // ── Event subscriptions ──────────────────────────────────────────────────

    _subscribeToEvents() {
        if (!this.eventBus || typeof this.eventBus.subscribe !== 'function') return;

        this.eventBus.subscribe('biomechanics.updated', (event) => {
            if (this.status === 'running') {
                this.processSnapshot(event.data || event || {});
            }
        });

        this.eventBus.subscribe('pose.detected', (event) => {
            if (this.status === 'running') {
                const d = event.data || event || {};
                this._lastTrackingQuality = parseFloat(d.tracking_quality ?? 100);
            }
        });
    }

    // ── Exercise selection ───────────────────────────────────────────────────

    setActiveExercise(exerciseId) {
        const cfg = this._exerciseConfigs[exerciseId];
        if (!cfg) return false;
        this._fsm = new ExerciseFSM(cfg);
        this._activeExerciseId = exerciseId;
        this.config.activeExerciseId = exerciseId;
        this.metrics.activeExercise = cfg.name;
        return true;
    }

    getAvailableExercises() {
        return Object.values(this._exerciseConfigs).map(cfg => ({
            id: cfg.id, name: cfg.name, category: cfg.category || 'dynamic'
        }));
    }

    // ── Core processing ──────────────────────────────────────────────────────

    processSnapshot(snapshot) {
        if (!this._fsm) {
            const idle = this._idleResult();
            this._publish('exercise.updated', idle);
            return idle;
        }

        const t0 = performance.now();
        const raw = this._fsm.update(snapshot, this._lastTrackingQuality);
        this._recognitionLatencyMs = performance.now() - t0;
        this._framesProcessed++;

        // Emit per-event events
        for (const evt of raw.events) {
            this._publish(evt, raw);
        }

        // Build ExerciseResult contract
        const result = {
            id:                   _uuid(),
            timestamp:            new Date().toISOString(),
            schema_version:       '2.0.0',
            source:               this.name,
            exercise_id:          raw.exerciseId,
            exercise_name:        raw.exerciseName,
            current_phase:        raw.currentPhase,
            rep_count:            raw.repCount,
            current_rep_duration: raw.currentRepDuration,
            average_rep_duration: raw.averageRepDuration,
            current_cadence:      raw.currentCadence,
            rom_percentage:       raw.romPercentage,
            movement_quality:     round1(Math.min(100, this._lastTrackingQuality)),
            hold_time:            raw.holdTime,
            tracking_quality:     round1(this._lastTrackingQuality),
        };

        // Update live metrics
        this.metrics = {
            activeExercise:       raw.exerciseName,
            fsmState:             raw.fsmState,
            repCount:             raw.repCount,
            currentPhase:         raw.currentPhase,
            currentRepDuration:   raw.currentRepDuration,
            averageRepDuration:   raw.averageRepDuration,
            currentCadence:       raw.currentCadence,
            romPercentage:        raw.romPercentage,
            holdTime:             raw.holdTime,
            movementDirection:    raw.movementDirection,
            angularVelocity:      raw.angularVelocity,
            exerciseDuration:     raw.exerciseDuration,
            recognitionLatencyMs: round2(this._recognitionLatencyMs),
            framesProcessed:      this._framesProcessed,
        };

        this._lastResult = result;
        this._publish('exercise.updated', result);
        return result;
    }

    _idleResult() {
        return {
            id: _uuid(), timestamp: new Date().toISOString(),
            schema_version: '2.0.0', source: this.name,
            exercise_id: 'none', exercise_name: 'None',
            current_phase: 'idle', rep_count: 0,
            current_rep_duration: 0, average_rep_duration: 0,
            current_cadence: 0, rom_percentage: 0,
            movement_quality: 100, hold_time: 0, tracking_quality: 100,
        };
    }

    // ── Diagnostics ──────────────────────────────────────────────────────────

    getDiagnostics() {
        const sessionDuration = this._sessionStartTime > 0
            ? round2((performance.now() - this._sessionStartTime) / 1000) : 0;
        return {
            name:         this.name,
            version:      this.version,
            status:       this.status,
            priority:     this.priority,
            dependencies: this.dependencies,
            config:       { ...this.config },
            metrics: {
                ...this.metrics,
                exerciseDuration: sessionDuration,
                loadedExercises:  Object.keys(this._exerciseConfigs).length,
            },
        };
    }

    _publish(eventName, data) {
        if (this.eventBus && typeof this.eventBus.publish === 'function') {
            this.eventBus.publish(eventName, data);
        }
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function round1(n) { return Math.round(n * 10) / 10; }
function round2(n) { return Math.round(n * 100) / 100; }
function _uuid()   { return Math.random().toString(36).substring(2, 11); }

// ---------------------------------------------------------------------------
// Built-in exercise config registry
// These mirror the YAML files in shared/config/current/exercises/
// The JS engine embeds them inline to avoid needing a fetch/YAML parser.
// ---------------------------------------------------------------------------

const _BUILTIN_EXERCISE_CONFIGS = {
    bodyweight_squat: {
        id: 'bodyweight_squat', name: 'Bodyweight Squat', category: 'dynamic',
        entry_conditions: {
            joint_constraints: { left_knee: [155, 180], right_knee: [155, 180] }
        },
        exit_conditions: { tracking_quality_below: 40 },
        phases: [
            { id: 'top',        name: 'Standing',   type: 'top',        trigger_ranges: { left_knee: [155, 180], right_knee: [155, 180] } },
            { id: 'concentric', name: 'Descending', type: 'concentric', trigger_ranges: { left_knee: [115, 155], right_knee: [115, 155] } },
            { id: 'bottom',     name: 'Bottom',     type: 'bottom',     trigger_ranges: { left_knee: [60,  115], right_knee: [60,  115] } },
            { id: 'eccentric',  name: 'Ascending',  type: 'eccentric',  trigger_ranges: { left_knee: [115, 155], right_knee: [115, 155] } },
        ],
        rep_completion: {
            required_phases: ['top', 'concentric', 'bottom', 'eccentric'],
            min_rom_percentage: 50, rom_joint: 'left_knee',
            rom_reference_top: 170, rom_reference_bottom: 90,
            prevent_bounce: true, debounce_ms: 400,
        },
        hold_config: null,
    },
    push_up: {
        id: 'push_up', name: 'Push-Up', category: 'dynamic',
        entry_conditions: {
            joint_constraints: { left_elbow: [155, 180], right_elbow: [155, 180] }
        },
        exit_conditions: { tracking_quality_below: 40 },
        phases: [
            { id: 'top',        name: 'Arms Extended', type: 'top',        trigger_ranges: { left_elbow: [155, 180], right_elbow: [155, 180] } },
            { id: 'concentric', name: 'Lowering',      type: 'concentric', trigger_ranges: { left_elbow: [100, 155], right_elbow: [100, 155] } },
            { id: 'bottom',     name: 'Bottom',        type: 'bottom',     trigger_ranges: { left_elbow: [60,  100], right_elbow: [60,  100] } },
            { id: 'eccentric',  name: 'Pushing Up',    type: 'eccentric',  trigger_ranges: { left_elbow: [100, 155], right_elbow: [100, 155] } },
        ],
        rep_completion: {
            required_phases: ['top', 'concentric', 'bottom', 'eccentric'],
            min_rom_percentage: 50, rom_joint: 'left_elbow',
            rom_reference_top: 170, rom_reference_bottom: 80,
            prevent_bounce: true, debounce_ms: 400,
        },
        hold_config: null,
    },
    lunge: {
        id: 'lunge', name: 'Lunge', category: 'dynamic',
        entry_conditions: {
            joint_constraints: { left_knee: [155, 180], right_knee: [155, 180] }
        },
        exit_conditions: { tracking_quality_below: 40 },
        phases: [
            { id: 'top',        name: 'Standing',      type: 'top',        trigger_ranges: { left_knee: [155, 180] } },
            { id: 'concentric', name: 'Lunging Down',  type: 'concentric', trigger_ranges: { left_knee: [110, 155] } },
            { id: 'bottom',     name: 'Lunge Position',type: 'bottom',     trigger_ranges: { left_knee: [60,  110] } },
            { id: 'eccentric',  name: 'Returning',     type: 'eccentric',  trigger_ranges: { left_knee: [110, 155] } },
        ],
        rep_completion: {
            required_phases: ['top', 'concentric', 'bottom', 'eccentric'],
            min_rom_percentage: 40, rom_joint: 'left_knee',
            rom_reference_top: 170, rom_reference_bottom: 90,
            prevent_bounce: true, debounce_ms: 400,
        },
        hold_config: null,
    },
    plank: {
        id: 'plank', name: 'Plank', category: 'static_hold',
        entry_conditions: {
            joint_constraints: { spine: [0, 25], left_hip: [155, 185], right_hip: [155, 185] }
        },
        exit_conditions: { tracking_quality_below: 40, joint_violation: { spine: [0, 35] } },
        phases: [
            { id: 'hold', name: 'Holding', type: 'hold', trigger_ranges: { spine: [0, 30], left_hip: [150, 190] } }
        ],
        rep_completion: { required_phases: [], min_rom_percentage: 0, prevent_bounce: false, debounce_ms: 0 },
        hold_config: { min_seconds: 10, milestone_seconds: [15, 30, 45, 60, 90, 120], count_unit: 'seconds' },
    },
    jumping_jack: {
        id: 'jumping_jack', name: 'Jumping Jack', category: 'dynamic',
        entry_conditions: {
            joint_constraints: { left_shoulder: [0, 40], right_shoulder: [0, 40] }
        },
        exit_conditions: { tracking_quality_below: 40 },
        phases: [
            { id: 'top',        name: 'Arms Down',    type: 'top',        trigger_ranges: { left_shoulder: [0,   45]  } },
            { id: 'concentric', name: 'Arms Rising',  type: 'concentric', trigger_ranges: { left_shoulder: [45,  135] } },
            { id: 'bottom',     name: 'Arms Overhead',type: 'bottom',     trigger_ranges: { left_shoulder: [130, 180] } },
            { id: 'eccentric',  name: 'Arms Lowering',type: 'eccentric',  trigger_ranges: { left_shoulder: [45,  130] } },
        ],
        rep_completion: {
            required_phases: ['top', 'concentric', 'bottom', 'eccentric'],
            min_rom_percentage: 40, rom_joint: 'left_shoulder',
            rom_reference_top: 20, rom_reference_bottom: 150,
            prevent_bounce: true, debounce_ms: 250,
        },
        hold_config: null,
    },
    wall_sit: {
        id: 'wall_sit', name: 'Wall Sit', category: 'static_hold',
        entry_conditions: {
            joint_constraints: { left_knee: [80, 110], right_knee: [80, 110], left_hip: [80, 110] }
        },
        exit_conditions: { tracking_quality_below: 40, joint_violation: { left_knee: [65, 125] } },
        phases: [
            { id: 'hold', name: 'Holding', type: 'hold', trigger_ranges: { left_knee: [75, 115], right_knee: [75, 115] } }
        ],
        rep_completion: { required_phases: [], min_rom_percentage: 0, prevent_bounce: false, debounce_ms: 0 },
        hold_config: { min_seconds: 10, milestone_seconds: [15, 30, 45, 60, 90, 120], count_unit: 'seconds' },
    },
    chair_pose_hold: {
        id: 'chair_pose_hold', name: 'Chair Pose Hold', category: 'static_hold',
        entry_conditions: {
            joint_constraints: { left_knee: [90, 130], right_knee: [90, 130], left_hip: [80, 120] }
        },
        exit_conditions: { tracking_quality_below: 35, joint_violation: { left_knee: [70, 150] } },
        phases: [
            { id: 'hold', name: 'Holding Chair', type: 'hold', trigger_ranges: { left_knee: [85, 135], right_knee: [85, 135] } }
        ],
        rep_completion: { required_phases: [], min_rom_percentage: 0, prevent_bounce: false, debounce_ms: 0 },
        hold_config: { min_seconds: 5, milestone_seconds: [10, 20, 30, 45, 60], count_unit: 'seconds' },
    },
    tree_pose_hold: {
        id: 'tree_pose_hold', name: 'Tree Pose Hold', category: 'static_hold',
        entry_conditions: {
            joint_constraints: { left_knee: [160, 180], right_knee: [30, 90] }
        },
        exit_conditions: { tracking_quality_below: 35, joint_violation: { right_knee: [20, 105] } },
        phases: [
            { id: 'hold', name: 'Tree Hold', type: 'hold', trigger_ranges: { left_knee: [155, 180], right_knee: [25, 95] } }
        ],
        rep_completion: { required_phases: [], min_rom_percentage: 0, prevent_bounce: false, debounce_ms: 0 },
        hold_config: { min_seconds: 5, milestone_seconds: [10, 20, 30, 45, 60], count_unit: 'seconds' },
    },
    warrior_ii_hold: {
        id: 'warrior_ii_hold', name: 'Warrior II Hold', category: 'static_hold',
        entry_conditions: {
            joint_constraints: { left_knee: [80, 110], right_knee: [160, 180], left_shoulder: [80, 105] }
        },
        exit_conditions: { tracking_quality_below: 35, joint_violation: { left_knee: [65, 130] } },
        phases: [
            { id: 'hold', name: 'Warrior II Hold', type: 'hold', trigger_ranges: { left_knee: [75, 115], right_knee: [155, 180], left_shoulder: [75, 110] } }
        ],
        rep_completion: { required_phases: [], min_rom_percentage: 0, prevent_bounce: false, debounce_ms: 0 },
        hold_config: { min_seconds: 5, milestone_seconds: [10, 20, 30, 45, 60], count_unit: 'seconds' },
    },
    bridge_hold: {
        id: 'bridge_hold', name: 'Bridge Hold', category: 'static_hold',
        entry_conditions: {
            joint_constraints: { left_hip: [150, 185], right_hip: [150, 185], left_knee: [80, 110] }
        },
        exit_conditions: { tracking_quality_below: 35, joint_violation: { left_hip: [130, 195] } },
        phases: [
            { id: 'hold', name: 'Bridge Hold', type: 'hold', trigger_ranges: { left_hip: [145, 190], right_hip: [145, 190] } }
        ],
        rep_completion: { required_phases: [], min_rom_percentage: 0, prevent_bounce: false, debounce_ms: 0 },
        hold_config: { min_seconds: 5, milestone_seconds: [10, 20, 30, 45, 60], count_unit: 'seconds' },
    },
};
