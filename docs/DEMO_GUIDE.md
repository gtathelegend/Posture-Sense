# PostureSense v2 Demo Guide

**Version:** 2.0.0  
**Target Audience:** Project Reviewers, Stakeholders, Technical Evaluators  
**Demo Duration:** 5 Minutes  

---

## 1. Demo Overview & Objective

This guide provides a structured 5-minute walkthrough for demonstrating PostureSense v2 live. It showcases real-time MediaPipe WASM pose tracking, biomechanical joint vector analysis, pose recognition, exercise state tracking, 8-dimension scoring, evidence-based coaching feedback, longitudinal analytics, and authenticated PDF report generation.

---

## 2. Prerequisites & Demo Setup

### Environment Requirements

1. **Browser**: Google Chrome, Microsoft Edge, or Brave (WebAssembly & WebGL enabled).
2. **Camera**: Integrated laptop webcam or USB webcam (minimum 720p 30 FPS).
3. **Lighting**: Adequate ambient room lighting (avoid direct high contrast backlighting).
4. **Local Server**: Running local Flask backend:
   ```bash
   python app.py
   ```
   *Application available at `http://localhost:8080`.*

---

## 3. Step-by-Step 5-Minute Demo Script

| Time | Step | Action | Key Talking Points | Expected Output |
|---|---|---|---|---|
| **0:00 - 0:30** | **1. Open Application & Privacy** | Open `http://localhost:8080`. Highlight landing page & privacy badge. | "PostureSense v2 is 100% privacy-first. Pose estimation runs locally in the browser via WebAssembly — no camera frames leave your device." | Clean, modern landing page with operational mode selection cards. |
| **0:30 - 1:00** | **2. Enable Camera & WASM Load** | Click **Ergonomic Desk Mode**. Grant browser camera permission. | "The MediaPipe WASM model loads instantly in a dedicated Web Worker thread to keep the UI smooth." | Camera stream initializes within <1.2s; green FPS indicator displays 30–60 FPS. |
| **1:00 - 1:45** | **3. Landmark Tracking & Skeleton Overlay** | Step back so upper body is visible. Observe the 33-point skeleton overlay. | "Notice the 33-point 3D keypoint tracking. Jitter is eliminated using Exponential Moving Average (EMA) filtering." | Neon blue skeleton overlay aligned with body joints in real-time. |
| **1:45 - 2:30** | **4. Pose Recognition & Biomechanics** | Transition into Tree Pose or Warrior II. | "The BiomechanicsEngine calculates joint angles and bilateral symmetry in real-time while the PoseRuleEngine evaluates pose classification." | Live joint angles update, pose card changes to **Tree Pose (92%)** or **Warrior II**. |
| **2:30 - 3:15** | **5. Perform Exercise & Rep Tracking** | Switch to **Exercise Mode**, select **Bodyweight Squat**. Perform 3 squats. | "The MovementEngine runs an 11-state Finite State Machine, auto-detecting Eccentric, Bottom Hold, and Concentric phases." | Rep counter increments cleanly (1, 2, 3) with range of motion (ROM) gate validation. |
| **3:15 - 3:45** | **6. Score & Feedback Display** | Complete session and observe score breakdown & coaching cues. | "The ScoringEngine evaluates form across 8 dimensions (alignment, ROM, symmetry, stability, tempo). Feedback is prioritized and evidence-based." | Overall Quality Score (e.g., 91.4 Excellent) with 8 breakdown bars and coaching cards. |
| **3:45 - 4:30** | **7. Longitudinal Analytics** | Navigate to Dashboard / Analytics section. | "Session metrics are saved to Supabase PostgreSQL, tracking 30-day activity heatmaps, personal records, and statistical trends." | 30-day activity heatmap, progress line chart showing **IMPROVING** classification. |
| **4:30 - 5:00** | **8. Generate PDF Performance Report** | Click **Export PDF Report**. | "Reports are generated securely with authenticated downloads and zero public file storage." | PDF report downloads containing session metrics, dimension tables, and joint curves. |

---

## 4. Expected Outputs Checklist

- [x] Camera feed launches at 30–60 FPS with green status indicator.
- [x] 33-point skeleton overlay tracks body movements accurately.
- [x] Joint angles (neck, shoulder, hip, knee) update in real-time.
- [x] Rep counter increments upon completion of full exercise ROM.
- [x] 8-dimension score gauge displays numeric quality score (0–100).
- [x] Feedback cues pop up without duplicate spam.
- [x] Analytics dashboard renders interactive trend chart and activity calendar.
- [x] PDF report exports cleanly and opens in PDF reader.

---

## 5. Troubleshooting & Common Demo Issues

| Symptom | Probable Cause | Immediate Remediation |
|---|---|---|
| Camera prompt does not appear | Browser permissions blocked | Click camera icon in browser address bar and select **Allow**. |
| Skeleton overlay flickering | Low room lighting or partial occlusion | Adjust lighting; step back so key joints (head to knees) are visible. |
| Rep counter not incrementing | Incomplete squat depth | Ensure full depth is achieved (knee flexion angle $<110^\circ$) to trigger ROM gate. |
| Backend connection error | Local Flask app not running | Verify `python app.py` is active in terminal on port 8080. |

---

## 6. Offline / Backup Demo Plan

If live webcam input is unavailable during a demonstration:
1. **Recorded Video Mode**: The application includes a fallback pre-recorded video stream selector in the developer settings panel.
2. **Mock Event Stream**: The engine test suite can be run with mock landmark inputs (`python -m pytest tests/test_movement_engine.py`) to demonstrate engine processing logic directly in the terminal.
