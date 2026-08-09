/**
 * MediaPipe Tasks Vision Web Worker
 * Performs off-main-thread 33-landmark pose detection using PoseLandmarker.
 * Preserves x, y, z, visibility, and presence metadata with safe fallbacks.
 */

try {
    importScripts('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/vision_bundle.js');
} catch (error) {
    console.error('[MediaPipeWorker] Failed to import vision_bundle.js script:', error);
}

const LANDMARK_NAMES = [
    'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer', 'right_eye_inner', 'right_eye',
    'right_eye_outer', 'left_ear', 'right_ear', 'mouth_left', 'mouth_right', 'left_shoulder',
    'right_shoulder', 'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'left_pinky',
    'right_pinky', 'left_index', 'right_index', 'left_thumb', 'right_thumb', 'left_hip',
    'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle', 'left_heel',
    'right_heel', 'left_foot_index', 'right_foot_index'
];

let poseLandmarker = null;

self.onmessage = async (e) => {
    const { action, payload } = e.data;

    if (action === 'LOAD_MODEL') {
        try {
            console.log('[MediaPipeWorker] Initializing FilesetResolver...');
            const vision = await self.tasksVision.FilesetResolver.forVisionTasks(
                'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm'
            );
            console.log('[MediaPipeWorker] FilesetResolver initialized. Creating PoseLandmarker...');

            poseLandmarker = await self.tasksVision.PoseLandmarker.createFromOptions(vision, {
                baseOptions: {
                    modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task',
                    delegate: 'GPU'
                },
                runningMode: 'IMAGE',
                numPoses: 1,
                minPoseDetectionConfidence: 0.5,
                minPosePresenceConfidence: 0.5,
                minTrackingConfidence: 0.5
            });

            console.log('[MediaPipeWorker] PoseLandmarker successfully created.');
            self.postMessage({ action: 'MODEL_LOADED', success: true });
        } catch (error) {
            console.error('[MediaPipeWorker] Error loading MediaPipe model:', error);
            self.postMessage({ action: 'MODEL_ERROR', error: error.message || String(error) });
        }
    } else if (action === 'PROCESS_FRAME') {
        if (!poseLandmarker) {
            self.postMessage({ action: 'FRAME_PROCESSED', landmarks: [], confidence: 0 });
            return;
        }
        try {
            const startTime = performance.now();
            const result = poseLandmarker.detect(payload.imageBitmap);
            const latency = performance.now() - startTime;

            const rawLandmarks = result.landmarks && result.landmarks[0] ? result.landmarks[0] : [];
            const landmarks = rawLandmarks.map((lm, i) => ({
                id: i,
                index: i,
                name: LANDMARK_NAMES[i] || `landmark_${i}`,
                x: lm.x,
                y: lm.y,
                z: lm.z !== undefined && lm.z !== null ? lm.z : 0.0,
                visibility: lm.visibility !== undefined && lm.visibility !== null ? lm.visibility : 0.0,
                presence: lm.presence !== undefined && lm.presence !== null ? lm.presence : 0.0
            }));

            self.postMessage({
                action: 'FRAME_PROCESSED',
                landmarks: landmarks,
                confidence: landmarks.length > 0 ? 0.95 : 0.0,
                latencyMs: latency,
                frameNumber: payload.frameNumber
            });
        } catch (error) {
            console.error('[MediaPipeWorker] Error processing frame:', error);
            self.postMessage({ action: 'FRAME_ERROR', error: error.message || String(error) });
        }
    }
};
