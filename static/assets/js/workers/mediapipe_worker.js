/**
 * MediaPipe Tasks Vision Web Worker
 * Performs off-main-thread 33-landmark pose detection using PoseLandmarker.
 * Uses only locally hosted MediaPipe assets from /static/vendor/mediapipe/v0.10.0/.
 */

const MEDIAPIPE_ASSET_BASE = '/static/vendor/mediapipe/v0.10.0';
const VISION_BUNDLE_PATH = `${MEDIAPIPE_ASSET_BASE}/vision_bundle.js`;
const WASM_ASSETS_PATH = `${MEDIAPIPE_ASSET_BASE}/wasm`;
const POSE_MODEL_PATH = `${MEDIAPIPE_ASSET_BASE}/pose_landmarker_lite.task`;

let visionLoaded = false;
let visionLoadError = null;

console.log('[MediaPipeWorker] Loading local Vision bundle...');
try {
    importScripts(VISION_BUNDLE_PATH);
    visionLoaded = true;
    console.log('[MediaPipeWorker] Vision bundle loaded successfully.');
} catch (err) {
    visionLoaded = false;
    visionLoadError = err;
    console.error(`[MediaPipeWorker] Failed to load Vision bundle from ${VISION_BUNDLE_PATH}:`, err);
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
            if (!visionLoaded || !self.tasksVision) {
                const errDetail = visionLoadError ? (visionLoadError.message || String(visionLoadError)) : 'self.tasksVision unavailable';
                const errorMsg = `Vision bundle missing or failed to load: ${VISION_BUNDLE_PATH} (${errDetail})`;
                console.error(`[MediaPipeWorker] ${errorMsg}`);
                self.postMessage({ action: 'MODEL_ERROR', error: errorMsg });
                return;
            }

            console.log('[MediaPipeWorker] Initializing local WASM runtime...');
            let vision = null;
            try {
                vision = await self.tasksVision.FilesetResolver.forVisionTasks(WASM_ASSETS_PATH);
                console.log('[MediaPipeWorker] WASM runtime initialized.');
            } catch (wasmErr) {
                const errorMsg = `WASM runtime missing or failed to initialize: ${WASM_ASSETS_PATH} (${wasmErr.message || wasmErr})`;
                console.error(`[MediaPipeWorker] ${errorMsg}`);
                self.postMessage({ action: 'MODEL_ERROR', error: errorMsg });
                return;
            }

            console.log('[MediaPipeWorker] Loading local pose model...');
            try {
                poseLandmarker = await self.tasksVision.PoseLandmarker.createFromOptions(vision, {
                    baseOptions: {
                        modelAssetPath: POSE_MODEL_PATH,
                        delegate: 'GPU'
                    },
                    runningMode: 'IMAGE',
                    numPoses: 1,
                    minPoseDetectionConfidence: 0.5,
                    minPosePresenceConfidence: 0.5,
                    minTrackingConfidence: 0.5
                });
                console.log('[MediaPipeWorker] Pose model loaded successfully.');
                console.log('[MediaPipeWorker] MediaPipe ready.');
                self.postMessage({ action: 'MODEL_LOADED', success: true });
            } catch (modelErr) {
                const errorMsg = `Pose model missing or failed to load: ${POSE_MODEL_PATH} (${modelErr.message || modelErr})`;
                console.error(`[MediaPipeWorker] ${errorMsg}`);
                self.postMessage({ action: 'MODEL_ERROR', error: errorMsg });
                return;
            }
        } catch (error) {
            const errorMsg = `MediaPipe initialization failure: ${error.message || String(error)}`;
            console.error('[MediaPipeWorker] Error loading MediaPipe model:', error);
            self.postMessage({ action: 'MODEL_ERROR', error: errorMsg });
        }
    } else if (action === 'PROCESS_FRAME') {
        if (!poseLandmarker) {
            self.postMessage({ action: 'FRAME_ERROR', error: 'PoseLandmarker is uninitialized.' });
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

