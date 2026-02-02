"""
Authentication Routes - API Key and Token Management

Provides endpoints for:
- Generating API keys
- Listing API keys
- Revoking API keys
- Generating JWT tokens
- Token refresh
"""

from flask import Blueprint, request, jsonify
from app.middleware.auth_middleware import (
    generate_api_key,
    generate_jwt_token,
    verify_jwt_token,
    require_auth,
    APIKey,
    AuthConfig
)
from app.factory import db
from datetime import datetime

auth_mgmt_bp = Blueprint('auth_management', __name__)


@auth_mgmt_bp.route('/auth/api-keys', methods=['POST'])
def create_api_key():
    """
    Generate a new API key
    
    POST /auth/api-keys
    {
        "project_id": "my-project",
        "name": "My API Key",
        "expires_days": 365
    }
    """
    data = request.get_json() or {}
    
    project_id = data.get('project_id')
    if not project_id:
        return jsonify({
            'error': {
                'code': 400,
                'message': 'project_id is required'
            }
        }), 400
    
    name = data.get('name')
    expires_days = data.get('expires_days')
    
    try:
        api_key, key_record = generate_api_key(project_id, name, expires_days)
        
        return jsonify({
            'api_key': api_key,  # Only shown once!
            'key_id': key_record.id,
            'name': key_record.name,
            'project_id': key_record.project_id,
            'created_at': key_record.created_at.isoformat() + 'Z',
            'expires_at': key_record.expires_at.isoformat() + 'Z' if key_record.expires_at else None,
            'warning': 'Save this API key now. It will not be shown again.'
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 500,
                'message': f'Failed to create API key: {str(e)}'
            }
        }), 500


@auth_mgmt_bp.route('/auth/api-keys', methods=['GET'])
def list_api_keys():
    """
    List API keys for a project
    
    GET /auth/api-keys?project_id=my-project
    """
    project_id = request.args.get('project_id')
    
    if not project_id:
        return jsonify({
            'error': {
                'code': 400,
                'message': 'project_id query parameter is required'
            }
        }), 400
    
    keys = APIKey.query.filter_by(project_id=project_id).all()
    
    return jsonify({
        'keys': [
            {
                'key_id': key.id,
                'name': key.name,
                'project_id': key.project_id,
                'created_at': key.created_at.isoformat() + 'Z',
                'expires_at': key.expires_at.isoformat() + 'Z' if key.expires_at else None,
                'last_used_at': key.last_used_at.isoformat() + 'Z' if key.last_used_at else None,
                'is_active': key.is_active,
                'is_valid': key.is_valid()
            }
            for key in keys
        ]
    }), 200


@auth_mgmt_bp.route('/auth/api-keys/<key_id>', methods=['DELETE'])
def revoke_api_key(key_id):
    """
    Revoke (deactivate) an API key
    
    DELETE /auth/api-keys/{key_id}
    """
    key = APIKey.query.filter_by(id=key_id).first()
    
    if not key:
        return jsonify({
            'error': {
                'code': 404,
                'message': f'API key not found: {key_id}'
            }
        }), 404
    
    key.is_active = False
    db.session.commit()
    
    return jsonify({
        'message': f'API key {key_id} revoked successfully'
    }), 200


@auth_mgmt_bp.route('/auth/api-keys/<key_id>', methods=['GET'])
def get_api_key(key_id):
    """
    Get API key details
    
    GET /auth/api-keys/{key_id}
    """
    key = APIKey.query.filter_by(id=key_id).first()
    
    if not key:
        return jsonify({
            'error': {
                'code': 404,
                'message': f'API key not found: {key_id}'
            }
        }), 404
    
    return jsonify({
        'key_id': key.id,
        'name': key.name,
        'project_id': key.project_id,
        'created_at': key.created_at.isoformat() + 'Z',
        'expires_at': key.expires_at.isoformat() + 'Z' if key.expires_at else None,
        'last_used_at': key.last_used_at.isoformat() + 'Z' if key.last_used_at else None,
        'is_active': key.is_active,
        'is_valid': key.is_valid()
    }), 200


@auth_mgmt_bp.route('/auth/tokens', methods=['POST'])
def create_jwt_token():
    """
    Generate a JWT token
    
    POST /auth/tokens
    {
        "user_id": "user@example.com",
        "project_id": "my-project",
        "scopes": ["storage.read", "compute.write"]
    }
    """
    data = request.get_json() or {}
    
    user_id = data.get('user_id')
    project_id = data.get('project_id')
    
    if not user_id or not project_id:
        return jsonify({
            'error': {
                'code': 400,
                'message': 'user_id and project_id are required'
            }
        }), 400
    
    scopes = data.get('scopes', ['*'])
    
    try:
        token = generate_jwt_token(user_id, project_id, scopes)
        
        return jsonify({
            'token': token,
            'token_type': 'Bearer',
            'expires_in': AuthConfig.JWT_EXPIRATION_HOURS * 3600,
            'user_id': user_id,
            'project_id': project_id,
            'scopes': scopes
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': {
                'code': 500,
                'message': f'Failed to create token: {str(e)}'
            }
        }), 500


@auth_mgmt_bp.route('/auth/tokens/verify', methods=['POST'])
def verify_token():
    """
    Verify a JWT token
    
    POST /auth/tokens/verify
    {
        "token": "eyJ..."
    }
    """
    data = request.get_json() or {}
    token = data.get('token')
    
    if not token:
        return jsonify({
            'error': {
                'code': 400,
                'message': 'token is required'
            }
        }), 400
    
    payload = verify_jwt_token(token)
    
    if not payload:
        return jsonify({
            'valid': False,
            'error': 'Token is invalid or expired'
        }), 200
    
    return jsonify({
        'valid': True,
        'user_id': payload.get('user_id'),
        'project_id': payload.get('project_id'),
        'scopes': payload.get('scopes'),
        'issued_at': payload.get('iat'),
        'expires_at': payload.get('exp')
    }), 200


@auth_mgmt_bp.route('/auth/config', methods=['GET'])
def get_auth_config():
    """
    Get current authentication configuration
    
    GET /auth/config
    """
    return jsonify({
        'auth_mode': AuthConfig.get_auth_mode(),
        'auth_required': AuthConfig.is_auth_required(),
        'jwt_expiration_hours': AuthConfig.JWT_EXPIRATION_HOURS,
        'api_key_header': AuthConfig.API_KEY_HEADER,
        'supported_auth_types': ['api_key', 'jwt', 'anonymous']
    }), 200
