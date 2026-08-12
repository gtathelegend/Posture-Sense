# PostureSense v2 — Dashboard Audit

## Overview

This audit documents the existing user dashboard implementation in PostureSense v2, covering `templates/dashboard.html`, `static/assets/js/services/dashboard_service.js`, `backend/app/blueprints/dashboard/routes.py`, and `backend/app/services/dashboard_service.py`.

---

# 1. Current Dashboard Structure

```
+-----------------------------------------------------------------------+
|  [Header Hero] "Your Dashboard"                                       |
|  Live Updates Active Badge (Pulse Dot)                               |
+-----------------------------------------------------------------------+
|  [Card 1: Total Sessions]  | [Card 2: Minutes Practiced] | [Card 3] |
|        12 Sessions         |        8.1 Mins             |  87.4%   |
+-----------------------------------------------------------------------+
|  [Pose Distribution Card]                                             |
|  Tree Pose   ===========================[80%] (5 sessions)            |
|  Warrior II  =====================[60%] (4 sessions)                  |
|  Plank       ==============[40%] (3 sessions)                         |
+-----------------------------------------------------------------------+
|  [Recent Sessions Table] (Up to 20 rows)                              |
|  Date & Time           | Pose        | Duration | Accuracy            |
|  2026-08-12 14:30:00   | Tree Pose   | 45.0s    | 92.5%               |
+-----------------------------------------------------------------------+
```

---

# 2. Detailed Element & Data Audit

### A. Summary Cards (Stats Cards)
1. **Total Sessions Card**
   - **Rendered HTML:** `<div class="dash-stat-num">{{ total_sessions }}</div>`
   - **Data Source:** `DashboardService.get_user_dashboard_data()` $\to$ `len(sessions)`
   - **Live Update:** Polled via `GET /api/dashboard_stats`, updated via `animateValue()`.

2. **Minutes Practiced Card**
   - **Rendered HTML:** `<div class="dash-stat-num">{{ "%.1f"|format(total_duration / 60) }}</div>`
   - **Data Source:** `sum(s.duration for s in sessions)` divided by 60.
   - **Live Update:** Polled via `GET /api/dashboard_stats`.

3. **Average Accuracy Card**
   - **Rendered HTML:** `<div class="dash-stat-num">{{ "%.1f"|format(avg_accuracy) }}%</div>`
   - **Data Source:** `sum(s.accuracy for s in sessions) / len(sessions)`.
   - **Live Update:** Polled via `GET /api/dashboard_stats`.

### B. Pose Distribution Component
- **Rendered HTML:** `<div class="pose-dist-card">`
- **Visualization Method:** Raw HTML/CSS progress bars with inline width percentage calculated against the pose with maximum count:
  $$\text{width \%} = \frac{\text{pose\_count}}{\max(\text{pose\_counts})} \times 100$$
- **Data Source:** `pose_counts` dictionary from `DashboardService`.
- **Limitation:** Only shows relative proportion against highest count; does not show average accuracy per pose or hold duration per pose.

### C. Recent Sessions Table
- **Rendered HTML:** `<table class="ps-table">`
- **Columns:** Date & Time (`timestamp`), Pose (`pose_label`), Duration (`duration`), Accuracy (`accuracy`).
- **Data Source:** `sessions[:20]` array returned by `SessionRepository.fetch_sessions_by_user_id()`.
- **Live Update:** Dynamically rebuilds `<tbody>` inner HTML on polling tick.

---

# 3. Client-Side Polling Architecture

- **Polling Logic in `dashboard.html`:**
```javascript
setInterval(updateDashboard, 3000);
document.addEventListener('visibilitychange', function() {
  if (!document.hidden) updateDashboard();
});
```
- **Execution:** Every 3 seconds, `updateDashboard()` issues `fetch('/api/dashboard_stats')`.
- **Performance Evaluation:** Polling database every 3 seconds for static session history causes unnecessary server load and SQL queries, especially when no active pose detection session is running.

---

# 4. Dead Data, Mock Data & Limitations

1. **Dead / Unused JS Service:**
   - `static/assets/js/services/dashboard_service.js` exports `DashboardService.fetchStats()`, but `dashboard.html` defines an inline `fetch('/api/dashboard_stats')` directly rather than importing `DashboardService`.

2. **Hardcoded / Fallback Analytics in Backend:**
   - In `ReportService.generate_session_report()`, reps and tracking quality are hardcoded (`completed_reps: 10`, `tracking_quality: 100.0`) due to missing database columns.
   - `AnalyticsRepository` hardcodes `streak_days: 0`.

3. **Missing Essential Dashboard Features:**
   - **No Charts:** No historical line charts for score trends over 7/30 days.
   - **No Biomechanics Analytics:** No cards or breakdown for Symmetry, Balance, Stability, or ROM.
   - **No Personal Records Card:** Does not display user achievements (Highest Score, Longest Hold).
   - **No Session Comparison:** Cannot compare current session performance to previous session.
   - **No Filter Controls:** No date range or pose filter options.

4. **Missing UX States:**
   - **Loading State:** No loading skeletons or spinners on page initialization.
   - **Error State:** If `fetch` fails or user session expires, it only logs `console.error` without alerting the user or displaying a retry button.

5. **Naming Inconsistencies:**
   - The UI refers to posture score as **"Accuracy"** (`avg_accuracy`, `badge-accuracy`), whereas perception engine contracts call it **`overall_score`** or **`posture_score`**.
