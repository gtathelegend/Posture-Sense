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

            const response = await fetch('/api/save_pose_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    pose_label: body.pose_label || body.poseLabel || 'Unknown Pose',
                    duration: Number(body.duration || 0.0),
                    accuracy: Number(body.accuracy || 0.0),
                    reps: Number(body.reps || 0),
                    symmetry_score: Number(body.symmetry_score ?? body.symmetryScore ?? 100.0),
                    balance_score: Number(body.balance_score ?? body.balanceScore ?? 100.0),
                    stability_score: Number(body.stability_score ?? body.stabilityScore ?? 100.0),
                    rom_score: Number(body.rom_score ?? body.romScore ?? 100.0),
                    hold_time: Number(body.hold_time ?? body.holdTime ?? 0.0),
                    tracking_quality: Number(body.tracking_quality ?? body.trackingQuality ?? 100.0),
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

