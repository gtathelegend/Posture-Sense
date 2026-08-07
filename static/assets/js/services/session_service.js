/**
 * SessionService
 * Manages pose session saving.
 */

export class SessionService {
    static async savePoseSession(poseLabel, duration = 0.0, accuracy = 0.0) {
        try {
            const response = await fetch('/save_pose_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    pose_label: poseLabel,
                    duration: duration,
                    accuracy: accuracy
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error saving pose session:', error);
            throw error;
        }
    }
}
