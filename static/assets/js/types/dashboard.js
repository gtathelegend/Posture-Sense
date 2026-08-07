/**
 * Dashboard Stats Type Definition
 */

export class DashboardStatsType {
    constructor({ total_sessions = 0, total_duration = 0, avg_accuracy = 0.0, pose_counts = {}, recent_sessions = [] } = {}) {
        this.total_sessions = total_sessions;
        this.total_duration = total_duration;
        this.avg_accuracy = avg_accuracy;
        this.pose_counts = pose_counts;
        this.recent_sessions = recent_sessions;
    }
}
