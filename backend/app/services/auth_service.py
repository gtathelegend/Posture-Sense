from backend.app.repositories.user_repository import UserRepository


class AuthService:
    @staticmethod
    def register_user(username, email, password, confirm_password):
        if not username or not email or not password:
            return None, 'All fields are required.'
        
        if password != confirm_password:
            return None, 'Passwords do not match.'
        
        if len(password) < 6:
            return None, 'Password must be at least 6 characters long.'
        
        if UserRepository.fetch_by_username(username):
            return None, 'Username already exists.'
        
        if UserRepository.fetch_by_email(email):
            return None, 'Email already registered.'
        
        user = UserRepository.create(username, email, password)
        if not user:
            return None, 'Unable to create your account right now.'
        
        return user, None

    @staticmethod
    def authenticate(username, password):
        user = UserRepository.fetch_by_username(username)
        if user and user.check_password(password):
            return user, None
        return None, 'Invalid username or password.'

    @staticmethod
    def get_user_by_id(user_id):
        return UserRepository.fetch_by_id(user_id)
