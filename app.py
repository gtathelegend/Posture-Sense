from flask import Flask, render_template, Response, jsonify, request, flash, redirect, url_for
from flask_cors import CORS
import cv2
from time import time
import mediapipe as mp
import math
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
# import pyttsx3

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)  # Required for flash messages

# ---------------------------------------------Pose Detection and Classification---------------------------------------------
# Initializing mediapipe pose class.
mp_pose = mp.solutions.pose

# Setting up the Pose function.
# from this:
# pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.3, model_complexity=2)

# to this (better for video):
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, model_complexity=1)


# Initializing mediapipe drawing class, useful for annotation.
mp_drawing = mp.solutions.drawing_utils

# Initialize a variable to store the status of the pose.
pose_status = "Scanning"

# Global variables for posture status
current_status = "Unknown"
last_status = "Unknown"
camera_active = False
camera = None

# Initialize text-to-speech engine
# tts_engine = pyttsx3.init()
# # tts_engine.setProperty('rate', 150)  # Speed of speech
# # tts_engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
# def speak_pose(pose_label):
#     try:
#         tts_engine.say(f"You are in {pose_label}")
#         tts_engine.runAndWait()
#     except Exception as e:
#         print(f"Voice feedback error: {str(e)}")


def find_working_camera(max_index=4):
    """Try camera indexes 0..max_index-1 and return first that works (or None)."""
    for idx in range(max_index):
        cap = cv2.VideoCapture(idx)
        if cap is None or not cap.isOpened():
            if cap:
                cap.release()
            continue
        # try one read
        ret, _ = cap.read()
        if ret:
            cap.release()
            return idx
        cap.release()
    return None

def open_camera(index=None):
    """Open camera and tune small params. Returns VideoCapture or None."""
    try:
        if index is None:
            idx = find_working_camera()
            if idx is None:
                return None
        else:
            idx = index
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)  # keep CAP_DSHOW on windows/WSL if needed
        # Optional: reduce buffer and set resolution
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

def gen_frames():
    global camera_active, current_status, last_status, camera
    camera = open_camera()  # open once
    if camera is None:
        print("Error: Could not open camera (no working index).")
        yield b''  # generator must yield something (client will see nothing)
        return

    camera_active = True
    failure_count = 0
    max_failures = 10

    try:
        while camera_active:
            success, frame = camera.read()
            if not success or frame is None:
                failure_count += 1
                print(f"gen_frames: failed to grab frame ({failure_count})")
                # attempt to reopen camera after some consecutive failures
                if failure_count >= 3:
                    # try reopen
                    camera.release()
                    camera = open_camera()
                    if camera is None:
                        print("gen_frames: unable to reopen camera, sleeping and retrying...")
                        import time as _t; _t.sleep(1)
                        failure_count = 0
                        continue
                    else:
                        print("gen_frames: camera reopened")
                        failure_count = 0
                        continue
                else:
                    # small delay then continue
                    import time as _t; _t.sleep(0.05)
                    continue
            failure_count = 0  # reset on success

            # flip & resize safely
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            target_h = 640
            scale = target_h / float(h)
            new_w = int(w * scale)
            frame = cv2.resize(frame, (new_w, target_h))

            # Detect pose and classify
            output_frame, landmarks = detectPose(frame, pose, display=False)
            if landmarks:
                label_img, label, ps = classifyPose(landmarks, output_frame, display=False)
                # Update last/current statuses
                if ps != current_status:
                    last_status = current_status
                    current_status = ps
                # optional: print debug
                # print(f"Current Status: {current_status}, Last Status: {last_status}")

            # encode & stream
            ret, buffer = cv2.imencode('.jpg', output_frame)
            if not ret:
                print("gen_frames: encode failed")
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        # end while
    except GeneratorExit:
        # client disconnected
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
        print("gen_frames: cleaned up camera")

# mp_pose = mp.solutions.pose

# # Setting up the Pose function.
# pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.3, model_complexity=2)

# # Initializing mediapipe drawing class, useful for annotation.
# mp_drawing = mp.solutions.drawing_utils

# # Initialize a variable to store the status of the pose.
# pose_status = "Scanning"

# # Global variables for posture status
# current_status = "Unknown"
# last_status = "Unknown"
# camera_active = False
# camera = None

# def gen_frames():
#     global camera_active, current_status, last_status
#     try:
#         video = cv2.VideoCapture("http://172.16.207.161:8080/video")
#         if not video.isOpened():
#             print("Error: Could not open camera")
#             return
            
#         while camera_active:
#             success, frame = video.read()  # read the camera frame
#             if not success:
#                 print("Failed to grab frame")
#                 break
#             else:
#                 frame = cv2.flip(frame, 1)  # flip the frame horizontally
#                 frame_height, frame_width, _ = frame.shape
#                 frame = cv2.resize(frame, (int(frame_width * (640 / frame_height)), 640))
                
#                 # Detect pose and classify
#                 frame, landmarks = detectPose(frame, pose, display=False)
#                 if landmarks:
#                     _, _, pose_status = classifyPose(landmarks, frame, display=False)
#                     # Update last status before changing current status
#                     if pose_status != current_status:
#                         last_status = current_status
#                         current_status = pose_status
#                     print(f"Current Status: {current_status}, Last Status: {last_status}")  # Debug print

#                 # Encode frame to JPEG
#                 ret, buffer = cv2.imencode('.jpg', frame)
#                 frame = buffer.tobytes()
#                 yield (b'--frame\r\n'
#                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                
#         # Clean up
#         video.release()
#     except Exception as e:
#         print(f"Error in gen_frames: {str(e)}")
#         if 'video' in locals():
#             video.release()
#         camera_active = False

def detectPose(image, pose, display=True):

    # Create a copy of the input image.
    output_image = image.copy()

    # Convert the image from BGR into RGB format.
    imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Perform the Pose Detection.
    results = pose.process(imageRGB)

    # Retrieve the height and width of the input image.
    height, width, _ = image.shape

    # Initialize a list to store the detected landmarks.
    landmarks = []

    # Check if any landmarks are detected.
    if results.pose_landmarks:

        # Draw Pose landmarks on the output image.
        mp_drawing.draw_landmarks(image=output_image, landmark_list=results.pose_landmarks,
                                  connections=mp_pose.POSE_CONNECTIONS)

        # Iterate over the detected landmarks.
        for landmark in results.pose_landmarks.landmark:
            # Append the landmark into the list.
            landmarks.append((int(landmark.x * width), int(landmark.y * height),
                              (landmark.z * width)))

    # Otherwise

    # Return the output image and the found landmarks.
    return output_image, landmarks

def calculateAngle(landmark1, landmark2, landmark3):
    '''
    This function calculates angle between three different landmarks.
    Args:
        landmark1: The first landmark containing the x,y and z coordinates.
        landmark2: The second landmark containing the x,y and z coordinates.
        landmark3: The third landmark containing the x,y and z coordinates.
    Returns:
        angle: The calculated angle between the three landmarks.

    '''

    # Get the required landmarks coordinates.
    x1, y1, _ = landmark1
    x2, y2, _ = landmark2
    x3, y3, _ = landmark3

    # Calculate the angle between the three points
    angle = math.degrees(math.atan2(y3 - y2, x3 - x2) - math.atan2(y1 - y2, x1 - x2))

    # Check if the angle is less than zero.
    if angle < 0:
        # Add 360 to the found angle.
        angle += 360

    # Return the calculated angle.
    return angle

def classifyPose(landmarks, output_image, display=False):
    '''
    This function classifies yoga poses depending upon the angles of various body joints.
    Args:
        landmarks: A list of detected landmarks of the person whose pose needs to be classified.
        output_image: A image of the person with the detected pose landmarks drawn.
        display: A boolean value that is if set to true the function displays the resultant image with the pose label 
        written on it and returns nothing.
    Returns:
        output_image: The image with the detected pose landmarks drawn and pose label written.
        label: The classified pose label of the person in the output_image.

    '''

    # Initialize the label of the pose. It is not known at this stage.
    label = 'Scanning ...'

    # Specify the color (Red) with which the label will be written on the image.
    color = (0, 0, 255)

    # Calculate the required angles.

    # Angle calculation code for other poses...

    # Get the angle between the left shoulder, elbow, and wrist points.
    left_elbow_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value],
                                    landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value],
                                    landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value])

    # Get the angle between the right shoulder, elbow, and wrist points.
    right_elbow_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
                                    landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value],
                                    landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value])

    # Get the angle between the left elbow, shoulder, and hip points.
    left_shoulder_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value],
                                        landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value],
                                        landmarks[mp_pose.PoseLandmark.LEFT_HIP.value])

    # Get the angle between the right hip, shoulder, and elbow points.
    right_shoulder_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value],
                                        landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
                                        landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value])

    # Get the angle between the left hip, knee, and ankle points.
    left_knee_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_HIP.value],
                                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value],
                                    landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value])

    # Get the angle between the right hip, knee, and ankle points.
    right_knee_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value],
                                    landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value],
                                    landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value])

    # Calculate the required angles for Cobra Pose.
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


    # Angle calculation code for other poses...

    # Check if it is the Warrior II pose or the T pose.
    # As for both of them, both arms should be straight and shoulders should be at the specific angle.

    # Check for Warrior II Pose
    if (left_elbow_angle > 165 and left_elbow_angle < 195 and
            right_elbow_angle > 165 and right_elbow_angle < 195 and
            left_shoulder_angle > 80 and left_shoulder_angle < 110 and
            right_shoulder_angle > 80 and right_shoulder_angle < 110):
        if (left_knee_angle > 165 and left_knee_angle < 195 or
                right_knee_angle > 165 and right_knee_angle < 195):
            if (left_knee_angle > 90 and left_knee_angle < 120 or
                    right_knee_angle > 90 and right_knee_angle < 120):
                label = 'Warrior II Pose'

    # Check for T Pose
    if (left_elbow_angle > 165 and left_elbow_angle < 195 and
            right_elbow_angle > 165 and right_elbow_angle < 195 and
            left_shoulder_angle > 80 and left_shoulder_angle < 110 and
            right_shoulder_angle > 80 and right_shoulder_angle < 110 and
            left_knee_angle > 160 and left_knee_angle < 195 and
            right_knee_angle > 160 and right_knee_angle < 195):
        label = 'T Pose'

    # Check for Tree Pose
    if (left_knee_angle > 165 and left_knee_angle < 195 or
            right_knee_angle > 165 and right_knee_angle < 195):
        if (left_knee_angle > 315 and left_knee_angle < 335 or
                right_knee_angle > 25 and right_knee_angle < 45):
            label = 'Tree Pose'

    # Check for Cobra Pose
    if (left_hip_knee_angle > 160 and left_hip_knee_angle < 200 and
            right_hip_knee_angle > 160 and right_hip_knee_angle < 200 and
            ((left_hip_shoulder_angle > 0 and left_hip_shoulder_angle < 40) or
             (right_hip_shoulder_angle > 320 and right_hip_shoulder_angle < 360))):
        label = 'Cobra Pose'

    # Check if the pose is classified successfully
    if label != 'Unknown Pose':
        # Update the color (to green) with which the label will be written on the image.
        color = (0, 255, 0)

    # Write the label on the output image.
    cv2.putText(output_image, label, (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, color, 2)

     # Return the output image and the classified label.
    global pose_status
    if label != 'Unknown Pose':
        pose_status = label
        # speak_pose(label) 
    else:
        pose_status = "Unknown"
    return output_image, label, pose_status
# -------------------------------------------------End Pose Detection and Classification---------------------------------------------

# -------------------------------------------------Update Status on HTML Page---------------------------------------------------------
# Add a route to send pose status updates as server-sent events
@app.route('/status')
def pose_status_updates():
    def generate():
        while True:
            # Send the current pose status as a server-sent event
            yield f"data: {pose_status}\n\n"
    return Response(generate(), content_type='text/event-stream')
# -------------------------------------------------End Update Status on HTML Page-----------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pose_detection')
def pose_detection():
    global current_status, last_status
    # Initialize status if not set
    if not current_status:
        current_status = 'Unknown'
    if not last_status:
        last_status = 'Unknown'
    return render_template('app.html', pose_status=current_status, last_status=last_status)

@app.route('/about')
def about():
    return render_template('#about')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Handle contact form submission
        
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            message = request.form.get('message')
        
        try:
            # Email configuration
            sender_email = os.getenv('EMAIL_USER')
            sender_password = os.getenv('EMAIL_PASSWORD')
            receiver_email = os.getenv('ADMIN_EMAIL')
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = f"New Message from {name}"
            
            # Email body
            body = f"""
            New Message from {name}:

            Email: {email}
            Message: {message}

            """
            

            
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            
            

            
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = email
            msg['Subject'] = f"Thank you for contacting {name}"
            
            # Email body
            body = f"""
            Thank you for contacting us {name} !
            We will contact you shortly.
            Thanks,
            Team Posture Sense

            """
            

            
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            return jsonify({'status': 'success', 'message': 'Thank you for contacting us!'})
        

        except Exception as e:
            print(f"Error sending contact email: {str(e)}")
            return jsonify({'status': 'error', 'message': 'An error occurred while processing your contact form. Please try again later.'}), 500
            # flash('Thank you for your message! We will get back to you soon.', 'success')
            # return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/yoga-poses')
def yoga_poses():
    return render_template('yoga-poses.html')

@app.route('/pricing')
def join_now():
    pass

# Route to process form submission
@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        # Handle contact form submission
        
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            message = request.form.get('message')
        
        try:
            # Email configuration
            sender_email = os.getenv('EMAIL_USER')
            sender_password = os.getenv('EMAIL_PASSWORD')
            receiver_email = os.getenv('ADMIN_EMAIL')
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = f"New Message from {name}"
            
            # Email body
            body = f"""
            New Message from {name}:

            Email: {email}
            Message: {message}

            """
            

            
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            return jsonify({'status': 'success', 'message': 'Thank you for contacting us!'})
            
        except Exception as e:
            print(f"Error sending contact email: {str(e)}")
            return jsonify({'status': 'error', 'message': 'An error occurred while processing your contact form. Please try again later.'}), 500
            # flash('Thank you for your message! We will get back to you soon.', 'success')
            # return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/get_status')
def get_status():
    global current_status, last_status
    return jsonify({
        'current_status': current_status,
        'last_status': last_status
    })

@app.route('/stop_camera')
def stop_camera():
    global camera, camera_active
    camera_active = False
    if camera is not None:
        camera.release()
        camera = None
    return jsonify({'status': 'success'})

@app.route('/video_feed')
def video_feed():
    global camera_active
    camera_active = True
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    if request.method == 'POST':
        email = request.form.get('email')
        
        try:
            # Email configuration
            sender_email = os.getenv('EMAIL_USER')
            sender_password = os.getenv('EMAIL_PASSWORD')
            receiver_email = os.getenv('ADMIN_EMAIL')
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = "New Newsletter Subscription"
            
            # Email body
            body = f"""
            New newsletter subscription:
            
            Email: {email}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            return jsonify({'status': 'success', 'message': 'Thank you for subscribing to our newsletter!'})
            
        except Exception as e:
            print(f"Error sending subscription email: {str(e)}")
            return jsonify({'status': 'error', 'message': 'An error occurred while processing your subscription. Please try again later.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
