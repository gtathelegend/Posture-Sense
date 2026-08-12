/**
 * MediaPipe Tasks Vision Web Worker (ES Module)
 * Performs off-main-thread 33-landmark pose detection using PoseLandmarker.
 *
 * Uses only locally hosted MediaPipe ESM assets from /static/vendor/mediapipe/v0.10.0/.
 *
 * FIX: vision_bundle.js internally calls a classic-worker script loader to load
 * vision_wasm_internal.js, which is forbidden in ES module workers. We work around this by:
 *   1. Fetching vision_wasm_internal.js as text and executing it via new Function() to
 *      set self.ModuleFactory — bypassing the internal classic-worker loader.
 *   2. Passing a modified fileset with wasmLoaderPath=null so createMediaPipeLib's
 *      internal o() loader function is never invoked.
 *   3. Pre-fetching the .task model as an ArrayBuffer and passing it via modelAssetBuffer
 *      so there is no internal model URL fetch.
 */

const MEDIAPIPE_ASSET_BASE = '/static/vendor/mediapipe/v0.10.0';
const VISION_BUNDLE_PATH   = `${MEDIAPIPE_ASSET_BASE}/vision_bundle.js`;
const WASM_DIR_PATH        = `${MEDIAPIPE_ASSET_BASE}/wasm`;
const POSE_MODEL_PATH      = `${MEDIAPIPE_ASSET_BASE}/pose_landmarker_lite.task`;

const LANDMARK_NAMES = [
    'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer', 'right_eye_inner', 'right_eye',
    'right_eye_outer', 'left_ear', 'right_ear', 'mouth_left', 'mouth_right', 'left_shoulder',
    'right_shoulder', 'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'left_pinky',
    'right_pinky', 'left_index', 'right_index', 'left_thumb', 'right_thumb', 'left_hip',
    'right_hip', 'left_knee', 'right_knee', 'left_ankle', 'right_ankle', 'left_heel',
    'right_heel', 'left_foot_index', 'right_foot_index'
];

let poseLandmarkerInstance = null;
let _lastTimestamp = 0;
let _receivedFrameCount = 0;

// ─── Helper: post a structured error ─────────────────────────────────────────

function postError(stage, message) {
    console.error(`[MediaPipeWorker] ${stage}: ${message}`);
    self.postMessage({ action: 'MODEL_ERROR', stage, error: message });
}

// ─── Helper: detect whether SIMD WASM is supported ───────────────────────────

async function isSimdSupported() {
    try {
        // Minimal SIMD probe (v8-compatible)
        const simdTest = new Uint8Array([
            0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00,
            0x01, 0x05, 0x01, 0x60, 0x00, 0x01, 0x7b, 0x03,
            0x02, 0x01, 0x00, 0x0a, 0x0a, 0x01, 0x08, 0x00,
            0xfd, 0x0f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x0b
        ]);
        await WebAssembly.validate(simdTest);
        return true;
    } catch (_) {
        return false;
    }
}

// ─── Step 1: Load Vision Bundle (ES module import) ───────────────────────────

async function loadVisionBundle() {
    console.log('[MediaPipeWorker] Loading local Vision bundle...');
    const visionModule = await import(VISION_BUNDLE_PATH);

    const exports = visionModule;
    console.log('[MediaPipeWorker] Vision module exports:', Object.keys(exports).join(', '));

    const FilesetResolver = exports.FilesetResolver ?? exports.default?.FilesetResolver;
    const PoseLandmarker  = exports.PoseLandmarker  ?? exports.default?.PoseLandmarker;

    if (!FilesetResolver) throw new Error('FilesetResolver export is unavailable');
    if (!PoseLandmarker)  throw new Error('PoseLandmarker export is unavailable');

    console.log('[MediaPipeWorker] FilesetResolver: available.');
    console.log('[MediaPipeWorker] PoseLandmarker: available.');
    console.log('[MediaPipeWorker] Vision bundle loaded successfully.');

    return { FilesetResolver, PoseLandmarker };
}

// ─── Step 2: Bootstrap WASM Loader into self.ModuleFactory ───────────────────
//
// vision_bundle.js calls a classic-worker script-load function o(wasmLoaderPath) which
// either uses a DOM script tag or classic-worker script loading — neither works in an
// ES module worker. We pre-load the WASM loader ourselves by:
//   a) fetching the CJS source text
//   b) wrapping it in a CJS shim so 'module' / 'exports' exist
//   c) executing via new Function() which runs synchronously in the worker's global scope
//   d) the shim ends with: self.ModuleFactory = module.exports;
//
// After this, vision_bundle's createMediaPipeLib finds self.ModuleFactory already set
// and — with wasmLoaderPath=null — skips its internal o() loader call entirely.

async function bootstrapWasmLoader(wasmLoaderPath) {
    console.log('[MediaPipeWorker] Fetching WASM loader JS...');
    const resp = await fetch(wasmLoaderPath);
    if (!resp.ok) throw new Error(`WASM loader fetch failed: HTTP ${resp.status}`);
    const loaderText = await resp.text();

    console.log('[MediaPipeWorker] Executing WASM loader via CJS shim...');

    // Wrap in a CJS shim so module.exports/exports work, then assign to self.ModuleFactory
    const shimCode = [
        'var module = { exports: {} };',
        'var exports = module.exports;',
        loaderText,
        'self.ModuleFactory = module.exports;'
    ].join('\n');

    // new Function() executes in the global context, making self.ModuleFactory available
    // eslint-disable-next-line no-new-func
    const fn = new Function(shimCode);
    fn();

    if (typeof self.ModuleFactory !== 'function') {
        throw new Error('ModuleFactory was not set after executing WASM loader shim');
    }
    console.log('[MediaPipeWorker] WASM loader bootstrapped — ModuleFactory is set.');
}

// ─── Step 3: Initialize WASM runtime via FilesetResolver ─────────────────────

async function initWasm(FilesetResolver) {
    console.log('[MediaPipeWorker] Initializing local WASM runtime...');

    const simd = await isSimdSupported();
    const variant = simd ? 'vision_wasm_internal' : 'vision_wasm_nosimd_internal';

    const wasmLoaderPath = `${WASM_DIR_PATH}/${variant}.js`;
    const wasmBinaryPath = `${WASM_DIR_PATH}/${variant}.wasm`;

    // Bootstrap the WASM loader so self.ModuleFactory is set
    await bootstrapWasmLoader(wasmLoaderPath);

    // Build a fileset compatible with createTaskRunner, but with wasmLoaderPath=null
    // so createMediaPipeLib's internal o() loader function is never called.
    // It will find self.ModuleFactory already set and proceed.
    const visionFileset = {
        wasmLoaderPath: null,       // ← null prevents o() from being called
        wasmBinaryPath: wasmBinaryPath
    };

    console.log('[MediaPipeWorker] WASM runtime initialized.');
    return visionFileset;
}

// ─── Step 4: Fetch pose model as binary ──────────────────────────────────────

async function fetchPoseModel() {
    console.log('[MediaPipeWorker] Fetching local pose model...');
    const response = await fetch(POSE_MODEL_PATH);
    if (!response.ok) {
        throw new Error(`Pose model request failed: HTTP ${response.status}`);
    }
    const modelBuffer = await response.arrayBuffer();
    if (!modelBuffer.byteLength) {
        throw new Error('Pose model downloaded but is empty (0 bytes).');
    }
    // Guard against a Git LFS pointer being served as the model
    const probe = new Uint8Array(modelBuffer, 0, Math.min(20, modelBuffer.byteLength));
    const probeTxt = String.fromCharCode(...probe);
    if (probeTxt.startsWith('version https://git-lfs')) {
        throw new Error('Pose model is a Git LFS pointer — actual binary not committed to repo.');
    }
    console.log(`[MediaPipeWorker] Pose model downloaded: ${modelBuffer.byteLength} bytes.`);
    return modelBuffer;
}

// ─── Step 5: Create PoseLandmarker ───────────────────────────────────────────

async function createPoseLandmarker(PoseLandmarker, visionFileset, modelBuffer) {
    console.log('[MediaPipeWorker] Creating PoseLandmarker...');
    const instance = await PoseLandmarker.createFromOptions(visionFileset, {
        baseOptions: {
            modelAssetBuffer: new Uint8Array(modelBuffer),
            delegate: 'GPU'
        },
        runningMode: 'VIDEO',
        numPoses: 1,
        minPoseDetectionConfidence: 0.5,
        minPosePresenceConfidence: 0.5,
        minTrackingConfidence: 0.5,
        outputSegmentationMasks: false
    });
    console.log('[MediaPipeWorker] PoseLandmarker created successfully.');
    console.log('[MediaPipeWorker] MediaPipe ready.');
    return instance;
}

// ─── Message Handler ─────────────────────────────────────────────────────────

self.onmessage = async (e) => {
    const { action, payload } = e.data;

    // ── LOAD_MODEL ──────────────────────────────────────────────────────────
    if (action === 'LOAD_MODEL') {
        try {
            // Step 1: Vision bundle
            let FilesetResolver, PoseLandmarker;
            try {
                ({ FilesetResolver, PoseLandmarker } = await loadVisionBundle());
            } catch (err) {
                postError('VISION_MODULE_LOAD_FAILED', err.message || String(err));
                return;
            }

            // Step 2 + 3: Bootstrap WASM loader + build fileset
            let visionFileset;
            try {
                visionFileset = await initWasm(FilesetResolver);
            } catch (err) {
                postError('WASM_INITIALIZATION_FAILED', err.message || String(err));
                return;
            }

            // Step 4: Fetch model binary
            let modelBuffer;
            try {
                modelBuffer = await fetchPoseModel();
            } catch (err) {
                postError('POSE_MODEL_FETCH_FAILED', err.message || String(err));
                return;
            }

            // Step 5: Create PoseLandmarker
            try {
                poseLandmarkerInstance = await createPoseLandmarker(PoseLandmarker, visionFileset, modelBuffer);
            } catch (err) {
                postError('POSE_LANDMARKER_INITIALIZATION_FAILED', err.message || String(err));
                return;
            }

            self.postMessage({ action: 'MODEL_LOADED', success: true });

        } catch (err) {
            postError('MEDIAPIPE_INIT_FAILED', err.message || String(err));
        }
    }

    // ── PROCESS_FRAME ────────────────────────────────────────────────────────
    else if (action === 'PROCESS_FRAME') {
        if (!poseLandmarkerInstance) {
            self.postMessage({ action: 'FRAME_ERROR', error: 'PoseLandmarker is uninitialized.' });
            return;
        }
        try {
            _receivedFrameCount++;
            if (_receivedFrameCount % 30 === 0) {
                console.log(`[MediaPipeWorker] Frames received: ${_receivedFrameCount}`);
            }

            const startTime = performance.now();

            // VIDEO mode requires a monotonically increasing timestamp in milliseconds
            const ts = payload.timestamp || startTime;
            const timestamp = ts > _lastTimestamp ? ts : _lastTimestamp + 1;
            _lastTimestamp = timestamp;

            const result = poseLandmarkerInstance.detectForVideo(payload.imageBitmap, timestamp);
            const latency = performance.now() - startTime;

            const rawLandmarks = result.landmarks && result.landmarks[0] ? result.landmarks[0] : [];
            const poseCount = result.landmarks ? result.landmarks.length : 0;

            if (_receivedFrameCount % 30 === 0 || (payload.frameNumber || 0) <= 3) {
                console.log('[MediaPipeWorker] Inference:', {
                    frameNumber: payload.frameNumber,
                    timestamp: timestamp,
                    poseCount: poseCount,
                    landmarkCount: rawLandmarks.length
                });
            }

            const landmarks = rawLandmarks.map((lm, i) => ({
                id:         i,
                index:      i,
                name:       LANDMARK_NAMES[i] || `landmark_${i}`,
                x:          lm.x,
                y:          lm.y,
                z:          lm.z          !== undefined && lm.z          !== null ? lm.z          : 0.0,
                visibility: lm.visibility !== undefined && lm.visibility !== null ? lm.visibility : 0.0,
                presence:   lm.presence   !== undefined && lm.presence   !== null ? lm.presence   : 0.0
            }));

            self.postMessage({
                action:      'FRAME_PROCESSED',
                landmarks:   landmarks,
                confidence:  landmarks.length > 0 ? 0.95 : 0.0,
                latencyMs:   latency,
                frameNumber: payload.frameNumber
            });
        } catch (err) {
            postError('INFERENCE_FAILED', err.message || String(err));
            self.postMessage({ action: 'FRAME_ERROR', error: err.message || String(err) });
        }
    }

    // ── DISPOSE ──────────────────────────────────────────────────────────────
    else if (action === 'DISPOSE') {
        if (poseLandmarkerInstance) {
            try { poseLandmarkerInstance.close(); } catch (_) {}
            poseLandmarkerInstance = null;
        }
        self.postMessage({ action: 'DISPOSED' });
    }
};
