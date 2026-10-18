import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'libraverse-cyber-purple-secret-key-2026-v1')
    DATABASE = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'instance', 'library.db'))
    EXPORTS_DIR = os.environ.get('EXPORTS_DIR', os.path.join(BASE_DIR, 'exports'))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max limit
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration for Render / cloud hosting."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() in ['true', '1']

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = False
    DATABASE = os.path.join(BASE_DIR, 'instance', 'test_library.db')
    EXPORTS_DIR = os.path.join(BASE_DIR, 'exports', 'test')
    SECRET_KEY = 'test-key-libraverse'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
