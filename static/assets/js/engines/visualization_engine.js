/**
 * VisualizationEngine
 * PostureSense v2 — Priority 6
 * High-performance Canvas-based real-time skeleton, biomechanics, and pose overlay renderer.
 *
 * Subscribes to:
 *   - landmarks.validated  (ValidatedLandmarkSet)
 *   - biomechanics.updated (BiomechanicsSnapshot)
 *   - pose.detected        (PoseResult)
 *
 * Publishes:
 *   - visualization.started
 *   - visualization.updated
 *   - visualization.paused
 *   - visualization.stopped
 *   - visualization.error
 *
 * No AI logic. No classification. No scoring. Pure rendering.
 */

export class VisualizationEngine {
    constructor(eventBus = null) {
        this.name = 'VisualizationEngine';
        this.version = '2.0.0';
        this.eventBus = eventBus;
        this.status = 'uninitialized';
        this.priority = 6;
        this.dependencies = ['landmark_engine', 'pose_rule_engine'];

        // Canvas state
        this.canvas = null;
        this.ctx = null;
        this.videoSource = null;
        this.devicePixelRatio = window.devicePixelRatio || 1;
        this._animationFrameId = null;

        // Latest data from EventBus subscriptions
        this._latestLandmarks = null;
        this._latestBiomechanics = null;
        this._latestPose = null;

        // Configurable display settings — no hardcoded values
        this.config = {
            // Rendering
            mirrorMode: true,
            targetFps: 60,
            // Toggles
            showSkeleton: true,
            showJointLabels: false,
            showJointAngles: true,
            showConfidenceColors: true,
            showCenterOfMass: true,
            showBalance: true,
            showRuleEvaluation: true,
            showPoseLabel: true,
            showOrientationAxes: false,
            showSymmetry: false,
            // Thresholds for color mapping
            confidenceGoodThreshold: 0.7,
            confidenceWarnThreshold: 0.4,
            // Joint circle sizes
            jointRadius: 5,
            boneLineWidth: 2.5,
            comRadius: 10,
            // Label typography
            labelFontSize: 11,
            angleFontSize: 12,
            poseLabelFontSize: 20
        };

        // Configurable color palette
        this.colors = {
            good:      '#22c55e',  // green-500
            warning:   '#eab308',  // yellow-500
            poor:      '#ef4444',  // red-500
            tracking:  '#3b82f6',  // blue-500
            missing:   '#6b7280',  // gray-500
            bone:      'rgba(255,255,255,0.55)',
            comMarker: '#f97316',  // orange-500
            balanceLine: '#a855f7', // purple-500
            poseLabel: '#ffffff',
            overlay:   'rgba(0, 0, 0, 0.55)',
            labelBg:   'rgba(15, 23, 42, 0.80)'
        };

        // MediaPipe 33-keypoint skeleton connections
        this.SKELETON_CONNECTIONS = [
            // Face
            [0, 1], [1, 2], [2, 3], [3, 7],
            [0, 4], [4, 5], [5, 6], [6, 8],
            [9, 10],
            // Upper body
            [11, 12], [11, 13], [13, 15], [15, 17], [15, 19], [15, 21],
            [17, 19],
            [12, 14], [14, 16], [16, 18], [16, 20], [16, 22],
            [18, 20],
            // Torso
            [11, 23], [12, 24], [23, 24],
            // Lower body
            [23, 25], [25, 27], [27, 29], [27, 31], [29, 31],
            [24, 26], [26, 28], [28, 30], [28, 32], [30, 32]
        ];

        // Diagnostics
        this.metrics = {
            renderFps: 0,
            canvasFps: 0,
            visualizationLatencyMs: 0,
            droppedFrames: 0,
            totalFrames: 0
        };

        this._fpsLastTime = performance.now();
        this._fpsFrameCount = 0;
    }

    // ─── Lifecycle ────────────────────────────────────────────────────────────

    async initialize(config = {}, colorOverrides = {}) {
        Object.assign(this.config, config);
        Object.assign(this.colors, colorOverrides);
        this.status = 'initialized';
        this._publish('visualization.initialized', this.getDiagnostics());
        return true;
    }

    async start(canvas, videoSource = null) {
        if (!canvas) {
            console.error('[VisualizationEngine] No canvas element provided.');
            this._publish('visualization.error', { reason: 'No canvas provided' });
            return false;
        }

        this.canvas = canvas;
        this.videoSource = videoSource;
        this.ctx = canvas.getContext('2d');
        this._configureHighDpi();

        this.status = 'running';
        this._subscribeToEvents();
        this._startRenderLoop();
        this._publish('visualization.started', this.getDiagnostics());
        return true;
    }

    pause() {
        if (this.status === 'running') {
            this.status = 'paused';
            if (this._animationFrameId) {
                cancelAnimationFrame(this._animationFrameId);
                this._animationFrameId = null;
            }
            this._publish('visualization.paused', this.getDiagnostics());
        }
    }

    resume() {
        if (this.status === 'paused') {
            this.status = 'running';
            this._startRenderLoop();
            this._publish('visualization.resumed', this.getDiagnostics());
        }
    }

    async stop() {
        this.status = 'stopped';
        if (this._animationFrameId) {
            cancelAnimationFrame(this._animationFrameId);
            this._animationFrameId = null;
        }
        if (this.ctx && this.canvas) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
        this._publish('visualization.stopped', this.getDiagnostics());
    }

    dispose() {
        this.stop();
        this.canvas = null;
        this.ctx = null;
        this.status = 'disposed';
    }

    // ─── Configuration Toggles ───────────────────────────────────────────────

    setOption(key, value) {
        if (key in this.config) {
            this.config[key] = value;
        }
    }

    setColor(key, value) {
        if (key in this.colors) {
            this.colors[key] = value;
        }
    }

    // ─── Event Bus Subscriptions ─────────────────────────────────────────────

    _subscribeToEvents() {
        if (!this.eventBus) return;
        this.eventBus.subscribe('landmarks.validated', (e) => {
            this._latestLandmarks = e.data || null;
        });
        this.eventBus.subscribe('biomechanics.updated', (e) => {
            this._latestBiomechanics = e.data || null;
        });
        this.eventBus.subscribe('pose.detected', (e) => {
            this._latestPose = e.data || null;
        });
    }

    // ─── Render Loop ─────────────────────────────────────────────────────────

    _startRenderLoop() {
        const loop = () => {
            if (this.status !== 'running') return;
            const t0 = performance.now();
            this._render();
            this.metrics.visualizationLatencyMs = roundVal(performance.now() - t0, 2);
            this._updateFpsCounter();
            this._animationFrameId = requestAnimationFrame(loop);
        };
        this._animationFrameId = requestAnimationFrame(loop);
    }

    _updateFpsCounter() {
        this._fpsFrameCount++;
        const now = performance.now();
        const elapsed = now - this._fpsLastTime;
        if (elapsed >= 1000) {
            this.metrics.renderFps = Math.round((this._fpsFrameCount * 1000) / elapsed);
            this.metrics.canvasFps = this.metrics.renderFps;
            this._fpsFrameCount = 0;
            this._fpsLastTime = now;
        }
        this.metrics.totalFrames++;
    }

    // ─── Main Render Dispatch ─────────────────────────────────────────────────

    _render() {
        if (!this.ctx || !this.canvas) return;

        const W = this.canvas.width / this.devicePixelRatio;
        const H = this.canvas.height / this.devicePixelRatio;
        const ctx = this.ctx;

        // Clear with transparent background so the <video> shows through
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        ctx.save();
        ctx.scale(this.devicePixelRatio, this.devicePixelRatio);

        // Mirror transform
        if (this.config.mirrorMode) {
            ctx.translate(W, 0);
            ctx.scale(-1, 1);
        }

        const trackingState = this._latestLandmarks?.tracking_state || 'NO_TRACKING';
        const coveragePct = this._latestLandmarks?.body_coverage_pct ?? 0.0;

        // 1. Skeleton & Joint Overlays (only if tracking is active)
        if (trackingState !== 'NO_TRACKING') {
            if (this.config.showSkeleton && this._latestLandmarks) {
                this._renderBones(ctx, W, H, this._latestLandmarks.landmarks || []);
                this._renderJoints(ctx, W, H, this._latestLandmarks.landmarks || []);
            }

            // 2. Joint angle labels
            if (this.config.showJointAngles && this._latestBiomechanics) {
                this._renderJointAngles(ctx, W, H, this._latestLandmarks?.landmarks || [], this._latestBiomechanics.joint_angles || []);
            }

            // 3. Joint name labels
            if (this.config.showJointLabels && this._latestLandmarks) {
                this._renderJointLabels(ctx, W, H, this._latestLandmarks.landmarks || []);
            }
        }

        // 4. Biomechanics overlays — do NOT mirror CoM/balance visuals (world-space)
        if (this.config.mirrorMode) { ctx.restore(); ctx.save(); ctx.scale(this.devicePixelRatio, this.devicePixelRatio); }

        if (trackingState !== 'NO_TRACKING') {
            if (this.config.showCenterOfMass && this._latestBiomechanics?.center_of_mass) {
                this._renderCenterOfMass(ctx, W, H, this._latestBiomechanics);
            }

            if (this.config.showBalance && this._latestBiomechanics?.balance) {
                this._renderBalanceBar(ctx, W, H, this._latestBiomechanics.balance);
            }

            if (this.config.showSymmetry && this._latestBiomechanics?.symmetry) {
                this._renderSymmetryIndicator(ctx, W, H, this._latestBiomechanics.symmetry);
            }

            if (this.config.showOrientationAxes && this._latestBiomechanics?.orientation) {
                this._renderOrientationAxes(ctx, W, H, this._latestBiomechanics.orientation);
            }
        }

        // 5. Pose overlay (top-left HUD)
        if (this.config.showPoseLabel && this._latestPose) {
            this._renderPoseHud(ctx, W, H, this._latestPose);
        }

        // 6. Rule evaluation overlay (bottom panel)
        if (this.config.showRuleEvaluation && this._latestPose) {
            this._renderRulePanel(ctx, W, H, this._latestPose);
        }

        // 7. Tracking Quality State Banner (Top Center Warning)
        if (trackingState !== 'FULL_BODY') {
            this._renderTrackingStateBanner(ctx, W, H, trackingState, coveragePct);
        }

        ctx.restore();

        this._publish('visualization.updated', {
            fps: this.metrics.renderFps,
            latencyMs: this.metrics.visualizationLatencyMs
        });
    }

    // ─── Skeleton Rendering ────────────────────────────────────────────────────

    _renderBones(ctx, W, H, landmarks) {
        ctx.lineWidth = this.config.boneLineWidth;
        ctx.strokeStyle = this.colors.bone;
        ctx.lineCap = 'round';

        for (const [a, b] of this.SKELETON_CONNECTIONS) {
            const lmA = landmarks[a];
            const lmB = landmarks[b];
            if (!lmA || !lmB) continue;
            const visA = lmA.visibility ?? 1.0;
            const visB = lmB.visibility ?? 1.0;
            const presA = lmA.presence ?? 1.0;
            const presB = lmB.presence ?? 1.0;

            if (visA < 0.6 || visB < 0.6 || presA < 0.6 || presB < 0.6) continue;

            const visMin = Math.min(visA, visB);
            ctx.globalAlpha = Math.min(1, 0.3 + visMin * 0.7);
            ctx.beginPath();
            ctx.moveTo(lmA.x * W, lmA.y * H);
            ctx.lineTo(lmB.x * W, lmB.y * H);
            ctx.stroke();
        }
        ctx.globalAlpha = 1;
    }

    _renderJoints(ctx, W, H, landmarks) {
        for (const lm of landmarks) {
            if (lm.x == null || lm.y == null) continue;
            const vis = lm.visibility ?? 1.0;
            const pres = lm.presence ?? 1.0;
            if (vis < 0.6 || pres < 0.6) continue;

            const color = this._visibilityColor(vis);
            ctx.beginPath();
            ctx.arc(lm.x * W, lm.y * H, this.config.jointRadius, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.globalAlpha = Math.min(1, 0.4 + vis * 0.6);
            ctx.fill();

            // White border
            ctx.strokeStyle = 'rgba(255,255,255,0.9)';
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }
        ctx.globalAlpha = 1;
    }

    // ─── Joint Labels & Angle Display ─────────────────────────────────────────

    _renderJointLabels(ctx, W, H, landmarks) {
        ctx.font = `${this.config.labelFontSize}px "Inter", monospace`;
        ctx.textAlign = 'left';
        for (const lm of landmarks) {
            if (!lm.name) continue;
            const vis = lm.visibility ?? 1.0;
            const pres = lm.presence ?? 1.0;
            if (vis < 0.6 || pres < 0.6) continue;
            const x = lm.x * W + 8;
            const y = lm.y * H - 4;
            this._drawLabelBox(ctx, lm.name, x, y, this.config.labelFontSize);
        }
    }

    _renderJointAngles(ctx, W, H, landmarks, jointAngles) {
        if (!jointAngles || jointAngles.length === 0) return;

        // Map landmark indices for angle anchor positions
        const ANGLE_ANCHORS = {
            left_knee:      25,
            right_knee:     26,
            left_hip:       23,
            right_hip:      24,
            left_elbow:     13,
            right_elbow:    14,
            left_shoulder:  11,
            right_shoulder: 12,
            neck:           0,
            spine:          23
        };

        ctx.font = `bold ${this.config.angleFontSize}px "Inter", monospace`;
        ctx.textAlign = 'center';

        for (const ja of jointAngles) {
            const idx = ANGLE_ANCHORS[ja.joint_name];
            if (idx == null) continue;
            const lm = landmarks[idx];
            if (!lm || (lm.visibility ?? 0) < 0.4) continue;

            const angle = (ja.angle ?? 0).toFixed(1);
            const x = lm.x * W;
            const y = lm.y * H - 14;
            const label = `${angle}°`;
            const color = this._angleColor(ja);
            this._drawLabelBox(ctx, label, x - 18, y - 8, this.config.angleFontSize, color);
        }
    }

    // ─── Biomechanics Overlays ────────────────────────────────────────────────

    _renderCenterOfMass(ctx, W, H, bioSnap) {
        const com = bioSnap.center_of_mass;
        if (!com) return;

        const x = com.x * W;
        const y = com.y * H;
        const r = this.config.comRadius;

        // Outer ring
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.strokeStyle = this.colors.comMarker;
        ctx.lineWidth = 2;
        ctx.stroke();

        // Inner dot
        ctx.beginPath();
        ctx.arc(x, y, r * 0.35, 0, Math.PI * 2);
        ctx.fillStyle = this.colors.comMarker;
        ctx.fill();

        // Label
        ctx.font = `10px "Inter", monospace`;
        ctx.fillStyle = this.colors.comMarker;
        ctx.textAlign = 'center';
        ctx.fillText('CoM', x, y + r + 12);
    }

    _renderBalanceBar(ctx, W, H, balance) {
        const barW = W * 0.35;
        const barH = 8;
        const barX = (W - barW) / 2;
        const barY = H - 32;
        const ratio = Math.max(0, Math.min(100, balance.leftRightRatio ?? 50)) / 100;

        // Background track
        ctx.fillStyle = 'rgba(0,0,0,0.4)';
        _roundRect(ctx, barX, barY, barW, barH, 4);
        ctx.fill();

        // Left side
        ctx.fillStyle = this.colors.balanceLine;
        _roundRect(ctx, barX, barY, barW * ratio, barH, 4);
        ctx.fill();

        // Centre mark
        const centerX = barX + barW / 2;
        ctx.beginPath();
        ctx.moveTo(centerX, barY - 3);
        ctx.lineTo(centerX, barY + barH + 3);
        ctx.strokeStyle = 'rgba(255,255,255,0.8)';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Labels
        ctx.font = '10px "Inter", monospace';
        ctx.fillStyle = 'rgba(255,255,255,0.8)';
        ctx.textAlign = 'left';
        ctx.fillText('L', barX - 12, barY + 7);
        ctx.textAlign = 'right';
        ctx.fillText('R', barX + barW + 12, barY + 7);
        ctx.textAlign = 'center';
        ctx.fillStyle = balance.isBalanced ? this.colors.good : this.colors.warning;
        ctx.fillText(`${(ratio * 100).toFixed(0)}% / ${((1 - ratio) * 100).toFixed(0)}%`, centerX, barY + barH + 16);
    }

    _renderSymmetryIndicator(ctx, W, H, symmetry) {
        if (!symmetry) return;
        const score = symmetry.overallSymmetry ?? 100;
        const color = score > 85 ? this.colors.good : score > 60 ? this.colors.warning : this.colors.poor;
        ctx.font = '11px "Inter", monospace';
        ctx.fillStyle = color;
        ctx.textAlign = 'right';
        ctx.fillText(`Symmetry ${score.toFixed(1)}%`, W - 12, 52);
    }

    _renderOrientationAxes(ctx, W, H, orientation) {
        if (!orientation) return;
        const cx = W - 50;
        const cy = H - 60;
        const len = 28;

        const fwd = (orientation.forwardLean ?? 0) * (Math.PI / 180);
        const side = (orientation.sideLean ?? 0) * (Math.PI / 180);

        // Forward axis (vertical)
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.sin(fwd) * len, cy - Math.cos(fwd) * len);
        ctx.strokeStyle = this.colors.good;
        ctx.lineWidth = 2;
        ctx.stroke();

        // Side axis (horizontal)
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(side) * len, cy + Math.sin(side) * len);
        ctx.strokeStyle = this.colors.tracking;
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.font = '9px monospace';
        ctx.fillStyle = 'rgba(255,255,255,0.7)';
        ctx.textAlign = 'center';
        ctx.fillText('Axis', cx, cy + 14);
    }

    // ─── Pose HUD ──────────────────────────────────────────────────────────────

    _renderPoseHud(ctx, W, H, poseResult) {
        const poseName  = poseResult.pose_name  ?? 'Unknown';
        const conf      = poseResult.confidence ?? 0;
        const holdTime  = poseResult.hold_time  ?? 0;

        const confColor = conf >= 80 ? this.colors.good : conf >= 50 ? this.colors.warning : this.colors.poor;

        // Background pill
        const padX = 14, padY = 8;
        const boxW = 200, boxH = 66;
        const bx = 14, by = 14;

        ctx.fillStyle = this.colors.overlay;
        _roundRect(ctx, bx, by, boxW, boxH, 10);
        ctx.fill();

        ctx.strokeStyle = confColor;
        ctx.lineWidth = 1.5;
        _roundRect(ctx, bx, by, boxW, boxH, 10);
        ctx.stroke();

        // Pose name
        ctx.font = `bold ${this.config.poseLabelFontSize}px "Inter", sans-serif`;
        ctx.fillStyle = this.colors.poseLabel;
        ctx.textAlign = 'left';
        ctx.fillText(poseName, bx + padX, by + padY + 18);

        // Confidence
        ctx.font = '12px "Inter", monospace';
        ctx.fillStyle = confColor;
        ctx.fillText(`${conf.toFixed(1)}% match`, bx + padX, by + padY + 36);

        // Hold timer
        ctx.fillStyle = 'rgba(255,255,255,0.65)';
        ctx.fillText(`Hold ${holdTime.toFixed(1)}s`, bx + padX, by + padY + 52);
    }

    // ─── Rule Evaluation Panel ─────────────────────────────────────────────────

    _renderRulePanel(ctx, W, H, poseResult) {
        const matched = poseResult.matched_rules ?? 0;
        const failed  = poseResult.failed_rules  ?? 0;
        const total   = matched + failed;
        if (total === 0) return;

        const panelW = 180, panelH = 44;
        const px = W - panelW - 14;
        const py = 14;

        ctx.fillStyle = this.colors.overlay;
        _roundRect(ctx, px, py, panelW, panelH, 8);
        ctx.fill();

        ctx.font = '11px "Inter", monospace';
        ctx.fillStyle = this.colors.good;
        ctx.textAlign = 'left';
        ctx.fillText(`✓ ${matched} rules matched`, px + 10, py + 18);

        ctx.fillStyle = failed > 0 ? this.colors.poor : 'rgba(255,255,255,0.4)';
        ctx.fillText(`✗ ${failed} rules failed`, px + 10, py + 34);
    }

    // ─── Helpers ──────────────────────────────────────────────────────────────

    _visibilityColor(vis) {
        if (!this.config.showConfidenceColors) return this.colors.tracking;
        if (vis >= this.config.confidenceGoodThreshold) return this.colors.good;
        if (vis >= this.config.confidenceWarnThreshold) return this.colors.warning;
        return this.colors.poor;
    }

    _angleColor(jointAngle) {
        const a = jointAngle.angle ?? 0;
        const inRange = a >= (jointAngle.expected_min ?? 0) && a <= (jointAngle.expected_max ?? 360);
        return inRange ? this.colors.good : this.colors.warning;
    }

    _drawLabelBox(ctx, text, x, y, fontSize, color = null) {
        const pad = 3;
        const tw  = ctx.measureText(text).width;
        ctx.fillStyle = this.colors.labelBg;
        _roundRect(ctx, x - pad, y - fontSize, tw + pad * 2, fontSize + pad * 2, 3);
        ctx.fill();
        ctx.fillStyle = color ?? 'rgba(255,255,255,0.9)';
        ctx.fillText(text, x, y);
    }

    _configureHighDpi() {
        if (!this.canvas) return;
        const dpr = window.devicePixelRatio || 1;
        this.devicePixelRatio = dpr;
        const cssW = this.canvas.clientWidth  || this.canvas.width;
        const cssH = this.canvas.clientHeight || this.canvas.height;
        this.canvas.width  = cssW * dpr;
        this.canvas.height = cssH * dpr;
        this.ctx.setTransform(1, 0, 0, 1, 0, 0); // reset
    }

    // ─── Resize & Fullscreen ──────────────────────────────────────────────────

    resize(width, height) {
        if (!this.canvas) return;
        const dpr = this.devicePixelRatio;
        this.canvas.style.width  = `${width}px`;
        this.canvas.style.height = `${height}px`;
        this.canvas.width  = width  * dpr;
        this.canvas.height = height * dpr;
    }

    requestFullscreen() {
        if (this.canvas?.requestFullscreen) {
            this.canvas.requestFullscreen();
        }
    }

    _renderTrackingStateBanner(ctx, W, H, trackingState, coveragePct) {
        ctx.save();
        const boxW = 340;
        const boxH = 56;
        const boxX = (W - boxW) / 2;
        const boxY = 16;

        ctx.fillStyle = trackingState === 'NO_TRACKING' ? 'rgba(220, 38, 38, 0.92)' : 'rgba(217, 119, 6, 0.92)';
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.lineWidth = 1.5;

        _roundRect(ctx, boxX, boxY, boxW, boxH, 8);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#FFFFFF';
        ctx.textAlign = 'center';

        if (trackingState === 'PARTIAL_BODY') {
            ctx.font = 'bold 14px "Inter", sans-serif';
            ctx.fillText('⚠️ Move farther away', W / 2, boxY + 22);
            ctx.font = '12px "Inter", sans-serif';
            ctx.fillText(`Full body not visible — Body visibility: ${coveragePct}%`, W / 2, boxY + 42);
        } else {
            ctx.font = 'bold 14px "Inter", sans-serif';
            ctx.fillText('🚫 No person detected', W / 2, boxY + 22);
            ctx.font = '12px "Inter", sans-serif';
            ctx.fillText('Step into frame or adjust camera angle', W / 2, boxY + 42);
        }
        ctx.restore();
    }

    // ─── Diagnostics & Publishing ─────────────────────────────────────────────

    getDiagnostics() {
        return {
            name:         this.name,
            version:      this.version,
            status:       this.status,
            priority:     this.priority,
            dependencies: this.dependencies,
            config:       { ...this.config },
            metrics:      { ...this.metrics }
        };
    }

    _publish(eventName, data) {
        if (this.eventBus && typeof this.eventBus.publish === 'function') {
            this.eventBus.publish(eventName, data);
        }
    }
}

// ─── Canvas Utilities ────────────────────────────────────────────────────────

function _roundRect(ctx, x, y, w, h, r = 4) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y,     x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
}

function roundVal(num, decimals = 2) {
    return Number(Math.round(num + 'e' + decimals) + 'e-' + decimals);
}
