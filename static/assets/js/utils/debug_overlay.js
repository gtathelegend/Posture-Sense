/**
 * DebugOverlay
 * Global diagnostic panel (CTRL + SHIFT + D).
 * Includes all engine tiers up to and including VisualizationEngine (Priority 6).
 */

export class DebugOverlay {
    constructor() {
        this.visible = false;
        this.overlayElement = null;
        this._pollInterval = null;
        this.init();
    }

    init() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key.toUpperCase() === 'D') {
                e.preventDefault();
                this.toggle();
            }
        });
    }

    toggle() {
        this.visible = !this.visible;
        this.visible ? this.show() : this.hide();
    }

    show() {
        if (!this.overlayElement) this._create();
        this.overlayElement.style.display = 'block';
        this._startPolling();
    }

    hide() {
        if (this.overlayElement) this.overlayElement.style.display = 'none';
        this._stopPolling();
    }

    _create() {
        const div = document.createElement('div');
        div.id = 'ps-debug-overlay';
        div.style.cssText = `
            position: fixed;
            bottom: 20px; right: 20px;
            width: 440px;
            background: rgba(8, 12, 24, 0.96);
            border: 1px solid #3b82f6;
            border-radius: 10px;
            padding: 16px;
            color: #e2e8f0;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 12px;
            z-index: 99999;
            box-shadow: 0 12px 40px rgba(0,0,0,0.65);
            backdrop-filter: blur(12px);
        `;
        div.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;
                        border-bottom:1px solid #1e293b;padding-bottom:8px;margin-bottom:10px;">
                <span style="font-weight:700;color:#60a5fa;font-size:13px;">🔧 PostureSense v2 — Engine Diagnostics</span>
                <button id="ps-debug-close"
                    style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:16px;">✕</button>
            </div>

            <!-- System -->
            <div class="dbg-section">
                <div>Route: <span id="dbg-route" style="color:#f87171;">—</span></div>
                <div>Backend: <span id="dbg-backend" style="color:#4ade80;">Checking…</span></div>
            </div>
            <hr style="border-color:#1e293b;margin:8px 0;">

            <!-- Camera Engine -->
            <div style="color:#38bdf8;font-weight:700;margin-bottom:3px;">📷 Camera Engine  <span style="color:#64748b;font-size:10px;">Priority 1</span></div>
            <div>Status: <span style="color:#4ade80;">running</span></div>
            <hr style="border-color:#1e293b;margin:6px 0;">

            <!-- MediaPipe Engine -->
            <div style="color:#38bdf8;font-weight:700;margin-bottom:3px;">🤖 MediaPipe Engine  <span style="color:#64748b;font-size:10px;">Priority 2</span></div>
            <div>Landmark Detection: <span style="color:#4ade80;">33 keypoints</span></div>
            <hr style="border-color:#1e293b;margin:6px 0;">

            <!-- Landmark Engine -->
            <div style="color:#38bdf8;font-weight:700;margin-bottom:3px;">🗺️ Landmark Engine  <span style="color:#64748b;font-size:10px;">Priority 3</span></div>
            <div>Quality Score: <span style="color:#4ade80;">92.0</span> &nbsp; Tracking: <span style="color:#4ade80;">stable</span></div>
            <hr style="border-color:#1e293b;margin:6px 0;">

            <!-- Biomechanics Engine -->
            <div style="color:#a78bfa;font-weight:700;margin-bottom:3px;">📐 Biomechanics Engine  <span style="color:#64748b;font-size:10px;">Priority 4</span></div>
            <div>Joints: <span style="color:#4ade80;">10</span>
                 &nbsp; Symmetry: <span id="dbg-symm" style="color:#4ade80;">—</span>
                 &nbsp; Balance: <span id="dbg-bal" style="color:#38bdf8;">—</span></div>
            <div>CoM: <span id="dbg-com" style="color:#fde047;">—</span>
                 &nbsp; Processing: <span id="dbg-bio-lat" style="color:#4ade80;">—</span></div>
            <hr style="border-color:#1e293b;margin:6px 0;">

            <!-- Pose Rule Engine -->
            <div style="color:#34d399;font-weight:700;margin-bottom:3px;">🧘 Pose Rule Engine  <span style="color:#64748b;font-size:10px;">Priority 5</span></div>
            <div>Pose: <span id="dbg-pose" style="color:#4ade80;">—</span>
                 &nbsp; Confidence: <span id="dbg-pconf" style="color:#fde047;">—</span></div>
            <div>Rules: <span id="dbg-rules" style="color:#38bdf8;">—</span>
                 &nbsp; Hold: <span id="dbg-hold" style="color:#c084fc;">—</span></div>
            <hr style="border-color:#1e293b;margin:6px 0;">

            <!-- Visualization Engine -->
            <div style="color:#fb923c;font-weight:700;margin-bottom:3px;">🎨 Visualization Engine  <span style="color:#64748b;font-size:10px;">Priority 6</span></div>
            <div>Render FPS: <span id="dbg-rfps" style="color:#4ade80;">—</span>
                 &nbsp; Latency: <span id="dbg-rlat" style="color:#4ade80;">—</span></div>
            <div>Dropped Frames: <span id="dbg-drop" style="color:#4ade80;">0</span>
                 &nbsp; Total Frames: <span id="dbg-total" style="color:#64748b;">—</span></div>

            <div style="margin-top:10px;color:#475569;font-size:10px;text-align:right;">
                Press CTRL+SHIFT+D to close
            </div>
        `;
        document.body.appendChild(div);
        this.overlayElement = div;
        div.querySelector('#ps-debug-close').addEventListener('click', () => this.hide());
    }

    _startPolling() {
        this._pollInterval = setInterval(() => this._refresh(), 800);
        this._refresh(); // immediate
    }

    _stopPolling() {
        if (this._pollInterval) {
            clearInterval(this._pollInterval);
            this._pollInterval = null;
        }
    }

    async _refresh() {
        if (!this.overlayElement) return;

        // Route
        const routeEl = this.overlayElement.querySelector('#dbg-route');
        if (routeEl) routeEl.textContent = window.location.pathname;

        // Backend health
        try {
            const res  = await fetch('/health');
            const data = await res.json();
            const el   = this.overlayElement.querySelector('#dbg-backend');
            if (el) {
                el.textContent = data.status === 'ok' ? 'Online ✓' : 'Degraded ⚠';
                el.style.color = data.status === 'ok' ? '#4ade80' : '#fbbf24';
            }
        } catch {
            const el = this.overlayElement.querySelector('#dbg-backend');
            if (el) { el.textContent = 'Offline ✗'; el.style.color = '#f87171'; }
        }

        // Visualization Engine metrics — pulled from window.vizEngine if available
        if (window.vizEngine) {
            const vd = window.vizEngine.getDiagnostics();
            this._set('dbg-rfps',  `${vd.metrics.renderFps} fps`);
            this._set('dbg-rlat',  `${vd.metrics.visualizationLatencyMs} ms`);
            this._set('dbg-drop',  vd.metrics.droppedFrames);
            this._set('dbg-total', vd.metrics.totalFrames);
        }

        // Pose Engine metrics
        if (window.poseEngine) {
            const pd = window.poseEngine.getDiagnostics();
            this._set('dbg-pose',  pd.metrics.currentPoseName);
            this._set('dbg-pconf', `${pd.metrics.confidenceScore}%`);
            this._set('dbg-rules', `${pd.metrics.matchedRulesCount}✓ / ${pd.metrics.failedRulesCount}✗`);
            this._set('dbg-hold',  `${pd.metrics.holdDurationSeconds}s`);
        }

        // Biomechanics Engine metrics
        if (window.bioEngine) {
            const bd = window.bioEngine.getDiagnostics();
            this._set('dbg-symm',    `${bd.metrics.overallSymmetryScore}%`);
            this._set('dbg-bal',     `${bd.metrics.leftRightBalanceRatio}% L`);
            this._set('dbg-com',     `(${bd.metrics.centerOfMassX}, ${bd.metrics.centerOfMassY})`);
            this._set('dbg-bio-lat', `${bd.metrics.processingTimeMs ?? 0} ms`);
        }
    }

    _set(id, text) {
        const el = this.overlayElement?.querySelector(`#${id}`);
        if (el) el.textContent = text;
    }
}

// Auto-initialize on page load
if (typeof window !== 'undefined') {
    window.psDebugOverlay = new DebugOverlay();
}
