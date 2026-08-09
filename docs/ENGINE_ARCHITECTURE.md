# Engine Architecture

**Project:** PostureSense v2  
**Version:** 2.0.0  
**Status:** Implementation Phase (Milestone 8 Completed — Reports & Export Subsystem)  
**Last Updated:** August 2026

See [SHARED_CORE.md](file:///d:/Github/Posture-Sense/docs/SHARED_CORE.md) for detailed contracts, Event Bus specifications, and configuration/plugin system implementations.

---

# 1. Purpose

This document defines the software architecture of the PostureSense AI Engine.

It serves as the single source of truth for every engineering decision related to the computer vision pipeline, biomechanics engine, analytics system, backend integration, and frontend architecture.

All future implementations should follow this document.

---

# 2. Architecture Philosophy

PostureSense is designed as a **modular event-driven platform** instead of a monolithic application.

Every major responsibility is isolated into its own independent engine.

Each engine:

- has one responsibility
- exposes a well-defined interface
- communicates through events
- is independently testable
- can be replaced without affecting other engines

This architecture allows PostureSense to evolve without requiring major rewrites.

---

# 3. Design Principles

The architecture follows several fundamental engineering principles.

---

## 3.1 Single Responsibility Principle

Each engine should perform exactly one task.

Examples

MediaPipe Engine

Responsible only for pose estimation.

Never computes scores.

Never stores analytics.

Never generates feedback.

---

Scoring Engine

Responsible only for converting measurements into scores.

Never reads webcam frames.

Never draws UI.

Never writes database records.

---

Analytics Engine

Responsible only for processing historical data.

Never performs pose estimation.

Never computes landmarks.

---

## 3.2 Event Driven Communication

No engine should directly control another engine.

Instead

```
MediaPipe

↓

Event

↓

LandmarksDetected

↓

Pose Engine
```

instead of

```
MediaPipe

↓

PoseEngine.process()
```

This reduces coupling.

---

## 3.3 Configuration over Hardcoding

Nothing should be hardcoded.

All of the following belong in configuration files.

- exercises

- yoga poses

- thresholds

- score weights

- joint definitions

- feedback rules

- colors

- timing

The source code should remain generic.

---

## 3.4 Explainability

Every decision produced by the AI should be explainable.

Example

Instead of

```
Score

82
```

Display

```
Shoulder Alignment

92

Knee Alignment

68

Back Alignment

81

Neck Alignment

88

Overall

82
```

Every score must be reproducible.

---

## 3.5 Privacy First

Raw webcam frames never leave the browser.

Only processed metadata may be transmitted to the backend.

Examples

Allowed

- pose score

- joint angles

- exercise

- duration

- timestamps

Never upload

- webcam images

- video recordings

- raw frame buffers

unless explicitly requested by the user.

---

## 3.6 Extensibility

Adding a new exercise should require

- configuration

- optional feedback rules

Nothing else.

No engine should need modification.

---

# 4. High Level Architecture

```
                Browser

        Next.js + React

                │

        Webcam Capture

                │

                ▼

      MediaPipe Engine

                │

                ▼

      Landmark Engine

                │

                ▼

   Biomechanics Engine

                │

                ▼

     Pose Rule Engine

                │

                ▼

   Movement Engine

                │

                ▼

     Scoring Engine

                │

                ▼

     Feedback Engine

                │

                ▼

    Analytics Engine

                │

                ▼

       Backend API

                │

                ▼

         Supabase
```

---

# 5. Engine Overview

The system is divided into multiple independent engines.

| Engine | Responsibility |
|---------|----------------|
| Camera Engine | Webcam access |
| MediaPipe Engine | Pose estimation |
| Landmark Engine | Landmark validation |
| Biomechanics Engine | Joint calculations |
| Pose Rule Engine | Static pose recognition |
| Movement Engine | Dynamic movement recognition |
| Scoring Engine | Quality evaluation |
| Feedback Engine | User guidance |
| Analytics Engine | Session analysis |
| Persistence Engine | Data storage |
| Notification Engine | Alerts |
| Report Engine | PDF & exports |

Each engine is discussed in detail later.

---

# 6. Engine Lifecycle

Every analysis session follows the same lifecycle.

```
Initialize

↓

Warm Up

↓

Detect

↓

Analyze

↓

Score

↓

Feedback

↓

Persist

↓

Shutdown
```

Each stage emits events.

---

## Initialize

Responsibilities

- initialize webcam

- initialize MediaPipe

- allocate buffers

- load configuration

---

## Warm Up

Purpose

Allow MediaPipe tracking to stabilize.

Frames collected

Approximately 30

No analytics generated.

---

## Detect

Responsibilities

- detect landmarks

- validate visibility

- reject low-quality frames

---

## Analyze

Responsibilities

- compute joint angles

- estimate biomechanics

- detect exercise

- detect posture

---

## Score

Responsibilities

- compute quality

- evaluate movement

- calculate confidence

---

## Feedback

Responsibilities

- determine mistakes

- prioritize corrections

- update UI

---

## Persist

Responsibilities

- aggregate metrics

- generate session summary

- save analytics

---

## Shutdown

Responsibilities

- stop camera

- release MediaPipe

- flush analytics

---

# 7. Engine Communication Model

No engine should directly call another engine.

Instead

```
MediaPipe Engine

↓

Event Bus

↓

Landmark Engine

↓

Event Bus

↓

Biomechanics Engine

↓

Event Bus

↓

Movement Engine
```

Advantages

- Loose coupling

- Easier testing

- Easier debugging

- Better scalability

- Easier future ML integration

---

# 8. Event Bus

The Event Bus is responsible for communication between engines.

Every engine publishes events.

Every engine subscribes to events it requires.

Example

```
FrameCaptured

↓

LandmarksDetected

↓

AnglesCalculated

↓

PoseRecognized

↓

MovementDetected

↓

ScoreUpdated

↓

FeedbackGenerated

↓

SessionCompleted
```

No engine knows which engine generated the previous event.

---

# 9. Event Types

Core events include

## Camera

FrameCaptured

CameraStarted

CameraStopped

CameraError

---

## Landmark

LandmarksDetected

LandmarksLost

TrackingRecovered

LowConfidenceFrame

---

## Pose

PoseRecognized

PoseLost

PoseChanged

---

## Exercise

ExerciseStarted

ExerciseCompleted

RepCompleted

ExercisePaused

---

## Analytics

SessionStarted

SessionEnded

StatisticsUpdated

DashboardRefresh

---

## User

Login

Logout

ProfileUpdated

GoalCompleted

---

# 10. Why Event Driven?

Without events

```
Camera

↓

MediaPipe

↓

Pose Engine

↓

Scoring

↓

Feedback
```

Everything depends on everything.

One modification breaks multiple modules.

---

With events

```
Camera

↓

Event

↓

MediaPipe

↓

Event

↓

Pose Engine

↓

Event

↓

Scoring
```

Every module becomes replaceable.

For example

MediaPipe can later be replaced by

- TensorFlow MoveNet

- ONNX Runtime

- OpenPose

without changing any downstream engines.

---

# End of Part 1

# 11. Camera Engine

## Purpose

The Camera Engine is responsible for managing access to the user's webcam and providing a continuous stream of video frames to the AI pipeline.

It acts as the entry point for all computer vision processing.

No other engine should interact directly with browser camera APIs.

---

## Responsibilities

- Request camera permissions
- Detect available cameras
- Handle camera switching
- Configure resolution
- Configure frame rate
- Start video stream
- Stop video stream
- Monitor camera health
- Emit captured frames
- Handle camera failures

---

## Inputs

- User permission
- Camera selection
- Resolution configuration
- FPS configuration

---

## Outputs

Events

```
CameraStarted

FrameCaptured

CameraPaused

CameraStopped

CameraError
```

---

## Public Interface

```typescript
initialize()

start()

pause()

resume()

stop()

switchCamera()

getAvailableCameras()

getStatus()
```

---

## Internal Components

```
Permission Manager

↓

Device Manager

↓

Video Stream

↓

Frame Scheduler

↓

Frame Publisher
```

---

## Performance Requirements

Camera startup

<2 seconds

Frame delivery

30 FPS minimum

Maximum dropped frames

<5%

---

## Failure Handling

Possible failures

- Camera unavailable
- Permission denied
- Camera disconnected
- Browser restriction

Recovery strategy

- Retry initialization
- Prompt user
- Allow camera selection
- Gracefully stop session

---

# 12. MediaPipe Engine

## Purpose

The MediaPipe Engine performs human pose estimation.

It converts raw video frames into body landmarks.

This engine knows nothing about

- exercises
- scores
- feedback
- analytics

It only performs inference.

---

## Responsibilities

- Load MediaPipe Tasks
- Initialize model
- Process video frames
- Detect landmarks
- Estimate confidence
- Publish landmarks

---

## Inputs

```
FrameCaptured
```

---

## Outputs

```
LandmarksDetected

LowConfidenceFrame

TrackingLost

TrackingRecovered
```

---

## Internal Pipeline

```
Frame

↓

MediaPipe Model

↓

33 Landmarks

↓

Confidence

↓

Publish Event
```

---

## Data Structure

```typescript
Landmark

{

id

x

y

z

visibility

}
```

Thirty-three landmarks are produced.

---

## Performance Targets

Inference

<35 ms

Tracking confidence

>0.8

---

## Failure Handling

If no body is detected

Publish

```
TrackingLost
```

Do not crash downstream engines.

---

# 13. Landmark Engine

## Purpose

The Landmark Engine validates and improves landmark quality before biomechanical analysis.

---

## Responsibilities

- Landmark validation
- Missing landmark detection
- Landmark interpolation
- Confidence filtering
- Temporal smoothing
- Coordinate normalization

---

## Inputs

```
LandmarksDetected
```

---

## Outputs

```
ValidatedLandmarks

LandmarkQualityUpdated
```

---

## Processing Steps

```
Raw Landmarks

↓

Visibility Check

↓

Outlier Detection

↓

Interpolation

↓

One Euro Filter

↓

Normalized Coordinates

↓

Publish
```

---

## Quality Metrics

Every frame receives

```
Visibility

Missing Landmarks

Tracking Stability

Frame Quality
```

Example

```
Visibility

97%

Missing

0

Stability

95%

Quality

96%
```

---

# 14. Biomechanics Engine

## Purpose

Transform landmarks into meaningful biomechanical measurements.

---

## Responsibilities

- Joint angle calculation
- Body symmetry
- Center of mass approximation
- Stability estimation
- Balance estimation
- Range of motion
- Movement velocity

---

## Inputs

```
ValidatedLandmarks
```

---

## Outputs

```
JointAnglesCalculated

BiomechanicsUpdated
```

---

## Internal Modules

```
Joint Calculator

↓

ROM Calculator

↓

Balance Calculator

↓

Symmetry Calculator

↓

Movement Metrics
```

---

## Generated Metrics

Shoulder Angle

Elbow Angle

Hip Angle

Knee Angle

Ankle Angle

Neck Angle

Torso Inclination

Center of Mass

Balance Score

Symmetry Score

Movement Velocity

---

## Design Goal

This engine should remain exercise-independent.

It computes measurements only.

It never determines whether a squat is correct.

---

# 15. Pose Rule Engine

## Purpose

Recognize static poses using configuration-driven rules.

---

## Responsibilities

- Load pose definitions
- Evaluate joint angles
- Compare against tolerances
- Generate pose score

---

## Inputs

```
JointAnglesCalculated
```

---

## Outputs

```
PoseRecognized

PoseLost

PoseChanged
```

---

## Rule Format

Every pose is defined in YAML or JSON.

Example

```yaml
tree_pose:

  joints:

    left_knee:

      target: 45

      tolerance: 15

  weights:

    legs: 0.5

    torso: 0.3

    balance: 0.2
```

No hardcoded if-statements should exist.

---

## Matching Strategy

For every pose

```
Load Rules

↓

Compare Angles

↓

Calculate Error

↓

Calculate Score

↓

Highest Score Wins
```

---

# 16. Movement Engine

## Purpose

Recognize dynamic exercises.

Unlike Pose Rule Engine

this engine tracks movement across multiple frames.

---

## Responsibilities

- Exercise recognition
- Phase detection
- Rep counting
- Tempo analysis
- Hold detection

---

## Inputs

```
BiomechanicsUpdated
```

---

## Outputs

```
ExerciseStarted

RepCompleted

ExerciseFinished
```

---

## Internal Pipeline

```
Joint Angles

↓

Movement Buffer

↓

State Machine

↓

Exercise Detector

↓

Rep Counter
```

---

## State Machine Example

Squat

```
Standing

↓

Descending

↓

Bottom

↓

Ascending

↓

Standing

↓

Rep++
```

The movement must complete the entire cycle.

---

## Metrics

Exercise

Current Phase

Rep Count

Movement Velocity

Average Depth

Tempo

---

## Why a State Machine?

Without one

```
Angle

<90

↓

Rep++
```

False repetitions occur.

State machines eliminate this issue.

---

# 17. Scoring Engine

## Purpose

Convert biomechanical measurements into meaningful quality scores.

---

## Responsibilities

- Normalize measurements
- Apply weighting
- Generate overall score
- Generate component scores

---

## Inputs

```
BiomechanicsUpdated

PoseRecognized

ExerciseDetected
```

---

## Outputs

```
ScoreUpdated
```

---

## Score Components

```
Joint Alignment

40%

Balance

20%

Symmetry

15%

ROM

15%

Confidence

10%
```

---

## Generated Scores

Overall

Joint

Balance

Symmetry

ROM

Confidence

Consistency

---

## Rules

Scores must never be random.

Every score must be traceable back to measurable values.

---

# End of Part 2

# 18. Feedback Engine

## Purpose

The Feedback Engine converts technical biomechanical measurements into human-understandable coaching instructions.

This is the primary interaction point between the AI system and the user.

The engine should never expose raw measurements without context.

Instead, it should translate measurements into actionable guidance.

---

## Responsibilities

- Analyze scoring results
- Identify posture deviations
- Rank mistakes by severity
- Generate corrective feedback
- Prioritize recommendations
- Trigger voice coaching
- Trigger visual indicators
- Publish coaching events

---

## Inputs

```
ScoreUpdated

PoseRecognized

ExerciseDetected

BiomechanicsUpdated
```

---

## Outputs

```
FeedbackGenerated

WarningGenerated

CorrectionApplied

CoachingUpdated
```

---

## Internal Pipeline

```
Score Report

↓

Rule Evaluation

↓

Violation Detection

↓

Priority Ranking

↓

Feedback Selection

↓

UI + Voice Output
```

---

## Feedback Categories

### Alignment

Example

```
Raise your left elbow.

Straighten your back.

Keep your shoulders level.
```

---

### Stability

Example

```
Reduce unnecessary body movement.

Maintain balance before descending.
```

---

### Symmetry

Example

```
Your right shoulder is lower than your left.

Keep both knees aligned.
```

---

### Ergonomics

Example

```
Lift your monitor slightly.

Keep your neck neutral.

Sit closer to the backrest.
```

---

### Rehabilitation

Example

```
Increase your knee flexion gradually.

Avoid locking your elbow completely.
```

---

## Feedback Priority

Multiple corrections may exist simultaneously.

They should always be prioritized.

Example

```
Critical

↓

High

↓

Medium

↓

Low
```

Only the most important corrections should appear on screen.

Never overwhelm the user.

---

## Voice Coaching

Future versions may include speech synthesis.

Example

```
Great job.

Keep your back straight.

Lower your hips slightly.
```

Voice coaching should consume the same feedback events as the UI.

---

# 19. Analytics Engine

## Purpose

Collect and analyze session data to generate meaningful insights.

This engine is responsible for transforming raw measurements into historical trends.

---

## Responsibilities

- Aggregate metrics
- Compute statistics
- Detect improvements
- Identify recurring mistakes
- Generate summaries
- Prepare dashboard data

---

## Inputs

```
SessionCompleted

ScoreUpdated

ExerciseCompleted

RepCompleted
```

---

## Outputs

```
StatisticsUpdated

DashboardUpdated

InsightGenerated
```

---

## Session Metrics

Every session stores

```
Session ID

User ID

Timestamp

Duration

Exercise

Pose

Average Score

Best Score

Worst Score

Rep Count

Mistakes

Corrections

Confidence

Joint Metrics
```

---

## Dashboard Metrics

Daily Sessions

Weekly Sessions

Monthly Sessions

Average Score

Average Session Duration

Most Practiced Exercise

Most Common Mistake

Improvement Trend

Consistency Score

Streak

---

## Insights

Example

```
Shoulder alignment has improved

12%

over the last seven sessions.
```

---

## Trend Detection

The engine should calculate

- Daily improvement
- Weekly improvement
- Monthly improvement
- Moving averages
- Personal bests
- Regression detection

---

# 20. Persistence Engine

## Purpose

Persist user information and session data.

The Persistence Engine abstracts database interactions from the rest of the application.

No engine should communicate directly with Supabase.

---

## Responsibilities

- Save sessions
- Save analytics
- Save settings
- Load history
- Load profiles
- Cache recent sessions

---

## Inputs

```
SessionCompleted

ProfileUpdated

GoalCompleted
```

---

## Outputs

```
SessionSaved

SessionLoaded

DatabaseError
```

---

## Data Sources

Primary

Supabase PostgreSQL

Optional

Supabase Storage

Future

Redis Cache

---

## Storage Policy

Allowed

- Scores
- Analytics
- Session summaries
- Exercise history
- Goals

Never Store

- Webcam frames
- Video streams
- Raw images
- Face images

---

# 21. Notification Engine

## Purpose

Deliver contextual notifications without interrupting the user.

---

## Responsibilities

- Reminder scheduling
- Achievement notifications
- Goal completion
- Ergonomic reminders
- Session summaries

---

## Notification Types

Exercise

```
Goal completed.
```

---

Ergonomics

```
You have been slouching for 12 minutes.
```

---

Achievements

```
New personal best.

Shoulder stability increased by 8%.
```

---

System

```
Camera tracking lost.

Please move into view.
```

---

# 22. Report Engine

## Purpose

Generate exportable reports for users.

Reports should summarize sessions using computed metrics.

---

## Supported Formats

PDF

CSV

JSON

---

## Report Sections

```
Summary

↓

Exercise Breakdown

↓

Joint Analysis

↓

Improvement Trends

↓

Recommendations

↓

Session Timeline
```

---

## Future Reports

- Therapist Report
- Coach Report
- Weekly Summary
- Monthly Summary
- Comparison Report

---

# 23. Configuration System

## Philosophy

Every configurable value should exist outside the application source code.

Examples

```
Thresholds

↓

Pose Definitions

↓

Exercise Definitions

↓

Feedback Rules

↓

Scoring Weights

↓

UI Themes
```

---

## Directory

```
config/

poses/

exercises/

feedback/

thresholds/

weights/

notifications/

system/
```

---

## Benefits

- No hardcoded values
- Easy tuning
- Easier experimentation
- Non-developers can adjust rules
- Version-controlled configurations

---

# 24. Plugin System

Every exercise is implemented as a plugin.

Example

```
plugins/

exercise/

squat/

config.yaml

feedback.yaml

metadata.json

---

pushup/

---

plank/

---

warrior/
```

---

## Plugin Contract

Every plugin provides

```
Metadata

↓

Recognition Rules

↓

Scoring Rules

↓

Feedback Rules

↓

Visualization
```

---

## Plugin Lifecycle

```
Load

↓

Validate

↓

Register

↓

Activate

↓

Unload
```

---

# 25. Data Contracts

Communication between engines must use strongly typed data contracts.

Examples

```
Frame

LandmarkSet

BiomechanicsSnapshot

PoseResult

ExerciseResult

ScoreReport

FeedbackMessage

AnalyticsReport

SessionSummary
```

Each contract must include

- unique identifier
- timestamp
- source engine
- schema version

This allows backward compatibility and easier testing.

---

# 26. Error Handling Strategy

Errors are classified into four levels.

## Recoverable

Examples

- Temporary landmark loss
- Camera lag
- Low confidence

Action

Retry automatically.

---

## User Action Required

Examples

- Camera permission denied
- Webcam disconnected

Action

Display instructions.

---

## System Errors

Examples

- Database unavailable
- Authentication failure

Action

Retry and log.

---

## Fatal Errors

Examples

- AI model initialization failed
- Configuration invalid

Action

Terminate session safely.

---

# 27. Folder Structure

```
frontend/

src/

components/

features/

hooks/

lib/

workers/

types/

styles/

backend/

app/

api/

core/

engines/

services/

repositories/

models/

schemas/

middleware/

database/

tests/

shared/

config/

plugins/

docs/
```

---

# 28. Testing Strategy

Every engine must be independently testable.

Testing Levels

### Unit Tests

Each engine

- inputs
- outputs
- rules

---

### Integration Tests

Engine communication

Event flow

Configuration loading

---

### End-to-End Tests

Complete user workflow

```
Login

↓

Camera

↓

Pose Detection

↓

Feedback

↓

Analytics

↓

Dashboard
```

---

### Performance Tests

- FPS
- Memory
- CPU
- Inference latency
- Database response

---

# 29. Future AI Evolution

The architecture should support replacing deterministic rules with machine learning models.

Current

```
Landmarks

↓

Rule Engine

↓

Score
```

Future

```
Landmarks

↓

ML Classifier

↓

Rule Validator

↓

Feedback
```

Potential future models

- TensorFlow.js
- ONNX Runtime Web
- MediaPipe Tasks
- Custom Transformer
- Temporal Action Recognition Models

No UI or backend changes should be required.

---

# 30. Architecture Principles Summary

Every implementation in PostureSense must follow these principles.

1. Browser-first AI
2. Privacy-first processing
3. Event-driven communication
4. Configuration over hardcoding
5. Modular engine design
6. Strongly typed data contracts
7. Plugin-based extensibility
8. Explainable AI
9. Independent testing
10. Production-ready engineering

These principles take precedence over implementation convenience.

Whenever a design decision conflicts with these principles, the implementation should be revised rather than compromising the architecture.

---

# End of ENGINE_ARCHITECTURE.md