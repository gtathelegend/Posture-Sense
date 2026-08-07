/**
 * Session & API Types Definition
 */

export class SessionType {
    constructor({ id, user_id, pose_label, timestamp, duration = 0.0, accuracy = 0.0 } = {}) {
        this.id = id || '';
        this.user_id = user_id || '';
        this.pose_label = pose_label || 'Unknown Pose';
        this.timestamp = timestamp || new Date().toISOString();
        this.duration = duration;
        this.accuracy = accuracy;
    }
}

export class ApiResponse {
    constructor({ status = 'success', message = '', data = null } = {}) {
        this.status = status;
        this.message = message;
        this.data = data;
    }

    isSuccess() {
        return this.status === 'success' || this.status === 'ok';
    }
}
