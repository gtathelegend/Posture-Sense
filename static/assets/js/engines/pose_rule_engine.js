/**
 * PoseRuleEngine
 * Production-grade, configuration-driven static pose recognition & hold detection engine for PostureSense v2.
 * Consumes BiomechanicsSnapshot contracts, evaluates joint constraints and required landmark coverage against supported poses,
 * and publishes PoseResult contracts.
 */

const LANDMARK_NAME_TO_INDEX = {
    left_shoulder: 11,
    right_shoulder: 12,
    left_elbow: 13,
    right_elbow: 14,
    left_wrist: 15,
    right_wrist: 16,
    left_hip: 23,
    right_hip: 24,
    left_knee: 25,
    right_knee: 26,
    left_ankle: 27,
    right_ankle: 28,
    nose: 0
};

export class PoseRuleEngine {
    constructor(eventBus = null) {
        this.name = "PoseRuleEngine";
        this.version = "2.0.0";
        this.eventBus = eventBus;
        this.status = "uninitialized";
        this.priority = 5;
        this.dependencies = ["biomechanics_engine"];

        // Configuration
        this.config = {
            min_confidence: 60.0,
            min_tracking_quality: 50.0,
            min_valid_landmarks: 10,
            min_body_coverage_threshold: 0.70 // 70% coverage required
        };

        // Supported Pose Definitions & Rule Constraints
        this.poseRules = {
            standing_neutral: {
                id: 'standing_neutral',
                name: 'Standing Neutral',
                minHoldTime: 2.0,
                required_landmarks: ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
                constraints: {
                    left_knee: [160, 180],
                    right_knee: [160, 180],
                    spine: [0, 15]
                }
            },
            t_pose: {
                id: 't_pose',
                name: 'T Pose',
                minHoldTime: 2.0,
                required_landmarks: ['left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow', 'left_hip', 'right_hip', 'left_knee', 'right_knee'],
                constraints: {
                    left_elbow: [160, 195],
                    right_elbow: [160, 195],
                    left_shoulder: [80, 110],
                    right_shoulder: [80, 110],
                    left_knee: [160, 195],
                    right_knee: [160, 195]
                }
            },
            tree_pose: {
                id: 'tree_pose',
                name: 'Tree Pose',
                minHoldTime: 3.0,
                required_landmarks: ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
                constraints: {
                    left_knee: [160, 180],
                    right_knee: [30, 90]
                }
            },
            warrior_ii: {
                id: 'warrior_ii',
                name: 'Warrior II',
                minHoldTime: 3.0,
                required_landmarks: ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
                constraints: {
                    left_knee: [80, 110],
                    right_knee: [160, 180],
                    left_shoulder: [80, 105],
                    right_shoulder: [80, 105]
                }
            },
            warrior_i: {
                id: 'warrior_i',
                name: 'Warrior I',
                minHoldTime: 3.0,
                required_landmarks: ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
                constraints: {
                    left_knee: [80, 110],
                    right_knee: [160, 180]
                }
            },
            chair_pose: {
                id: 'chair_pose',
                name: 'Chair Pose',
                minHoldTime: 3.0,
                required_landmarks: ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
                constraints: {
                    left_knee: [90, 130],
                    right_knee: [90, 130],
                    left_hip: [80, 120]
                }
            },
            triangle_pose: {
                id: 'triangle_pose',
                name: 'Triangle Pose',
                minHoldTime: 3.0,
                required_landmarks: ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
                constraints: {
                    left_knee: [160, 180],
                    right_knee: [160, 180]
                }
            },
            downward_dog: {
                id: 'downward_dog',
                name: 'Downward Dog',
                minHoldTime: 3.0,
                required_landmarks: ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
                constraints: {
                    spine: [30, 70]
                }
            },
            cobra: {
                id: 'cobra',
                name: 'Cobra Pose',
                minHoldTime: 3.0,
                required_landmarks: ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
                constraints: {
                    spine: [10, 45],
                    left_hip: [150, 180],
                    right_hip: [150, 180],
                    left_knee: [160, 180],
                    right_knee: [160, 180]
                }
            },
            bridge: {
                id: 'bridge',
                name: 'Bridge Pose',
                minHoldTime: 3.0,
                required_landmarks: ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
                constraints: {
                    left_hip: [150, 180]
                }
            },
            child_pose: {
                id: 'child_pose',
                name: "Child's Pose",
                minHoldTime: 3.0,
                required_landmarks: ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
                constraints: {
                    left_knee: [20, 60]
                }
            },
            mountain_pose: {
                id: 'mountain_pose',
                name: 'Mountain Pose',
                minHoldTime: 2.0,
                required_landmarks: ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle'],
                constraints: {
                    left_knee: [165, 180],
                    right_knee: [165, 180]
                }
            },
            seated_neutral: {
                id: 'seated_neutral',
                name: 'Seated Neutral',
                minHoldTime: 2.0,
                required_landmarks: ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip', 'left_knee', 'right_knee'],
                constraints: {
                    spine: [0, 25]
                }
            }
        };

        // State Tracking for Holds
        this.currentPoseId = null;
        this.poseStartTime = null;
        this.holdState = 'idle'; // 'idle', 'entered', 'holding', 'completed'

        // Metrics & Diagnostics
        this.metrics = {
            currentPoseName: 'Unknown Pose',
            confidenceScore: 0.0,
            matchedRulesCount: 0,
            failedRulesCount: 0,
            holdDurationSeconds: 0.0,
            evaluationsCount: 0,
            requiredLandmarksCount: 0,
            visibleLandmarksCount: 0,
            missingLandmarksCount: 0,
            visibleLandmarksList: [],
            missingLandmarksList: [],
            bodyCoveragePct: 0.0,
            poseRejectionReason: 'None'
        };
    }

    async initialize(config = {}) {
        if (config.poses) Object.assign(this.poseRules, config.poses);
        if (config.min_confidence !== undefined) this.config.min_confidence = config.min_confidence;
        if (config.min_tracking_quality !== undefined) this.config.min_tracking_quality = config.min_tracking_quality;
        this.status = "initialized";
        this._publish("pose.initialized", this.getDiagnostics());
        return true;
    }

    async start() {
        this.status = "running";
        this._subscribeToBiomechanics();
        this._publish("pose.started", this.getDiagnostics());
        return true;
    }

    pause() {
        if (this.status === 'running') {
            this.status = "paused";
            this._publish("pose.paused", this.getDiagnostics());
        }
    }

    resume() {
        if (this.status === 'paused') {
            this.status = "running";
            this._publish("pose.resumed", this.getDiagnostics());
        }
    }

    async stop() {
        this.status = "stopped";
        this._publish("pose.stopped", this.getDiagnostics());
    }

    dispose() {
        this.stop();
        this.status = "disposed";
        this._publish("pose.disposed", this.getDiagnostics());
    }

    _subscribeToBiomechanics() {
        if (this.eventBus && typeof this.eventBus.subscribe === 'function') {
            this.eventBus.subscribe('biomechanics.updated', (event) => {
                if (this.status === 'running') {
                    this.evaluateSnapshot(event.data || {});
                }
            });
            this.eventBus.subscribe('tracking.lost', (event) => {
                if (this.status === 'running') {
                    this._returnUnknownState(event.data?.reason || "Tracking lost", 0.0);
                }
            });
        }
    }

    evaluateSnapshot(snapshot) {
        this.metrics.evaluationsCount++;
        const trackingQuality = snapshot.tracking_quality !== undefined ? snapshot.tracking_quality : 100.0;
        const landmarks = snapshot.landmarks || [];
        const jointAngles = snapshot.joint_angles || [];

        // Quality Gate 1: Minimum tracking quality check (< 50%)
        if (trackingQuality < this.config.min_tracking_quality) {
            return this._returnUnknownState("Low Tracking Quality (< 50%)", trackingQuality);
        }

        const anglesMap = {};
        jointAngles.forEach(j => {
            if (j.angle !== null && j.angle !== undefined && !isNaN(j.angle)) {
                anglesMap[j.joint_name] = j.angle;
            }
        });

        let bestMatch = null;
        let highestConfidence = 0.0;
        let lastRejectionReason = "No pose matched confidence threshold";

        // Evaluate snapshot against all pose rules
        for (const [pid, rule] of Object.entries(this.poseRules)) {
            const evalResult = this._evaluatePoseRule(rule, anglesMap, landmarks, jointAngles);

            if (evalResult.rejected) {
                lastRejectionReason = evalResult.rejectionReason;
                continue;
            }

            if (evalResult.confidence > highestConfidence && evalResult.confidence >= this.config.min_confidence) {
                highestConfidence = evalResult.confidence;
                bestMatch = { id: pid, rule: rule, ...evalResult };
            }
        }

        const now = performance.now();

        if (bestMatch) {
            if (this.currentPoseId !== bestMatch.id) {
                // Pose Changed / Entered
                if (this.currentPoseId) {
                    this._publish("pose.exited", { pose_id: this.currentPoseId });
                }
                this.currentPoseId = bestMatch.id;
                this.poseStartTime = now;
                this.holdState = 'entered';
                this._publish("pose.changed", { pose_id: bestMatch.id, pose_name: bestMatch.rule.name });
                this._publish("pose.entered", { pose_id: bestMatch.id, pose_name: bestMatch.rule.name });
            } else {
                // Pose Hold Tracking
                const elapsedSeconds = (now - this.poseStartTime) / 1000.0;
                this.metrics.holdDurationSeconds = roundVal(elapsedSeconds, 1);

                if (elapsedSeconds >= 1.0 && this.holdState === 'entered') {
                    this.holdState = 'holding';
                    this._publish("pose.hold_started", { pose_id: bestMatch.id, holdTime: elapsedSeconds });
                }
                if (elapsedSeconds >= bestMatch.rule.minHoldTime && this.holdState !== 'completed') {
                    this.holdState = 'completed';
                    this._publish("pose.hold_completed", { pose_id: bestMatch.id, holdTime: elapsedSeconds });
                }
            }

            this.metrics.currentPoseName = bestMatch.rule.name;
            this.metrics.confidenceScore = roundVal(bestMatch.confidence, 1);
            this.metrics.matchedRulesCount = bestMatch.matchedRules;
            this.metrics.failedRulesCount = bestMatch.failedRules;
            this.metrics.requiredLandmarksCount = bestMatch.totalRequiredLandmarks;
            this.metrics.visibleLandmarksCount = bestMatch.visibleLandmarks.length;
            this.metrics.missingLandmarksCount = bestMatch.missingLandmarks.length;
            this.metrics.visibleLandmarksList = bestMatch.visibleLandmarks;
            this.metrics.missingLandmarksList = bestMatch.missingLandmarks;
            this.metrics.bodyCoveragePct = bestMatch.coveragePct;
            this.metrics.poseRejectionReason = "None";
        } else {
            return this._returnUnknownState(lastRejectionReason, trackingQuality);
        }

        // Construct PoseResult Payload
        const poseResultPayload = {
            id: Math.random().toString(36).substring(2, 11),
            timestamp: new Date().toISOString(),
            schema_version: '2.0.0',
            source: 'PoseRuleEngine',
            pose_id: this.currentPoseId || 'unknown',
            pose_name: this.metrics.currentPoseName,
            confidence: this.metrics.confidenceScore,
            matched_rules: this.metrics.matchedRulesCount,
            failed_rules: this.metrics.failedRulesCount,
            hold_time: this.metrics.holdDurationSeconds,
            tracking_quality: trackingQuality,
            required_landmarks: this.metrics.requiredLandmarksCount,
            visible_landmarks: this.metrics.visibleLandmarksList,
            missing_landmarks: this.metrics.missingLandmarksList,
            body_coverage_pct: this.metrics.bodyCoveragePct,
            pose_rejection_reason: this.metrics.poseRejectionReason
        };

        this._publish("pose.detected", poseResultPayload);
        return poseResultPayload;
    }

    _evaluatePoseRule(rule, anglesMap, landmarks, jointAngles = []) {
        const requiredLandmarks = rule.required_landmarks || [];
        const constraints = rule.constraints || {};

        const totalRequiredLandmarks = requiredLandmarks.length;
        const totalJointConstraints = Object.keys(constraints).length;

        // FORMULA REQUIREMENT: matched / required
        const totalRequired = totalJointConstraints + totalRequiredLandmarks;

        // Extract valid landmark names
        const visibleLandmarks = [];
        const missingLandmarks = [];

        if (landmarks && landmarks.length > 0) {
            const landmarkMap = {};
            landmarks.forEach(lm => {
                if (lm.name) landmarkMap[lm.name.toLowerCase()] = lm;
                if (lm.index !== undefined) {
                    // Reverse map index to name if needed
                    const entry = Object.entries(LANDMARK_NAME_TO_INDEX).find(([n, idx]) => idx === lm.index);
                    if (entry) landmarkMap[entry[0]] = lm;
                }
            });

            for (const lmName of requiredLandmarks) {
                const lm = landmarkMap[lmName.toLowerCase()];
                const isVis = lm && (lm.visibility === undefined || lm.visibility >= 0.6) && (lm.presence === undefined || lm.presence >= 0.6);
                if (isVis) {
                    visibleLandmarks.push(lmName);
                } else {
                    missingLandmarks.push(lmName);
                }
            }
        } else {
            // Fallback checking joint angles availability if landmarks raw array is absent
            const availableJoints = new Set((jointAngles || []).map(j => j.joint_name));
            for (const lmName of requiredLandmarks) {
                if (lmName.includes('knee') && (availableJoints.has('left_knee') || availableJoints.has('right_knee'))) {
                    visibleLandmarks.push(lmName);
                } else if (lmName.includes('shoulder') && (availableJoints.has('left_shoulder') || availableJoints.has('right_shoulder'))) {
                    visibleLandmarks.push(lmName);
                } else if (lmName.includes('hip') && (availableJoints.has('left_hip') || availableJoints.has('right_hip'))) {
                    visibleLandmarks.push(lmName);
                } else {
                    missingLandmarks.push(lmName);
                }
            }
        }

        const visibleCount = visibleLandmarks.length;
        const coverage = totalRequiredLandmarks > 0 ? (visibleCount / totalRequiredLandmarks) : 1.0;
        const coveragePct = roundVal(coverage * 100.0, 1);

        // BODY COVERAGE VALIDATION: If coverage < 70%, return pose = UNKNOWN, confidence = 0, reason = "Insufficient body visibility"
        if (coverage < this.config.min_body_coverage_threshold) {
            return {
                rejected: true,
                confidence: 0.0,
                coveragePct: coveragePct,
                visibleLandmarks: visibleLandmarks,
                missingLandmarks: missingLandmarks,
                totalRequiredLandmarks: totalRequiredLandmarks,
                rejectionReason: "Insufficient body visibility"
            };
        }

        // Evaluate Joint Angle Constraints
        let matchedJoints = 0;
        for (const [joint, [minA, maxA]] of Object.entries(constraints)) {
            const angle = anglesMap[joint];
            if (angle !== undefined && angle >= minA && angle <= maxA) {
                matchedJoints++;
            }
        }

        // CONFIDENCE FORMULA: (matched_joints + visible_required_landmarks) / (total_joint_constraints + total_required_landmarks)
        const totalMatched = matchedJoints + visibleCount;
        const confidence = totalRequired > 0 ? (totalMatched / totalRequired) * 100.0 : 0.0;

        return {
            rejected: false,
            confidence: roundVal(confidence, 1),
            matchedRules: totalMatched,
            failedRules: totalRequired - totalMatched,
            totalRequired: totalRequired,
            totalRequiredLandmarks: totalRequiredLandmarks,
            visibleLandmarks: visibleLandmarks,
            missingLandmarks: missingLandmarks,
            coveragePct: coveragePct,
            rejectionReason: "None"
        };
    }

    _returnUnknownState(reason, trackingQuality) {
        if (this.currentPoseId) {
            this._publish("pose.exited", { pose_id: this.currentPoseId });
            this.currentPoseId = null;
            this.poseStartTime = null;
            this.holdState = 'idle';
        }

        this.metrics.currentPoseName = 'Unknown Pose';
        this.metrics.confidenceScore = 0.0;
        this.metrics.matchedRulesCount = 0;
        this.metrics.failedRulesCount = 0;
        this.metrics.holdDurationSeconds = 0.0;
        this.metrics.poseRejectionReason = reason;

        const payload = {
            id: Math.random().toString(36).substring(2, 11),
            timestamp: new Date().toISOString(),
            schema_version: '2.0.0',
            source: 'PoseRuleEngine',
            pose_id: 'unknown',
            pose_name: 'Unknown Pose',
            confidence: 0.0,
            matched_rules: 0,
            failed_rules: 0,
            hold_time: 0.0,
            tracking_quality: trackingQuality,
            required_landmarks: this.metrics.requiredLandmarksCount,
            visible_landmarks: this.metrics.visibleLandmarksList,
            missing_landmarks: this.metrics.missingLandmarksList,
            body_coverage_pct: this.metrics.bodyCoveragePct,
            pose_rejection_reason: reason
        };

        this._publish("pose.detected", payload);
        return payload;
    }

    getDiagnostics() {
        return {
            name: this.name,
            version: this.version,
            status: this.status,
            priority: this.priority,
            dependencies: this.dependencies,
            config: { ...this.config },
            metrics: { ...this.metrics }
        };
    }

    _publish(eventName, data) {
        if (this.eventBus && typeof this.eventBus.publish === 'function') {
            this.eventBus.publish(eventName, data);
        }
    }
}

function roundVal(num, decimals = 2) {
    return Number(Math.round(num + 'e' + decimals) + 'e-' + decimals);
}
