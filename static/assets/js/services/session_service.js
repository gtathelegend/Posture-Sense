/**
 * SessionService
 * Manages pose session saving.
 */

export class SessionService {
    static async savePoseSession(payloadOrPoseLabel, duration = 0.0, accuracy = 0.0) {
        try {
            const body = typeof payloadOrPoseLabel === 'object' && payloadOrPoseLabel !== null
                ? payloadOrPoseLabel
                : { pose_label: payloadOrPoseLabel, duration: duration, accuracy: accuracy };

            const parseMetric = (val) => (val !== null && val !== undefined && !isNaN(val)) ? Number(val) : null;

            const response = await fetch('/api/save_pose_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    pose_label: body.pose_label || body.poseLabel || 'Unknown Pose',
                    duration: Number(body.duration || 0.0),
                    accuracy: Number(body.accuracy ?? body.overall_score ?? 0.0),
                    reps: Number(body.reps || 0),
                    symmetry_score: parseMetric(body.symmetry_score ?? body.symmetryScore),
                    balance_score: parseMetric(body.balance_score ?? body.balanceScore),
                    stability_score: parseMetric(body.stability_score ?? body.stabilityScore),
                    rom_score: parseMetric(body.rom_score ?? body.romScore),
                    hold_time: Number(body.hold_time ?? body.holdTime ?? 0.0),
                    tracking_quality: parseMetric(body.tracking_quality ?? body.trackingQuality),
                    failed_rules: Array.isArray(body.failed_rules) ? body.failed_rules : (Array.isArray(body.failedRules) ? body.failedRules : [])
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error saving pose session:', error);
            throw error;
        }
    }
}

