/**
 * PoseRuleEngine
 * Production-grade, configuration-driven static pose recognition & hold detection engine for PostureSense v2.
 * Consumes BiomechanicsSnapshot contracts, evaluates joint constraints and required landmark coverage against supported poses,
 * and publishes PoseResult contracts.
 */

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
            min_valid_landmarks: 10
        };

        // Supported Pose Definitions & Rule Constraints
        this.poseRules = {
            standing_neutral: {
                id: 'standing_neutral',
                name: 'Standing Neutral',
                minHoldTime: 2.0,
                requiresFullBody: true,
                requiredRegions: ['head', 'shoulders', 'hips', 'knees', 'ankles'],
                constraints: {
                    left_knee: [160, 180],
                    right_knee: [160, 180],
                    spine: [0, 15]
                }
            },
            tree_pose: {
                id: 'tree_pose',
                name: 'Tree Pose',
                minHoldTime: 3.0,
                requiresFullBody: true,
                requiredRegions: ['head', 'shoulders', 'hips', 'knees', 'ankles'],
                constraints: {
                    left_knee: [160, 180],
                    right_knee: [30, 90]
                }
            },
            warrior_ii: {
                id: 'warrior_ii',
                name: 'Warrior II',
                minHoldTime: 3.0,
                requiresFullBody: true,
                requiredRegions: ['head', 'shoulders', 'hips', 'knees', 'ankles'],
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
                requiresFullBody: true,
                requiredRegions: ['head', 'shoulders', 'hips', 'knees', 'ankles'],
                constraints: {
                    left_knee: [80, 110],
                    right_knee: [160, 180]
                }
            },
            chair_pose: {
                id: 'chair_pose',
                name: 'Chair Pose',
                minHoldTime: 3.0,
                requiresFullBody: true,
                requiredRegions: ['head', 'shoulders', 'hips', 'knees', 'ankles'],
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
                requiresFullBody: true,
                requiredRegions: ['head', 'shoulders', 'hips', 'knees', 'ankles'],
                constraints: {
                    left_knee: [160, 180],
                    right_knee: [160, 180]
                }
            },
            downward_dog: {
                id: 'downward_dog',
                name: 'Downward Dog',
                minHoldTime: 3.0,
                requiresFullBody: true,
                requiredRegions: ['head', 'shoulders', 'hips', 'knees', 'ankles'],
                constraints: {
                    spine: [30, 70]
                }
            },
            cobra: {
                id: 'cobra',
                name: 'Cobra Pose',
                minHoldTime: 3.0,
                requiresFullBody: true,
                requiredRegions: ['head', 'shoulders', 'hips', 'knees', 'ankles'],
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
                requiresFullBody: true,
                requiredRegions: ['head', 'shoulders', 'hips', 'knees', 'ankles'],
                constraints: {
                    left_hip: [150, 180]
                }
            },
            child_pose: {
                id: 'child_pose',
                name: "Child's Pose",
                minHoldTime: 3.0,
                requiresFullBody: true,
                requiredRegions: ['head', 'shoulders', 'hips', 'knees', 'ankles'],
                constraints: {
                    left_knee: [20, 60]
                }
            },
            mountain_pose: {
                id: 'mountain_pose',
                name: 'Mountain Pose',
                minHoldTime: 2.0,
                requiresFullBody: true,
                requiredRegions: ['head', 'shoulders', 'hips', 'knees', 'ankles'],
                constraints: {
                    left_knee: [165, 180],
                    right_knee: [165, 180]
                }
            },
            seated_neutral: {
                id: 'seated_neutral',
                name: 'Seated Neutral',
                minHoldTime: 2.0,
                requiresFullBody: false,
                requiredRegions: ['head', 'shoulders', 'hips'],
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
            availableLandmarksCount: 0,
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
        }
    }

    evaluateSnapshot(snapshot) {
        this.metrics.evaluationsCount++;
        const trackingQuality = snapshot.tracking_quality !== undefined ? snapshot.tracking_quality : 100.0;
        const landmarks = snapshot.landmarks || [];
        const jointAngles = snapshot.joint_angles || [];

        // Quality Gate 1: Tracking Quality Threshold Check
        if (trackingQuality < this.config.min_tracking_quality) {
            return this._returnUnknownState("Low Tracking Quality (< 50%)", trackingQuality);
        }

        // Body Coverage Analysis
        const bodyCoverage = this._checkBodyCoverage(landmarks, jointAngles);
        this.metrics.availableLandmarksCount = bodyCoverage.validCount;
        this.metrics.bodyCoveragePct = bodyCoverage.coveragePct;

        // Quality Gate 2: Insufficient Keypoints Check
        if (bodyCoverage.validCount < this.config.min_valid_landmarks) {
            return this._returnUnknownState("Insufficient Valid Landmarks (< 10)", trackingQuality);
        }

        const anglesMap = {};
        jointAngles.forEach(j => {
            if (j.angle !== null && j.angle !== undefined && !isNaN(j.angle)) {
                anglesMap[j.joint_name] = j.angle;
            }
        });

        let bestMatch = null;
        let highestConfidence = 0.0;

        // Evaluate snapshot against all pose rules
        for (const [pid, rule] of Object.entries(this.poseRules)) {
            const evalResult = this._evaluatePoseRule(rule, anglesMap, bodyCoverage);
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
            this.metrics.requiredLandmarksCount = bestMatch.totalRequired;
            this.metrics.poseRejectionReason = "None";
        } else {
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
            this.metrics.poseRejectionReason = bodyCoverage.rejectionReason || "No pose matched confidence threshold";
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
            available_landmarks: this.metrics.availableLandmarksCount,
            body_coverage_pct: this.metrics.bodyCoveragePct,
            pose_rejection_reason: this.metrics.poseRejectionReason
        };

        this._publish("pose.detected", poseResultPayload);
        return poseResultPayload;
    }

    _evaluatePoseRule(rule, anglesMap, bodyCoverage) {
        let matched = 0;

        const constraints = rule.constraints || {};
        const requiredRegions = rule.requiredRegions || [];

        const totalJointConstraints = Object.keys(constraints).length;
        const totalRequiredRegions = requiredRegions.length;

        // FORMULA REQUIREMENT: total_required_rules = total_joint_constraints + total_required_landmarks
        const totalRequired = totalJointConstraints + totalRequiredRegions;

        // 1. Evaluate Joint Angle Constraints
        for (const [joint, [minA, maxA]] of Object.entries(constraints)) {
            const angle = anglesMap[joint];
            if (angle !== undefined && angle >= minA && angle <= maxA) {
                matched++;
            }
        }

        // 2. Evaluate Required Landmark Regions
        for (const region of requiredRegions) {
            if (bodyCoverage.availableRegions.includes(region)) {
                matched++;
            }
        }

        // 3. Full Body Gate Check
        if (rule.requiresFullBody && !bodyCoverage.hasFullBody) {
            return {
                confidence: 0.0,
                matchedRules: matched,
                failedRules: totalRequired - matched,
                totalRequired: totalRequired,
                rejectionReason: "Requires full body tracking (lower body keypoints missing)"
            };
        }

        const confidence = totalRequired > 0 ? (matched / totalRequired) * 100.0 : 0.0;
        return {
            confidence: roundVal(confidence, 1),
            matchedRules: matched,
            failedRules: totalRequired - matched,
            totalRequired: totalRequired,
            rejectionReason: "None"
        };
    }

    _checkBodyCoverage(landmarks, jointAngles = []) {
        if (!landmarks || landmarks.length === 0) {
            // Fallback checking joint angles availability if landmarks raw array is empty
            const availableJoints = new Set((jointAngles || []).map(j => j.joint_name));
            const hasLegs = availableJoints.has('left_knee') || availableJoints.has('right_knee');
            const hasUpper = availableJoints.has('left_shoulder') || availableJoints.has('right_shoulder');
            const regions = [];
            if (hasUpper) { regions.push('head'); regions.push('shoulders'); regions.push('hips'); }
            if (hasLegs) { regions.push('knees'); regions.push('ankles'); }

            return {
                validCount: availableJoints.size * 2,
                availableRegions: regions,
                coveragePct: (regions.length / 5.0) * 100.0,
                hasFullBody: hasLegs && hasUpper,
                rejectionReason: hasLegs ? "None" : "Missing lower body keypoints"
            };
        }

        const validLms = landmarks.filter(lm => (lm.visibility === undefined || lm.visibility >= 0.5));
        const validIndices = new Set(validLms.map(lm => lm.index));

        const regions = [];
        // Region 1: Head (0..10)
        const hasHead = [0,1,2,3,4,5,6,7,8,9,10].some(i => validIndices.has(i));
        if (hasHead) regions.push('head');

        // Region 2: Shoulders (11, 12)
        const hasShoulders = validIndices.has(11) || validIndices.has(12);
        if (hasShoulders) regions.push('shoulders');

        // Region 3: Hips (23, 24)
        const hasHips = validIndices.has(23) || validIndices.has(24);
        if (hasHips) regions.push('hips');

        // Region 4: Knees (25, 26)
        const hasKnees = validIndices.has(25) || validIndices.has(26);
        if (hasKnees) regions.push('knees');

        // Region 5: Ankles (27, 28)
        const hasAnkles = validIndices.has(27) || validIndices.has(28);
        if (hasAnkles) regions.push('ankles');

        const hasFullBody = hasHead && hasShoulders && hasHips && hasKnees && hasAnkles;
        let rejectionReason = "None";
        if (!hasKnees || !hasAnkles) {
            rejectionReason = "Lower body missing (knees/ankles cut off)";
        }

        return {
            validCount: validLms.length,
            availableRegions: regions,
            coveragePct: roundVal((regions.length / 5.0) * 100.0, 1),
            hasFullBody: hasFullBody,
            rejectionReason: rejectionReason
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
            required_landmarks: 0,
            available_landmarks: this.metrics.availableLandmarksCount,
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
