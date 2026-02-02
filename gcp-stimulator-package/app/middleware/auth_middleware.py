"""
Authentication Middleware - Production-grade JWT and API Key authentication

Supports:
- JWT token validation
- API key authentication
- Service account authentication
- Token expiration and refresh
- Configurable auth modes (development/production)
"""

import jwt
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from app.factory import db
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class APIKey(db.Model):
    """API Key model for authentication"""
    __tablename__ = 'api_keys'
    
    id = Column(String(64), primary_key=True)
    key_hash = Column(String(128), nullable=False, unique=True)
    name = Column(String(256))
    project_id = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    scopes = Column(String(2048))  # JSON string of allowed scopes
    
    def verify_key(self, api_key: str) -> bool:
        """Verify if provided key matches this record"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return key_hash == self.key_hash
    
    def is_valid(self) -> bool:
        """Check if key is still valid"""
        if not self.is_active:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
    
    def update_last_used(self):
        """Update last used timestamp"""
        self.last_used_at = datetime.utcnow()
        db.session.commit()


class AuthConfig:
    """Authentication configuration"""
    
    # JWT settings
    JWT_SECRET_KEY = None
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24
    
    # API Key settings
    API_KEY_HEADER = 'X-API-Key'
    API_KEY_LENGTH = 64
    
    # Auth modes
    AUTH_MODE_DISABLED = 'disabled'  # No auth (development)
    AUTH_MODE_OPTIONAL = 'optional'  # Auth optional, tracks usage
    AUTH_MODE_REQUIRED = 'required'  # Auth required (production)
    
    @staticmethod
    def get_auth_mode():
        """Get current authentication mode"""
        return current_app.config.get('AUTH_MODE', AuthConfig.AUTH_MODE_DISABLED)
    
    @staticmethod
    def is_auth_required():
        """Check if authentication is required"""
        return AuthConfig.get_auth_mode() == AuthConfig.AUTH_MODE_REQUIRED
    
    @staticmethod
    def initialize(app):
        """Initialize authentication configuration"""
        # Generate JWT secret if not provided
        if not app.config.get('JWT_SECRET_KEY'):
            app.config['JWT_SECRET_KEY'] = secrets.token_urlsafe(64)
            AuthConfig.JWT_SECRET_KEY = app.config['JWT_SECRET_KEY']
        else:
            AuthConfig.JWT_SECRET_KEY = app.config['JWT_SECRET_KEY']
        
        # Set defaults
        app.config.setdefault('AUTH_MODE', AuthConfig.AUTH_MODE_DISABLED)
        app.config.setdefault('JWT_EXPIRATION_HOURS', 24)
        app.config.setdefault('API_KEY_HEADER', 'X-API-Key')


def generate_jwt_token(user_id: str, project_id: str, scopes: list = None) -> str:
    """
    Generate JWT token for authentication
    
    Args:
        user_id: User identifier
        project_id: Project ID
        scopes: List of authorized scopes
    
    Returns:
        JWT token string
    """
    payload = {
        'user_id': user_id,
        'project_id': project_id,
        'scopes': scopes or ['*'],
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=AuthConfig.JWT_EXPIRATION_HOURS)
    }
    
    return jwt.encode(payload, AuthConfig.JWT_SECRET_KEY, algorithm=AuthConfig.JWT_ALGORITHM)


def verify_jwt_token(token: str) -> dict:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            AuthConfig.JWT_SECRET_KEY,
            algorithms=[AuthConfig.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_api_key(project_id: str, name: str = None, expires_days: int = None) -> tuple:
    """
    Generate new API key
    
    Args:
        project_id: Project ID for the key
        name: Optional name/description
        expires_days: Optional expiration in days
    
    Returns:
        Tuple of (api_key_string, api_key_record)
    """
    # Generate random key
    api_key = f"gcps_{secrets.token_urlsafe(AuthConfig.API_KEY_LENGTH)}"
    
    # Hash the key for storage
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Create record
    key_record = APIKey(
        id=secrets.token_urlsafe(16),
        key_hash=key_hash,
        name=name or f"API Key {datetime.utcnow().isoformat()}",
        project_id=project_id,
        expires_at=datetime.utcnow() + timedelta(days=expires_days) if expires_days else None,
        scopes='["*"]'  # All scopes by default
    )
    
    db.session.add(key_record)
    db.session.commit()
    
    return api_key, key_record


def verify_api_key(api_key: str) -> APIKey:
    """
    Verify API key and return record
    
    Args:
        api_key: API key string
    
    Returns:
        APIKey record or None if invalid
    """
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    key_record = APIKey.query.filter_by(key_hash=key_hash).first()
    
    if not key_record or not key_record.is_valid():
        return None
    
    # Update last used
    key_record.update_last_used()
    
    return key_record


def extract_auth_from_request():
    """
    Extract authentication credentials from request
    
    Returns:
        dict with auth_type and credentials, or None
    """
    # Check for API Key
    api_key = request.headers.get(AuthConfig.API_KEY_HEADER)
    if api_key:
        return {'type': 'api_key', 'credential': api_key}
    
    # Check for JWT Bearer token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        return {'type': 'jwt', 'credential': token}
    
    return None


def authenticate_request():
    """
    Authenticate the current request
    
    Returns:
        dict with user info or None if auth fails
    """
    auth_mode = AuthConfig.get_auth_mode()
    
    # If auth disabled, allow all requests
    if auth_mode == AuthConfig.AUTH_MODE_DISABLED:
        return {
            'user_id': 'anonymous',
            'project_id': request.args.get('project', 'default-project'),
            'scopes': ['*'],
            'auth_type': 'disabled'
        }
    
    # Extract auth credentials
    auth = extract_auth_from_request()
    
    # If no auth provided
    if not auth:
        if auth_mode == AuthConfig.AUTH_MODE_OPTIONAL:
            return {
                'user_id': 'anonymous',
                'project_id': request.args.get('project', 'default-project'),
                'scopes': ['*'],
                'auth_type': 'anonymous'
            }
        else:  # REQUIRED
            return None
    
    # Verify API Key
    if auth['type'] == 'api_key':
        key_record = verify_api_key(auth['credential'])
        if key_record:
            return {
                'user_id': key_record.id,
                'project_id': key_record.project_id,
                'scopes': ['*'],  # Parse from key_record.scopes if needed
                'auth_type': 'api_key'
            }
    
    # Verify JWT
    elif auth['type'] == 'jwt':
        payload = verify_jwt_token(auth['credential'])
        if payload:
            return {
                'user_id': payload.get('user_id'),
                'project_id': payload.get('project_id'),
                'scopes': payload.get('scopes', ['*']),
                'auth_type': 'jwt'
            }
    
    # Auth failed
    if auth_mode == AuthConfig.AUTH_MODE_REQUIRED:
        return None
    else:  # OPTIONAL
        return {
            'user_id': 'anonymous',
            'project_id': request.args.get('project', 'default-project'),
            'scopes': ['*'],
            'auth_type': 'failed'
        }


def require_auth(f):
    """
    Decorator to require authentication on endpoints
    
    Usage:
        @app.route('/api/resource')
        @require_auth
        def get_resource():
            user_info = request.user_info
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Authenticate request
        user_info = authenticate_request()
        
        if not user_info:
            return jsonify({
                'error': {
                    'code': 401,
                    'message': 'Authentication required',
                    'status': 'UNAUTHENTICATED'
                }
            }), 401
        
        # Attach user info to request
        request.user_info = user_info
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_project_access(f):
    """
    Decorator to verify user has access to project in request
    
    Usage:
        @app.route('/api/projects/<project_id>/resources')
        @require_project_access
        def list_resources(project_id):
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Authenticate request
        user_info = authenticate_request()
        
        if not user_info:
            return jsonify({
                'error': {
                    'code': 401,
                    'message': 'Authentication required',
                    'status': 'UNAUTHENTICATED'
                }
            }), 401
        
        # Get project ID from kwargs or query params
        project_id = kwargs.get('project_id') or request.args.get('project')
        
        # Verify access (in disabled mode, allow all)
        if AuthConfig.get_auth_mode() != AuthConfig.AUTH_MODE_DISABLED:
            if project_id and user_info.get('project_id') != project_id:
                return jsonify({
                    'error': {
                        'code': 403,
                        'message': f'Access denied to project: {project_id}',
                        'status': 'PERMISSION_DENIED'
                    }
                }), 403
        
        # Attach user info to request
        request.user_info = user_info
        
        return f(*args, **kwargs)
    
    return decorated_function
