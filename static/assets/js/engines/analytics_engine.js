/**
 * AnalyticsEngine
 * ===============
 * Production-grade, browser-side Analytics & User Progress Engine for PostureSense v2.
 *
 * Priority    : 10
 * Dependencies: feedback_engine, scoring_engine, movement_engine, pose_rule_engine, biomechanics_engine
 * Subscribes  : score.session_completed  (ScoreReport / session summary)
 *               score.exercise_completed (ScoreReport)
 *               score.rep_completed       (ScoreReport / rep data)
 *               feedback.session_summary (FeedbackSessionSummary)
 *               exercise.completed       (ExerciseResult)
 * Publishes   : analytics.session_completed
 *               analytics.updated
 *               analytics.trend_detected
 *               analytics.record_broken
 *               analytics.progress_updated
 *
 * DO NOT process camera frames or raw landmarks.
 * DO NOT generate coaching advice or feedback.
 * DO NOT calculate or alter scores.
 * DO NOT use ML for trend classification.
 * DO NOT persist raw video or landmark streams.
 */

export class AnalyticsEngine {
    constructor(eventBus = null) {
        this.name = "AnalyticsEngine";
        this.version = "2.0.0";
        this.eventBus = eventBus;
        this.status = "uninitialized";
        this.priority = 10;
        this.dependencies = ["feedback_engine", "scoring_engine", "movement_engine", "pose_rule_engine", "biomechanics_engine"];

        this.config = {
            version: "2.0.0",
            settings: {
                min_trend_observations: 3,
                improvement_threshold_pct: 2.0,
                decline_threshold_pct: -2.0,
                min_quality_confidence: 0.4
            }
        };

        this._activeUserId = "anonymous";
        this._sessions = [];
        this._exerciseAnalytics = {};
        this._personalRecords = {};

        this._sessionsProcessedCount = 0;
        this._recordsBrokenCount = 0;
        this._processingTimeMs = 0.0;
        this._lastScoreReport = null;
        this._handlers = [];
    }

    async initialize(config = null) {
        if (config) {
            Object.assign(this.config, config);
        }

        if (this.eventBus) {
            this._subscribe('score.session_completed',  e => this._onScoreSessionCompleted(e));
            this._subscribe('score.exercise_completed', e => this._onScoreExerciseCompleted(e));
            this._subscribe('score.rep_completed',      e => this._onScoreRepCompleted(e));
            this._subscribe('feedback.session_summary', e => this._onFeedbackSessionSummary(e));
            this._subscribe('exercise.completed',     e => this._onExerciseCompleted(e));
        }

        this.status = "initialized";
        this._publish("analytics.initialized", this.getDiagnostics());
        return true;
    }

    async start() {
        this.status = "running";
        this._publish("analytics.started", this.getDiagnostics());
        return true;
    }

    async pause() {
        this.status = "paused";
        this._publish("analytics.paused", this.getDiagnostics());
        return true;
    }

    async resume() {
        this.status = "running";
        this._publish("analytics.resumed", this.getDiagnostics());
        return true;
    }

    async stop() {
        this.status = "stopped";
        this._publish("analytics.stopped", this.getDiagnostics());
        return true;
    }

    async dispose() {
        this.status = "disposed";
        this._sessions = [];
        this._exerciseAnalytics = {};
        this._personalRecords = {};
        this._lastScoreReport = null;
        this._publish("analytics.disposed", this.getDiagnostics());
        return true;
    }

    setActiveUser(userId) {
        this._activeUserId = userId ? String(userId) : "anonymous";
    }

    // ---------------------------------------------------------------------------
    // Event Handlers
    // ---------------------------------------------------------------------------

    _onScoreSessionCompleted(event) {
        if (this.status !== 'running') return;
        this.recordSession(event.data || event);
    }

    _onScoreExerciseCompleted(event) {
        if (this.status !== 'running') return;
        this._lastScoreReport = event.data || event;
    }

    _onScoreRepCompleted(event) {
        if (this.status !== 'running') return;
    }

    _onFeedbackSessionSummary(event) {
        if (this.status !== 'running') return;
    }

    _onExerciseCompleted(event) {
        if (this.status !== 'running') return;
        this.recordSession(event.data || event);
    }

    // ---------------------------------------------------------------------------
    // Core Session Analytics & Records
    // ---------------------------------------------------------------------------

    recordSession(payload) {
        const t0 = performance.now();
        const report = this._lastScoreReport;

        const sessionId   = payload?.session_id || payload?.sessionId || `sess_${Date.now()}`;
        const exerciseId  = report?.exercise_id || payload?.exercise_id || "unknown";
        const duration    = Number(payload?.duration || report?.session_summary?.duration || 0.0);
        const avgScore    = Number(payload?.average_score ?? report?.overall_score ?? report?.overallScore ?? 0.0);
        let bestScore   = avgScore;
        let worstScore  = avgScore;
        let reps        = Number(payload?.completed_reps || payload?.total_reps || 0);

        if (report?.rep_scores && report.rep_scores.length > 0) {
            reps = report.rep_scores.length;
            const scores = report.rep_scores.map(r => r.overall_score ?? r.overallScore ?? 0.0);
            bestScore  = Math.max(...scores);
            worstScore = Math.min(...scores);
        }

        const session = {
            session_id: sessionId,
            user_id: this._activeUserId,
            timestamp: new Date().toISOString(),
            duration: Number(duration.toFixed(1)),
            exercise_id: exerciseId,
            completed_reps: reps,
            average_score: Number(avgScore.toFixed(1)),
            best_score: Number(bestScore.toFixed(1)),
            worst_score: Number(worstScore.toFixed(1)),
            tracking_quality: Number(report?.components?.tracking_quality?.score ?? 100.0)
        };

        this._sessions.push(session);
        this._sessionsProcessedCount++;

        // Update Exercise Analytics
        this._updateExerciseAnalytics(session, report);

        // Evaluate Personal Records
        this._evaluatePersonalRecords(session, report);

        // Compute Trends
        const trends = this.computeTrends();

        this._processingTimeMs = performance.now() - t0;

        this._publish("analytics.session_completed", session);
        this._publish("analytics.updated", this.getSummary());
        this._publish("analytics.progress_updated", {
            user_id: this._activeUserId,
            session_id: sessionId,
            overall_score: avgScore,
            trends_count: Object.keys(trends).length
        });

        return session;
    }

    _updateExerciseAnalytics(session, report) {
        const exId = session.exercise_id;
        const prev = this._exerciseAnalytics[exId];

        const totalSessions = prev ? prev.total_sessions + 1 : 1;
        const totalReps     = prev ? prev.total_repetitions + session.completed_reps : session.completed_reps;
        const bestScore     = Math.max(prev?.best_score || 0.0, session.average_score);
        const prevAvg       = prev?.average_score || session.average_score;
        const avgScore      = (prevAvg * (totalSessions - 1) + session.average_score) / totalSessions;

        const compRom  = Number(report?.components?.rom?.score ?? 0.0);
        const compForm = Number(report?.components?.form?.score ?? 0.0);
        const compStab = Number(report?.components?.stability?.score ?? 0.0);
        const compSymm = Number(report?.components?.symmetry?.score ?? 0.0);

        const bestRom  = Math.max(prev?.best_rom || 0.0, compRom);
        const avgRom   = prev ? (prev.average_rom * (totalSessions - 1) + compRom) / totalSessions : compRom;
        const avgForm  = prev ? (prev.average_form * (totalSessions - 1) + compForm) / totalSessions : compForm;
        const avgStab  = prev ? (prev.average_stability * (totalSessions - 1) + compStab) / totalSessions : compStab;
        const avgSymm  = prev ? (prev.average_symmetry * (totalSessions - 1) + compSymm) / totalSessions : compSymm;

        let impPct = 0.0;
        if (prev && prev.average_score > 0) {
            impPct = ((avgScore - prev.average_score) / prev.average_score) * 100.0;
        }

        this._exerciseAnalytics[exId] = {
            exercise_id: exId,
            total_sessions: totalSessions,
            total_repetitions: totalReps,
            best_score: Number(bestScore.toFixed(1)),
            average_score: Number(avgScore.toFixed(1)),
            best_rom: Number(bestRom.toFixed(1)),
            average_rom: Number(avgRom.toFixed(1)),
            average_stability: Number(avgStab.toFixed(1)),
            average_symmetry: Number(avgSymm.toFixed(1)),
            average_form: Number(avgForm.toFixed(1)),
            improvement_percentage: Number(impPct.toFixed(1)),
            last_performed: new Date().toISOString()
        };
    }

    _evaluatePersonalRecords(session, report) {
        const candidates = [
            ["Highest Score", session.average_score, "points"],
            ["Most Reps", session.completed_reps, "reps"]
        ];

        if (report?.components?.rom?.score !== undefined) candidates.push(["Best ROM", Number(report.components.rom.score), "%"]);
        if (report?.components?.stability?.score !== undefined) candidates.push(["Best Stability", Number(report.components.stability.score), "%"]);
        if (report?.components?.symmetry?.score !== undefined) candidates.push(["Best Symmetry", Number(report.components.symmetry.score), "%"]);

        for (const [rType, val, unit] of candidates) {
            const prev = this._personalRecords[rType];
            const prevVal = prev ? prev.value : null;

            if (prevVal === null || val > prevVal) {
                const newRec = {
                    record_type: rType,
                    exercise_id: session.exercise_id,
                    value: Number(val.toFixed(1)),
                    unit: unit,
                    previous_value: prevVal !== null ? Number(prevVal.toFixed(1)) : null,
                    achieved_at: new Date().toISOString()
                };
                this._personalRecords[rType] = newRec;
                if (prevVal !== null) {
                    this._recordsBrokenCount++;
                    this._publish("analytics.record_broken", newRec);
                }
            }
        }
    }

    computeTrends() {
        const minObs = this.config.settings?.min_trend_observations || 3;
        const scores = this._sessions.map(s => s.average_score);

        const [dir, slope, pctChange] = this._calculateStatisticalTrend(scores, minObs);

        const trend = {
            metric_name: "overall_score",
            timeframe: "session",
            trend_direction: dir,
            observation_count: scores.length,
            slope: Number(slope.toFixed(4)),
            percentage_change: Number(pctChange.toFixed(2)),
            sample_values: scores
        };

        if (dir !== "INSUFFICIENT_DATA") {
            this._publish("analytics.trend_detected", trend);
        }

        return { overall_score: trend };
    }

    _calculateStatisticalTrend(values, minObs) {
        const n = values.length;
        if (n < minObs) return ["INSUFFICIENT_DATA", 0.0, 0.0];

        const first = values[0];
        const last  = values[n - 1];
        const pctChange = first > 0 ? ((last - first) / first) * 100.0 : 0.0;

        const xMean = (n - 1) / 2.0;
        const yMean = values.reduce((a, b) => a + b, 0) / n;

        let num = 0.0;
        let den = 0.0;
        for (let i = 0; i < n; i++) {
            num += (i - xMean) * (values[i] - yMean);
            den += (i - xMean) ** 2;
        }
        const slope = den !== 0 ? num / den : 0.0;

        const upThresh   = Number(this.config.settings?.improvement_threshold_pct || 2.0);
        const downThresh = Number(this.config.settings?.decline_threshold_pct || -2.0);

        let direction = "STABLE";
        if (pctChange > upThresh || slope > 0.2) direction = "IMPROVING";
        else if (pctChange < downThresh || slope < -0.2) direction = "DECLINING";

        return [direction, slope, pctChange];
    }

    calculateStreak() {
        if (this._sessions.length === 0) return 0;
        const dates = [...new Set(this._sessions.map(s => s.timestamp.split("T")[0]))].sort();
        let streak = 1;
        for (let i = dates.length - 1; i > 0; i--) {
            const d1 = new Date(dates[i]);
            const d2 = new Date(dates[i - 1]);
            const diffDays = Math.round((d1 - d2) / (1000 * 60 * 60 * 24));
            if (diffDays === 1) streak++;
            else break;
        }
        return streak;
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

    getSummary() {
        const totalSessions = this._sessions.length;
        const totalDuration = this._sessions.reduce((acc, s) => acc + s.duration, 0.0);
        const overallAvg    = totalSessions > 0 ? this._sessions.reduce((acc, s) => acc + s.average_score, 0.0) / totalSessions : 0.0;

        return {
            user_id: this._activeUserId,
            total_sessions: totalSessions,
            total_duration: Number(totalDuration.toFixed(1)),
            overall_average_score: Number(overallAvg.toFixed(1)),
            streak_days: this.calculateStreak(),
            recent_sessions: this._sessions.slice(-10),
            exercise_history: this._exerciseAnalytics,
            active_trends: this.computeTrends(),
            personal_records: Object.values(this._personalRecords)
        };
    }

    getDiagnostics() {
        const latest = this._sessions.length > 0 ? this._sessions[this._sessions.length - 1].average_score : 0.0;
        const trends = this.computeTrends();

        return {
            name: this.name,
            version: this.version,
            status: this.status,
            priority: this.priority,
            dependencies: this.dependencies,
            metrics: {
                activeUserId: this._activeUserId,
                sessionsProcessedCount: this._sessionsProcessedCount,
                exercisesTrackedCount: Object.keys(this._exerciseAnalytics).length,
                personalRecordsCount: Object.keys(this._personalRecords).length,
                recordsBrokenCount: this._recordsBrokenCount,
                trendCount: Object.keys(trends).length,
                latestScore: Number(latest.toFixed(1)),
                analyticsLatencyMs: Number(this._processingTimeMs.toFixed(2))
            }
        };
    }
}
