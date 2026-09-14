import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Redis configuration for persistence
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    USE_REDIS = os.environ.get('USE_REDIS', 'false').lower() == 'true'

    # SQLite fallback for persistence
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'queue_data.db')

    # Authentication
    REQUIRE_API_KEY = os.environ.get('REQUIRE_API_KEY', 'false').lower() == 'true'
    API_KEYS = os.environ.get('API_KEYS', '').split(',') if os.environ.get('API_KEYS') else []

    # Queue settings
    MAX_QUEUE_SIZE = int(os.environ.get('MAX_QUEUE_SIZE', '1000'))
    TASK_TIMEOUT = int(os.environ.get('TASK_TIMEOUT', '3600'))  # 1 hour default
    ENABLE_PRIORITY_QUEUE = os.environ.get('ENABLE_PRIORITY_QUEUE', 'true').lower() == 'true'

    # Monitoring
    ENABLE_METRICS = os.environ.get('ENABLE_METRICS', 'true').lower() == 'true'
    METRICS_RETENTION_DAYS = int(os.environ.get('METRICS_RETENTION_DAYS', '7'))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    REQUIRE_API_KEY = True

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    USE_REDIS = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
