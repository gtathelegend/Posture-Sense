import time


def register_middleware(app):
    @app.before_request
    def before_request_func():
        request_start_time = time.time()
        # Keep request timing context available if needed
        pass

    @app.after_request
    def apply_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(self)'
        return response
