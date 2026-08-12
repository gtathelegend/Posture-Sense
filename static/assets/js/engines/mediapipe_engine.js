/**
 * MediaPipeEngine
 * Production-grade client MediaPipe Tasks Vision Pose Landmarker wrapper engine for PostureSense v2.
 * Offloads inference to a Web Worker, processes camera frames, emits landmarks.detected & tracking.lost events,
 * and handles model load failures gracefully.
 */

export class MediaPipeEngine {
    constructor(eventBus = null) {
        this.name = "MediaPipeEngine";
        this.version = "2.0.0";
        this.eventBus = eventBus;
        this.status = "uninitialized";
        this.priority = 2;
        this.dependencies = ["camera_engine"];

        this.worker = null;
        this.isModelLoaded = false;
        this.isTracking = false;
        this.isInferenceBusy = false;
        this.fpsTimer = null;
        this.frameCountInSecond = 0;

        // Metrics & Diagnostics
        this.metrics = {
            modelLoadTimeMs: 0.0,
            inferenceLatencyMs: 0.0,
            inferenceFps: 0.0,
            framesReceived: 0,
            framesProcessed: 0,
            framesDropped: 0,
            landmarkCount: 0,
            trackingConfidence: 0.0
        };
    }

    async initialize(config = {}) {
        this.status = "initialized";
        this._publish("mediapipe.initialized", this.getDiagnostics());
        return true;
    }

    async loadModel() {
        const startTime = performance.now();
        console.log('[MediaPipeEngine] Creating MediaPipe module worker...');

        return new Promise((resolve) => {
            try {
                this.worker = new Worker('/static/assets/js/workers/mediapipe_worker.js', { type: 'module' });

                this.worker.onerror = (err) => {
                    const errorMsg = err.message || 'MediaPipe Web Worker failed to load or execute.';
                    console.error('[MediaPipeEngine] Worker error:', errorMsg);
                    this.status = 'failed';
                    this.isModelLoaded = false;
                    this._publish("mediapipe.failed", { error: errorMsg });
                    this._publish("tracking.lost", {
                        reason: "MediaPipe Worker Error",
                        error: errorMsg,
                        timestamp: new Date().toISOString()
                    });
                    resolve(false);
                };

                this.worker.onmessage = (e) => {
                    const { action, success, landmarks, confidence, latencyMs, error } = e.data;
                    if (action === 'MODEL_LOADED' && success) {
                        this.isModelLoaded = true;
                        this.metrics.modelLoadTimeMs = performance.now() - startTime;
                        this.status = 'ready';
                        this._publish("mediapipe.model_loaded", this.getDiagnostics());
                        resolve(true);
                    } else if (action === 'MODEL_ERROR') {
                        this.status = "failed";
                        this.isModelLoaded = false;
                        this._publish("mediapipe.failed", { error });
                        this._publish("tracking.lost", {
                            reason: "MediaPipe Model Load Failure",
                            error: error,
                            timestamp: new Date().toISOString()
                        });
                        resolve(false);
                    } else if (action === 'FRAME_PROCESSED') {
                        this.isInferenceBusy = false;
                        this._handleFrameProcessed(landmarks || [], confidence || 0.0, latencyMs || 0.0);
                    } else if (action === 'FRAME_ERROR') {
                        this.isInferenceBusy = false;
                        console.warn('[MediaPipeEngine] Frame processing error:', error);
                        this._publish("mediapipe.error", { error });
                        this._publish("tracking.lost", {
                            reason: "MediaPipe Frame Error",
                            error: error,
                            timestamp: new Date().toISOString()
                        });
                    }
                };

                this.worker.postMessage({ action: 'LOAD_MODEL' });
            } catch (err) {
                const errorMsg = err.message || String(err);
                console.warn('[MediaPipeEngine] Web Worker init exception:', errorMsg);
                this.status = "failed";
                this.isModelLoaded = false;
                this._publish("mediapipe.failed", { error: errorMsg });
                this._publish("tracking.lost", {
                    reason: "MediaPipe Web Worker Init Exception",
                    error: errorMsg,
                    timestamp: new Date().toISOString()
                });
                resolve(false);
            }
        });
    }

    async warmup() {
        if (this.isModelLoaded) {
            console.log('[MediaPipeEngine] Model warmed up.');
        }
    }

    async start() {
        if (!this.isModelLoaded) {
            const loaded = await this.loadModel();
            if (!loaded) {
                console.error('[MediaPipeEngine] Start aborted — model loading failed.');
                this.status = 'failed';
                return false;
            }
        }
        this.status = "running";
        this.isInferenceBusy = false;
        this._startFpsTimer();
        this._subscribeToCameraFrames();
        this._publish("mediapipe.started", this.getDiagnostics());
        return true;
    }

    pause() {
        if (this.status === 'running') {
            this.status = "paused";
            this.isInferenceBusy = false;
            this._publish("mediapipe.paused", this.getDiagnostics());
        }
    }

    resume() {
        if (this.status === 'paused') {
            this.status = "running";
            this.isInferenceBusy = false;
            this._publish("mediapipe.resumed", this.getDiagnostics());
        }
    }

    async stop() {
        this.status = "stopped";
        this.isInferenceBusy = false;
        if (this.fpsTimer) {
            clearInterval(this.fpsTimer);
            this.fpsTimer = null;
        }
        this._publish("mediapipe.stopped", this.getDiagnostics());
    }

    dispose() {
        this.stop();
        if (this.worker) {
            this.worker.terminate();
            this.worker = null;
        }
        this.status = "disposed";
        this._publish("mediapipe.disposed", this.getDiagnostics());
    }

    _subscribeToCameraFrames() {
        if (!this.eventBus || typeof this.eventBus.subscribe !== 'function') return;

        const onFrame = async (event) => {
            if (this.status !== 'running' || !this.worker) return;

            this.metrics.framesReceived++;
            if (this.metrics.framesReceived % 30 === 0) {
                const data = event.data || {};
                console.log(`[MediaPipeEngine] Frames received: ${this.metrics.framesReceived}`, {
                    frameNumber: data.frame_number || data.frameNumber || this.metrics.framesReceived,
                    width: data.width || 1280,
                    height: data.height || 720,
                    timestamp: data.timestamp || new Date().toISOString()
                });
            }

            if (this.isInferenceBusy) {
                this.metrics.framesDropped++;
                if (event.data && event.data.imageBitmap && typeof event.data.imageBitmap.close === 'function') {
                    try { event.data.imageBitmap.close(); } catch (_) {}
                }
                return;
            }

            let bitmap = event.data?.imageBitmap || null;
            if (!bitmap && event.data?.videoElement && event.data.videoElement.readyState >= 2) {
                try {
                    bitmap = await createImageBitmap(event.data.videoElement);
                } catch (_) {}
            }

            if (bitmap) {
                this.isInferenceBusy = true;
                this.metrics.framesProcessed++;
                this.frameCountInSecond++;
                this.worker.postMessage({
                    action: 'PROCESS_FRAME',
                    payload: {
                        imageBitmap: bitmap,
                        frameNumber: this.metrics.framesProcessed,
                        timestamp: performance.now()
                    }
                }, [bitmap]);
            }
        };

        this.eventBus.subscribe('frame.captured', onFrame);
        this.eventBus.subscribe('camera.frame_ready', onFrame);
    }

    _handleFrameProcessed(landmarks, confidence, latencyMs) {
        this.metrics.inferenceLatencyMs = latencyMs || 0.0;
        this.metrics.landmarkCount = landmarks.length;
        this.metrics.trackingConfidence = confidence || 0.0;

        if (this.metrics.framesProcessed % 30 === 0) {
            console.log('[MediaPipeEngine] landmarks.detected:', {
                frameNumber: this.metrics.framesProcessed,
                landmarkCount: landmarks.length,
                confidence: confidence
            });
        }

        if (landmarks.length > 0) {
            if (!this.isTracking) {
                this.isTracking = true;
                this._publish("tracking.recovered", { confidence });
            }

            const landmarkSetPayload = {
                id: Math.random().toString(36).substring(2, 11),
                timestamp: new Date().toISOString(),
                schema_version: '2.0.0',
                source: 'MediaPipeEngine',
                confidence: confidence,
                landmarks: landmarks
            };

            this._publish("landmarks.detected", landmarkSetPayload);
        } else {
            if (this.isTracking) {
                this.isTracking = false;
                this._publish("tracking.lost", {
                    reason: "No landmarks detected in frame",
                    confidence: 0.0,
                    timestamp: new Date().toISOString()
                });
            }
        }
    }

    _startFpsTimer() {
        this.fpsTimer = setInterval(() => {
            this.metrics.inferenceFps = this.frameCountInSecond;
            this.frameCountInSecond = 0;
        }, 1000);
    }

    getDiagnostics() {
        return {
            name: this.name,
            version: this.version,
            status: this.status,
            priority: this.priority,
            dependencies: this.dependencies,
            config: {
                isModelLoaded: this.isModelLoaded,
                isTracking: this.isTracking
            },
            metrics: { ...this.metrics }
        };
    }

    _publish(eventName, data) {
        if (this.eventBus && typeof this.eventBus.publish === 'function') {
            this.eventBus.publish(eventName, data);
        }
    }
}
