from datetime import datetime
from flask_login import UserMixin
from backend.app.extensions import bcrypt


def parse_timestamp(value):
    if isinstance(value, datetime):
        return value
    if not value:
        return datetime.utcnow()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=None)
        except ValueError:
            pass
    return datetime.utcnow()


class User(UserMixin):
    def __init__(self, id, username, email, password_hash, created_at=None):
        self.id = str(id)
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = parse_timestamp(created_at)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


def build_user(record):
    if not record:
        return None
    return User(
        id=record.get('id'),
        username=record.get('username'),
        email=record.get('email'),
        password_hash=record.get('password_hash'),
        created_at=record.get('created_at'),
    )
