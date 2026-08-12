from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from backend.app.services.dashboard_service import DashboardService

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    data = DashboardService.get_user_dashboard_data(current_user.id)
    return render_template(
        'dashboard.html',
        sessions=data['sessions'],
        total_sessions=data['total_sessions'],
        total_duration=data['total_duration'],
        avg_accuracy=data['avg_accuracy'],
        pose_counts=data['pose_counts']
    )


@dashboard_bp.route('/api/dashboard_stats')
@login_required
def dashboard_stats():
    data = DashboardService.get_user_dashboard_data(current_user.id)
    return jsonify({
        'total_sessions': data['total_sessions'],
        'total_duration': data['total_duration'],
        'avg_accuracy': data['avg_accuracy'],
        'biomechanics': data.get('biomechanics', {}),
        'totals': data.get('totals', {}),
        'pose_counts': data['pose_counts'],
        'recent_sessions': data['recent_sessions']
    })

