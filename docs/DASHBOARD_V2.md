# PostureSense v2 — Dashboard V2 & User Progress Intelligence Documentation

## 1. Architecture Overview

Dashboard V2 transforms raw persisted session telemetry from Supabase into actionable longitudinal posture intelligence.

```text
Supabase PostgreSQL (pose_sessions table)
         ↓
SessionRepository.fetch_sessions_by_user_id(user_id)
         ↓
DashboardService.get_user_dashboard_overview(user_id, timeframe)
         ↓
GET /api/dashboard/overview?timeframe=30d
         ↓
Client Dashboard UI (templates/dashboard.html + Chart.js)
```

---

## 2. API Contract

### Endpoint: `GET /api/dashboard/overview`

**Query Parameters:**
- `timeframe`: `'7d'` | `'30d'` | `'all'` (default: `'30d'`)

**Headers:**
- Cookie / Session authorization required (`@login_required`)

**Response Schema:**
```json
{
  "timeframe": "30d",
  "total_sessions": 12,
  "total_sessions_all": 15,
  "total_duration": 450.0,
  "overall_average_score": 87.4,
  "streak_days": 7,
  "seven_day_delta": 4.2,
  "biomechanics": {
    "symmetry": 92.4,
    "balance": 88.7,
    "stability": 94.1,
    "rom": 89.2,
    "tracking_quality": 97.8,
    "tracking_status": "Excellent"
  },
  "totals": {
    "reps": 0,
    "hold_time": 420.0
  },
  "trend": {
    "points": [
      {
        "session_id": 101,
        "date": "2026-08-10",
        "score": 82.5,
        "duration": 45.0,
        "pose_label": "Tree Pose"
      }
    ],
    "slope": 5.2,
    "direction": "IMPROVING",
    "observation_count": 12
  },
  "pose_counts": {
    "Tree Pose": 8,
    "Warrior II": 4
  },
  "pose_cards": [
    {
      "pose_label": "Tree Pose",
      "sessions": 8,
      "avg_score": 91.4,
      "best_score": 96.2,
      "avg_hold": 38.0,
      "best_hold": 52.0,
      "avg_reps": 0.0,
      "best_symmetry": 95.0,
      "best_rom": 94.0
    }
  ],
  "strongest_pose": { "pose_label": "Tree Pose", "avg_score": 91.4 },
  "weakest_pose": { "pose_label": "Warrior II", "avg_score": 81.2 },
  "personal_records": [
    {
      "id": "rec_score",
      "record_type": "Highest Score",
      "pose_label": "Tree Pose",
      "value": 96.2,
      "unit": "pts",
      "date": "Aug 12, 2026"
    }
  ],
  "insights": [
    {
      "id": "insight_score_imp_Tree Pose",
      "title": "Pose Progress",
      "message": "Your Tree Pose score improved 12.5% across your recent sessions.",
      "type": "achievement",
      "icon": "📈"
    }
  ],
  "session_comparison": {
    "has_comparison": true,
    "latest_session": {},
    "previous_session": {},
    "metrics": {
      "overall_score": { "prev": 82.4, "latest": 89.2, "delta": "+6.8", "semantic": "positive" }
    }
  },
  "recent_sessions": []
}
```

---

## 3. UI Component Architecture

1. **Dashboard Header:** Greeting, current date, active streak pill (`🔥 7 day streak`), CTA button to `/pose_detection`.
2. **Overview Cards Grid:** 4-column layout displaying Total Sessions, Practice Time (`<60m`: `42 min`, `>=60m`: `2h 14m`), Posture Score (`87.4% (+4.2% vs last week)`), and Practice Streak (`🔥 7 Days` / `Start your streak today`).
3. **Score Progress Chart:** Chronological Chart.js line chart with timeframe filters (`7d`, `30d`, `all`), slope badges, tooltips, and insufficient data notices (<3 sessions).
4. **Movement Quality Panel:** Symmetry, Balance, Stability, ROM progress bars with period comparison. Null values default to `'N/A'` and `0%` width without fabricating 100%.
5. **Tracking Quality Card:** Separate telemetry health indicator with threshold classifications (`>=90` Excellent, `>=75` Good, `>=50` Fair, `<50` Low) and explanation tooltips.
6. **Personal Records Grid:** 7 achievement badges for Highest Score, Longest Hold, Best Symmetry, Best Balance, Best Stability, Best ROM, and Most Repetitions. Shows "No record yet" when unachieved.
7. **Deterministic Insights Engine:** Evaluates 5 strict rules without LLMs:
   - Score Improvement (`>=3` sessions, `>=10%` gain)
   - Symmetry Improvement (`>=5%` gain)
   - Hold Record (latest hold > previous best)
   - Consistency (`>=7` of last 10 sessions `>=80`)
   - Streak Milestones (`3`, `7`, `14`, `30`, `60`, `100` days)
   - Baseline messages for 0 or 1-2 sessions.
8. **Pose Performance Breakdown:** Individual pose cards with session frequency, scores, hold times, repetitions, best symmetry, best ROM, and Strongest vs Needs Practice comparison callout (`>=2` poses).
9. **Latest vs Previous Session Comparison:** Delta breakdown table comparing latest 2 sessions across 8 metrics with positive/negative/neutral semantic badges.
10. **Recent Sessions History:** Expandable table detailing date, pose, score, duration, hold, reps, tracking quality, form corrections (`failed_rules`), or legacy session notices.

---

## 4. Refresh Architecture & UX States

- **No Continuous Polling:** Eliminated `setInterval(updateDashboard, 3000)`.
- **Triggered Refreshes:** Initial load, timeframe filter click, manual retry button, window visibility tab focus (throttled to max 1 per 30s).
- **Loading State:** Shimmering skeleton placeholders during fetch.
- **Empty State:** Dedicated onboarding card when `total_sessions_all == 0`.
- **Error State:** Red alert notification banner with manual `[ Retry ]` button.

---

## 5. Legacy Data & Privacy Safety

- Legacy sessions lacking rich telemetry preserve `NULL` columns.
- `NULL` metrics display as `'N/A'` or `'Detailed analytics unavailable'` in the UI and are never converted to fake `100%` values.
- Landmark coordinates, canvas drawings, and camera streams remain local to the browser memory and are never transmitted to the backend.
