import os
from typing import Optional
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from supabase import create_client, Client

bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

_supabase_client: Optional[Client] = None


def init_supabase(app) -> Optional[Client]:
    global _supabase_client
    url = app.config.get('SUPABASE_URL') or os.getenv('SUPABASE_URL')
    secret_key = app.config.get('SUPABASE_SECRET_KEY') or os.getenv('SUPABASE_SECRET_KEY')
    pub_key = app.config.get('SUPABASE_PUBLISHABLE_KEY') or os.getenv('SUPABASE_PUBLISHABLE_KEY')
    key = secret_key or pub_key
    
    if not url or not key:
        _supabase_client = None
        return None
    
    _supabase_client = create_client(url, key)
    return _supabase_client


def get_supabase_client() -> Optional[Client]:
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SECRET_KEY') or os.getenv('SUPABASE_PUBLISHABLE_KEY')
    if url and key:
        _supabase_client = create_client(url, key)
        return _supabase_client
    return None


def require_supabase() -> Client:
    client = get_supabase_client()
    if client is None:
        raise RuntimeError('SUPABASE_URL and SUPABASE_SECRET_KEY must be set.')
    return client
