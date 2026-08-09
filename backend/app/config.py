import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base application configuration with production hardening."""

    ENV = os.getenv('FLASK_ENV', os.getenv('ENV', 'development')).lower()
    DEBUG = ENV == 'development'
    TESTING = ENV == 'testing'

    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-secret-key-change-in-production')
    
    # Production Secret Validation Guard
    if ENV == 'production':
        if not SECRET_KEY or 'dev' in SECRET_KEY or 'default' in SECRET_KEY or len(SECRET_KEY) < 16:
            raise ValueError("FATAL: Production FLASK_ENV requires a secure SECRET_KEY (min 16 bytes). Default development keys are prohibited.")

    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_PUBLISHABLE_KEY = os.getenv('SUPABASE_PUBLISHABLE_KEY')
    SUPABASE_SECRET_KEY = os.getenv('SUPABASE_SECRET_KEY')
    
    # SMTP / Email Configuration
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')

    # CORS Configuration
    raw_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000')
    ALLOWED_ORIGINS = [o.strip() for o in raw_origins.split(',') if o.strip()]
    
    # Flask Session & Security Cookie Hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = ENV == 'production'

    # Request Resource Limits (16MB maximum body payload to prevent DoS)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

