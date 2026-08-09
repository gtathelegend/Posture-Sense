/**
 * ScoringEngine
 * ===============
 * Production-grade, configuration-driven browser-side Scoring Engine for PostureSense v2.
 *
 * Priority    : 8
 * Dependencies: movement_engine, biomechanics_engine, pose_rule_engine
 * Subscribes  : biomechanics.updated  (BiomechanicsSnapshot)
 *               pose.detected         (PoseResult)
 *               exercise.started      (ExerciseResult)
 *               exercise.phase_changed (ExerciseResult)
 *               exercise.rep_completed (ExerciseResult)
 *               exercise.completed    (ExerciseResult)
 * Publishes   : score.updated
 *               score.rep_completed
 *               score.exercise_completed
 *               score.session_completed
 *               score.unavailable
 *               score.quality_warning
 *
 * DO NOT implement posture scoring in movement engine.
 * DO NOT implement coaching feedback.
 * DO NOT use ML classifiers.
 */

export class ScoringEngine {
    constructor(eventBus = null) {
        this.name = "ScoringEngine";
        this.version = "2.0.0";
        this.eventBus = eventBus;
        this.status = "uninitialized";
        this.priority = 8;
        this.dependencies = ["movement_engine", "biomechanics_engine", "pose_rule_engine"];

        // Configuration
        this.config = {
            version: "2.0.0",
            default_weights: {
                form: 0.30,
                rom: 0.20,
                stability: 0.15,
                symmetry: 0.15,
                control: 0.10,
                tempo: 0.10
            },
            categories: {
                dynamic: {
                    form: 0.30,
                    rom: 0.20,
                    stability: 0.15,
                    symmetry: 0.15,
                    control: 0.10,
                    tempo: 0.10
                },
                static_hold: {
                    form: 0.25,
                    stability: 0.30,
                    symmetry: 0.20,
                    control: 0.15,
                    tracking_quality: 0.10
                }
            },
            score_bands: [
                { min: 90.0, max: 100.0, label: "Excellent" },
                { min: 75.0, max: 89.99, label: "Good" },
                { min: 60.0, max: 74.99, label: "Needs Improvement" },
                { min: 0.0,  max: 59.99, label: "Poor" }
            ],
            quality_gates: {
                min_tracking_quality: 50.0,
                min_pose_confidence: 0.4,
                min_landmark_visibility: 0.5,
                min_samples: 3
            }
        };

        // Internal State
        this._lastBiomechanics = null;
        this._lastPose = null;
        this._lastExercise = null;

        this._activeExerciseId = "unknown";
        this._activeExerciseName = "Unknown";
        this._exerciseCategory = "dynamic";

        this._repScores = [];
        this._sampleCount = 0;
        this._evaluationsCount = 0;
        this._processingTimeMs = 0.0;
        this._lastScoreReport = null;

        this._sessionStartTime = 0.0;
        this._completedRepsCount = 0;
        this._invalidRepsCount = 0;

        this._handlers = [];
    }

    async initialize(config = null) {
        if (config) {
            Object.assign(this.config, config);
        }

        if (this.eventBus) {
            this._subscribe('biomechanics.updated',  e => this._onBiomechanicsUpdated(e));
            this._subscribe('pose.detected',         e => this._onPoseDetected(e));
            this._subscribe('exercise.started',      e => this._onExerciseStarted(e));
            this._subscribe('exercise.phase_changed', e => this._onExercisePhaseChanged(e));
            this._subscribe('exercise.rep_completed', e => this._onRepCompleted(e));
            this._subscribe('exercise.completed',    e => this._onExerciseCompleted(e));
        }

        this.status = "initialized";
        this._publish("score.initialized", this.getDiagnostics());
        return true;
    }

    async start() {
        this.status = "running";
        this._sessionStartTime = Date.now() / 1000.0;
        this._publish("score.started", this.getDiagnostics());
        return true;
    }

    async pause() {
        this.status = "paused";
        this._publish("score.paused", this.getDiagnostics());
        return true;
    }

    async resume() {
        this.status = "running";
        this._publish("score.resumed", this.getDiagnostics());
        return true;
    }

    async stop() {
        this.status = "stopped";
        this._publish("score.stopped", this.getDiagnostics());
        return true;
    }

    async dispose() {
        this.status = "disposed";
        this._repScores = [];
        this._lastBiomechanics = null;
        this._lastPose = null;
        this._lastExercise = null;
        this._lastScoreReport = null;
        this._publish("score.disposed", this.getDiagnostics());
        return true;
    }

    // ---------------------------------------------------------------------------
    // Event Handlers
    // ---------------------------------------------------------------------------

    _onBiomechanicsUpdated(event) {
        if (this.status !== 'running') return;
        this._lastBiomechanics = event.data || event;
        this._evaluateAndPublish();
    }

    _onPoseDetected(event) {
        if (this.status !== 'running') return;
        this._lastPose = event.data || event;
    }

    _onExerciseStarted(event) {
        if (this.status !== 'running') return;
        const data = event.data || event || {};
        this._activeExerciseId   = data.exercise_id || data.exerciseId || "unknown";
        this._activeExerciseName = data.exercise_name || data.exerciseName || "Unknown";
        this._exerciseCategory   = data.category || "dynamic";
        this._repScores = [];
        this._completedRepsCount = 0;
        this._invalidRepsCount   = 0;
    }

    _onExercisePhaseChanged(event) {
        if (this.status !== 'running') return;
        this._lastExercise = event.data || event;
        if (this._lastExercise) {
            this._activeExerciseId   = this._lastExercise.exercise_id || this._lastExercise.exerciseId || this._activeExerciseId;
            this._activeExerciseName = this._lastExercise.exercise_name || this._lastExercise.exerciseName || this._activeExerciseName;
        }
        this._evaluateAndPublish();
    }

    _onRepCompleted(event) {
        if (this.status !== 'running') return;
        const exRes = event.data || event;
        this._lastExercise = exRes;
        this._completedRepsCount++;

        const report = this.evaluateScore();
        const repData = {
            rep_number: exRes.rep_count || exRes.repCount || this._completedRepsCount,
            overall_score: report.overall_score,
            form_score: report.components?.form?.score ?? report.overall_score,
            rom: report.components?.rom?.score ?? 0.0,
            stability: report.components?.stability?.score ?? 0.0,
            control: report.components?.control?.score ?? 0.0,
            duration: exRes.current_rep_duration || exRes.currentRepDuration || 0.0,
            quality: exRes.movement_quality || exRes.movementQuality || 100.0
        };
        this._repScores.push(repData);

        this._publish("score.rep_completed", {
            rep_score: repData,
            score_report: report
        });
    }

    _onExerciseCompleted(event) {
        if (this.status !== 'running') return;
        const finalReport = this.evaluateScore();
        this._publish("score.exercise_completed", finalReport);
        this._publish("score.session_completed", {
            session_summary: finalReport.session_summary,
            score_report: finalReport
        });
    }

    // ---------------------------------------------------------------------------
    // Scoring Calculation
    // ---------------------------------------------------------------------------

    evaluateScore() {
        const t0 = performance.now();
        this._evaluationsCount++;
        this._sampleCount++;

        // Quality Gate Check
        const trackingQuality = this._lastExercise?.tracking_quality ?? this._lastExercise?.trackingQuality ?? 100.0;
        let poseConfidence  = this._lastPose?.confidence ?? 1.0;
        if (poseConfidence > 1.0) poseConfidence /= 100.0;

        const qGates = this.config.quality_gates || {};
        const minTq  = qGates.min_tracking_quality ?? 50.0;
        const minPc  = qGates.min_pose_confidence ?? 0.4;

        let qualityGatePassed = true;
        let qualityWarning = null;

        if (trackingQuality < minTq) {
            qualityGatePassed = false;
            qualityWarning = `Tracking quality low (${trackingQuality.toFixed(1)}% < ${minTq}%)`;
        } else if (poseConfidence < minPc) {
            qualityGatePassed = false;
            qualityWarning = `Pose confidence low (${poseConfidence.toFixed(2)} < ${minPc})`;
        }

        // Active Weights Profile
        const exWeights = this.config.categories?.[this._exerciseCategory] || this.config.default_weights;

        // Raw Component Normalization
        const rawComponents = this._extractRawDimensions();
        const evaluatedComponents = {};
        const missingMetrics = [];
        let activeWeightsSum = 0.0;

        for (const [dim, weight] of Object.entries(exWeights)) {
            if (rawComponents[dim] !== null && rawComponents[dim] !== undefined) {
                const val = Math.max(0.0, Math.min(100.0, Number(rawComponents[dim])));
                const status = this._getMetricStatus(val);
                evaluatedComponents[dim] = {
                    score: Number(val.toFixed(1)),
                    weight: weight,
                    status: status,
                    raw_value: Number(val.toFixed(2)),
                    contribution: 0.0,
                    explainability: `${dim.toUpperCase()} evaluated at ${val.toFixed(1)}/100 (${status})`
                };
                activeWeightsSum += weight;
            } else {
                missingMetrics.push(dim);
                evaluatedComponents[dim] = {
                    score: null,
                    weight: weight,
                    status: "UNAVAILABLE",
                    raw_value: null,
                    contribution: 0.0,
                    explainability: `Metric ${dim} is unavailable due to missing input data`
                };
            }
        }

        // Aggregate Overall Score
        let overallScore = 0.0;
        if (activeWeightsSum > 1e-6) {
            for (const [dim, item] of Object.entries(evaluatedComponents)) {
                if (item.status !== "UNAVAILABLE" && item.score !== null) {
                    const effectiveWeight = item.weight / activeWeightsSum;
                    const contrib = item.score * effectiveWeight;
                    item.contribution = Number(contrib.toFixed(2));
                    overallScore += contrib;
                }
            }
        } else {
            overallScore = 0.0;
            qualityGatePassed = false;
            qualityWarning = "All scoring metrics are unavailable";
        }
        overallScore = Math.max(0.0, Math.min(100.0, overallScore));

        // Score Band
        let categoryLabel = this._mapScoreBand(overallScore);
        if (!qualityGatePassed && activeWeightsSum <= 1e-6) {
            categoryLabel = "Unavailable";
        }

        // Score Confidence
        const totalDims = Object.keys(evaluatedComponents).length || 1;
        const availableRatio = (totalDims - missingMetrics.length) / totalDims;
        let scoreConfidence = (trackingQuality / 100.0) * 0.4 + poseConfidence * 0.3 + availableRatio * 0.3;
        scoreConfidence = Math.max(0.0, Math.min(1.0, scoreConfidence));

        // Hold Score
        let holdScore = null;
        if (this._exerciseCategory === "static_hold" || (this._lastExercise && (this._lastExercise.hold_time || this._lastExercise.holdTime) > 0)) {
            holdScore = {
                hold_stability: evaluatedComponents.stability?.score ?? 100.0,
                alignment: evaluatedComponents.symmetry?.score ?? 100.0,
                balance: this._lastBiomechanics?.balance_score ?? this._lastBiomechanics?.balanceScore ?? 100.0,
                duration: this._lastExercise?.hold_time ?? this._lastExercise?.holdTime ?? 0.0,
                tracking_quality: trackingQuality
            };
        }

        // Session Summary
        const sessionSummary = this._buildSessionSummary(overallScore);

        const report = {
            overall_score: Number(overallScore.toFixed(1)),
            score_confidence: Number(scoreConfidence.toFixed(2)),
            category: categoryLabel,
            components: evaluatedComponents,
            exercise_id: this._activeExerciseId,
            exercise_name: this._activeExerciseName,
            rep_scores: [...this._repScores],
            hold_score: holdScore,
            session_summary: sessionSummary,
            missing_metrics: missingMetrics,
            quality_gate_passed: qualityGatePassed,
            quality_warning: qualityWarning,
            // Backward-compat aliases
            posture_score: evaluatedComponents.form?.score ?? Number(overallScore.toFixed(1)),
            alignment_score: evaluatedComponents.symmetry?.score ?? Number(overallScore.toFixed(1)),
            stability_score: evaluatedComponents.stability?.score ?? Number(overallScore.toFixed(1)),
            schema_version: "2.0.0",
            source: this.name
        };

        this._processingTimeMs = performance.now() - t0;
        this._lastScoreReport = report;
        return report;
    }

    _evaluateAndPublish() {
        const report = this.evaluateScore();
        if (!report.quality_gate_passed && report.quality_warning) {
            this._publish("score.quality_warning", {
                warning: report.quality_warning,
                score_confidence: report.score_confidence
            });
        }
        if (report.category === "Unavailable" || report.missing_metrics.length === Object.keys(report.components).length) {
            this._publish("score.unavailable", {
                missing_metrics: report.missing_metrics,
                exercise_id: report.exercise_id
            });
        }
        this._publish("score.updated", report);
    }

    _extractRawDimensions() {
        const res = {};

        // Form
        if (this._lastExercise) {
            res.form = Number(this._lastExercise.movement_quality ?? this._lastExercise.movementQuality ?? 100.0);
        } else if (this._lastPose) {
            let conf = this._lastPose.confidence ?? 1.0;
            if (conf <= 1.0) conf *= 100.0;
            res.form = conf;
        } else {
            res.form = null;
        }

        // ROM
        if (this._lastExercise) {
            res.rom = Number(this._lastExercise.rom_percentage ?? this._lastExercise.romPercentage ?? 0.0);
        } else {
            res.rom = null;
        }

        // Stability
        if (this._lastBiomechanics) {
            res.stability = Number(this._lastBiomechanics.balance_score ?? this._lastBiomechanics.balanceScore ?? 100.0);
        } else {
            res.stability = null;
        }

        // Symmetry
        if (this._lastBiomechanics) {
            res.symmetry = Number(this._lastBiomechanics.symmetry_score ?? this._lastBiomechanics.symmetryScore ?? 100.0);
        } else {
            res.symmetry = null;
        }

        // Control
        if (this._lastExercise) {
            const dur = Number(this._lastExercise.current_rep_duration ?? this._lastExercise.currentRepDuration ?? 0.0);
            const avg = Number(this._lastExercise.average_rep_duration ?? this._lastExercise.averageRepDuration ?? 0.0);
            if (avg > 0 && dur > 0) {
                const dev = Math.abs(dur - avg) / avg;
                res.control = Math.max(0.0, 100.0 - (dev * 50.0));
            } else {
                res.control = Number(this._lastExercise.movement_quality ?? this._lastExercise.movementQuality ?? 100.0);
            }
        } else {
            res.control = null;
        }

        // Tempo
        if (this._lastExercise) {
            const cad = Number(this._lastExercise.current_cadence ?? this._lastExercise.currentCadence ?? 0.0);
            if (cad > 0) {
                if (cad >= 10.0 && cad <= 40.0) {
                    res.tempo = 100.0;
                } else {
                    const diff = Math.min(Math.abs(cad - 10.0), Math.abs(cad - 40.0));
                    res.tempo = Math.max(0.0, 100.0 - (diff * 2.5));
                }
            } else {
                res.tempo = null;
            }
        } else {
            res.tempo = null;
        }

        // Consistency
        if (this._repScores.length >= 2) {
            const scores = this._repScores.map(r => r.overall_score);
            const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
            const variance = scores.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / scores.length;
            res.consistency = Math.max(0.0, 100.0 - (Math.sqrt(variance) * 3.0));
        } else if (this._repScores.length === 1) {
            res.consistency = 100.0;
        } else {
            res.consistency = null;
        }

        // Tracking Quality
        if (this._lastExercise) {
            res.tracking_quality = Number(this._lastExercise.tracking_quality ?? this._lastExercise.trackingQuality ?? 100.0);
        } else {
            res.tracking_quality = null;
        }

        return res;
    }

    _getMetricStatus(score) {
        if (score >= 80.0) return "GOOD";
        if (score >= 60.0) return "WARNING";
        return "POOR";
    }

    _mapScoreBand(score) {
        for (const band of this.config.score_bands) {
            if (score >= band.min && score <= band.max) {
                return band.label;
            }
        }
        if (score >= 90.0) return "Excellent";
        if (score >= 75.0) return "Good";
        if (score >= 60.0) return "Needs Improvement";
        return "Poor";
    }

    _buildSessionSummary(currentOverall) {
        const scores = this._repScores.map(r => r.overall_score);
        if (scores.length === 0) scores.push(currentOverall);

        const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
        const best = Math.max(...scores);
        const worst = Math.min(...scores);
        const variance = scores.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / scores.length;
        const duration = this._sessionStartTime > 0 ? (Date.now() / 1000.0 - this._sessionStartTime) : 0.0;

        return {
            avg_score: Number(avg.toFixed(1)),
            best_rep_score: Number(best.toFixed(1)),
            worst_rep_score: Number(worst.toFixed(1)),
            score_variance: Number(variance.toFixed(2)),
            consistency_score: Number(Math.max(0.0, 100.0 - (Math.sqrt(variance) * 3.0)).toFixed(1)),
            completed_reps: this._completedRepsCount,
            invalid_reps: this._invalidRepsCount,
            duration_seconds: Number(duration.toFixed(1)),
            exercise_id: this._activeExerciseId,
            exercise_name: this._activeExerciseName
        };
    }

    // PubSub helpers
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
        const report = this._lastScoreReport;
        return {
            name: this.name,
            version: this.version,
            status: this.status,
            priority: this.priority,
            dependencies: this.dependencies,
            metrics: {
                evaluationsCount: this._evaluationsCount,
                sampleCount: this._sampleCount,
                processingTimeMs: Number(this._processingTimeMs.toFixed(2)),
                activeExerciseId: this._activeExerciseId,
                activeExerciseName: this._activeExerciseName,
                exerciseCategory: this._exerciseCategory,
                completedReps: this._completedRepsCount,
                overallScore: report ? report.overall_score : 0.0,
                scoreConfidence: report ? report.score_confidence : 1.0,
                scoreBand: report ? report.category : "Standby",
                missingMetricsCount: report ? report.missing_metrics.length : 0
            }
        };
    }
}
