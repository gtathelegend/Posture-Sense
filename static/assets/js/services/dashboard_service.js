/**
 * DashboardService
 * Fetches analytics stats for user dashboard.
 */

export class DashboardService {
    static async fetchStats() {
        try {
            const response = await fetch('/api/dashboard_stats');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching dashboard stats:', error);
            throw error;
        }
    }
}
