# PostureSense v2 — Dashboard V2 & User Progress Intelligence Specification

## 1. Executive Summary

Dashboard V2 transforms raw real-time posture perception data into actionable longitudinal fitness intelligence. By elevating browser-side perception metrics into dimensional biomechanics (symmetry, balance, stability, range of motion), practice habits (streaks, consistency), personal records, deterministic feedback insights, and session-over-session deltas, the dashboard empowers users to track posture correction over time.

---

## 2. Information Architecture

```text
+-----------------------------------------------------------------------------------+
|  HEADER: Greeting, Active User Profile, Practice Streak Badge, Quick Action Button |
+-----------------------------------------------------------------------------------+
|  SECTION 1: OVERVIEW METRIC CARDS (4-Column Layout)                               |
|  [ Total Sessions ] [ Practice Time ] [ Overall Posture Score ] [ Active Streak ] |
+-----------------------------------------------------------------------------------+
|  SECTION 2: PROGRESS & TREND ANALYTICS (2-Column Main Grid)                      |
|  +-------------------------------------------+----------------------------------+ |
|  | Main Chart: 7d / 30d / All Score Trend  | Biomechanics Bar & Data Quality  | |
|  | Chart.js line chart with trend slope     | Symmetry, Balance, Stability, ROM| |
|  +-------------------------------------------+----------------------------------+ |
+-----------------------------------------------------------------------------------+
|  SECTION 3: PERSONAL RECORDS & INSIGHTS (2-Column Grid)                           |
|  +-------------------------------------------+----------------------------------+ |
|  | Personal Records Grid                     | Deterministic Insights Feed      | |
|  | - Highest Score   - Best Symmetry         | - "Warrior II score +12%..."     | |
|  | - Longest Hold    - Best ROM             | - "Streak milestone unlocked!"   | |
|  +-------------------------------------------+----------------------------------+ |
+-----------------------------------------------------------------------------------+
|  SECTION 4: POSE & EXERCISE PERFORMANCE BREAKDOWN                                 |
|  Interactive Pose Cards with Session Count, Best Score, Avg Hold Time, ROM        |
|  Strongest Pose vs Needs Practice Comparison Callout                              |
+-----------------------------------------------------------------------------------+
|  SECTION 5: LATEST VS PREVIOUS SESSION COMPARISON MATRIX                          |
|  Metric-by-metric comparison with semantic color states (+/-)                    |
+-----------------------------------------------------------------------------------+
|  SECTION 6: RECENT SESSION HISTORY                                                |
|  Expandable table rows showing telemetry detail, form flaws, or legacy notice     |
+-----------------------------------------------------------------------------------+
```

---

## 3. Dashboard API Contract (`GET /api/dashboard/overview`)

**Request:** `GET /api/dashboard/overview?timeframe=30d` (Supports `7d`, `30d`, `all`)

**Response Schema:**
```json
{
  "timeframe": "30d",
  "total_sessions": 12,
  "total_sessions_all": 12,
  "total_duration": 485.5,
  "avg_accuracy": 87.4,
  "overall_average_score": 87.4,
  "streak_days": 7,
  "seven_day_delta": 3.2,
  "biomechanics": {
    "symmetry": 94.2,
    "balance": 88.5,
    "stability": 91.0,
    "rom": 95.0,
    "tracking_quality": 98.4,
    "tracking_status": "Excellent"
  },
  "totals": {
    "reps": 18,
    "hold_time": 142.5
  },
  "trend": {
    "points": [
      {
        "session_id": "101",
        "date": "2026-08-10",
        "score": 82.5,
        "duration": 30.0,
        "pose_label": "Tree Pose"
      }
    ],
    "slope": 5.2,
    "direction": "IMPROVING",
    "observation_count": 12
  },
  "pose_cards": [
    {
      "pose_label": "Tree Pose",
      "sessions": 5,
      "avg_score": 91.4,
      "best_score": 96.2,
      "avg_hold": 38.0,
      "best_hold": 52.0,
      "best_symmetry": 95.0,
      "best_rom": 96.0
    }
  ],
  "strongest_pose": { "pose_label": "Tree Pose", "avg_score": 91.4 },
  "weakest_pose": { "pose_label": "Warrior II", "avg_score": 76.8 },
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
      "id": "rule_streak_7",
      "title": "Streak Milestone",
      "message": "You're on a 7-day practice streak!",
      "type": "habit",
      "icon": "🔥"
    }
  ],
  "session_comparison": {
    "has_comparison": true,
    "metrics": {
      "overall_score": { "prev": 84.2, "latest": 91.5, "delta": "+7.3", "semantic": "positive" },
      "symmetry": { "prev": 88.1, "latest": 94.0, "delta": "+5.9", "semantic": "positive" }
    }
  },
  "recent_sessions": [
    {
      "session_id": "105",
      "timestamp": "2026-08-12 14:30:00",
      "pose_label": "Warrior II",
      "duration": 45.0,
      "accuracy": 92.5,
      "reps": 0,
      "symmetry_score": 94.2,
      "balance_score": 88.5,
      "stability_score": 91.0,
      "rom_score": 95.0,
      "hold_time": 42.5,
      "tracking_quality": 98.4,
      "failed_rules": ["left_knee_angle_low"],
      "is_legacy": false
    }
  ]
}
```

---

## 4. Deterministic Insights Rules (Non-LLM)

1. **Score Improvement Rule:** $\ge 3$ sessions for pose AND percentage change $\ge 10\%$.
   - *Message:* `"Your {pose} score improved {pct}% over your last {N} sessions."`
2. **Symmetry Milestone Rule:** Postural symmetry in period improves $\ge 5\%$.
   - *Message:* `"Your postural symmetry improved {pct}%."`
3. **Hold Record Rule:** Latest hold time > previous best hold for pose.
   - *Message:* `"New record: {pose} hold for {duration}s."`
4. **Consistency Benchmark Rule:** $\ge 7$ of last 10 sessions score $\ge 80$.
   - *Message:* `"Great consistency — {count} of your last 10 sessions scored 80+."`
5. **Streak Milestone Rule:** Streak is in `[3, 7, 14, 30, 60, 100]`.
   - *Message:* `"You're on a {N}-day practice streak!"`
6. **Insufficient Data Fallback:** $< 2$ total sessions exist.
   - *Message:* `"Complete 2 more sessions to establish a progress trend."`

---

## 5. UI States & Refresh Architecture

- **Elimination of 3-Second Database Polling:** High-frequency polling has been removed to conserve server resources and prevent database lock contention.
- **Refresh Triggers:**
  1. Initial page load (`fetchDashboardData(timeframe)`).
  2. Timeframe filter click (`7d`, `30d`, `all`).
  3. Window visibility change (at most once every 30 seconds when re-focusing tab).
  4. Manual retry button click on error.
- **Loading State:** Skeleton shimmering cards and chart placeholders.
- **Empty State (`total_sessions_all == 0`):** Friendly onboarding panel with call-to-action button *"Start Pose Detection"*. Zero scores are hidden.
- **Error State:** Visible red alert banner with retry button.

---

## 6. Legacy Data Handling & Security

- **Legacy Detection:** Database rows stored prior to analytics persistence migration are identified by `is_legacy: true`.
- **UI Guard:** Expanded session history table displays `"Detailed biomechanics unavailable for this session"` instead of rendering fabricated 100% scores.
- **User Data Isolation:** All endpoint queries enforce strict user isolation via `current_user.id` and Supabase `.eq('user_id', str(user_id))`.
- **Privacy Boundary:** Video streams, canvas renders, and raw 33 MediaPipe landmark coordinate arrays remain strictly browser-local.
