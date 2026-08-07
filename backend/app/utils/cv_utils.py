import math
import cv2
import mediapipe as mp

# Initializing mediapipe pose class.
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, model_complexity=1)
mp_drawing = mp.solutions.drawing_utils

# Global state variables for camera and posture status
pose_status = "Scanning"
current_status = "Unknown"
last_status = "Unknown"
camera_active = False
camera = None


def find_working_camera(max_index=4):
    for idx in range(max_index):
        cap = cv2.VideoCapture(idx)
        if cap is None or not cap.isOpened():
            if cap:
                cap.release()
            continue
        ret, _ = cap.read()
        if ret:
            cap.release()
            return idx
        cap.release()
    return None


def open_camera(index=None):
    try:
        if index is None:
            idx = find_working_camera()
            if idx is None:
                return None
        else:
            idx = index
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        try:
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        except Exception:
            pass
        if not cap.isOpened():
            cap.release()
            return None
        return cap
    except Exception as e:
        print(f"open_camera error: {e}")
        return None


def calculateAngle(landmark1, landmark2, landmark3):
    x1, y1, _ = landmark1
    x2, y2, _ = landmark2
    x3, y3, _ = landmark3
    angle = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2))
    if angle < 0:
        angle += 360
    return angle


def detectPose(image, pose_instance, display=True):
    output_image = image.copy()
    imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose_instance.process(imageRGB)
    height, width, _ = image.shape
    landmarks = []
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(image=output_image, landmark_list=results.pose_landmarks,
                                  connections=mp_pose.POSE_CONNECTIONS)
        for landmark in results.pose_landmarks.landmark:
            landmarks.append((int(landmark.x * width), int(landmark.y * height), (landmark.z * width)))
    return output_image, landmarks


def classifyPose(landmarks, output_image, display=False):
    global pose_status
    label = 'Scanning ...'
    color = (0, 0, 255)

    left_elbow_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value],
                                    landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value],
                                    landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value])
    right_elbow_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
                                     landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value],
                                     landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value])
    left_shoulder_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value],
                                        landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value],
                                        landmarks[mp_pose.PoseLandmark.LEFT_HIP.value])
    right_shoulder_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value],
                                         landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
                                         landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value])
    left_knee_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_HIP.value],
                                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value],
                                    landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value])
    right_knee_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value],
                                     landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value],
                                     landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value])
    left_hip_knee_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_HIP.value],
                                        landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value],
                                        landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value])
    right_hip_knee_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value],
                                         landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value],
                                         landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value])
    left_hip_shoulder_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_HIP.value],
                                            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value],
                                            landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value])
    right_hip_shoulder_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value],
                                             landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
                                             landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value])

    if (left_elbow_angle > 165 and left_elbow_angle < 195 and
            right_elbow_angle > 165 and right_elbow_angle < 195 and
            left_shoulder_angle > 80 and left_shoulder_angle < 110 and
            right_shoulder_angle > 80 and right_shoulder_angle < 110):
        if (left_knee_angle > 165 and left_knee_angle < 195 or
                right_knee_angle > 165 and right_knee_angle < 195):
            if (left_knee_angle > 90 and left_knee_angle < 120 or
                    right_knee_angle > 90 and right_knee_angle < 120):
                label = 'Warrior II Pose'

    if (left_elbow_angle > 165 and left_elbow_angle < 195 and
            right_elbow_angle > 165 and right_elbow_angle < 195 and
            left_shoulder_angle > 80 and left_shoulder_angle < 110 and
            right_shoulder_angle > 80 and right_shoulder_angle < 110 and
            left_knee_angle > 160 and left_knee_angle < 195 and
            right_knee_angle > 160 and right_knee_angle < 195):
        label = 'T Pose'

    if (left_knee_angle > 165 and left_knee_angle < 195 or
            right_knee_angle > 165 and right_knee_angle < 195):
        if (left_knee_angle > 315 and left_knee_angle < 335 or
                right_knee_angle > 25 and right_knee_angle < 45):
            label = 'Tree Pose'

    if (left_hip_knee_angle > 160 and left_hip_knee_angle < 200 and
            right_hip_knee_angle > 160 and right_hip_knee_angle < 200 and
            ((left_hip_shoulder_angle > 0 and left_hip_shoulder_angle < 40) or
             (right_hip_shoulder_angle > 320 and right_hip_shoulder_angle < 360))):
        label = 'Cobra Pose'

    if label != 'Unknown Pose':
        color = (0, 255, 0)

    cv2.putText(output_image, label, (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, color, 2)

    if label != 'Unknown Pose':
        pose_status = label
    else:
        pose_status = "Unknown"
    return output_image, label, pose_status


def gen_frames():
    global camera_active, current_status, last_status, camera
    camera = open_camera()
    if camera is None:
        print("Error: Could not open camera (no working index).")
        yield b''
        return

    camera_active = True
    failure_count = 0

    try:
        while camera_active:
            success, frame = camera.read()
            if not success or frame is None:
                failure_count += 1
                if failure_count >= 3:
                    camera.release()
                    camera = open_camera()
                    if camera is None:
                        import time as _t; _t.sleep(1)
                        failure_count = 0
                        continue
                    else:
                        failure_count = 0
                        continue
                else:
                    import time as _t; _t.sleep(0.05)
                    continue
            failure_count = 0

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            target_h = 640
            scale = target_h / float(h)
            new_w = int(w * scale)
            frame = cv2.resize(frame, (new_w, target_h))

            output_frame, landmarks = detectPose(frame, pose, display=False)
            if landmarks:
                label_img, label, ps = classifyPose(landmarks, output_frame, display=False)
                if ps != current_status:
                    last_status = current_status
                    current_status = ps

            ret, buffer = cv2.imencode('.jpg', output_frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    except GeneratorExit:
        print("gen_frames: client disconnected")
    except Exception as e:
        print(f"Error in gen_frames main loop: {e}")
    finally:
        try:
            if camera is not None:
                camera.release()
                camera = None
        except Exception:
            pass
        camera_active = False
