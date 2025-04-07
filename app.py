from flask import Flask, render_template, Response, jsonify, request, flash, redirect, url_for
import cv2
from time import time
import mediapipe as mp
import math
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for flash messages

# ---------------------------------------------Pose Detection and Classification---------------------------------------------
# Initializing mediapipe pose class.
mp_pose = mp.solutions.pose

# Setting up the Pose function.
pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.3, model_complexity=2)

# Initializing mediapipe drawing class, useful for annotation.
mp_drawing = mp.solutions.drawing_utils

# Initialize a variable to store the status of the pose.
pose_status = "Scanning"

# Global variables for posture status
current_status = "Unknown"
last_status = "Unknown"
camera_active = False
camera = None

def init_camera():
    global camera
    if camera is None:
        # Try to find an available camera
        available_cameras = []
        for i in range(4):  # Try up to 4 camera indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(i)
                cap.release()
        
        if not available_cameras:
            raise Exception("No camera devices found. Please make sure a camera is connected and accessible.")
        
        # Use the first available camera
        camera = cv2.VideoCapture(available_cameras[0])
        if not camera.isOpened():
            raise Exception(f"Failed to open camera at index {available_cameras[0]}")
        
        # Set camera properties for better performance
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
    
    return camera

def gen_frames():
    camera = init_camera()
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Flip the frame horizontally for a mirror effect
            frame = cv2.flip(frame, 1)
            
            # Resize frame for better performance
            frame = cv2.resize(frame, (640, 480))
            
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

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
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        try:
            # Email configuration
            sender_email = os.getenv('EMAIL_USER')
            sender_password = os.getenv('EMAIL_PASSWORD')
            receiver_email = os.getenv('ADMIN_EMAIL')
            
            # Create message for admin
            admin_msg = MIMEMultipart()
            admin_msg['From'] = sender_email
            admin_msg['To'] = receiver_email
            admin_msg['Subject'] = f"Posture Sense New Contact Form Submission from {name}"
            
            # Admin email body
            admin_body = f"""
            New contact form submission:
            
            Name: {name}
            Email: {email}
            Message: {message}
            """
            
            admin_msg.attach(MIMEText(admin_body, 'plain'))
            
            # Create confirmation message for sender
            sender_msg = MIMEMultipart()
            sender_msg['From'] = sender_email
            sender_msg['To'] = email
            sender_msg['Subject'] = "Thank you for contacting Posture Sense"
            
            # Sender confirmation email body
            sender_body = f"""
            Dear {name},

            Thank you for contacting Posture Sense. We have received your message and will get back to you as soon as possible.

            Here's a copy of your message:
            {message}

            Best regards,
            Posture Sense Team
            """
            
            sender_msg.attach(MIMEText(sender_body, 'plain'))
            
            # Send emails
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                
                # Send to admin
                server.send_message(admin_msg)
                
                # Send confirmation to sender
                server.send_message(sender_msg)
            
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")  # Add this line for debugging
            flash('An error occurred while sending your message. Please try again later.', 'error')
            return redirect(url_for('index'))
    
    return render_template('index.html')

@app.route('/pricing')
def join_now():
    pass

# Route to process form submission
@app.route('/submit', methods=['POST'])
def submit():
    # Process form data here
    return 'Form submitted successfully!'

@app.route('/get_status')
def get_status():
    global current_status, last_status
    return jsonify({
        'current_status': current_status,
        'last_status': last_status
    })

@app.route('/start_camera')
def start_camera():
    try:
        camera = init_camera()
        if camera.isOpened():
            return jsonify({
                'status': 'success', 
                'message': 'Camera started successfully',
                'camera_index': camera.get(cv2.CAP_PROP_BACKEND)
            })
        else:
            return jsonify({
                'status': 'error', 
                'message': 'Failed to start camera. Please check if a camera is connected and accessible.'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500

@app.route('/stop_camera')
def stop_camera():
    try:
        global camera
        if camera is not None:
            camera.release()
            camera = None
        return jsonify({
            'status': 'success', 
            'message': 'Camera stopped successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame',
                   headers={
                       'Cache-Control': 'no-cache, no-store, must-revalidate',
                       'Pragma': 'no-cache',
                       'Expires': '0'
                   })

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

<<<<<<< HEAD
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

=======
if __name__ == '__main__':
    app.run(debug=True)
>>>>>>> parent of c4bc870 (yoga-pose page add)
