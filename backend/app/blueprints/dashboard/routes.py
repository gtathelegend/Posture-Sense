from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from backend.app.services.dashboard_service import DashboardService

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    timeframe = request.args.get('timeframe', '30d')
    data = DashboardService.get_user_dashboard_overview(current_user.id, timeframe=timeframe)
    return render_template(
        'dashboard.html',
        sessions=data['sessions'],
        total_sessions=data['total_sessions'],
        total_duration=data['total_duration'],
        avg_accuracy=data['avg_accuracy'],
        pose_counts=data['pose_counts'],
        timeframe=timeframe
    )


@dashboard_bp.route('/api/dashboard_stats')
@login_required
def dashboard_stats():
    timeframe = request.args.get('timeframe', '30d')
    data = DashboardService.get_user_dashboard_overview(current_user.id, timeframe=timeframe)
    return jsonify({
        'total_sessions': data['total_sessions'],
        'total_duration': data['total_duration'],
        'avg_accuracy': data['avg_accuracy'],
        'biomechanics': data.get('biomechanics', {}),
        'totals': data.get('totals', {}),
        'pose_counts': data['pose_counts'],
        'recent_sessions': data['recent_sessions'],
        'streak_days': data.get('streak_days', 0),
        'timeframe': timeframe
    })


@dashboard_bp.route('/api/dashboard/overview')
@login_required
def dashboard_overview():
    timeframe = request.args.get('timeframe', '30d')
    data = DashboardService.get_user_dashboard_overview(current_user.id, timeframe=timeframe)
    return jsonify(data)


@dashboard_bp.route('/reports/view/session/<session_id>')
@login_required
def view_session_report(session_id):
    from backend.app.services.report_service import ReportService
    rep = ReportService.generate_session_report(current_user.id, session_id)
    return render_template('report_detail.html', report=rep, report_type='session', session_id=session_id)


@dashboard_bp.route('/reports/view/progress')
@login_required
def view_progress_report():
    from backend.app.services.report_service import ReportService
    timeframe = request.args.get('timeframe', '30d')
    rep = ReportService.generate_progress_report(current_user.id, timeframe=timeframe)
    return render_template('report_detail.html', report=rep, report_type='progress', timeframe=timeframe)


@dashboard_bp.route('/reports/view/comprehensive')
@login_required
def view_comprehensive_report():
    from backend.app.services.report_service import ReportService
    rep = ReportService.generate_comprehensive_report(current_user.id)
    return render_template('report_detail.html', report=rep, report_type='comprehensive')

