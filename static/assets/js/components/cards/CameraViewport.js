/**
 * CameraViewport
 * Reusable UI card rendering video preview stream, loading spinner, permission alert, and state badges.
 */

export class CameraViewport {
    constructor(containerId, cameraEngine = null) {
        this.container = document.getElementById(containerId);
        this.cameraEngine = cameraEngine;
        this.init();
    }

    init() {
        if (!this.container) return;
        this.container.innerHTML = `
            <div class="ps-camera-viewport position-relative bg-dark rounded-3 overflow-hidden d-flex align-items-center justify-content-center" style="min-height: 400px; border: 1px solid #334155;">
                <video id="ps-viewport-video" autoplay playsinline muted style="width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); display: none;"></video>
                
                <!-- State 1: Placeholder / Stopped -->
                <div id="ps-viewport-stopped" class="text-center p-4">
                    <div class="mb-3" style="font-size: 48px;">📷</div>
                    <h5 class="text-white">Camera Offline</h5>
                    <p class="text-muted small">Click "Start Camera" to initialize the video feed.</p>
                </div>

                <!-- State 2: Loading -->
                <div id="ps-viewport-loading" class="text-center p-4" style="display: none;">
                    <div class="spinner-border text-primary mb-3" role="status"></div>
                    <h5 class="text-white">Requesting Camera Access...</h5>
                    <p class="text-muted small">Please allow webcam permissions in your browser prompt.</p>
                </div>

                <!-- State 3: Permission Denied -->
                <div id="ps-viewport-denied" class="text-center p-4 text-danger" style="display: none;">
                    <div class="mb-3" style="font-size: 48px;">⚠️</div>
                    <h5>Webcam Permission Denied</h5>
                    <p class="text-muted small">Please check browser site settings to allow camera permissions.</p>
                </div>

                <!-- Diagnostic Overlay Badge -->
                <div class="position-absolute top-0 start-0 m-3 p-2 bg-dark bg-opacity-75 rounded text-white small" style="backdrop-filter: blur(4px);">
                    <span id="ps-cam-status-badge" class="badge bg-secondary">Offline</span>
                    <span id="ps-cam-res-badge" class="ms-2 text-info">1280x720</span>
                    <span id="ps-cam-fps-badge" class="ms-2 text-warning">0 FPS</span>
                </div>
            </div>
        `;

        this.videoElement = document.getElementById('ps-viewport-video');
        this.stoppedEl = document.getElementById('ps-viewport-stopped');
        this.loadingEl = document.getElementById('ps-viewport-loading');
        this.deniedEl = document.getElementById('ps-viewport-denied');
        this.statusBadge = document.getElementById('ps-cam-status-badge');
        this.resBadge = document.getElementById('ps-cam-res-badge');
        this.fpsBadge = document.getElementById('ps-cam-fps-badge');
    }

    setLoading() {
        this.stoppedEl.style.display = 'none';
        this.deniedEl.style.display = 'none';
        this.videoElement.style.display = 'none';
        this.loadingEl.style.display = 'block';
        this.statusBadge.className = 'badge bg-warning text-dark';
        this.statusBadge.textContent = 'Connecting';
    }

    setLive() {
        this.stoppedEl.style.display = 'none';
        this.loadingEl.style.display = 'none';
        this.deniedEl.style.display = 'none';
        this.videoElement.style.display = 'block';
        this.statusBadge.className = 'badge bg-success';
        this.statusBadge.textContent = 'LIVE';
    }

    setDenied() {
        this.stoppedEl.style.display = 'none';
        this.loadingEl.style.display = 'none';
        this.videoElement.style.display = 'none';
        this.deniedEl.style.display = 'block';
        this.statusBadge.className = 'badge bg-danger';
        this.statusBadge.textContent = 'Permission Denied';
    }

    setStopped() {
        this.videoElement.style.display = 'none';
        this.loadingEl.style.display = 'none';
        this.deniedEl.style.display = 'none';
        this.stoppedEl.style.display = 'block';
        this.statusBadge.className = 'badge bg-secondary';
        this.statusBadge.textContent = 'Offline';
    }

    updateMetrics(fps, resolution) {
        if (this.fpsBadge) this.fpsBadge.textContent = `${fps} FPS`;
        if (this.resBadge) this.resBadge.textContent = resolution;
    }
}
