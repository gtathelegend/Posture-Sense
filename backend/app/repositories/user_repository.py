from backend.app.extensions import require_supabase, bcrypt
from backend.app.models.user import build_user


class UserRepository:
    @staticmethod
    def fetch_by_id(user_id):
        response = require_supabase().table('users').select('*').eq('id', str(user_id)).limit(1).execute()
        data = response.data or []
        return build_user(data[0]) if data else None

    @staticmethod
    def fetch_by_username(username):
        response = require_supabase().table('users').select('*').eq('username', username).limit(1).execute()
        data = response.data or []
        return build_user(data[0]) if data else None

    @staticmethod
    def fetch_by_email(email):
        response = require_supabase().table('users').select('*').eq('email', email).limit(1).execute()
        data = response.data or []
        return build_user(data[0]) if data else None

    @staticmethod
    def create(username, email, password):
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        payload = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
        }
        response = require_supabase().table('users').insert(payload).execute()
        data = response.data or []
        if data:
            return build_user(data[0])
        return UserRepository.fetch_by_username(username)
