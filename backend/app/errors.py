from flask import render_template, jsonify, request


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'status': 'error', 'message': 'Resource not found'}), 404
        return render_template('index.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal Server Error: {error}")
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
        return render_template('index.html'), 500

    @app.errorhandler(RuntimeError)
    def handle_runtime_error(error):
        app.logger.error(f"Runtime Error: {error}")
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({'status': 'error', 'message': str(error)}), 500
        return render_template('index.html'), 500
