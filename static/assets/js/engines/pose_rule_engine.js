/**
 * PoseRuleEngine
 * Production-grade, configuration-driven static pose recognition & hold detection engine for PostureSense v2.
 * Consumes BiomechanicsSnapshot contracts, evaluates joint constraints against 12 supported poses, and publishes PoseResult contracts.
 */

export class PoseRuleEngine {
    constructor(eventBus = null) {
        this.name = "PoseRuleEngine";
        this.version = "2.0.0";
        this.eventBus = eventBus;
        this.status = "uninitialized";
        this.priority = 5;
        this.dependencies = ["biomechanics_engine"];

        // Supported Pose Definitions & Rule Constraints
        this.poseRules = {
            standing_neutral: {
                id: 'standing_neutral',
                name: 'Standing Neutral',
                minHoldTime: 2.0,
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
                constraints: {
                    left_knee: [160, 180],
                    right_knee: [30, 90]
                }
            },
            warrior_ii: {
                id: 'warrior_ii',
                name: 'Warrior II',
                minHoldTime: 3.0,
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
                constraints: {
                    left_knee: [80, 110],
                    right_knee: [160, 180]
                }
            },
            chair_pose: {
                id: 'chair_pose',
                name: 'Chair Pose',
                minHoldTime: 3.0,
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
                constraints: {
                    left_knee: [160, 180],
                    right_knee: [160, 180]
                }
            },
            downward_dog: {
                id: 'downward_dog',
                name: 'Downward Dog',
                minHoldTime: 3.0,
                constraints: {
                    spine: [30, 70]
                }
            },
            cobra: {
                id: 'cobra',
                name: 'Cobra Pose',
                minHoldTime: 3.0,
                constraints: {
                    spine: [10, 45]
                }
            },
            bridge: {
                id: 'bridge',
                name: 'Bridge Pose',
                minHoldTime: 3.0,
                constraints: {
                    left_hip: [150, 180]
                }
            },
            child_pose: {
                id: 'child_pose',
                name: "Child's Pose",
                minHoldTime: 3.0,
                constraints: {
                    left_knee: [20, 60]
                }
            },
            mountain_pose: {
                id: 'mountain_pose',
                name: 'Mountain Pose',
                minHoldTime: 2.0,
                constraints: {
                    left_knee: [165, 180],
                    right_knee: [165, 180]
                }
            },
            seated_neutral: {
                id: 'seated_neutral',
                name: 'Seated Neutral',
                minHoldTime: 2.0,
                constraints: {
                    left_knee: [80, 110],
                    right_knee: [80, 110]
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
            evaluationsCount: 0
        };
    }

    async initialize(config = {}) {
        if (config.poses) Object.assign(this.poseRules, config.poses);
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
        const jointAngles = snapshot.joint_angles || [];
        if (jointAngles.length === 0) return null;

        const anglesMap = {};
        jointAngles.forEach(j => { anglesMap[j.joint_name] = j.angle; });

        let bestMatch = null;
        let highestConfidence = 0.0;

        // Evaluate snapshot against all pose rules
        for (const [pid, rule] of Object.entries(this.poseRules)) {
            const evalResult = this._evaluatePoseRule(rule, anglesMap);
            if (evalResult.confidence > highestConfidence && evalResult.confidence >= 60.0) {
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
        }

        this.metrics.evaluationsCount++;

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
            tracking_quality: snapshot.tracking_quality || 100.0
        };

        this._publish("pose.detected", poseResultPayload);
        return poseResultPayload;
    }

    _evaluatePoseRule(rule, anglesMap) {
        let matched = 0;
        let total = 0;

        for (const [joint, [minA, maxA]] of Object.entries(rule.constraints)) {
            total++;
            const angle = anglesMap[joint];
            if (angle !== undefined && angle >= minA && angle <= maxA) {
                matched++;
            }
        }

        const confidence = total > 0 ? (matched / total) * 100.0 : 0.0;
        return {
            confidence: confidence,
            matchedRules: matched,
            failedRules: total - matched
        };
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
