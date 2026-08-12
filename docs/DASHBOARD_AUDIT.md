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

# 3. Client-Side Polling Architecture (REMOVED & RESOLVED)

- **Previous Polling Logic:** `setInterval(updateDashboard, 3000)` has been **eliminated**.
- **Current V2 Refresh Architecture:** Initial page load, timeframe filter toggle, manual retry button, and window visibility tab re-focus (throttled to at most once per 30s).

---

# 4. Audit Resolutions in Dashboard V2

1. **JS Service Integration:** ✅ **RESOLVED**. `static/assets/js/services/dashboard_service.js` exports `fetchOverview()` and `fetchStats()` for modular fetch calls.
2. **Hardcoded / Fallback Analytics:** ✅ **RESOLVED**. `ReportService` and `AnalyticsRepository` now aggregate real DB values; hardcoded fallbacks eliminated.
3. **Dashboard V2 Features:**
   - **Score Trend Chart:** ✅ **RESOLVED**. Integrated Chart.js interactive line chart with 7d/30d/all toggles.
   - **Biomechanics Analytics:** ✅ **RESOLVED**. Added Movement Quality horizontal bars (Symmetry, Balance, Stability, ROM) + Tracking Quality card.
   - **Personal Records Card:** ✅ **RESOLVED**. Achievements grid displaying Highest Score, Longest Hold, Best Symmetry, Best Balance, Best ROM, Most Reps.
   - **Session Comparison:** ✅ **RESOLVED**. Latest vs Previous session metric comparison table with semantic color deltas.
   - **Filter Controls:** ✅ **RESOLVED**. 7 Days, 30 Days, All Time timeframe selectors.
4. **UX States:**
   - **Loading State:** ✅ **RESOLVED**. Shimmering skeleton placeholders implemented.
   - **Error State:** ✅ **RESOLVED**. Visible red alert banner with manual `[ Retry ]` button.
   - **Empty State:** ✅ **RESOLVED**. Friendly onboarding card for `total_sessions == 0`.
5. **Naming Inconsistencies:** ✅ **RESOLVED**. UI labels updated to `"Posture Score"` and `"Overall Score"`.
