/**
 * CameraEngine
 * Production-grade browser camera engine for PostureSense v2.
 * Captures video frames using getUserMedia(), collects performance metrics, and publishes frame.captured events.
 */

export class CameraEngine {
    constructor(eventBus = null) {
        this.name = "CameraEngine";
        this.version = "2.0.0";
        this.eventBus = eventBus;
        this.status = "uninitialized";

        // Media Stream & Video Elements
        this.stream = null;
        this.videoElement = null;
        this.selectedDeviceId = localStorage.getItem('ps_camera_device_id') || null;

        // Configurations
        this.config = {
            width: 1280,
            height: 720,
            frameRate: 30,
            facingMode: 'user',
            mirror: true
        };

        // Performance Metrics
        this.metrics = {
            fps: 0,
            frameCount: 0,
            droppedFrames: 0,
            resolution: '1280x720',
            deviceName: 'Default Camera',
            permissionStatus: 'prompt',
            latencyMs: 0
        };

        // Internal State & Loop
        this.animationFrameId = null;
        this.lastFrameTime = performance.now();
        this.frameCountWindow = 0;
        this.fpsTimer = null;
    }

    async initialize(config = {}) {
        Object.assign(this.config, config);
        this.status = "initialized";
        this._publish("camera.initialized", this.getDiagnostics());
        return true;
    }

    async enumerateDevices() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
            return [];
        }
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            return devices.filter(d => d.kind === 'videoinput');
        } catch (error) {
            console.error('[CameraEngine] Error enumerating devices:', error);
            return [];
        }
    }

    async start(videoElement = null) {
        if (videoElement) {
            this.videoElement = videoElement;
        }

        this.status = "starting";
        const constraints = {
            audio: false,
            video: {
                width: { ideal: this.config.width },
                height: { ideal: this.config.height },
                frameRate: { ideal: this.config.frameRate }
            }
        };

        if (this.selectedDeviceId) {
            constraints.video.deviceId = { exact: this.selectedDeviceId };
        } else {
            constraints.video.facingMode = this.config.facingMode;
        }

        try {
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.metrics.permissionStatus = 'granted';

            const track = this.stream.getVideoTracks()[0];
            if (track) {
                const settings = track.getSettings();
                this.metrics.resolution = `${settings.width || this.config.width}x${settings.height || this.config.height}`;
                this.metrics.deviceName = track.label || 'Webcam';
            }

            if (this.videoElement) {
                this.videoElement.srcObject = this.stream;
                this.videoElement.play();
            }

            this.status = "running";
            this._startFpsTimer();
            this._startFrameLoop();
            this._publish("camera.started", this.getDiagnostics());
            return true;
        } catch (error) {
            this.status = "failed";
            this.metrics.permissionStatus = error.name === 'NotAllowedError' ? 'denied' : 'error';
            this._publish("camera.error", { error: error.message, name: error.name });
            throw error;
        }
    }

    async setDevice(deviceId) {
        this.selectedDeviceId = deviceId;
        localStorage.setItem('ps_camera_device_id', deviceId);
        if (this.status === 'running' || this.status === 'starting') {
            await this.stop();
            await this.start();
        }
    }

    async setResolution(width, height) {
        this.config.width = width;
        this.config.height = height;
        if (this.status === 'running') {
            await this.stop();
            await this.start();
        }
    }

    pause() {
        if (this.status === 'running') {
            this.status = "paused";
            if (this.videoElement) this.videoElement.pause();
            this._publish("camera.paused", this.getDiagnostics());
        }
    }

    resume() {
        if (this.status === 'paused') {
            this.status = "running";
            if (this.videoElement) this.videoElement.play();
            this._publish("camera.resumed", this.getDiagnostics());
        }
    }

    async stop() {
        this.status = "stopping";
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
        if (this.fpsTimer) {
            clearInterval(this.fpsTimer);
            this.fpsTimer = null;
        }
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        if (this.videoElement) {
            this.videoElement.srcObject = null;
        }
        this.status = "stopped";
        this._publish("camera.stopped", this.getDiagnostics());
    }

    dispose() {
        this.stop();
        this.status = "disposed";
        this._publish("camera.disposed", this.getDiagnostics());
    }

    _startFrameLoop() {
        const loop = async () => {
            if (this.status === 'running') {
                const now = performance.now();
                this.metrics.frameCount++;
                this.frameCountWindow++;

                let imageBitmap = null;
                if (this.videoElement && this.videoElement.readyState >= 2) {
                    try {
                        imageBitmap = await createImageBitmap(this.videoElement);
                    } catch (_) {}
                }

                // Publish Frame Event contract
                const framePayload = {
                    id: Math.random().toString(36).substring(2, 11),
                    timestamp: new Date().toISOString(),
                    schema_version: '2.0.0',
                    source: 'CameraEngine',
                    frame_number: this.metrics.frameCount,
                    width: this.videoElement ? (this.videoElement.videoWidth || this.config.width) : this.config.width,
                    height: this.videoElement ? (this.videoElement.videoHeight || this.config.height) : this.config.height,
                    fps: this.metrics.fps,
                    imageBitmap: imageBitmap,
                    videoElement: this.videoElement
                };

                this._publish("frame.captured", framePayload);
                this._publish("camera.frame_ready", framePayload);
                this.lastFrameTime = now;
            }
            if (this.status === 'running' || this.status === 'paused') {
                this.animationFrameId = requestAnimationFrame(loop);
            }
        };
        this.animationFrameId = requestAnimationFrame(loop);
    }

    _startFpsTimer() {
        this.fpsTimer = setInterval(() => {
            this.metrics.fps = this.frameCountWindow;
            this.frameCountWindow = 0;
        }, 1000);
    }

    getDiagnostics() {
        return {
            name: this.name,
            version: this.version,
            status: this.status,
            metrics: { ...this.metrics },
            config: { ...this.config }
        };
    }

    _publish(eventName, data) {
        if (this.eventBus && typeof this.eventBus.publish === 'function') {
            this.eventBus.publish(eventName, data);
        }
    }
}
