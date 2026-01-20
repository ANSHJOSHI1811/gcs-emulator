"""
IAM Enforcement Utility - Check permissions on resources
"""
from flask import request, jsonify
from functools import wraps
from app.models.iam_policy import IamPolicy, get_role_permissions


def get_current_identity():
    """
    Extract identity from request headers
    In emulator mode, this is simplified - real GCP would validate JWT tokens
    
    Returns:
        dict with 'type' and 'email'
    """
    auth_header = request.headers.get('Authorization', '')
    
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        # In emulator mode, accept any token
        # Real implementation would validate token and extract identity
        return {
            'type': 'user',
            'email': 'emulator-user@gcp-emulator.local',
            'member': 'user:emulator-user@gcp-emulator.local'
        }
    
    # Default: allow anonymous with allUsers
    return {
        'type': 'anonymous',
        'email': 'anonymous',
        'member': 'allUsers'
    }


def check_permission(resource_type: str, resource_id: str, permission: str) -> bool:
    """
    Check if current identity has permission on resource
    
    Args:
        resource_type: 'project', 'bucket', 'instance'
        resource_id: Resource identifier
        permission: Permission to check (e.g. 'storage.buckets.get')
    
    Returns:
        True if permission granted, False otherwise
    """
    # In emulator mode with MOCK_AUTH, allow all by default
    from flask import current_app
    if current_app.config.get('MOCK_AUTH_ENABLED', True):
        return True
    
    identity = get_current_identity()
    member = identity['member']
    
    # Get IAM policy for resource
    policy = IamPolicy.query.filter_by(
        resource_type=resource_type,
        resource_id=resource_id
    ).first()
    
    if not policy:
        # No policy = deny by default (except for allUsers/allAuthenticatedUsers)
        return member in ['allUsers', 'allAuthenticatedUsers']
    
    return policy.has_permission(member, permission)


def require_permission(resource_type: str, permission: str, resource_id_param: str = None):
    """
    Decorator to enforce IAM permissions on endpoints
    
    Args:
        resource_type: 'project', 'bucket', 'instance'
        permission: Permission required (e.g. 'storage.buckets.create')
        resource_id_param: Name of URL parameter containing resource ID (optional)
    
    Usage:
        @require_permission('bucket', 'storage.buckets.get', 'bucket_name')
        def get_bucket(bucket_name):
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Extract resource ID from kwargs if specified
            if resource_id_param:
                resource_id = kwargs.get(resource_id_param)
            else:
                # For create operations, use project from query params
                resource_id = request.args.get('project', 'default-project')
            
            # Check permission
            if not check_permission(resource_type, resource_id, permission):
                return jsonify({
                    "error": {
                        "code": 403,
                        "message": f"Permission denied: {permission}",
                        "status": "PERMISSION_DENIED"
                    }
                }), 403
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


def get_filtered_resources(resources: list, resource_type: str, permission: str) -> list:
    """
    Filter list of resources based on IAM permissions
    Only returns resources that user has permission to view
    
    Args:
        resources: List of resource objects with 'id' or 'name' attribute
        resource_type: 'project', 'bucket', 'instance'
        permission: Permission to check
    
    Returns:
        Filtered list of resources
    """
    from flask import current_app
    if current_app.config.get('MOCK_AUTH_ENABLED', True):
        return resources  # Allow all in emulator mode
    
    filtered = []
    for resource in resources:
        resource_id = getattr(resource, 'id', None) or getattr(resource, 'name', None)
        if resource_id and check_permission(resource_type, resource_id, permission):
            filtered.append(resource)
    
    return filtered
