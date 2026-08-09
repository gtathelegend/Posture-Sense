/**
 * PosePipelineController
 * PostureSense v2 Browser Pipeline Orchestrator.
 * 
 * Responsibilities:
 * - Instantiate and wire the EventBus across all 9 browser JS engines.
 * - Initialize and start engines in strict dependency order.
 * - Monitor pipeline health state (HEALTHY vs DEGRADED).
 * - Handle MediaPipe worker failure and clear stale tracking cache across engines.
 * - Log structured diagnostic telemetry to the browser console.
 */

import { EventBus } from '../utils/event_bus.js';
import { CameraEngine } from '../engines/camera_engine.js';
import { MediaPipeEngine } from '../engines/mediapipe_engine.js';
import { LandmarkEngine } from '../engines/landmark_engine.js';
import { BiomechanicsEngine } from '../engines/biomechanics_engine.js';
import { PoseRuleEngine } from '../engines/pose_rule_engine.js';
import { VisualizationEngine } from '../engines/visualization_engine.js';
import { MovementEngine } from '../engines/movement_engine.js';
import { ScoringEngine } from '../engines/scoring_engine.js';
import { FeedbackEngine } from '../engines/feedback_engine.js';
import { EngineAdapter } from '../adapters/EngineAdapter.js';
import { EngineContext } from '../context/EngineContext.js';

export class PosePipelineController {
    constructor() {
        this.status = 'uninitialized';
        this.healthState = 'uninitialized'; // 'HEALTHY', 'DEGRADED', 'ERROR'
        this.eventBus = new EventBus();
        this.engineContext = new EngineContext();
        this.adapter = new EngineAdapter(this.eventBus, this.engineContext);

        // Instantiate all 9 pipeline engines
        this.cameraEngine = new CameraEngine(this.eventBus);
        this.mediaPipeEngine = new MediaPipeEngine(this.eventBus);
        this.landmarkEngine = new LandmarkEngine(this.eventBus);
        this.biomechanicsEngine = new BiomechanicsEngine(this.eventBus);
        this.poseRuleEngine = new PoseRuleEngine(this.eventBus);
        this.visualizationEngine = new VisualizationEngine(this.eventBus);
        this.movementEngine = new MovementEngine(this.eventBus);
        this.scoringEngine = new ScoringEngine(this.eventBus);
        this.feedbackEngine = new FeedbackEngine(this.eventBus);

        this.videoElement = null;
        this.canvasElement = null;

        this._subscribeToHealthEvents();
    }

    _subscribeToHealthEvents() {
        this.eventBus.subscribe('mediapipe.failed', (e) => {
            console.error('[PostureSense][Pipeline] MediaPipe Engine failure reported:', e.data);
            this.healthState = 'DEGRADED';
            this.clearStalePipelineCache(e.data?.error || "MediaPipe engine failed");
        });

        this.eventBus.subscribe('tracking.lost', (e) => {
            if (e.data?.reason && (e.data.reason.includes("MediaPipe") || e.data.reason.includes("Failure"))) {
                this.healthState = 'DEGRADED';
                this.clearStalePipelineCache(e.data.reason);
            }
        });
    }

    clearStalePipelineCache(reason = "Tracking lost") {
        if (this.visualizationEngine && typeof this.visualizationEngine.resetVisualizationState === 'function') {
            this.visualizationEngine.resetVisualizationState(reason);
        }
        if (this.poseRuleEngine && typeof this.poseRuleEngine._returnUnknownState === 'function') {
            this.poseRuleEngine._returnUnknownState(reason, 0.0);
        }
    }

    /**
     * Initialize all engines in strict dependency order
     */
    async initialize({ videoElement, canvasElement, config = {} }) {
        if (!videoElement || !canvasElement) {
            throw new Error('[PostureSense][Pipeline] Video and Canvas elements are required for initialization.');
        }

        this.videoElement = videoElement;
        this.canvasElement = canvasElement;

        console.log('[PostureSense][Pipeline] Initializing 9-engine browser pipeline...');

        this.adapter.attach();

        await this.cameraEngine.initialize(config.camera || {});
        await this.mediaPipeEngine.initialize(config.mediapipe || {});
        await this.landmarkEngine.initialize(config.landmark || {});
        await this.biomechanicsEngine.initialize(config.biomechanics || {});
        await this.poseRuleEngine.initialize(config.poseRule || {});
        await this.visualizationEngine.initialize(config.visualization || {});
        await this.movementEngine.initialize(config.movement || {});
        await this.scoringEngine.initialize(config.scoring || {});
        await this.feedbackEngine.initialize(config.feedback || {});

        this.status = 'initialized';
        this.healthState = 'INITIALIZED';
        console.log('[PostureSense][Pipeline] Pipeline initialized successfully.');
        return true;
    }

    /**
     * Start the camera and activate all pipeline engines
     */
    async start() {
        if (this.status === 'running') {
            console.warn('[PostureSense][Pipeline] Pipeline is already running.');
            return true;
        }

        console.log('[PostureSense][Pipeline] Starting camera and engines...');

        // Start engines in priority order
        await this.cameraEngine.start(this.videoElement);
        const mpStarted = await this.mediaPipeEngine.start();
        await this.landmarkEngine.start();
        await this.biomechanicsEngine.start();
        await this.poseRuleEngine.start();
        await this.visualizationEngine.start(this.canvasElement, this.videoElement);
        await this.movementEngine.start();
        await this.scoringEngine.start();
        await this.feedbackEngine.start();

        const cameraRunning = this.cameraEngine.status === 'running';
        const mediaPipeReady = mpStarted && this.mediaPipeEngine.isModelLoaded && this.mediaPipeEngine.status !== 'failed';

        if (cameraRunning && mediaPipeReady) {
            this.status = 'running';
            this.healthState = 'HEALTHY';
            console.log('[PostureSense][Pipeline] All engines running smoothly.');
        } else {
            this.status = 'running';
            this.healthState = 'DEGRADED';
            this.clearStalePipelineCache("MediaPipe inference unavailable");
            console.warn('[PostureSense][Pipeline] Pipeline running in DEGRADED state — MediaPipe tracking unavailable.');
        }

        return true;
    }

    pause() {
        if (this.status !== 'running') return;

        console.log('[PostureSense][Pipeline] Pausing pipeline...');
        this.cameraEngine.pause();
        this.mediaPipeEngine.pause();
        this.landmarkEngine.pause();
        this.biomechanicsEngine.pause();
        this.poseRuleEngine.pause();
        this.visualizationEngine.pause();
        this.movementEngine.pause();
        this.scoringEngine.pause();
        this.feedbackEngine.pause();

        this.status = 'paused';
    }

    resume() {
        if (this.status !== 'paused') return;

        console.log('[PostureSense][Pipeline] Resuming pipeline...');
        this.cameraEngine.resume();
        this.mediaPipeEngine.resume();
        this.landmarkEngine.resume();
        this.biomechanicsEngine.resume();
        this.poseRuleEngine.resume();
        this.visualizationEngine.resume();
        this.movementEngine.resume();
        this.scoringEngine.resume();
        this.feedbackEngine.resume();

        this.status = 'running';
    }

    async stop() {
        console.log('[PostureSense][Pipeline] Stopping pipeline and camera...');

        await this.feedbackEngine.stop();
        await this.scoringEngine.stop();
        await this.movementEngine.stop();
        await this.visualizationEngine.stop();
        await this.poseRuleEngine.stop();
        await this.biomechanicsEngine.stop();
        await this.landmarkEngine.stop();
        await this.mediaPipeEngine.stop();
        await this.cameraEngine.stop();

        this.status = 'stopped';
        this.clearStalePipelineCache("Pipeline stopped");
        console.log('[PostureSense][Pipeline] Pipeline stopped cleanly.');
    }

    dispose() {
        console.log('[PostureSense][Pipeline] Disposing pipeline resources...');

        this.adapter.detach();

        this.feedbackEngine.dispose();
        this.scoringEngine.dispose();
        this.movementEngine.dispose();
        this.visualizationEngine.dispose();
        this.poseRuleEngine.dispose();
        this.biomechanicsEngine.dispose();
        this.landmarkEngine.dispose();
        this.mediaPipeEngine.dispose();
        this.cameraEngine.dispose();

        this.eventBus.clear();
        this.status = 'disposed';
        this.healthState = 'DISPOSED';
        console.log('[PostureSense][Pipeline] Pipeline disposed.');
    }

    getDiagnostics() {
        return {
            status: this.status,
            healthState: this.healthState,
            camera: this.cameraEngine.getDiagnostics(),
            mediaPipe: this.mediaPipeEngine.getDiagnostics(),
            landmark: this.landmarkEngine.getDiagnostics(),
            biomechanics: this.biomechanicsEngine.getDiagnostics(),
            poseRule: this.poseRuleEngine.getDiagnostics(),
            visualization: this.visualizationEngine.getDiagnostics(),
            movement: this.movementEngine.getDiagnostics(),
            scoring: this.scoringEngine.getDiagnostics(),
            feedback: this.feedbackEngine.getDiagnostics()
        };
    }
}
