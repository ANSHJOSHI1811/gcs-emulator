"""
Flask application configuration
"""
import os


class Config:
    """Base configuration"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-not-for-production")
    
    # SDK Compatibility Settings
    SDK_COMPATIBLE_MODE = os.getenv("SDK_COMPATIBLE_MODE", "true").lower() == "true"
    MOCK_AUTH_ENABLED = os.getenv("MOCK_AUTH_ENABLED", "true").lower() == "true"
    EMULATOR_HOST = os.getenv("STORAGE_EMULATOR_HOST", "http://localhost:8080")
    
    # Optional: Strict GCS compatibility mode (validates all fields)
    STRICT_GCS_MODE = os.getenv("STRICT_GCS_MODE", "false").lower() == "true"
    
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator"
    )
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://gcs_user:gcs_password@postgres:5432/gcs_emulator"
    )


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
