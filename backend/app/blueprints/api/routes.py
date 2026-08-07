from flask import Blueprint, Response, jsonify, request
from flask_login import login_required, current_user
import backend.app.utils.cv_utils as cv_utils
from backend.app.services.session_service import SessionService

api_bp = Blueprint('api', __name__)


@api_bp.route('/status')
def pose_status_updates():
    def generate():
        while True:
            yield f"data: {cv_utils.pose_status}\n\n"
    return Response(generate(), content_type='text/event-stream')


@api_bp.route('/get_status')
def get_status():
    return jsonify({
        'current_status': cv_utils.current_status,
        'last_status': cv_utils.last_status
    })


@api_bp.route('/stop_camera')
def stop_camera():
    cv_utils.camera_active = False
    if cv_utils.camera is not None:
        cv_utils.camera.release()
        cv_utils.camera = None
    return jsonify({'status': 'success'})


@api_bp.route('/save_pose_session', methods=['POST'])
@login_required
def save_pose_session():
    data = request.get_json() or {}
    pose_label = data.get('pose_label')
    duration = data.get('duration', 0.0)
    accuracy = data.get('accuracy', 0.0)

    session, error = SessionService.save_session(current_user.id, pose_label, duration, accuracy)
    if session:
        return jsonify({'status': 'success', 'message': 'Pose session saved'})
    return jsonify({'status': 'error', 'message': error or 'Invalid pose data'})


@api_bp.route('/video_feed')
def video_feed():
    cv_utils.camera_active = True
    return Response(cv_utils.gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@api_bp.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'PostureSense v2 Backend'})


@api_bp.route('/version')
def version():
    return jsonify({'version': '2.0.0', 'phase': 'Architecture Migration Phase 1'})
