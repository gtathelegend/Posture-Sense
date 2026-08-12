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
    
    # Ignore any client-provided user_id and strictly enforce authenticated current_user.id
    user_id = current_user.id

    pose_label = data.get('pose_label')
    duration = data.get('duration', 0.0)
    accuracy = data.get('accuracy') if 'accuracy' in data else data.get('overall_score', 0.0)
    reps = data.get('reps', 0)
    symmetry_score = data.get('symmetry_score')
    balance_score = data.get('balance_score')
    stability_score = data.get('stability_score')
    rom_score = data.get('rom_score')
    hold_time = data.get('hold_time', 0.0)
    tracking_quality = data.get('tracking_quality')
    failed_rules = data.get('failed_rules', [])

    session, error = SessionService.save_session(
        user_id=user_id,
        pose_label=pose_label,
        duration=duration,
        accuracy=accuracy,
        reps=reps,
        symmetry_score=symmetry_score,
        balance_score=balance_score,
        stability_score=stability_score,
        rom_score=rom_score,
        hold_time=hold_time,
        tracking_quality=tracking_quality,
        failed_rules=failed_rules
    )
    if session:
        return jsonify({'status': 'success', 'message': 'Pose session saved', 'session_id': session.id})
    return jsonify({'status': 'error', 'message': error or 'Invalid pose data'}), 400




@api_bp.route('/video_feed')
def video_feed():
    cv_utils.camera_active = True
    return Response(cv_utils.gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@api_bp.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'PostureSense v2 Backend',
        'pipeline_status': 'operational',
        'version': '2.0.0'
    })


@api_bp.route('/version')
def version():
    import os
    git_sha = os.getenv('RENDER_GIT_COMMIT', 'cefc6ea0ea793e2e4fe94180f962de662c84357b')
    env = os.getenv('FLASK_ENV', 'production')
    return jsonify({
        'version': '2.0.0',
        'application_version': '2.0.0',
        'git_commit': git_sha,
        'environment': env,
        'engine_runtime_version': '2.0.0',
        'pipeline_architecture': 'v2 Browser Native Pipeline',
        'status': 'operational'
    })




# ── Analytics Endpoints (Scoped to current_user for strict user isolation) ───

@api_bp.route('/analytics/summary', methods=['GET'])
@login_required
def get_analytics_summary():
    from backend.app.repositories.analytics_repository import AnalyticsRepository
    summary = AnalyticsRepository.get_user_analytics_summary(current_user.id)
    return jsonify(summary)


@api_bp.route('/analytics/progress', methods=['GET'])
@login_required
def get_analytics_progress():
    from backend.app.repositories.analytics_repository import AnalyticsRepository
    progress = AnalyticsRepository.get_user_progress(current_user.id)
    return jsonify(progress)


@api_bp.route('/analytics/exercises', methods=['GET'])
@login_required
def get_analytics_exercises():
    from backend.app.repositories.analytics_repository import AnalyticsRepository
    exercises = AnalyticsRepository.get_exercise_history(current_user.id)
    return jsonify(exercises)


@api_bp.route('/analytics/trends', methods=['GET'])
@login_required
def get_analytics_trends():
    from backend.app.repositories.analytics_repository import AnalyticsRepository
    trends = AnalyticsRepository.get_user_trends(current_user.id)
    return jsonify(trends)


@api_bp.route('/analytics/records', methods=['GET'])
@login_required
def get_analytics_records():
    from backend.app.repositories.analytics_repository import AnalyticsRepository
    records = AnalyticsRepository.get_personal_records(current_user.id)
    return jsonify({'user_id': str(current_user.id), 'records': records})


# ── Reports & Export Endpoints (Scoped to current_user for strict user isolation) ──

@api_bp.route('/reports/session/<session_id>', methods=['GET'])
@login_required
def get_session_report(session_id):
    from backend.app.services.report_service import ReportService
    rep = ReportService.generate_session_report(current_user.id, session_id)
    return jsonify(rep)


@api_bp.route('/reports/exercise/<exercise_id>', methods=['GET'])
@login_required
def get_exercise_report(exercise_id):
    from backend.app.services.report_service import ReportService
    rep = ReportService.generate_exercise_report(current_user.id, exercise_id)
    return jsonify(rep)


@api_bp.route('/reports/progress', methods=['GET'])
@login_required
def get_progress_report():
    from backend.app.services.report_service import ReportService
    rep = ReportService.generate_progress_report(current_user.id)
    return jsonify(rep)


@api_bp.route('/reports/comprehensive', methods=['GET'])
@login_required
def get_comprehensive_report():
    from backend.app.services.report_service import ReportService
    rep = ReportService.generate_comprehensive_report(current_user.id)
    return jsonify(rep)


@api_bp.route('/reports/session/<session_id>/pdf', methods=['GET'])
@login_required
def get_session_report_pdf(session_id):
    from backend.app.services.report_service import ReportService
    export_res = ReportService.export_session_pdf(current_user.id, session_id)
    return Response(export_res['content'], mimetype='text/html', headers={
        'Content-Disposition': f'inline; filename="{export_res["filename"]}"'
    })


@api_bp.route('/reports/session/<session_id>/json', methods=['GET'])
@login_required
def get_session_report_json(session_id):
    from backend.app.services.report_service import ReportService
    export_res = ReportService.export_session_json(current_user.id, session_id)
    return Response(export_res['content'], mimetype='application/json', headers={
        'Content-Disposition': f'attachment; filename="{export_res["filename"]}"'
    })


@api_bp.route('/reports/progress.csv', methods=['GET'])
@login_required
def get_progress_csv():
    from backend.app.services.report_service import ReportService
    export_res = ReportService.export_progress_csv(current_user.id)
    return Response(export_res['content'], mimetype='text/csv', headers={
        'Content-Disposition': f'attachment; filename="{export_res["filename"]}"'
    })


