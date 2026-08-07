class EventNames:
    # Camera Events
    CAMERA_STARTED = "camera.started"
    FRAME_CAPTURED = "camera.frame_captured"
    CAMERA_PAUSED = "camera.paused"
    CAMERA_STOPPED = "camera.stopped"
    CAMERA_ERROR = "camera.error"

    # Landmark Events
    LANDMARKS_DETECTED = "landmark.detected"
    LANDMARKS_LOST = "landmark.lost"
    TRACKING_RECOVERED = "landmark.recovered"
    LOW_CONFIDENCE_FRAME = "landmark.low_confidence"

    # Biomechanics & Pose Events
    ANGLES_CALCULATED = "biomechanics.angles_calculated"
    POSE_RECOGNIZED = "pose.recognized"
    POSE_LOST = "pose.lost"
    POSE_CHANGED = "pose.changed"

    # Movement & Exercise Events
    EXERCISE_STARTED = "exercise.started"
    EXERCISE_COMPLETED = "exercise.completed"
    REP_COMPLETED = "exercise.rep_completed"
    EXERCISE_PAUSED = "exercise.paused"

    # Scoring & Feedback Events
    SCORE_UPDATED = "scoring.updated"
    FEEDBACK_GENERATED = "feedback.generated"

    # Analytics & Session Events
    SESSION_STARTED = "analytics.session_started"
    SESSION_ENDED = "analytics.session_ended"
    STATISTICS_UPDATED = "analytics.stats_updated"
    DASHBOARD_REFRESH = "analytics.dashboard_refresh"

    # System & User Events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    PROFILE_UPDATED = "user.profile_updated"
    GOAL_COMPLETED = "user.goal_completed"
