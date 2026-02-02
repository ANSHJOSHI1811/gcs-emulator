"""
Production Security Configuration

Environment-based security configuration for development vs production.
"""

import os
from typing import Dict, Any


class SecurityConfig:
    """Security configuration for different environments"""
    
    # Base configuration
    BASE_CONFIG = {
        'SECRET_KEY': os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
        'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY'),  # Will be auto-generated if None
        'DATABASE_URL': os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/gcs_emulator'),
    }
    
    # Development configuration
    DEVELOPMENT = {
        **BASE_CONFIG,
        'DEBUG': True,
        'TESTING': False,
        
        # Authentication
        'AUTH_MODE': 'disabled',  # disabled, optional, required
        'MOCK_AUTH_ENABLED': True,
        'JWT_EXPIRATION_HOURS': 24,
        
        # Rate limiting
        'RATE_LIMITING_ENABLED': False,
        'REDIS_URL': None,  # Use in-memory rate limiting
        
        # HTTPS/TLS
        'HTTPS_ENABLED': False,
        'FORCE_HTTPS': False,
        'SSL_CERT_FILE': None,
        'SSL_KEY_FILE': None,
        
        # CORS
        'CORS_ORIGINS': ['*'],  # Allow all in development
        
        # Logging
        'LOG_LEVEL': 'DEBUG',
        'LOG_FILE': 'logs/gcs_emulator.log',
    }
    
    # Production configuration
    PRODUCTION = {
        **BASE_CONFIG,
        'DEBUG': False,
        'TESTING': False,
        
        # Authentication
        'AUTH_MODE': 'required',  # Require authentication in production
        'MOCK_AUTH_ENABLED': False,
        'JWT_EXPIRATION_HOURS': 24,
        'API_KEY_HEADER': 'X-API-Key',
        
        # Rate limiting
        'RATE_LIMITING_ENABLED': True,
        'REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        
        # HTTPS/TLS
        'HTTPS_ENABLED': True,
        'FORCE_HTTPS': True,
        'SSL_CERT_FILE': os.environ.get('SSL_CERT_FILE', '/etc/ssl/certs/server.crt'),
        'SSL_KEY_FILE': os.environ.get('SSL_KEY_FILE', '/etc/ssl/private/server.key'),
        
        # CORS
        'CORS_ORIGINS': os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else [],
        
        # Logging
        'LOG_LEVEL': 'INFO',
        'LOG_FILE': '/var/log/gcs_emulator/app.log',
        
        # Security headers
        'SECURITY_HEADERS_ENABLED': True,
    }
    
    # Testing configuration
    TESTING = {
        **BASE_CONFIG,
        'DEBUG': False,
        'TESTING': True,
        
        # Authentication
        'AUTH_MODE': 'optional',
        'MOCK_AUTH_ENABLED': True,
        
        # Rate limiting
        'RATE_LIMITING_ENABLED': False,
        
        # Database
        'DATABASE_URL': os.environ.get('TEST_DATABASE_URL', 'postgresql://postgres:postgres@localhost/gcs_emulator_test'),
        
        # Logging
        'LOG_LEVEL': 'WARNING',
    }
    
    @staticmethod
    def get_config(environment: str = None) -> Dict[str, Any]:
        """
        Get configuration for specified environment
        
        Args:
            environment: Environment name ('development', 'production', 'testing')
                        If None, uses FLASK_ENV environment variable
        
        Returns:
            Configuration dictionary
        """
        if environment is None:
            environment = os.environ.get('FLASK_ENV', 'development')
        
        configs = {
            'development': SecurityConfig.DEVELOPMENT,
            'dev': SecurityConfig.DEVELOPMENT,
            'production': SecurityConfig.PRODUCTION,
            'prod': SecurityConfig.PRODUCTION,
            'testing': SecurityConfig.TESTING,
            'test': SecurityConfig.TESTING,
        }
        
        config = configs.get(environment.lower(), SecurityConfig.DEVELOPMENT)
        
        # Override with environment variables where applicable
        config = config.copy()
        
        # Check for environment-specific overrides
        if os.environ.get('AUTH_MODE'):
            config['AUTH_MODE'] = os.environ.get('AUTH_MODE')
        
        if os.environ.get('RATE_LIMITING_ENABLED'):
            config['RATE_LIMITING_ENABLED'] = os.environ.get('RATE_LIMITING_ENABLED').lower() == 'true'
        
        if os.environ.get('HTTPS_ENABLED'):
            config['HTTPS_ENABLED'] = os.environ.get('HTTPS_ENABLED').lower() == 'true'
        
        return config
    
    @staticmethod
    def print_security_status(config: Dict[str, Any]):
        """Print security configuration status"""
        print("\n" + "="*60)
        print("🔒 SECURITY CONFIGURATION STATUS")
        print("="*60)
        
        # Authentication
        print(f"\n📋 Authentication:")
        print(f"   Mode: {config.get('AUTH_MODE', 'unknown').upper()}")
        print(f"   Mock Auth: {'✅ ENABLED' if config.get('MOCK_AUTH_ENABLED') else '❌ DISABLED'}")
        print(f"   JWT Expiration: {config.get('JWT_EXPIRATION_HOURS', 24)} hours")
        
        # Rate Limiting
        print(f"\n⚡ Rate Limiting:")
        print(f"   Status: {'✅ ENABLED' if config.get('RATE_LIMITING_ENABLED') else '❌ DISABLED'}")
        if config.get('REDIS_URL'):
            print(f"   Backend: Redis ({config.get('REDIS_URL')})")
        else:
            print(f"   Backend: In-Memory")
        
        # HTTPS/TLS
        print(f"\n🔐 HTTPS/TLS:")
        print(f"   HTTPS: {'✅ ENABLED' if config.get('HTTPS_ENABLED') else '❌ DISABLED'}")
        print(f"   Force HTTPS: {'✅ YES' if config.get('FORCE_HTTPS') else '❌ NO'}")
        if config.get('SSL_CERT_FILE'):
            print(f"   Certificate: {config.get('SSL_CERT_FILE')}")
        
        # CORS
        print(f"\n🌐 CORS:")
        origins = config.get('CORS_ORIGINS', [])
        if '*' in origins:
            print(f"   ⚠️  WARNING: All origins allowed (not recommended for production)")
        elif origins:
            print(f"   Allowed Origins: {len(origins)} configured")
            for origin in origins[:3]:
                print(f"      - {origin}")
            if len(origins) > 3:
                print(f"      ... and {len(origins) - 3} more")
        else:
            print(f"   ❌ No origins configured")
        
        # Environment
        print(f"\n🌍 Environment:")
        print(f"   Mode: {os.environ.get('FLASK_ENV', 'development').upper()}")
        print(f"   Debug: {'✅ ON' if config.get('DEBUG') else '❌ OFF'}")
        print(f"   Log Level: {config.get('LOG_LEVEL', 'INFO')}")
        
        # Warnings
        print(f"\n⚠️  Security Warnings:")
        warnings = []
        
        if config.get('AUTH_MODE') == 'disabled':
            warnings.append("Authentication is DISABLED - not recommended for production")
        
        if config.get('MOCK_AUTH_ENABLED'):
            warnings.append("Mock authentication is ENABLED - disable in production")
        
        if not config.get('RATE_LIMITING_ENABLED'):
            warnings.append("Rate limiting is DISABLED - enable for production")
        
        if not config.get('HTTPS_ENABLED'):
            warnings.append("HTTPS is DISABLED - enable for production")
        
        if '*' in config.get('CORS_ORIGINS', []):
            warnings.append("CORS allows all origins - restrict for production")
        
        if config.get('DEBUG'):
            warnings.append("Debug mode is ON - turn off for production")
        
        if warnings:
            for warning in warnings:
                print(f"   ⚠️  {warning}")
        else:
            print(f"   ✅ No security warnings")
        
        print("\n" + "="*60 + "\n")


# Migration database table for API keys
MIGRATION_SQL = """
-- Migration: Add API Keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id VARCHAR(64) PRIMARY KEY,
    key_hash VARCHAR(128) NOT NULL UNIQUE,
    name VARCHAR(256),
    project_id VARCHAR(256) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    scopes VARCHAR(2048)
);

CREATE INDEX IF NOT EXISTS idx_api_keys_project ON api_keys(project_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);
"""


def run_security_migrations(db_connection):
    """
    Run security-related database migrations
    
    Args:
        db_connection: Database connection object
    """
    print("🔄 Running security migrations...")
    
    try:
        cursor = db_connection.cursor()
        cursor.execute(MIGRATION_SQL)
        db_connection.commit()
        print("✅ Security migrations completed successfully")
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        db_connection.rollback()
        raise


if __name__ == '__main__':
    # Test configuration loading
    print("Testing configuration for different environments:\n")
    
    for env in ['development', 'production', 'testing']:
        print(f"\n{'='*60}")
        print(f"Environment: {env.upper()}")
        print('='*60)
        config = SecurityConfig.get_config(env)
        SecurityConfig.print_security_status(config)
