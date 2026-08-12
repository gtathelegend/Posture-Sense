# PostureSense v2 — Dashboard Product Specification & Architecture

## 1. Product Goal

The objective of the PostureSense v2 Dashboard is to transform real-time posture perception telemetry into actionable, longitudinal fitness intelligence. By elevating raw scores into dimensional insights (symmetry, balance, stability, ROM), practice habits (streaks, consistency), personal achievements, and session-over-session progress, the dashboard empowers users to track posture correction and physical movement progress over time.

---

## 2. User Questions Answered

The redesigned dashboard directly answers key user questions:
1. *"Am I improving my posture accuracy over time?"* (Score trends & progress %)
2. *"Is my left/right physical symmetry getting better?"* (Biomechanics symmetry trend)
3. *"Which poses or exercises am I strongest and weakest at?"* (Pose performance breakdown)
4. *"What are my personal records and longest pose holds?"* (Personal Records card)
5. *"How did my latest session compare to my previous session?"* (Session comparison delta)
6. *"Am I maintaining a consistent practice routine?"* (Streak calendar & consistency score)

---

## 3. Information Architecture

```
+-----------------------------------------------------------------------------------+
|  HEADER: Greeting, Active User Profile, Practice Streak Badge, Quick Action Button |
+-----------------------------------------------------------------------------------+
|  SECTION 1: OVERVIEW METRIC CARDS (4-Column Layout)                               |
|  [ Total Sessions ] [ Practice Time ] [ Overall Average Score ] [ Active Streak ]  |
+-----------------------------------------------------------------------------------+
|  SECTION 2: PROGRESS & TREND ANALYTICS (2-Column Main Grid)                      |
|  +-------------------------------------------+----------------------------------+ |
|  | Main Chart: 7d / 30d Score Trend         | Biomechanics Radar / Bar Chart   | |
|  | Line chart with confidence bounds         | Symmetry, Balance, Stability, ROM| |
|  +-------------------------------------------+----------------------------------+ |
+-----------------------------------------------------------------------------------+
|  SECTION 3: PERSONAL RECORDS & INSIGHTS (2-Column Grid)                           |
|  +-------------------------------------------+----------------------------------+ |
|  | Personal Records Grid                     | Deterministic Insights Feed      | |
|  | - Highest Score   - Best Symmetry         | - "Warrior II score +12%..."     | |
|  | - Longest Hold    - Best ROM             | - "Streak achievement unlocked!" | |
|  +-------------------------------------------+----------------------------------+ |
+-----------------------------------------------------------------------------------+
|  SECTION 4: POSE & EXERCISE PERFORMANCE BREAKDOWN                                 |
|  Interactive Pose Cards with Session Count, Best Score, Avg Hold Time, ROM       |
+-----------------------------------------------------------------------------------+
|  SECTION 5: RECENT SESSIONS & COMPARISON TABLE                                    |
|  Interactive table with session row expander showing detailed component deltas   |
+-----------------------------------------------------------------------------------+
```

---

## 4. Summary Cards Specification

1. **Total Sessions Card:** Total completed posture detection sessions. (Icon: 📷)
2. **Practice Time Card:** Total accumulated practice minutes, formatted dynamically (e.g. `45 mins` or `2.5 hrs`). (Icon: ⏱️)
3. **Overall Average Score Card:** Mean accuracy score with 7-day delta badge (e.g., `88.5% (+3.2% vs last week)`). (Icon: 📈)
4. **Practice Streak Card:** Current consecutive active days count with flame indicator. (Icon: 🔥)

---

## 5. Visual Charts Specification

1. **Score Progression Chart:**
   - **Type:** Line Chart (Chart.js or SVG).
   - **Timeframe Toggles:** `7 Days`, `30 Days`, `All Time`.
   - **Data Points:** Session average scores chronologically plotted with trendline (linear regression slope).
2. **Biomechanics Dimensional Radar / Bar Chart:**
   - **Type:** 4-Axis Radar or Grouped Bar Chart.
   - **Metrics:** `Symmetry`, `Balance`, `Stability`, `Range of Motion (ROM)`.
   - **Benchmark:** Current Session score vs 30-Day Average score.

---

## 6. Pose Analytics & Hold Duration

- **Card Layout per Pose:**
  - Pose Name & Icon (e.g., Tree Pose, Warrior II, Plank).
  - Session Count & Frequency percentage.
  - Average Score & All-Time Best Score.
  - Longest Hold Duration (seconds) & Average Hold Duration.
  - Common posture flaw tag (derived from `failed_rules`).

---

## 7. Biomechanics Analytics Specification

- **Symmetry Metric:** Bilateral alignment score (0-100%). Measures shoulder and hip tilt symmetry.
- **Balance Metric:** Center of mass stability score (0-100%). Measures body weight centering over base of support.
- **Stability Metric:** Postural steadiness score (0-100%). Measures body sway amplitude during static holds.
- **Range of Motion (ROM):** Joint flexibility depth score (0-100%). Measures angular extension vs target joint angle.

---

## 8. Personal Records Specification

Renders achievement badges highlighting user milestones:
- **Highest Score:** Max `accuracy` across all sessions.
- **Longest Hold:** Max `hold_time` / `duration` for static pose.
- **Best Symmetry:** Highest recorded bilateral symmetry score.
- **Best Balance:** Highest recorded balance alignment score.
- **Best ROM:** Deepest range of motion achieved.
- **Most Repetitions:** Highest completed rep count in a single exercise session.

---

## 9. Session Comparison Design Matrix

The following matrix classifies all metrics for comparing **Current Session vs Previous Session**:

| Comparison Metric | Availability Status | Calculation & Source Method |
| :--- | :--- | :--- |
| **Score Delta** | **AVAILABLE** | $\text{Score}_{\text{current}} - \text{Score}_{\text{previous}}$ using `pose_sessions.accuracy`. |
| **Duration Delta** | **AVAILABLE** | $\text{Duration}_{\text{current}} - \text{Duration}_{\text{previous}}$ using `pose_sessions.duration`. |
| **Pose Frequency** | **AVAILABLE** | Grouping count comparison using `pose_sessions.pose_label`. |
| **Symmetry Delta** | **REQUIRES PERSISTENCE** | Requires `symmetry_score` column in `pose_sessions`. |
| **Balance Delta** | **REQUIRES PERSISTENCE** | Requires `balance_score` column in `pose_sessions`. |
| **Stability Delta** | **REQUIRES PERSISTENCE** | Requires `stability_score` column in `pose_sessions`. |
| **ROM Delta** | **REQUIRES PERSISTENCE** | Requires `rom_score` column in `pose_sessions`. |
| **Hold Time Delta** | **REQUIRES PERSISTENCE** | Requires `hold_time` column in `pose_sessions`. |
| **Repetition Delta** | **REQUIRES PERSISTENCE** | Requires `reps` column in `pose_sessions`. |
| **Tracking Quality Delta** | **REQUIRES PERSISTENCE** | Requires `tracking_quality` column in `pose_sessions`. |
| **Raw Landmark Delta** | **NOT AVAILABLE** | Raw 3D landmark arrays are deliberately unpersisted for user privacy. |

---

## 10. Insight Engine Design (Deterministic & Non-LLM)

The Insight Engine evaluates rule templates against user analytics. **No LLM is used.**

### Insight Rule Definitions:

1. **Exercise Improvement Rule:**
   - *Condition:* $N \ge 3$ sessions for `exercise_id` AND score percentage change $\ge +10\%$.
   - *Message Template:* `"Your {pose_label} score improved {pct}% over your last {N} sessions!"`

2. **Symmetry Milestone Rule:**
   - *Condition:* Monthly mean symmetry score exceeds previous month mean by $\ge 5\%$.
   - *Message Template:* `"Your overall postural symmetry improved {pct}% this month."`

3. **Personal Record Hold Rule:**
   - *Condition:* Current session `hold_time` > stored `best_hold_time` for pose.
   - *Message Template:* `"You achieved your longest {pose_label} hold: {duration}s!"`

4. **Consistency Benchmark Rule:**
   - *Condition:* $\ge 7$ of last 10 sessions have `accuracy` $\ge 80.0$.
   - *Message Template:* `"Great consistency! You scored above 80 in {count} of your last 10 sessions."`

5. **Streak Milestone Rule:**
   - *Condition:* `streak_days` in `[3, 7, 14, 30, 60, 100]`.
   - *Message Template:* `"You're on a {streak_days}-day practice streak! Keep it up!"`

---

## 11. Data Quality & Quality Gates

- **Quality Gate Rule:** If `tracking_quality < 50.0` or `score_confidence < 0.4`, the session data is flagged as `LOW_QUALITY`.
- **Filtering:** Low-quality sessions are excluded from trend regression calculations, streak calculations, and personal record evaluations to prevent camera occlusion or poor lighting artifacts from skewing user progress metrics.

---

## 12. Privacy & Persistence Boundaries

- **Browser-Local Only (Never Sent to Server):**
  - Camera video frames & Canvas images.
  - Raw 33 MediaPipe 3D Landmark coordinate arrays.
- **Persisted to Supabase Database:**
  - Session metadata: `user_id`, `pose_label`, `timestamp`, `duration`.
  - Aggregated performance scores: `accuracy`, `symmetry_score`, `balance_score`, `stability_score`, `rom_score`, `hold_time`, `reps`, `tracking_quality`.
- **Privacy Guarantee:** No facial imagery, raw video streams, or biomaterial coordinates leave the user's browser device.

---

## 13. Recommended Product Feature Matrix

### P0 — Must Have (Core Dashboard V2)
1. **Redesigned Overview Cards:** Total Sessions, Practice Time, Overall Score, Practice Streak.
2. **Historical Score Trend Chart:** 7-day and 30-day interactive line charts.
3. **Database Schema Update:** Add `reps`, `symmetry_score`, `balance_score`, `stability_score`, `rom_score`, `hold_time`, `tracking_quality` columns to `pose_sessions`.
4. **Enhanced API Payload:** Update `/save_pose_session` and `/api/dashboard_stats`.
5. **Pose Performance Grid:** Cards listing sessions, avg score, best score per pose.

### P1 — High Value (Product Intelligence)
1. **Biomechanics Dimensional Radar Chart:** Visualizing Symmetry, Balance, Stability, ROM.
2. **Personal Records Cards:** Displaying all-time achievements.
3. **Deterministic Insight Engine:** Rules generating automated text feedback cards.
4. **Session Comparison Panel:** Current vs Previous session delta breakdown.
5. **Interactive Date Range Filters:** 7d, 30d, all-time selectors.

### P2 — Future Infrastructure
1. **PDF & CSV Export Downloads from UI:** Direct download button in dashboard.
2. **Practice Goals & Target Setting:** Weekly practice minute goal setting.
3. **Achievement Badges:** Gamified milestone badges.

---

## 14. UI States Specification

- **Loading State:** Shimmering skeleton cards and chart placeholder blocks while fetching `/api/dashboard_stats`.
- **Empty State:** Friendly onboarding illustration with call-to-action button *"Start your first pose detection session"* when `total_sessions == 0`.
- **Error State:** Banner notification with *"Unable to load dashboard stats. Retrying in 5s..."* and a manual *"Retry Now"* button.
- **Mobile Responsive Layout:** 4-column cards stack single-column on screens $< 768\text{px}$; charts collapse horizontally with touch-scroll enabled.
