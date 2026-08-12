/**
 * FeedbackEngine
 * ===============
 * Production-grade, configuration-driven browser-side Feedback Engine for PostureSense v2.
 *
 * Priority    : 9
 * Dependencies: scoring_engine, movement_engine, pose_rule_engine, biomechanics_engine
 * Subscribes  : score.updated       (ScoreReport)
 *               score.rep_completed   (ScoreReport / rep data)
 *               score.exercise_completed (ScoreReport)
 *               score.session_completed  (ScoreReport / session summary)
 *               pose.detected       (PoseResult)
 *               exercise.completed  (ExerciseResult)
 * Publishes   : feedback.generated
 *               feedback.updated
 *               feedback.dismissed
 *               feedback.session_summary
 *
 * DO NOT perform computer vision.
 * DO NOT calculate scores.
 * DO NOT change measurements.
 * DO NOT classify poses.
 * DO NOT detect exercises.
 * DO NOT use LLM text generation.
 */

const SEVERITY_WEIGHTS = {
    critical: 5,
    high: 4,
    medium: 3,
    low: 2,
    info: 1
};

export class FeedbackEngine {
    constructor(eventBus = null) {
        this.name = "FeedbackEngine";
        this.version = "2.0.0";
        this.eventBus = eventBus;
        this.status = "uninitialized";
        this.priority = 9;
        this.dependencies = ["scoring_engine", "movement_engine", "pose_rule_engine", "biomechanics_engine"];

        // Configuration
        this.config = {
            version: "2.0.0",
            settings: {
                default_cooldown_seconds: 4.0,
                high_severity_cooldown_seconds: 2.5,
                critical_severity_cooldown_seconds: 1.0,
                max_active_feedback_queue: 5
            },
            rules: [
                {
                    id: 'rule_form_quality_low',
                    category: 'Form',
                    type: 'correction',
                    severity: 'high',
                    metric: 'form',
                    condition: 'below',
                    threshold: 60.0,
                    message: 'Maintain upright torso and proper alignment.',
                    template_key: 'feedback.form.low_quality',
                    cooldown_seconds: 4.0
                },
                {
                    id: 'rule_form_quality_excellent',
                    category: 'Form',
                    type: 'positive',
                    severity: 'info',
                    metric: 'form',
                    condition: 'above',
                    threshold: 88.0,
                    message: 'Excellent body posture and execution!',
                    template_key: 'feedback.form.excellent',
                    cooldown_seconds: 8.0
                },
                {
                    id: 'rule_rom_shallow',
                    category: 'Range of Motion',
                    type: 'correction',
                    severity: 'medium',
                    metric: 'rom',
                    condition: 'below',
                    threshold: 70.0,
                    message: 'Increase your range of motion to reach recommended depth.',
                    template_key: 'feedback.rom.shallow',
                    cooldown_seconds: 4.0
                },
                {
                    id: 'rule_stability_unstable',
                    category: 'Stability',
                    type: 'correction',
                    severity: 'high',
                    metric: 'stability',
                    condition: 'below',
                    threshold: 65.0,
                    message: 'Engage your core to stabilize balance.',
                    template_key: 'feedback.stability.unstable',
                    cooldown_seconds: 3.5
                },
                {
                    id: 'rule_symmetry_asymmetric',
                    category: 'Symmetry',
                    type: 'correction',
                    severity: 'medium',
                    metric: 'symmetry',
                    condition: 'below',
                    threshold: 75.0,
                    message: 'Keep both sides aligned symmetrically.',
                    template_key: 'feedback.symmetry.asymmetric',
                    cooldown_seconds: 4.0
                },
                {
                    id: 'rule_tracking_quality_low',
                    category: 'Tracking Quality',
                    type: 'warning',
                    severity: 'critical',
                    metric: 'tracking_quality',
                    condition: 'below',
                    threshold: 50.0,
                    message: 'Tracking confidence is low. Ensure clear camera view.',
                    template_key: 'feedback.tracking.low_quality',
                    cooldown_seconds: 3.0
                }
            ]
        };

        // Internal State
        this._lastScoreReport = null;
        this._lastPose = null;
        this._lastExercise = null;

        this._ruleCooldowns = {};
        this._messageCooldowns = {};
        this._activeFeedback = [];
        this._generatedCount = 0;
        this._processingTimeMs = 0.0;
        this._handlers = [];
    }

    async initialize(config = null) {
        if (config) {
            Object.assign(this.config, config);
        }

        if (this.eventBus) {
            this._subscribe('score.updated',          e => this._onScoreUpdated(e));
            this._subscribe('score.rep_completed',    e => this._onScoreRepCompleted(e));
            this._subscribe('score.exercise_completed', e => this._onScoreExerciseCompleted(e));
            this._subscribe('score.session_completed', e => this._onScoreSessionCompleted(e));
            this._subscribe('pose.detected',          e => this._onPoseDetected(e));
            this._subscribe('exercise.completed',     e => this._onExerciseCompleted(e));
        }

        this.status = "initialized";
        this._publish("feedback.initialized", this.getDiagnostics());
        return true;
    }

    async start() {
        this.status = "running";
        this._publish("feedback.started", this.getDiagnostics());
        return true;
    }

    async pause() {
        this.status = "paused";
        this._publish("feedback.paused", this.getDiagnostics());
        return true;
    }

    async resume() {
        this.status = "running";
        this._publish("feedback.resumed", this.getDiagnostics());
        return true;
    }

    async stop() {
        this.status = "stopped";
        this._publish("feedback.stopped", this.getDiagnostics());
        return true;
    }

    async dispose() {
        this.status = "disposed";
        this._activeFeedback = [];
        this._ruleCooldowns = {};
        this._messageCooldowns = {};
        this._lastScoreReport = null;
        this._lastPose = null;
        this._lastExercise = null;
        this._publish("feedback.disposed", this.getDiagnostics());
        return true;
    }

    // ---------------------------------------------------------------------------
    // Event Handlers
    // ---------------------------------------------------------------------------

    _onScoreUpdated(event) {
        if (this.status !== 'running') return;
        this._lastScoreReport = event.data || event;
        this._evaluateAndPublishFeedback();
    }

    _onScoreRepCompleted(event) {
        if (this.status !== 'running') return;
        this._evaluateAndPublishFeedback();
    }

    _onScoreExerciseCompleted(event) {
        if (this.status !== 'running') return;
        this._evaluateAndPublishFeedback();
    }

    _onScoreSessionCompleted(event) {
        if (this.status !== 'running') return;
        this._generateAndPublishSessionSummary(event.data || event);
    }

    _onPoseDetected(event) {
        if (this.status !== 'running') return;
        this._lastPose = event.data || event;
    }

    _onExerciseCompleted(event) {
        if (this.status !== 'running') return;
        this._generateAndPublishSessionSummary(event.data || event);
    }

    // ---------------------------------------------------------------------------
    // Rule Evaluation & Prioritization
    // ---------------------------------------------------------------------------

    evaluateFeedbackRules() {
        const t0 = performance.now();
        if (!this._lastScoreReport) return [];

        const report = this._lastScoreReport;
        const now = Date.now() / 1000.0;
        const rules = this.config.rules || [];
        const candidates = [];

        // Metrics source dictionary
        const metricValues = {
            overall_score: [report.overall_score ?? report.overallScore ?? 0.0, "overall_score"],
            tracking_quality: [this._lastExercise?.tracking_quality ?? report.components?.tracking_quality?.score ?? 100.0, "tracking_quality"]
        };

        if (report.components) {
            for (const [dim, comp] of Object.entries(report.components)) {
                if (comp && comp.score !== null && comp.score !== undefined) {
                    metricValues[dim] = [Number(comp.score), dim];
                }
            }
        }

        // Evaluate each rule
        for (const rule of rules) {
            const ruleId    = rule.id || "unnamed_rule";
            const metric    = rule.metric || "";
            const condition = rule.condition || "below";
            const threshold = Number(rule.threshold || 0.0);

            const valTuple = metricValues[metric];
            if (!valTuple || valTuple[0] === null || valTuple[0] === undefined) continue;

            const [rawVal, metricSrc] = valTuple;
            let triggered = false;

            if (condition === "below" && rawVal < threshold) triggered = true;
            else if (condition === "above" && rawVal > threshold) triggered = true;
            else if (condition === "equals" && Math.abs(rawVal - threshold) < 1e-3) triggered = true;

            if (!triggered) continue;

            // Check Cooldown
            const cooldownSec = Number(rule.cooldown_seconds || this.config.settings?.default_cooldown_seconds || 4.0);
            const lastTrig = this._ruleCooldowns[ruleId] || 0.0;
            if ((now - lastTrig) < cooldownSec) continue;

            const diff = Math.abs(rawVal - threshold);
            const evidence = {
                raw_value: Number(rawVal.toFixed(2)),
                threshold: Number(threshold.toFixed(2)),
                difference: Number(diff.toFixed(2)),
                unit: metric.includes("score") || report.components?.[metric] ? "points" : "%",
                metric_source: metricSrc,
                rule_condition: condition
            };

            const variables = {
                raw_value: Number(rawVal.toFixed(1)),
                threshold: Number(threshold.toFixed(1)),
                metric_name: metric,
                exercise_name: report.exercise_name || report.exerciseName || "Exercise"
            };

            candidates.push({
                feedback_id: `fb_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`,
                category: rule.category || "Form",
                type: rule.type || "correction",
                severity: rule.severity || "medium",
                message: rule.message || "Form violation detected.",
                evidence: evidence,
                metric_source: metricSrc,
                confidence: report.score_confidence ?? report.scoreConfidence ?? 1.0,
                exercise_id: report.exercise_id || report.exerciseId || "unknown",
                pose_id: this._lastPose?.pose_name || this._lastPose?.poseName || null,
                rule_triggered: ruleId,
                template_key: rule.template_key || "feedback.generic",
                variables: variables,
                timestamp: new Date().toISOString(),
                source: this.name
            });
        }

        // Sort by Severity (critical > high > medium > low > info) then Confidence
        candidates.sort((a, b) => {
            const wa = SEVERITY_WEIGHTS[a.severity.toLowerCase()] || 1;
            const wb = SEVERITY_WEIGHTS[b.severity.toLowerCase()] || 1;
            if (wb !== wa) return wb - wa;
            return b.confidence - a.confidence;
        });

        // Filter duplicates against message suppression buffer
        const filtered = [];
        for (const item of candidates) {
            const msgLast = this._messageCooldowns[item.message] || 0.0;
            const msgCooldown = this._getSeverityCooldown(item.severity);
            if ((now - msgLast) >= msgCooldown) {
                filtered.push(item);
                this._ruleCooldowns[item.rule_triggered] = now;
                this._messageCooldowns[item.message] = now;
            }
        }

        const maxQueue = this.config.settings?.max_active_feedback_queue || 5;
        const result = filtered.slice(0, maxQueue);

        this._processingTimeMs = performance.now() - t0;
        return result;
    }

    _evaluateAndPublishFeedback() {
        const newFeedback = this.evaluateFeedbackRules();
        if (!newFeedback || newFeedback.length === 0) return;

        this._activeFeedback = newFeedback;
        this._generatedCount += newFeedback.length;

        for (const item of newFeedback) {
            this._publish("feedback.generated", item);
        }

        this._publish("feedback.updated", {
            active_feedback: this._activeFeedback,
            count: this._activeFeedback.length
        });
    }

    _generateAndPublishSessionSummary(data) {
        const report = this._lastScoreReport;
        const sessionId  = data?.session_id || data?.sessionId || "session_unknown";
        const exerciseId = report?.exercise_id || report?.exerciseId || "unknown";

        const strengths = [];
        const weakAreas = [];
        const commonMistakes = [];
        const improvementAreas = [];

        if (report && report.components) {
            for (const [dim, comp] of Object.entries(report.components)) {
                if (comp && comp.score !== null && comp.score !== undefined) {
                    const score = Number(comp.score);
                    if (score >= 80.0) {
                        strengths.push(`Strong ${dim.toUpperCase()} performance (${score.toFixed(1)}/100)`);
                    } else if (score < 60.0) {
                        weakAreas.push(`${dim.toUpperCase()} needs attention (${score.toFixed(1)}/100)`);
                        improvementAreas.push(`Focus on improving ${dim} consistency`);
                    }
                }
            }
        }

        if (report && report.rep_scores) {
            const lowReps = report.rep_scores.filter(r => (r.overall_score ?? r.overallScore ?? 100) < 65.0);
            if (lowReps.length > 0) {
                commonMistakes.push(`Form dropped on ${lowReps.length} repetition(s)`);
            }
        }

        if (strengths.length === 0) strengths.push("Session completed successfully");
        if (weakAreas.length === 0) weakAreas.push("No critical weaknesses detected");
        if (improvementAreas.length === 0) improvementAreas.push("Maintain steady pace and posture");

        const summary = {
            session_id: sessionId,
            exercise_id: exerciseId,
            strengths: strengths,
            weak_areas: weakAreas,
            common_mistakes: commonMistakes,
            improvement_areas: improvementAreas,
            schema_version: "2.0.0",
            source: this.name
        };

        this._publish("feedback.session_summary", summary);
    }

    _getSeverityCooldown(severity) {
        const settings = this.config.settings || {};
        const sev = (severity || "").toLowerCase();
        if (sev === "critical") return Number(settings.critical_severity_cooldown_seconds || 1.0);
        if (sev === "high") return Number(settings.high_severity_cooldown_seconds || 2.5);
        return Number(settings.default_cooldown_seconds || 4.0);
    }

    _subscribe(eventName, handler) {
        if (this.eventBus && typeof this.eventBus.subscribe === 'function') {
            this.eventBus.subscribe(eventName, handler);
            this._handlers.push({ eventName, handler });
        }
    }

    _publish(eventName, data) {
        if (this.eventBus && typeof this.eventBus.publish === 'function') {
            this.eventBus.publish(eventName, data);
        }
    }

    getDiagnostics() {
        let highestSeverity = "info";
        if (this._activeFeedback.length > 0) {
            const topFb = this._activeFeedback.reduce((max, f) => {
                const wa = SEVERITY_WEIGHTS[(f.severity || "").toLowerCase()] || 1;
                const wm = SEVERITY_WEIGHTS[(max.severity || "").toLowerCase()] || 1;
                return wa > wm ? f : max;
            }, this._activeFeedback[0]);
            highestSeverity = topFb.severity;
        }

        const lastMsg = this._activeFeedback[0]?.message || "None";

        return {
            name: this.name,
            version: this.version,
            status: this.status,
            priority: this.priority,
            dependencies: this.dependencies,
            metrics: {
                generatedCount: this._generatedCount,
                activeFeedbackCount: this._activeFeedback.length,
                highestSeverity: highestSeverity,
                lastFeedbackMessage: lastMsg,
                generationLatencyMs: Number(this._processingTimeMs.toFixed(2)),
                activeRulesCount: (this.config.rules || []).length
            }
        };
    }
}
