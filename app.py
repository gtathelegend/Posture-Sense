"""
PostureSense v2 Application Entrypoint
Serves the Flask application created by backend.app.create_app()
"""

from backend.app import create_app
from backend.app.extensions import get_supabase_client

app = create_app()

if __name__ == '__main__':
    supabase = get_supabase_client()
    if supabase is None:
        print('Warning: SUPABASE_URL and SUPABASE_SECRET_KEY are not configured.')
    app.run(host='0.0.0.0', port=8080, debug=True)
