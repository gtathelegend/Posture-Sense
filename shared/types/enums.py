from enum import Enum


class PluginMode(str, Enum):
    EXERCISE = "exercise"
    YOGA = "yoga"
    ERGONOMICS = "ergonomics"
    REHABILITATION = "rehabilitation"


class EngineStatus(str, Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class ContractSource(str, Enum):
    CAMERA = "camera_engine"
    MEDIAPIPE = "mediapipe_engine"
    LANDMARK = "landmark_engine"
    BIOMECHANICS = "biomechanics_engine"
    POSE_RULE = "pose_rule_engine"
    MOVEMENT = "movement_engine"
    SCORING = "scoring_engine"
    FEEDBACK = "feedback_engine"
    ANALYTICS = "analytics_engine"
    PERSISTENCE = "persistence_engine"
    NOTIFICATION = "notification_engine"
    REPORT = "report_engine"
    USER = "user_input"
    SYSTEM = "system"
