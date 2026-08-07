# Product Requirements Document (PRD)

**Project:** PostureSense v2  
**Version:** 2.0.0  
**Status:** Planning  
**Author:** Vedaang Sharma  
**Last Updated:** August 2026

---

# 1. Executive Summary

## Overview

PostureSense is a browser-based AI posture analysis platform that leverages on-device computer vision to provide real-time biomechanical feedback during exercise, yoga, ergonomic work, and rehabilitation.

Unlike traditional fitness applications that rely on wearable sensors or manual user input, PostureSense performs pose estimation directly from a standard webcam using MediaPipe Tasks running entirely inside the browser. This enables users to receive instant posture correction, movement analysis, and performance insights without requiring additional hardware or transmitting video data to external servers.

The platform is designed with a privacy-first architecture where all computer vision inference occurs locally on the user's device. The backend is responsible only for authentication, analytics, session storage, and user management.

PostureSense aims to demonstrate production-grade software engineering practices by combining computer vision, modern web technologies, cloud infrastructure, scalable backend services, and user-centered design into a single integrated platform.

---

# 2. Vision

## Vision Statement

To build the most accessible browser-based posture analysis platform that enables anyone with a webcam to improve movement quality through real-time AI-powered biomechanical feedback.

---

## Long-Term Vision

PostureSense should evolve into a comprehensive movement intelligence platform capable of supporting:

- Fitness coaching
- Yoga guidance
- Workplace ergonomics
- Rehabilitation monitoring
- Educational demonstrations
- Sports performance analysis

while maintaining privacy through on-device AI inference.

---

## Product Philosophy

The product is built around five fundamental principles.

### Privacy First

User video should never leave the local device.

Only processed metadata (joint angles, scores, session summaries, analytics) may be stored if the user explicitly chooses.

---

### Real-Time Feedback

Users should receive posture correction while performing movements rather than after completing them.

---

### Explainable AI

Every recommendation should be supported by measurable biomechanical data.

Instead of:

> "Bad posture"

the application should explain:

> "Your neck is tilted forward by 16° beyond the recommended range."

---

### Accessibility

The platform should require only:

- a modern web browser
- a webcam
- an internet connection for authentication

No expensive equipment should be necessary.

---

### Engineering Excellence

The application should showcase modern software engineering practices including:

- modular architecture
- clean code
- scalable backend
- browser AI
- production deployment
- automated testing
- comprehensive documentation

---

# 3. Problem Statement

## Background

Poor posture has become increasingly common due to prolonged computer usage, sedentary lifestyles, and the growing popularity of home workouts.

Many individuals unknowingly perform exercises incorrectly or maintain unhealthy sitting positions for extended periods, increasing the risk of discomfort, reduced performance, and long-term musculoskeletal issues.

Existing solutions typically fall into one of several categories:

- wearable posture sensors
- expensive motion capture systems
- fitness applications without posture analysis
- AI applications that require uploading videos to cloud servers

These approaches often suffer from one or more limitations:

- high cost
- privacy concerns
- hardware requirements
- delayed feedback
- platform restrictions

---

## Core Problem

Users lack access to a privacy-preserving, browser-based system capable of delivering real-time posture analysis using only a standard webcam.

---

## Opportunity

Recent advances in browser-based machine learning (MediaPipe Tasks, WebAssembly, WebGPU) make it possible to execute high-performance pose estimation directly on consumer devices.

This enables an entirely new class of privacy-preserving AI applications.

PostureSense aims to demonstrate this capability.

---

# 4. Product Goals

The primary goals of PostureSense are listed below.

## Goal 1

Provide accurate real-time pose estimation directly inside the browser.

---

## Goal 2

Deliver understandable posture correction based on biomechanical analysis rather than generic messages.

---

## Goal 3

Support multiple use cases through specialized operating modes.

These include:

- Exercise Mode
- Yoga Mode
- Ergonomic Mode
- Rehabilitation Mode

---

## Goal 4

Track user progress across sessions through historical analytics and reports.

---

## Goal 5

Demonstrate production-quality software engineering suitable for technical interviews, internships, research opportunities, and graduate admissions.

---

# 5. Success Metrics

The success of the project will be measured using both technical and product-oriented metrics.

## Technical Metrics

| Metric | Target |
|----------|---------|
| Pose inference latency | < 50 ms |
| Camera FPS | 30 FPS or higher |
| Browser CPU usage | < 40% |
| Pose detection confidence | > 0.85 average |
| Deployment uptime | 99%+ |
| Lighthouse Performance | 90+ |
| Lighthouse Accessibility | 95+ |

---

## Product Metrics

- User can start analysis within 30 seconds.

- Session history loads within 2 seconds.

- AI feedback updates in real time.

- Dashboard accurately reflects completed sessions.

- Reports generate in under 5 seconds.

---

## Portfolio Goals

The project should demonstrate competency in:

- Computer Vision
- Artificial Intelligence
- Full Stack Development
- Backend Engineering
- Cloud Deployment
- Database Design
- System Architecture
- Performance Optimization
- UI/UX Design
- Technical Documentation

---

# 6. Target Audience

The application is intended for several categories of users.

---

## Primary Audience

### Students

Students learning computer vision, machine learning, or software engineering who wish to understand pose estimation technologies.

---

### Fitness Enthusiasts

Individuals performing bodyweight exercises or strength training who want posture guidance.

---

### Yoga Practitioners

Users seeking assistance with alignment during yoga sessions.

---

### Office Workers

Individuals spending long hours at desks who require posture monitoring and ergonomic feedback.

---

### Developers

Developers interested in browser-based AI applications and MediaPipe.

---

## Secondary Audience

- Researchers
- Physical therapists
- Sports coaches
- Educational institutions

---

# 7. User Personas

## Persona 1 — Fitness Enthusiast

Age: 22

Goals:

- Improve squat technique
- Avoid injuries
- Count repetitions
- Track progress

Pain Points:

- No coach available
- Unsure about exercise form
- Wants objective feedback

---

## Persona 2 — Office Professional

Age: 29

Goals:

- Reduce neck pain
- Improve sitting posture
- Receive posture reminders

Pain Points:

- Long hours at desk
- Poor ergonomic habits

---

## Persona 3 — Yoga Practitioner

Age: 35

Goals:

- Improve pose alignment
- Learn yoga safely

Pain Points:

- No instructor
- Cannot identify alignment mistakes

---

## Persona 4 — Computer Science Student

Age: 20

Goals:

- Learn MediaPipe
- Study browser AI
- Explore biomechanics

Pain Points:

- Existing demos are simplistic
- Wants production-quality architecture

---

# 8. Product Scope

The project is divided into two categories.

---

## In Scope

### Authentication

- User registration
- User login
- Session management

---

### AI Vision

- Browser webcam
- MediaPipe Tasks
- Pose estimation
- Skeleton visualization

---

### Analysis

- Joint angle calculations
- Pose scoring
- Real-time posture feedback

---

### Modes

- Exercise
- Yoga
- Ergonomic
- Rehabilitation

---

### Analytics

- Session history
- Progress tracking
- Charts
- Reports

---

### Dashboard

- Performance overview
- Goals
- Trends
- Recommendations

---

### Deployment

- Browser inference
- Cloud backend
- Free-tier hosting

---

## Out of Scope (v2)

The following are intentionally excluded from the initial release.

- Mobile native applications
- Wearable device integration
- Multiplayer sessions
- Live coach video calls
- Payment processing
- Premium subscriptions
- Social media features
- AI-generated workout plans
- Smartwatch integration
- Medical diagnosis
- Clinical decision support

These may be considered in future versions.

---

# 9. MVP Definition

The Minimum Viable Product must support the following workflow.

1. User logs into the application.

2. User grants webcam permission.

3. Browser initializes MediaPipe Tasks.

4. Skeleton is rendered in real time.

5. Joint angles are calculated.

6. Exercise or posture is identified.

7. User receives live corrective feedback.

8. Session summary is generated.

9. Analytics are saved.

10. Dashboard updates automatically.

Successful completion of this workflow constitutes the MVP.

---

# 10. Future Scope

Potential future enhancements include:

- Multi-person tracking
- AI voice coaching
- Personalized exercise plans
- Mobile applications
- Apple Health integration
- Google Fit integration
- Wearable sensor fusion
- Real-time multiplayer coaching
- Trainer dashboard
- Therapist dashboard
- Team management
- Enterprise ergonomics platform
- Edge TPU acceleration
- WebGPU optimization
- Custom pose creation
- Motion replay
- Biomechanical heatmaps

---

# 11. Competitive Analysis

## Market Overview

The posture correction and fitness technology market has grown rapidly due to increased remote work, home workouts, and accessibility of AI-powered computer vision.

Most existing solutions fall into one of four categories:

- Wearable posture devices
- Mobile fitness applications
- AI workout assistants
- Professional rehabilitation software

While these products provide useful functionality, they often sacrifice one or more of the following:

- Privacy
- Accessibility
- Cost
- Platform compatibility
- Explainability

PostureSense is designed to bridge these gaps using browser-native AI.

---

## Competitor Comparison

| Feature | PostureSense | MediaPipe Demo | Home Workout Apps | Wearable Posture Devices | Professional Rehab Software |
|----------|--------------|----------------|-------------------|--------------------------|-----------------------------|
| Browser-based | ✅ | ✅ | ❌ | ❌ | ❌ |
| Webcam Only | ✅ | ✅ | ❌ | ❌ | ❌ |
| No Additional Hardware | ✅ | ✅ | ✅ | ❌ | ❌ |
| On-device AI | ✅ | ✅ | ❌ | ❌ | ❌ |
| Real-time Feedback | ✅ | ❌ | Partial | Partial | ✅ |
| Exercise Recognition | ✅ | ❌ | ✅ | ❌ | Partial |
| Yoga Analysis | ✅ | ❌ | Partial | ❌ | ❌ |
| Ergonomic Monitoring | ✅ | ❌ | ❌ | ✅ | Partial |
| Rehabilitation Support | ✅ | ❌ | ❌ | ❌ | ✅ |
| Analytics Dashboard | ✅ | ❌ | Partial | Partial | ✅ |
| Explainable Feedback | ✅ | ❌ | ❌ | ❌ | Partial |
| Open Source | ✅ | Partial | ❌ | ❌ | ❌ |

---

## Unique Selling Propositions

PostureSense differentiates itself through the following characteristics.

### Browser-First AI

No installation.

No plugins.

No GPU servers.

Everything runs directly inside the browser.

---

### Privacy-First Design

No webcam video is uploaded.

Only processed posture metrics are stored when the user explicitly saves a session.

---

### Multi-Domain Platform

Unlike applications focused on only one use case, PostureSense supports

- Fitness
- Yoga
- Ergonomics
- Rehabilitation

using the same AI pipeline.

---

### Explainable Feedback

Instead of displaying generic confidence scores, every recommendation is supported by measurable biomechanical data.

Example:

Incorrect

> Bad posture

Correct

> Left knee flexion is 18° below the recommended range.

---

### Engineering Showcase

The project demonstrates modern software engineering through

- Computer Vision
- Browser AI
- Full-stack architecture
- Cloud deployment
- Analytics
- Documentation
- Clean system design

making it valuable as both a product and an educational reference.

---

# 12. User Journey

## Journey 1 — First-Time User

1. User opens the application.
2. User creates an account.
3. User verifies their email (future release).
4. User completes onboarding.
5. User grants webcam permission.
6. Browser initializes MediaPipe.
7. User selects a mode.
8. Analysis begins.
9. User receives live posture feedback.
10. Session is saved.
11. Dashboard displays analytics.

---

## Journey 2 — Returning User

1. User logs in.
2. Dashboard loads previous sessions.
3. User starts a new analysis.
4. AI provides live corrections.
5. Updated statistics appear automatically.

---

## Journey 3 — Office Worker

1. User selects Ergonomic Mode.
2. Webcam continuously monitors posture.
3. System detects slouching.
4. User receives notification.
5. Daily posture score updates.

---

## Journey 4 — Yoga Practitioner

1. User selects Yoga Mode.
2. Desired pose is chosen.
3. Skeleton appears.
4. AI evaluates alignment.
5. Corrections appear until pose quality improves.

---

# 13. User Stories

## Authentication

As a user,

I want to create an account,

so that my workout history is stored securely.

---

As a user,

I want to log in,

so I can continue previous sessions.

---

## Camera

As a user,

I want the browser to access my webcam,

so posture analysis can begin.

---

## Pose Detection

As a user,

I want to see my detected skeleton,

so I know the AI is tracking me correctly.

---

## Exercise Recognition

As a fitness enthusiast,

I want the system to recognize my exercise,

so I don't need to select it manually.

---

## Feedback

As a user,

I want real-time corrective feedback,

so I can improve my posture while exercising.

---

## Analytics

As a user,

I want to review previous sessions,

so I can measure long-term improvement.

---

## Reports

As a user,

I want downloadable reports,

so I can share progress with a trainer or therapist.

---

## Ergonomics

As an office worker,

I want posture reminders,

so I avoid sitting incorrectly for long periods.

---

# 14. Acceptance Criteria

The following criteria define when the MVP can be considered complete.

---

## Authentication

- Registration succeeds.
- Login succeeds.
- Logout succeeds.
- Protected routes require authentication.

---

## Camera

- Browser requests webcam permission.
- Camera initializes successfully.
- User can switch cameras.
- Video stream renders smoothly.

---

## Pose Detection

- Skeleton renders within two seconds.
- Thirty-three landmarks are detected.
- Tracking remains stable during movement.

---

## Feedback

- Feedback updates in real time.
- Joint angles are recalculated every frame.
- Scores update dynamically.

---

## Dashboard

- Session history displays correctly.
- Charts load successfully.
- Statistics update after each session.

---

## Performance

- Browser maintains at least 30 FPS.
- Average inference latency remains below 50 ms.
- Memory usage remains stable during a 30-minute session.

---

## Deployment

- Frontend deploys successfully.
- Backend deploys successfully.
- Browser inference works in production.
- No server webcam dependency exists.

---

# 15. Product Modes

The application supports four operational modes.

---

## Exercise Mode

Purpose

Improve exercise technique.

Supported Activities

- Squats
- Push-ups
- Lunges
- Planks
- Shoulder Press
- Jumping Jacks

Features

- Rep counting
- Form scoring
- Stability analysis
- Tempo analysis

---

## Yoga Mode

Purpose

Improve alignment.

Supported Poses

- Mountain
- Tree
- Warrior I
- Warrior II
- Triangle
- Chair
- Cobra
- Child Pose
- Bridge
- Downward Dog

Features

- Alignment scoring
- Balance analysis
- Hold timer
- Flexibility tracking

---

## Ergonomic Mode

Purpose

Improve workplace posture.

Features

- Slouch detection
- Neck angle
- Shoulder symmetry
- Sitting timer
- Reminder notifications
- Daily posture score

---

## Rehabilitation Mode

Purpose

Support movement recovery.

Features

- Range of motion
- Left-right comparison
- Symmetry score
- Progress tracking
- Session reports

---

# 16. MVP vs Full Product

## MVP

- Authentication
- Browser MediaPipe
- Skeleton rendering
- Joint angle calculations
- Pose detection
- Exercise recognition
- Live feedback
- Dashboard
- Analytics
- Session history

---

## Version 2.1

- Voice coaching
- PDF reports
- Weekly goals
- Heatmaps
- Exercise library expansion

---

## Version 2.2

- Offline mode
- WebGPU acceleration
- AI recommendations
- Motion replay
- Personalized training

---

## Version 3.0

- Multi-person tracking
- Therapist portal
- Team dashboard
- Coach dashboard
- Smartwatch integration
- Mobile application

---

# 17. AI & Computer Vision Pipeline

## Overview

The AI engine is the core of PostureSense.

Unlike traditional computer vision systems that rely on backend processing, PostureSense performs all pose estimation, landmark detection, biomechanical analysis, and posture evaluation directly inside the user's browser.

The backend never processes webcam frames.

This architecture improves:

- Privacy
- Performance
- Scalability
- Deployment simplicity
- User experience

---

## AI Pipeline Overview

```
Webcam

↓

MediaPipe Tasks Vision

↓

33 Body Landmarks

↓

Landmark Validation

↓

Landmark Smoothing

↓

Joint Angle Engine

↓

Exercise Detection

↓

Biomechanics Engine

↓

Posture Evaluation

↓

Feedback Generator

↓

Analytics Engine

↓

Dashboard
```

---

# AI Pipeline Stages

## Stage 1 — Camera Capture

Input

Live webcam stream.

Responsibilities

- Initialize browser camera.
- Select optimal resolution.
- Handle permissions.
- Support multiple cameras.
- Maintain target FPS.

Output

Continuous video frames.

---

## Stage 2 — Pose Estimation

Technology

MediaPipe Tasks Vision

Output

33 landmarks.

Each landmark contains

```typescript
{
    x: number,
    y: number,
    z: number,
    visibility: number
}
```

Expected latency

< 40ms

---

## Stage 3 — Landmark Validation

Each frame should be validated.

Checks include

- Minimum visibility threshold
- Missing landmarks
- Out-of-frame joints
- Confidence filtering

If confidence is below threshold

- ignore frame
- interpolate previous frame

---

## Stage 4 — Landmark Smoothing

Raw landmarks often jitter.

Apply

One Euro Filter

or

Exponential Moving Average.

Purpose

- reduce shaking
- improve stability
- improve angle consistency

---

## Stage 5 — Joint Angle Engine

The angle engine computes biomechanical measurements.

Supported joints

- Neck
- Spine
- Left Shoulder
- Right Shoulder
- Left Elbow
- Right Elbow
- Left Hip
- Right Hip
- Left Knee
- Right Knee
- Left Ankle
- Right Ankle

---

## Angle Formula

Three landmarks define one angle.

```
A

 \

  B

 /

C
```

Angle

```
ABC
```

Calculated using

```
atan2()
```

The implementation should remain modular and reusable.

---

## Stage 6 — Pose Classification

Purpose

Identify static poses.

Initially support

Yoga

- Mountain
- Tree
- Warrior I
- Warrior II
- Chair
- Triangle
- Cobra
- Child Pose
- Bridge
- Downward Dog

Future additions should be configuration-driven rather than hardcoded.

---

## Stage 7 — Exercise Detection

Purpose

Identify dynamic movements.

Supported MVP

- Squat
- Push-up
- Lunge
- Plank
- Jumping Jack

Future

- Deadlift
- Burpee
- Pull-up
- Bench Press
- Shoulder Press

Exercise detection should use

- landmark trajectories
- joint angles
- movement direction
- movement phases

---

## Stage 8 — Repetition Counter

Each exercise should define

```
Top Position

↓

Descending

↓

Bottom Position

↓

Ascending

↓

Top Position
```

A repetition is counted only after completing the full state transition.

This avoids false positives.

---

## Stage 9 — Biomechanics Engine

This engine converts landmarks into meaningful metrics.

Metrics include

- Joint Angles
- Balance
- Stability
- Symmetry
- Center of Mass Approximation
- Range of Motion
- Movement Velocity
- Pose Duration

These values become the foundation for all scoring.

---

# 18. Pose Scoring System

Every detected pose receives an overall score.

```
Overall Score

100
```

The score is composed of weighted components.

| Component | Weight |
|------------|----------|
| Joint Alignment | 40% |
| Stability | 20% |
| Symmetry | 15% |
| Range of Motion | 15% |
| Pose Confidence | 10% |

---

## Example

```
Joint Alignment

91

Stability

87

Symmetry

94

ROM

90

Confidence

97

Overall

91
```

---

## Color Coding

90-100

Excellent

Green

---

75-89

Good

Blue

---

60-74

Needs Improvement

Orange

---

Below 60

Poor

Red

---

# 19. Feedback Engine

Feedback must be explainable.

Never display

```
Incorrect
```

Instead

Display

```
Raise your right elbow slightly.

↓

Straighten your back.

↓

Move your knees outward.

↓

Keep your neck neutral.
```

---

## Feedback Categories

### Alignment

Example

Shoulders uneven

---

### Balance

Example

Shift weight toward left foot.

---

### Stability

Example

Reduce upper body movement.

---

### Timing

Example

Slow down during descent.

---

### Symmetry

Example

Left arm is higher than right arm.

---

### Ergonomics

Example

Lift monitor to eye level.

---

# 20. Analytics Pipeline

Every completed session generates analytics.

Stored information

```
Duration

Exercise

Pose

Joint Angles

Average Score

Max Score

Lowest Score

Mistakes

Corrections

Timestamp
```

---

## Dashboard Metrics

Daily Sessions

Weekly Sessions

Monthly Sessions

Total Duration

Best Exercise

Most Common Mistake

Average Accuracy

Improvement

Consistency

---

# 21. AI Coach

After every session

The AI Coach summarizes performance.

Example

```
Today's Summary

Great improvement.

Shoulder alignment improved by 12%.

The most common issue remains forward neck posture.

Recommendation

Focus on keeping your chin tucked during squats.

Estimated improvement

8% next week if consistency is maintained.
```

The coach should only generate recommendations supported by session data.

---

# 22. Performance Targets

The AI engine should satisfy the following targets.

| Metric | Target |
|----------|---------|
| FPS | ≥30 |
| Inference Latency | ≤50ms |
| Landmark Detection | ≤35ms |
| Dashboard Update | ≤100ms |
| Camera Startup | ≤2s |
| Session Save | ≤1s |

---

# 23. AI System Constraints

The AI engine must satisfy the following constraints.

## Privacy

- Webcam frames never leave the browser.
- No raw images stored.
- Only analytics uploaded.

---

## Reliability

- Continue tracking under moderate occlusion.
- Recover after temporary landmark loss.

---

## Performance

- Work on integrated GPUs.
- Support mid-range laptops.
- Gracefully degrade on slower devices.

---

## Explainability

Every score must be traceable to measurable biomechanical metrics.

No fabricated percentages.

No random scores.

Every displayed value must be computed from actual landmark data.

---

## Extensibility

Adding a new exercise or yoga pose should require only:

- defining expected joint angles
- specifying thresholds
- providing feedback rules

No changes to the core AI engine should be necessary.

---

# 24. Data Flow

```
Browser Webcam
        │
        ▼
MediaPipe Tasks Vision
        │
        ▼
33 Landmarks
        │
        ▼
Landmark Smoothing
        │
        ▼
Joint Angle Engine
        │
        ▼
Biomechanics Engine
        │
        ▼
Exercise / Pose Detection
        │
        ▼
Scoring Engine
        │
        ▼
Feedback Generator
        │
        ▼
Session Analytics
        │
        ▼
FastAPI Backend
        │
        ▼
Supabase Database
        │
        ▼
Dashboard
```

---
