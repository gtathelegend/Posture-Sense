python
def calculate_joint_angle(point_a, point_b, point_c):
    """Calculate angle at point_b formed by points a-b-c"""
    ba = point_a - point_b
    bc = point_c - point_b
    
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1, 1))
    
    return np.degrees(angle)

# Key angles for exercise analysis
ANALYSIS_ANGLES = {
    'squat': ['hip_knee_ankle', 'torso_vertical'],
    'pushup': ['shoulder_elbow_wrist', 'torso_vertical'],
    'lunge': ['front_knee_angle', 'back_knee_angle', 'torso_vertical']
}


def detect_exercise_phase(landmarks, exercise_type):
    """Identify current phase of exercise repetition"""
    if exercise_type == 'squat':
        hip_height = landmarks[23].y + landmarks[24].y / 2  # Average hip landmarks
        knee_angles = calculate_knee_angles(landmarks)
        
        # Phase logic based on height and angles
        if hip_height > threshold_high:
            return 'start'
        elif hip_height < threshold_low and knee_angles[0] < 90:
            return 'bottom'
        else:
            return 'transition'
