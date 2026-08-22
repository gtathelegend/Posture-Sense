import os
from flask import Blueprint, render_template, send_file, redirect, current_app
from flask_login import login_required
import backend.app.utils.cv_utils as cv_utils

main_bp = Blueprint('main', __name__)


def _get_root_file(filename):
    root_dir = os.path.abspath(os.path.join(current_app.root_path, '..', '..'))
    return os.path.join(root_dir, filename)


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/landing')
def landing():
    return redirect('/', code=302)


@main_bp.route('/favicon.ico')
def favicon():
    return send_file(_get_root_file('favicon.ico'), mimetype='image/x-icon')


@main_bp.route('/sitemap.xml')
def sitemap():
    return send_file(_get_root_file('sitemap.xml'), mimetype='text/xml')


@main_bp.route('/sitemap2.xml')
def sitemap2():
    return send_file(_get_root_file('sitemap.xml'), mimetype='text/xml')


@main_bp.route('/robots.txt')
def robots():
    return send_file(_get_root_file('robots.txt'), mimetype='text/plain')


@main_bp.route('/pose_detection')
@login_required
def pose_detection():
    if not cv_utils.current_status:
        cv_utils.current_status = 'Unknown'
    if not cv_utils.last_status:
        cv_utils.last_status = 'Unknown'
    return render_template('app.html', pose_status=cv_utils.current_status, last_status=cv_utils.last_status)


@main_bp.route('/about')
def about():
    return redirect('/#about')


@main_bp.route('/team')
def team():
    return redirect('/#team')


@main_bp.route('/yoga-poses')
def yoga_poses():
    return render_template('yoga-poses.html')


@main_bp.route('/pricing')
def join_now():
    return redirect('/#features')


@main_bp.route('/playground')
def playground():
    return render_template('playground.html')


# ── Backward Compatibility Alias Routes ───────────────────────────────────────

@main_bp.route('/get_status')
def get_status_alias():
    from backend.app.blueprints.api.routes import get_status
    return get_status()


@main_bp.route('/stop_camera')
def stop_camera_alias():
    from backend.app.blueprints.api.routes import stop_camera
    return stop_camera()


@main_bp.route('/video_feed')
def video_feed_alias():
    from backend.app.blueprints.api.routes import video_feed
    return video_feed()


@main_bp.route('/save_pose_session', methods=['POST'])
def save_pose_session_alias():
    from backend.app.blueprints.api.routes import save_pose_session
    return save_pose_session()


@main_bp.route('/status')
def status_alias():
    from backend.app.blueprints.api.routes import pose_status_updates
    return pose_status_updates()


@main_bp.route('/health')
def health_alias():
    from backend.app.blueprints.api.routes import health
    return health()


@main_bp.route('/version')
def version_alias():
    from backend.app.blueprints.api.routes import version
    return version()


