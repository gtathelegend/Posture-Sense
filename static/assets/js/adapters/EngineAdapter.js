/**
 * EngineAdapter
 * Translates EventBus events into frontend EngineContext state updates.
 */

export class EngineAdapter {
    constructor(eventBus, engineContext) {
        this.eventBus = eventBus;
        this.engineContext = engineContext;
        this.subscriptions = [];
    }

    attach() {
        if (!this.eventBus) return;

        // Translate Camera Events
        this._subscribe('camera.started', (event) => {
            this.engineContext.updateState({ isCameraActive: true, status: 'running' });
        });

        this._subscribe('camera.stopped', (event) => {
            this.engineContext.updateState({ isCameraActive: false, status: 'stopped' });
        });

        // Translate Pose Events
        this._subscribe('pose.recognized', (event) => {
            const data = event.data || {};
            this.engineContext.updateState({
                currentPose: data.pose_name || 'Recognized Pose',
                status: 'tracking'
            });
        });

        this._subscribe('pose.changed', (event) => {
            const data = event.data || {};
            this.engineContext.updateState({
                lastPose: this.engineContext.currentPose,
                currentPose: data.pose_name || 'Changed Pose'
            });
        });

        // Translate Error Events
        this._subscribe('camera.error', (event) => {
            this.engineContext.updateState({ status: 'error' });
        });
    }

    _subscribe(eventName, handler) {
        if (this.eventBus && typeof this.eventBus.subscribe === 'function') {
            this.eventBus.subscribe(eventName, handler);
            this.subscriptions.push({ eventName, handler });
        }
    }

    detach() {
        if (!this.eventBus) return;
        this.subscriptions.forEach(({ eventName, handler }) => {
            if (typeof this.eventBus.unsubscribe === 'function') {
                this.eventBus.unsubscribe(eventName, handler);
            }
        });
        this.subscriptions = [];
    }
}
