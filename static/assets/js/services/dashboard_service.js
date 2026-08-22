/**
 * DashboardService
 * Client-side service layer for fetching Dashboard V2 overview analytics,
 * timeframe trends, biomechanics aggregates, and personal records.
 */

export class DashboardService {
    static async fetchOverview(timeframe = '30d') {
        try {
            const response = await fetch(`/api/dashboard/overview?timeframe=${timeframe}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching dashboard overview analytics:', error);
            throw error;
        }
    }

    static async fetchStats(timeframe = '30d') {
        try {
            const response = await fetch(`/api/dashboard_stats?timeframe=${timeframe}`);
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
