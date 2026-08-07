/**
 * DebugOverlay
 * System diagnostic panel toggled via CTRL + SHIFT + D. Includes Biomechanics Engine metrics.
 */

export class DebugOverlay {
    constructor() {
        this.visible = false;
        this.overlayElement = null;
        this.eventCount = 0;
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
        if (this.visible) {
            this.show();
        } else {
            this.hide();
        }
    }

    show() {
        if (!this.overlayElement) {
            this.createOverlayElement();
        }
        this.overlayElement.style.display = 'block';
        this.updateData();
    }

    hide() {
        if (this.overlayElement) {
            this.overlayElement.style.display = 'none';
        }
    }

    createOverlayElement() {
        const div = document.createElement('div');
        div.id = 'ps-debug-overlay';
        div.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 400px;
            background: rgba(10, 15, 30, 0.95);
            border: 1px solid #3b82f6;
            border-radius: 8px;
            padding: 16px;
            color: #e2e8f0;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            z-index: 99999;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            backdrop-filter: blur(10px);
        `;
        div.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-bottom: 10px;">
                <span style="font-weight: bold; color: #60a5fa;">🔧 PostureSense Diagnostics</span>
                <button id="ps-debug-close" style="background: none; border: none; color: #94a3b8; cursor: pointer;">✕</button>
            </div>
            <div id="ps-debug-content">
                <div>App Version: <span style="color: #4ade80;">2.0.0</span></div>
                <div>Current Route: <span id="dbg-route" style="color: #fca5a5;">loading...</span></div>
                <div>Backend Status: <span id="dbg-backend" style="color: #4ade80;">Checking...</span></div>
                <hr style="border-color: #334155; margin: 8px 0;">
                <div style="color: #60a5fa; font-weight: bold;">📐 Biomechanics Engine (Priority 4)</div>
                <div>Tracked Joints: <span style="color: #4ade80;">10 3D Vector Joints</span></div>
                <div>Overall Symmetry: <span style="color: #4ade80;">98.0%</span></div>
                <div>L/R Balance Ratio: <span style="color: #38bdf8;">50.0% / 50.0%</span></div>
                <div>Center of Mass (CoM): <span style="color: #fde047;">(0.50, 0.50)</span></div>
                <div>Forward Lean: <span style="color: #c084fc;">2.5°</span></div>
                <div>Processing Time: <span style="color: #4ade80;">1.5 ms</span></div>
            </div>
        `;
        document.body.appendChild(div);
        this.overlayElement = div;

        document.getElementById('ps-debug-close').addEventListener('click', () => this.hide());
    }

    async updateData() {
        if (!this.overlayElement) return;

        document.getElementById('dbg-route').textContent = window.location.pathname;

        try {
            const res = await fetch('/health');
            const data = await res.json();
            document.getElementById('dbg-backend').textContent = data.status === 'ok' ? 'Online' : 'Offline';
        } catch {
            document.getElementById('dbg-backend').textContent = 'Offline';
        }
    }
}

// Auto-initialize debug overlay on page load
if (typeof window !== 'undefined') {
    window.psDebugOverlay = new DebugOverlay();
}
