"""
Flask application configuration

WSL Migration Notes:
- All file paths now use Linux paths (no Windows backslashes)
- Storage directory uses /home/anshjoshi/gcp_emulator_storage (Linux-native)
- Docker Engine runs inside WSL Ubuntu with /var/run/docker.sock
- Docker SDK auto-detects correct socket via docker.from_env()
- No Windows path assumptions or Docker Desktop references
"""
import os
import platform


def _is_wsl():
    """Detect if running inside WSL Ubuntu"""
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except (FileNotFoundError, PermissionError):
        return False


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
    
    # WSL-specific storage configuration
    # Always use Linux paths in WSL environment
    if _is_wsl():
        BASE_STORAGE_PATH = os.getenv("STORAGE_PATH", "/home/anshjoshi/gcp_emulator_storage")
    else:
        # Fallback for non-WSL environments (development on Linux)
        BASE_STORAGE_PATH = os.getenv("STORAGE_PATH", "./storage")
    
    # Compute Service Settings
    COMPUTE_ENABLED = os.getenv("COMPUTE_ENABLED", "true").lower() == "true"
    COMPUTE_NETWORK = os.getenv("COMPUTE_NETWORK", "gcs-compute-net")
    COMPUTE_PUBLIC_PORT_RANGE = (int(os.getenv("COMPUTE_PORT_MIN", "30000")), 
                                  int(os.getenv("COMPUTE_PORT_MAX", "40000")))
    COMPUTE_SYNC_INTERVAL = int(os.getenv("COMPUTE_SYNC_INTERVAL", "5"))  # seconds
    
    # Docker configuration (WSL-native)
    # Docker Engine runs inside WSL - SDK auto-detects /var/run/docker.sock
    DOCKER_ENABLED = True
    DOCKER_SOCKET = "/var/run/docker.sock"  # Standard Linux socket path
    
    
class DevelopmentConfig(Config):
    """Development configuration for WSL environment"""
    DEBUG = True
    TESTING = False
    # PostgreSQL on localhost (running in Docker container)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator"
    )
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Testing configuration (use PostgreSQL test database)"""
    DEBUG = True
    TESTING = True
    # For testing, use a separate PostgreSQL database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator_test"
    )
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
