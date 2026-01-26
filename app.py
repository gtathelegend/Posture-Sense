from flask import Flask, render_template, Response, jsonify, request, flash, redirect, url_for, session, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
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
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))  # Required for flash messages and sessions

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posture_sense.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# ---------------------------------------------Database Models---------------------------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sessions = db.relationship('PoseSession', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class PoseSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pose_label = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    duration = db.Column(db.Float, default=0.0)  # Duration in seconds
    accuracy = db.Column(db.Float, default=0.0)  # Accuracy percentage
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

# -------------------------------------------------Authentication Routes---------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's pose sessions
    sessions = PoseSession.query.filter_by(user_id=current_user.id).order_by(PoseSession.timestamp.desc()).all()
    
    # Calculate statistics
    total_sessions = len(sessions)
    total_duration = sum(s.duration for s in sessions)
    avg_accuracy = sum(s.accuracy for s in sessions) / total_sessions if total_sessions > 0 else 0
    
    # Get pose distribution
    pose_counts = {}
    for session in sessions:
        pose_counts[session.pose_label] = pose_counts.get(session.pose_label, 0) + 1
    
    return render_template('dashboard.html', 
                         sessions=sessions, 
                         total_sessions=total_sessions,
                         total_duration=total_duration,
                         avg_accuracy=avg_accuracy,
                         pose_counts=pose_counts)

@app.route('/api/dashboard_stats')
@login_required
def dashboard_stats():
    # Get user's pose sessions
    sessions = PoseSession.query.filter_by(user_id=current_user.id).order_by(PoseSession.timestamp.desc()).all()
    
    # Calculate statistics
    total_sessions = len(sessions)
    total_duration = sum(s.duration for s in sessions)
    avg_accuracy = sum(s.accuracy for s in sessions) / total_sessions if total_sessions > 0 else 0
    
    # Get pose distribution
    pose_counts = {}
    for session in sessions:
        pose_counts[session.pose_label] = pose_counts.get(session.pose_label, 0) + 1
    
    # Format recent sessions
    recent_sessions = []
    for session in sessions[:20]:
        recent_sessions.append({
            'timestamp': session.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'pose_label': session.pose_label,
            'duration': round(session.duration, 1),
            'accuracy': round(session.accuracy, 1)
        })
    
    return jsonify({
        'total_sessions': total_sessions,
        'total_duration': total_duration,
        'avg_accuracy': round(avg_accuracy, 1),
        'pose_counts': pose_counts,
        'recent_sessions': recent_sessions
    })

# -------------------------------------------------End Authentication Routes-----------------------------------------------------

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

@app.route('/sitemap.xml')
def sitemap():
    return send_file('sitemap.xml', mimetype='text/xml')

@app.route('/robots.txt')
def robots():
    return send_file('robots.txt', mimetype='text/plain')

@app.route('/pose_detection')
@login_required
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

@app.route('/save_pose_session', methods=['POST'])
@login_required
def save_pose_session():
    data = request.get_json()
    pose_label = data.get('pose_label')
    duration = data.get('duration', 0.0)
    accuracy = data.get('accuracy', 0.0)
    
    if pose_label and pose_label != 'Unknown' and pose_label != 'Scanning ...':
        session = PoseSession(
            user_id=current_user.id,
            pose_label=pose_label,
            duration=duration,
            accuracy=accuracy
        )
        db.session.add(session)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Pose session saved'})
    
    return jsonify({'status': 'error', 'message': 'Invalid pose data'})

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
    # Create database tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
