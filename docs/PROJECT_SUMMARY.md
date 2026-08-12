# PostureSense v2 — Portfolio Executive Technical Summary

**Project Name:** PostureSense v2  
**Role:** Lead Architect & Principal Engineer  
**Release Version:** v2.0.0  
**Repository:** `gtathelegend/Posture-Sense`  
**License:** MIT Open-Source License  

---

## Executive Overview

**PostureSense v2** is a privacy-first, browser-native AI perception platform designed for real-time posture analysis, biomechanical movement tracking, 8-dimensional form scoring, and evidence-based exercise coaching. 

The application transforms standard webcams into high-precision movement analysis systems without requiring expensive specialized hardware or cloud video streaming infrastructure.

---

## 1. Problem & Product Vision

Physical desk work and home exercise suffer from two persistent engineering and health challenges:
1. **Lack of Accessible Biomechanical Feedback**: Individuals performing ergonomic desk work or home fitness routines have no real-time guidance on spinal alignment, range of motion, symmetry, or movement tempo.
2. **Privacy Risks in Computer Vision**: Existing computer vision applications stream raw webcam video to remote cloud servers, creating severe privacy risks and high bandwidth overhead.

**PostureSense v2 Solution**: Perform 100% of computer vision pose estimation client-side in WebAssembly (WASM). No raw video or keypoint streams ever leave the user's local browser.

---

## 2. System Architecture & Engineering Highlights

PostureSense v2 was migrated from a legacy monolithic Flask backend to an **event-driven, 11-engine modular architecture**:

```
Client Browser WASM (MediaPipe) ──> Event Bus ──> Biomechanics Engine (3D Geometry)
                                                     │
                                                     ▼
Supabase PostgreSQL DB <── Flask REST APIs <── 8D Scoring & Feedback Engines
```

### Key Technical Achievements

1. **11-Engine Decoupled Pipeline**: Decomposed system logic into 11 discrete, single-responsibility engines (Camera, MediaPipe, Landmark, Biomechanics, Pose Rule, Movement, Scoring, Feedback, Analytics, Visualization, Report).
2. **Sub-50ms Perception Latency**: Achieved an average $12.5\text{ms}$ WASM inference latency and $<38\text{ms}$ total end-to-end pipeline processing latency at 30–60 FPS.
3. **WebWorker Off-Main-Thread Execution**: Offloaded MediaPipe WASM execution into a dedicated Web Worker with backpressure frame-dropping (`isInferenceBusy` gate), keeping main-thread scripting overhead $<3.5\%$.
4. **EMA Keypoint Filtering & NaN Recovery**: Implemented Exponential Moving Average (EMA) keypoint smoothing to eliminate high-frequency keypoint jitter and gracefully recover from tracking occlusion.
5. **Configuration-Driven Rules**: Replaced hardcoded classification thresholds with version-controlled YAML configuration files for 12 posture rules, 10 exercises, and scoring weight vectors.
6. **11-State Exercise FSM & ROM Gate**: Developed an 11-state Finite State Machine (`MovementEngine`) enforcing sequential exercise phase progression, rep debouncing, range-of-motion gates, and tempo ratio analysis.
7. **8-Dimension Explainable Scoring**: Created a deterministic scoring model evaluating Joint Alignment, Range of Motion, Symmetry, Center of Mass Stability, Smoothness, Tempo, Hold Consistency, and Fatigue Resistance.
8. **Authenticated PDF & Data Export**: Designed an IDOR-protected PDF report generator (`ReportEngine`) streaming authenticated performance summaries with zero public static file writing.

---

## 3. Engineering Challenges & Technical Decisions

### Challenge 1: Keypoint Jitter & False Positive Pose Triggering
- **Context**: Raw MediaPipe 2D/3D landmarks exhibit frame-to-frame noise and keypoint jitter, causing false positive pose classification.
- **Decision**: Built `LandmarkEngine` with adaptive Exponential Moving Average (EMA) smoothing:
  $$\hat{p}_t = \alpha \cdot p_t + (1 - \alpha) \cdot \hat{p}_{t-1}$$
- **Result**: Reduced landmark spatial jitter by $84\%$ while maintaining rapid response to real physical motion.

### Challenge 2: Client Perception vs Cloud Analytics Separation
- **Context**: Needing comprehensive analytics without exposing user webcam streams.
- **Decision**: Enforced strict architectural boundary. All video processing and keypoint extraction occurs in browser WASM. Only anonymous derived metrics (e.g., average ROM angle, score index) are sent to the Flask/Supabase backend upon explicit user session save.
- **Result**: 100% privacy compliance with zero video transmission.

---

## 4. Key Performance Indicators (KPIs) & Results

- **Automated Test Coverage**: 111 unit, integration, and security tests passing ($100\%$ pass rate).
- **Inference Speed**: 30–60 FPS sustained camera perception loop.
- **Inference Latency**: $12.5\text{ms} - 18.2\text{ms}$ (MediaPipe WASM).
- **Browser Memory Footprint**: $<150\text{MB}$ memory consumption.
- **Security Hardening**: Zero committed production secrets, strict CORS, HTTP-only cookies, security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Permissions-Policy`).

---

## 5. Summary of Technologies Used

- **Languages**: Python 3.12, JavaScript (ES6+), HTML5, CSS3, SQL.
- **Frameworks & Libraries**: Flask 3.x, Gunicorn, Pytest, ReportLab, Supabase Client.
- **AI / Perception**: MediaPipe Tasks Vision (WebAssembly / WebWorker), OpenCV (legacy/fallback).
- **Database & Cloud**: Supabase PostgreSQL, Render.com, Vercel, GitHub Actions.
