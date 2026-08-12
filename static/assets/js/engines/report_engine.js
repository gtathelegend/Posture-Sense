/**
 * ReportEngine
 * ============
 * Production-grade, browser-side Reports & Export Engine for PostureSense v2.
 *
 * Priority    : 11
 * Dependencies: analytics_engine, feedback_engine, scoring_engine, movement_engine, pose_rule_engine, biomechanics_engine
 * Publishes   : report.generated
 *               report.exported
 *
 * DO NOT recalculate biomechanics, scores, pose rules, or analytics.
 * DO NOT generate new coaching advice or feedback.
 * DO NOT process camera frames or raw landmarks.
 * DO NOT introduce ML or create a second analytics system.
 * DO NOT persist raw video or landmark streams.
 */

export class ReportEngine {
    constructor(eventBus = null) {
        this.name = "ReportEngine";
        this.version = "2.0.0";
        this.eventBus = eventBus;
        this.status = "uninitialized";
        this.priority = 11;
        this.dependencies = ["analytics_engine", "feedback_engine", "scoring_engine", "movement_engine", "pose_rule_engine", "biomechanics_engine"];

        this.config = {
            version: "2.0.0",
            application_name: "PostureSense AI Pipeline"
        };

        this._activeUserId = "anonymous";
        this._reportsGeneratedCount = 0;
        this._lastExportFormat = "json";
        this._processingTimeMs = 0.0;
        this._handlers = [];
    }

    async initialize(config = null) {
        if (config) {
            Object.assign(this.config, config);
        }

        this.status = "initialized";
        this._publish("report.initialized", this.getDiagnostics());
        return true;
    }

    async start() {
        this.status = "running";
        this._publish("report.started", this.getDiagnostics());
        return true;
    }

    async pause() {
        this.status = "paused";
        this._publish("report.paused", this.getDiagnostics());
        return true;
    }

    async resume() {
        this.status = "running";
        this._publish("report.resumed", this.getDiagnostics());
        return true;
    }

    async stop() {
        this.status = "stopped";
        this._publish("report.stopped", this.getDiagnostics());
        return true;
    }

    async dispose() {
        this.status = "disposed";
        this._publish("report.disposed", this.getDiagnostics());
        return true;
    }

    setActiveUser(userId) {
        this._activeUserId = userId ? String(userId) : "anonymous";
    }

    // ---------------------------------------------------------------------------
    // Composition Routines
    // ---------------------------------------------------------------------------

    generateSessionReport(sessionData = {}, scoreReport = null, feedbackItems = []) {
        const t0 = performance.now();
        const sessionId = sessionData.session_id || sessionData.sessionId || `sess_${Date.now()}`;

        const report = {
            metadata: {
                report_type: "session",
                user_id: this._activeUserId,
                generated_at: new Date().toISOString(),
                schema_version: "2.0.0",
                source_data_version: "2.0.0"
            },
            session_info: {
                session_id: sessionId,
                exercise_id: sessionData.exercise_id || "unknown",
                duration: sessionData.duration || 0.0,
                completed_reps: sessionData.completed_reps || 0
            },
            performance: {
                overall_score: sessionData.average_score ?? scoreReport?.overall_score ?? 0.0,
                category: scoreReport?.category || "Evaluated",
                components: scoreReport?.components || {}
            },
            assessment: {
                feedback_messages: feedbackItems || [],
                strengths: scoreReport?.components ? Object.keys(scoreReport.components).filter(k => scoreReport.components[k].score >= 80) : []
            },
            data_quality: {
                tracking_quality: sessionData.tracking_quality || 100.0,
                quality_gate_passed: scoreReport?.quality_gate_passed ?? True,
                confidence: scoreReport?.score_confidence ?? 1.0
            }
        };

        this._reportsGeneratedCount++;
        this._processingTimeMs = performance.now() - t0;
        this._publish("report.generated", report);
        return report;
    }

    exportJson(reportDict) {
        const t0 = performance.now();
        const repType = reportDict.metadata?.report_type || "session";
        const filename = `posturesense_${repType}_report_${Date.now()}.json`;
        const content = JSON.stringify(reportDict, null, 2);

        const res = {
            report_type: repType,
            format: "json",
            filename: filename,
            content: content,
            content_type: "application/json"
        };

        this._lastExportFormat = "json";
        this._processingTimeMs = performance.now() - t0;
        this._publish("report.exported", res);
        return res;
    }

    exportCsv(sessionsList = []) {
        const t0 = performance.now();
        const filename = `posturesense_progress_${Date.now()}.csv`;

        let csvStr = "Date,Exercise,Score,ROM,Stability,Symmetry,Cadence,Repetitions,Duration,Tracking Quality\n";
        for (const s of sessionsList) {
            csvStr += `${s.timestamp || "N/A"},${s.exercise_id || "unknown"},${s.average_score || 0.0},${s.rom || "N/A"},${s.stability || "N/A"},${s.symmetry || "N/A"},${s.cadence || "N/A"},${s.completed_reps || 0},${s.duration || 0.0},${s.tracking_quality || 100.0}\n`;
        }

        const res = {
            report_type: "progress_csv",
            format: "csv",
            filename: filename,
            content: csvStr,
            content_type: "text/csv"
        };

        this._lastExportFormat = "csv";
        this._processingTimeMs = performance.now() - t0;
        this._publish("report.exported", res);
        return res;
    }

    exportPdf(reportDict) {
        const t0 = performance.now();
        const repType = (reportDict.metadata?.report_type || "session").toUpperCase();
        const filename = `posturesense_${repType.toLowerCase()}_report_${Date.now()}.pdf.html`;

        const html = `<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>PostureSense AI — ${repType} REPORT</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; }
        .header { border-bottom: 2px solid #38bdf8; padding-bottom: 10px; }
        .score { font-size: 32px; font-weight: bold; color: #4ade80; }
    </style>
</head>
<body>
    <div class="header">
        <h2>🏆 PostureSense AI Performance Report</h2>
        <p>Type: ${repType} | User: ${reportDict.metadata?.user_id || "anonymous"} | Generated: ${new Date().toISOString()}</p>
    </div>
    <div>
        <h3>Overall Performance Score</h3>
        <div class="score">${reportDict.performance?.overall_score || 0.0} / 100</div>
    </div>
</body>
</html>`;

        const res = {
            report_type: repType.toLowerCase(),
            format: "pdf",
            filename: filename,
            content: html,
            content_type: "application/pdf"
        };

        this._lastExportFormat = "pdf";
        this._processingTimeMs = performance.now() - t0;
        this._publish("report.exported", res);
        return res;
    }

    _publish(eventName, data) {
        if (this.eventBus && typeof this.eventBus.publish === 'function') {
            this.eventBus.publish(eventName, data);
        }
    }

    getDiagnostics() {
        return {
            name: this.name,
            version: this.version,
            status: this.status,
            priority: this.priority,
            dependencies: this.dependencies,
            metrics: {
                activeUserId: this._activeUserId,
                reportsGeneratedCount: this._reportsGeneratedCount,
                lastExportFormat: this._lastExportFormat,
                processingLatencyMs: Number(this._processingTimeMs.toFixed(2))
            }
        };
    }
}
