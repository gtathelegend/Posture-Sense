/**
 * LandmarkEngine
 * Production-grade landmark validation, temporal smoothing, body coverage analysis,
 * and tracking quality classification engine for PostureSense v2.
 * Consumes raw LandmarkSet events, enforces visibility/presence thresholds,
 * classifies tracking state (FULL_BODY, PARTIAL_BODY, NO_TRACKING), and publishes ValidatedLandmarkSet contracts.
 */

const REQUIRED_BODY_LANDMARKS = [
    { name: 'nose', index: 0, region: 'head' },
    { name: 'left_shoulder', index: 11, region: 'shoulders' },
    { name: 'right_shoulder', index: 12, region: 'shoulders' },
    { name: 'left_hip', index: 23, region: 'torso' },
    { name: 'right_hip', index: 24, region: 'torso' },
    { name: 'left_knee', index: 25, region: 'legs' },
    { name: 'right_knee', index: 26, region: 'legs' },
    { name: 'left_ankle', index: 27, region: 'legs' },
    { name: 'right_ankle', index: 28, region: 'legs' }
];

export class LandmarkEngine {
    constructor(eventBus = null) {
        this.name = "LandmarkEngine";
        this.version = "2.0.0";
        this.eventBus = eventBus;
        this.status = "uninitialized";
        this.priority = 3;
        this.dependencies = ["mediapipe_engine"];

        // Configuration Parameters
        this.config = {
            visibilityThreshold: 0.6,
            presenceThreshold: 0.6,
            qualityThreshold: 60.0,
            fullBodyThreshold: 0.70,   // >=70% coverage -> FULL_BODY
            partialBodyThreshold: 0.30, // 30-70% coverage -> PARTIAL_BODY
            maxInterpolationFrames: 5,
            smoothingMethod: 'ema',     // 'ema', 'one_euro', 'none'
            emaAlpha: 0.35,
            oneEuroBeta: 0.007
        };

        // Historical state for smoothing & interpolation
        this.previousLandmarks = null;

        // Metrics & Diagnostics
        this.metrics = {
            framesAccepted: 0,
            framesRejected: 0,
            averageQualityScore: 100.0,
            jitterScore: 0.0,
            interpolationCount: 0,
            filterLatencyMs: 0.0,
            trackingState: 'NO_TRACKING', // 'FULL_BODY', 'PARTIAL_BODY', 'NO_TRACKING'
            bodyCoveragePct: 0.0,
            visibleLandmarksCount: 0,
            missingLandmarksCount: 0,
            visibleLandmarksList: [],
            missingLandmarksList: []
        };

        this.totalQualitySum = 0;
    }

    async initialize(config = {}) {
        Object.assign(this.config, config);
        this.status = "initialized";
        this._publish("landmark.initialized", this.getDiagnostics());
        return true;
    }

    async start() {
        this.status = "running";
        this._subscribeToRawLandmarks();
        this._publish("landmark.started", this.getDiagnostics());
        return true;
    }

    pause() {
        if (this.status === 'running') {
            this.status = "paused";
            this._publish("landmark.paused", this.getDiagnostics());
        }
    }

    resume() {
        if (this.status === 'paused') {
            this.status = "running";
            this._publish("landmark.resumed", this.getDiagnostics());
        }
    }

    async stop() {
        this.status = "stopped";
        this._publish("landmark.stopped", this.getDiagnostics());
    }

    dispose() {
        this.stop();
        this.status = "disposed";
        this._publish("landmark.disposed", this.getDiagnostics());
    }

    _subscribeToRawLandmarks() {
        if (this.eventBus && typeof this.eventBus.subscribe === 'function') {
            this.eventBus.subscribe('landmarks.detected', (event) => {
                if (this.status === 'running') {
                    this.processLandmarkSet(event.data || {});
                }
            });
        }
    }

    processLandmarkSet(rawLandmarkSet) {
        const startTime = performance.now();
        const rawLandmarks = rawLandmarkSet.landmarks || [];
        const confidence = rawLandmarkSet.confidence || 0.0;

        // Step 1: Annotate Landmark Confidence & Filter
        const annotatedLandmarks = this._annotateLandmarks(rawLandmarks);

        // Step 2: Body Coverage & Tracking State Classification
        const coverageAnalysis = this._analyzeBodyCoverage(annotatedLandmarks);
        this.metrics.bodyCoveragePct = coverageAnalysis.coveragePct;
        this.metrics.trackingState = coverageAnalysis.trackingState;
        this.metrics.visibleLandmarksList = coverageAnalysis.visibleList;
        this.metrics.missingLandmarksList = coverageAnalysis.missingList;
        this.metrics.visibleLandmarksCount = coverageAnalysis.visibleList.length;
        this.metrics.missingLandmarksCount = coverageAnalysis.missingList.length;

        // If NO_TRACKING, reject frame early
        if (coverageAnalysis.trackingState === 'NO_TRACKING') {
            this.metrics.framesRejected++;
            this._publish("landmarks.invalid", { reason: "Insufficient body visibility (<30%)" });
            this._publish("tracking.lost", { confidence: 0.0 });
            return null;
        }

        // Step 3: Missing Landmark Interpolation & Temporal Smoothing
        const interpolated = this._interpolateMissing(annotatedLandmarks);
        const smoothed = this._applySmoothing(interpolated);

        // Step 4: Quality Assessment & Jitter Metrics
        const qualityScore = this._calculateQualityScore(smoothed, confidence);
        const jitter = this._calculateJitter(smoothed);

        this.metrics.framesAccepted++;
        this.totalQualitySum += qualityScore;
        this.metrics.averageQualityScore = roundVal(this.totalQualitySum / this.metrics.framesAccepted, 1);
        this.metrics.jitterScore = roundVal(jitter, 3);
        this.metrics.filterLatencyMs = roundVal(performance.now() - startTime, 2);

        if (this.metrics.framesAccepted % 30 === 0) {
            console.log('[LandmarkEngine] Validated landmarks:', {
                frameNumber: this.metrics.framesAccepted,
                qualityScore: qualityScore,
                trackingState: this.metrics.trackingState
            });
        }

        // Construct ValidatedLandmarkSet payload
        const validatedPayload = {
            id: Math.random().toString(36).substring(2, 11),
            timestamp: new Date().toISOString(),
            schema_version: '2.0.0',
            source: 'LandmarkEngine',
            quality_score: qualityScore,
            filtering_method: this.config.smoothingMethod,
            tracking_state: this.metrics.trackingState,
            body_coverage_pct: this.metrics.bodyCoveragePct,
            visible_landmarks: this.metrics.visibleLandmarksList,
            missing_landmarks: this.metrics.missingLandmarksList,
            confidence: confidence,
            landmarks: smoothed
        };

        this.previousLandmarks = smoothed;
        this._publish("landmarks.validated", validatedPayload);
        this._publish("landmarks.filtered", { method: this.config.smoothingMethod, trackingState: this.metrics.trackingState });
        return validatedPayload;
    }

    _annotateLandmarks(landmarks) {
        if (!landmarks || landmarks.length === 0) return [];

        return landmarks.map((lm, i) => {
            const vis = lm.visibility !== undefined && lm.visibility !== null ? lm.visibility : 0.0;
            const pres = lm.presence !== undefined && lm.presence !== null ? lm.presence : 0.0;

            const isVisValid = vis >= this.config.visibilityThreshold;
            const isPresValid = pres >= this.config.presenceThreshold;
            const isCoordValid = !isNaN(lm.x) && !isNaN(lm.y) && isFinite(lm.x) && isFinite(lm.y) &&
                                lm.x >= -0.5 && lm.x <= 1.5 && lm.y >= -0.5 && lm.y <= 1.5;

            const isValid = isVisValid && isPresValid && isCoordValid;
            let reason = "valid";
            if (!isCoordValid) reason = "out_of_bounds";
            else if (!isVisValid) reason = "low_visibility";
            else if (!isPresValid) reason = "low_presence";

            return {
                ...lm,
                id: lm.id !== undefined ? lm.id : i,
                index: lm.index !== undefined ? lm.index : i,
                name: lm.name || `landmark_${i}`,
                visibility: vis,
                presence: pres,
                visible: isValid,
                reason: reason
            };
        });
    }

    _analyzeBodyCoverage(landmarks) {
        if (!landmarks || landmarks.length === 0) {
            return {
                coveragePct: 0.0,
                trackingState: 'NO_TRACKING',
                visibleList: [],
                missingList: REQUIRED_BODY_LANDMARKS.map(r => r.name)
            };
        }

        const landmarkMap = {};
        landmarks.forEach(lm => {
            if (lm.name) landmarkMap[lm.name.toLowerCase()] = lm;
            if (lm.index !== undefined) landmarkMap[lm.index] = lm;
        });

        const visibleList = [];
        const missingList = [];

        for (const req of REQUIRED_BODY_LANDMARKS) {
            const lm = landmarkMap[req.name.toLowerCase()] || landmarkMap[req.index];
            if (lm && lm.visible === true) {
                visibleList.push(req.name);
            } else {
                missingList.push(req.name);
            }
        }

        const visibleCount = visibleList.length;
        const totalRequired = REQUIRED_BODY_LANDMARKS.length;
        const coverage = totalRequired > 0 ? (visibleCount / totalRequired) : 0.0;
        const coveragePct = roundVal(coverage * 100.0, 1);

        let trackingState = 'NO_TRACKING';
        if (coverage >= this.config.fullBodyThreshold) {
            trackingState = 'FULL_BODY';
        } else if (coverage >= this.config.partialBodyThreshold) {
            trackingState = 'PARTIAL_BODY';
        } else {
            trackingState = 'NO_TRACKING';
        }

        return {
            coveragePct,
            trackingState,
            visibleList,
            missingList
        };
    }

    _interpolateMissing(landmarks) {
        if (!this.previousLandmarks) return landmarks;

        return landmarks.map((lm, i) => {
            if (!lm.visible) {
                const prev = this.previousLandmarks[i];
                if (prev && prev.visible) {
                    this.metrics.interpolationCount++;
                    this._publish("landmarks.interpolated", { index: i, name: lm.name });
                    return {
                        ...lm,
                        x: prev.x,
                        y: prev.y,
                        z: prev.z,
                        visibility: prev.visibility,
                        presence: prev.presence,
                        visible: true,
                        is_interpolated: true
                    };
                }
            }
            return lm;
        });
    }

    _applySmoothing(landmarks) {
        if (this.config.smoothingMethod === 'none' || !this.previousLandmarks) {
            return landmarks;
        }

        const alpha = this.config.emaAlpha;
        return landmarks.map((lm, i) => {
            const prev = this.previousLandmarks[i];
            if (!prev || !lm.visible || !prev.visible) return lm;

            return {
                ...lm,
                x: roundVal(alpha * lm.x + (1 - alpha) * prev.x, 4),
                y: roundVal(alpha * lm.y + (1 - alpha) * prev.y, 4),
                z: roundVal(alpha * lm.z + (1 - alpha) * prev.z, 4)
            };
        });
    }

    _calculateQualityScore(landmarks, confidence) {
        const validLms = landmarks.filter(lm => lm.visible);
        if (landmarks.length === 0 || validLms.length === 0) return 0.0;
        const avgVis = validLms.reduce((acc, lm) => acc + (lm.visibility || 0), 0) / validLms.length;
        const score = (avgVis * 50.0) + (confidence * 50.0);
        return roundVal(Math.min(100.0, Math.max(0.0, score)), 1);
    }

    _calculateJitter(landmarks) {
        if (!this.previousLandmarks || landmarks.length === 0) return 0.0;
        let totalDiff = 0.0;
        let count = 0;
        landmarks.forEach((lm, i) => {
            const prev = this.previousLandmarks[i];
            if (prev && lm.visible && prev.visible) {
                totalDiff += Math.sqrt((lm.x - prev.x)**2 + (lm.y - prev.y)**2);
                count++;
            }
        });
        return count > 0 ? totalDiff / count : 0.0;
    }

    getDiagnostics() {
        return {
            name: this.name,
            version: this.version,
            status: this.status,
            priority: this.priority,
            dependencies: this.dependencies,
            config: { ...this.config },
            metrics: { ...this.metrics }
        };
    }

    _publish(eventName, data) {
        if (this.eventBus && typeof this.eventBus.publish === 'function') {
            this.eventBus.publish(eventName, data);
        }
    }
}

function roundVal(num, decimals = 2) {
    return Number(Math.round(num + 'e' + decimals) + 'e-' + decimals);
}
