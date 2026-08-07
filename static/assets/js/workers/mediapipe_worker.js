/**
 * MediaPipe Tasks Vision Web Worker
 * Performs off-main-thread 33-landmark pose detection using PoseLandmarker.
 */

importScripts('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm/vision_bundle.js');

let poseLandmarker = null;

self.onmessage = async (e) => {
    const { action, payload } = e.data;

    if (action === 'LOAD_MODEL') {
        try {
            const vision = await self.tasksVision.FilesetResolver.forVisionTasks(
                'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm'
            );
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
            self.postMessage({ action: 'MODEL_LOADED', success: true });
        } catch (error) {
            self.postMessage({ action: 'MODEL_ERROR', error: error.message });
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

            const landmarks = result.landmarks && result.landmarks[0] ? result.landmarks[0] : [];
            self.postMessage({
                action: 'FRAME_PROCESSED',
                landmarks: landmarks,
                confidence: landmarks.length > 0 ? 0.95 : 0.0,
                latencyMs: latency,
                frameNumber: payload.frameNumber
            });
        } catch (error) {
            self.postMessage({ action: 'FRAME_ERROR', error: error.message });
        }
    }
};
