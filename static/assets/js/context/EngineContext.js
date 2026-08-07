/**
 * EngineContext
 * State container for future engine status, fps, landmark tracking state, and current pose.
 */

export class EngineContext {
    constructor() {
        this.status = 'uninitialized';
        this.fps = 0;
        this.currentPose = 'Unknown';
        this.lastPose = 'Unknown';
        this.isCameraActive = false;
        this.listeners = [];
    }

    updateState(newState) {
        Object.assign(this, newState);
        this.notify();
    }

    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    notify() {
        this.listeners.forEach(listener => listener(this));
    }
}
