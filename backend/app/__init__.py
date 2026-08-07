import os
from flask import Flask, url_for as flask_url_for
from flask_cors import CORS
from backend.app.config import Config
from backend.app.extensions import bcrypt, login_manager, init_supabase
from backend.app.services.auth_service import AuthService
from backend.app.logging import setup_logging
from backend.app.errors import register_error_handlers
from backend.app.middleware.security import register_middleware
from backend.app.blueprints import main_bp, auth_bp, dashboard_bp, contact_bp, api_bp


def create_app(config_class=Config):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    template_folder = os.path.join(base_dir, 'templates')
    static_folder = os.path.join(base_dir, 'static')

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    app.config.from_object(config_class)

    # Initialize Extensions
    CORS(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return AuthService.get_user_by_id(user_id)

    # Supabase Client
    init_supabase(app)

    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(api_bp)

    # Alias map for backward compatibility with templates and legacy url_for calls
    endpoint_aliases = {
        'index': 'main.index',
        'landing': 'main.landing',
        'favicon': 'main.favicon',
        'sitemap': 'main.sitemap',
        'sitemap2': 'main.sitemap2',
        'robots': 'main.robots',
        'pose_detection': 'main.pose_detection',
        'about': 'main.about',
        'yoga_poses': 'main.yoga_poses',
        'join_now': 'main.join_now',
        'playground': 'main.playground',
        'login': 'auth.login',
        'logout': 'auth.logout',
        'register': 'auth.register',
        'dashboard': 'dashboard.dashboard',
        'dashboard_stats': 'dashboard.dashboard_stats',
        'contact': 'contact.contact',
        'submit': 'contact.submit',
        'subscribe': 'contact.subscribe',
        'pose_status_updates': 'api.pose_status_updates',
        'get_status': 'api.get_status',
        'stop_camera': 'api.stop_camera',
        'save_pose_session': 'api.save_pose_session',
        'video_feed': 'api.video_feed',
    }

    def smart_url_for(endpoint, **values):
        if endpoint in endpoint_aliases:
            endpoint = endpoint_aliases[endpoint]
        return flask_url_for(endpoint, **values)

    app.jinja_env.globals['url_for'] = smart_url_for

    # Register Logging, Error Handlers, and Middleware
    setup_logging(app)
    register_error_handlers(app)
    register_middleware(app)

    return app
