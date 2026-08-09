/**
 * PosePipelineController
 * PostureSense v2 Browser Pipeline Orchestrator.
 * 
 * Responsibilities:
 * - Instantiate and wire the EventBus across all 9 browser JS engines.
 * - Initialize engines in strict dependency order:
 *   1. CameraEngine (Priority 1)
 *   2. MediaPipeEngine (Priority 2)
 *   3. LandmarkEngine (Priority 3)
 *   4. BiomechanicsEngine (Priority 4)
 *   5. PoseRuleEngine (Priority 5)
 *   6. VisualizationEngine (Priority 6)
 *   7. MovementEngine (Priority 7)
 *   8. ScoringEngine (Priority 8)
 *   9. FeedbackEngine (Priority 9)
 * - Provide lifecycle control (initialize, start, pause, resume, stop, dispose).
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
    }

    /**
     * Initialize all engines in strict dependency order
     * @param {Object} options
     * @param {HTMLVideoElement} options.videoElement
     * @param {HTMLCanvasElement} options.canvasElement
     * @param {Object} [options.config]
     */
    async initialize({ videoElement, canvasElement, config = {} }) {
        if (!videoElement || !canvasElement) {
            throw new Error('[PostureSense][Pipeline] Video and Canvas elements are required for initialization.');
        }

        this.videoElement = videoElement;
        this.canvasElement = canvasElement;

        console.log('[PostureSense][Pipeline] Initializing 9-engine browser pipeline...');

        this.adapter.attach();

        // 1. Camera Engine (Priority 1)
        await this.cameraEngine.initialize(config.camera || {});

        // 2. MediaPipe Engine (Priority 2)
        await this.mediaPipeEngine.initialize(config.mediapipe || {});

        // 3. Landmark Engine (Priority 3)
        await this.landmarkEngine.initialize(config.landmark || {});

        // 4. Biomechanics Engine (Priority 4)
        await this.biomechanicsEngine.initialize(config.biomechanics || {});

        // 5. Pose Rule Engine (Priority 5)
        await this.poseRuleEngine.initialize(config.poseRule || {});

        // 6. Visualization Engine (Priority 6)
        await this.visualizationEngine.initialize(config.visualization || {});

        // 7. Movement Engine (Priority 7)
        await this.movementEngine.initialize(config.movement || {});

        // 8. Scoring Engine (Priority 8)
        await this.scoringEngine.initialize(config.scoring || {});

        // 9. Feedback Engine (Priority 9)
        await this.feedbackEngine.initialize(config.feedback || {});

        this.status = 'initialized';
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
        await this.mediaPipeEngine.start();
        await this.landmarkEngine.start();
        await this.biomechanicsEngine.start();
        await this.poseRuleEngine.start();
        await this.visualizationEngine.start(this.canvasElement, this.videoElement);
        await this.movementEngine.start();
        await this.scoringEngine.start();
        await this.feedbackEngine.start();

        this.status = 'running';
        console.log('[PostureSense][Pipeline] All engines running smoothly.');
        return true;
    }

    /**
     * Pause the running camera and engines
     */
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

    /**
     * Resume a paused pipeline
     */
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

    /**
     * Stop all engines and release camera hardware
     */
    async stop() {
        console.log('[PostureSense][Pipeline] Stopping pipeline and camera...');

        // Stop in reverse dependency order
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
        console.log('[PostureSense][Pipeline] Pipeline stopped cleanly.');
    }

    /**
     * Dispose all engine resources
     */
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
        console.log('[PostureSense][Pipeline] Pipeline disposed.');
    }

    /**
     * Get aggregate diagnostics across all pipeline components
     */
    getDiagnostics() {
        return {
            status: this.status,
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
