"""
IAM Handlers - HTTP request handlers for IAM API endpoints
"""
from flask import Blueprint, request, jsonify
from typing import Dict, Any
from app.services.iam_service import ServiceAccountService, IAMPolicyService, RoleService
from app.serializers.iam_serializers import (
    ServiceAccountSerializer, ServiceAccountKeySerializer,
    IAMPolicySerializer, RoleSerializer
)
from app.utils.gcs_errors import (
    not_found_error,
    invalid_argument_error,
    internal_error,
    conflict_error
)

# Create blueprints
service_accounts_bp = Blueprint('service_accounts', __name__)
iam_policies_bp = Blueprint('iam_policies', __name__)
roles_bp = Blueprint('iam_roles', __name__)

# Initialize services
sa_service = ServiceAccountService()
policy_service = IAMPolicyService()
role_service = RoleService()


# ============================================================================
# Service Account Endpoints
# ============================================================================

@service_accounts_bp.route('/v1/projects/<project_id>/serviceAccounts', methods=['POST'])
def create_service_account(project_id: str):
    """Create a service account"""
    try:
        data = request.get_json()
        account_id = data.get('accountId')
        
        if not account_id:
            return invalid_argument_error("accountId is required")
        
        service_account = sa_service.create_service_account(
            project_id=project_id,
            account_id=account_id,
            display_name=data.get('displayName'),
            description=data.get('description')
        )
        
        return jsonify(ServiceAccountSerializer.to_dict(service_account)), 201
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@service_accounts_bp.route('/v1/projects/<project_id>/serviceAccounts', methods=['GET'])
def list_service_accounts(project_id: str):
    """List service accounts for a project"""
    try:
        accounts = sa_service.list_service_accounts(project_id)
        return jsonify({
            "accounts": [ServiceAccountSerializer.to_list_item(sa) for sa in accounts]
        }), 200
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@service_accounts_bp.route('/v1/projects/<project_id>/serviceAccounts/<account_email>', methods=['GET'])
def get_service_account(project_id: str, account_email: str):
    """Get a service account"""
    try:
        # Reconstruct full email if needed
        if '@' not in account_email:
            account_email = f"{account_email}@{project_id}.iam.gserviceaccount.com"
        
        service_account = sa_service.get_service_account(account_email)
        if not service_account:
            return not_found_error(account_email, "service account")
        
        return jsonify(ServiceAccountSerializer.to_dict(service_account)), 200
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@service_accounts_bp.route('/v1/projects/<project_id>/serviceAccounts/<account_email>', methods=['PATCH', 'PUT'])
def update_service_account(project_id: str, account_email: str):
    """Update a service account"""
    try:
        if '@' not in account_email:
            account_email = f"{account_email}@{project_id}.iam.gserviceaccount.com"
        
        data = request.get_json()
        service_account = sa_service.update_service_account(
            email=account_email,
            display_name=data.get('displayName'),
            description=data.get('description')
        )
        
        return jsonify(ServiceAccountSerializer.to_dict(service_account)), 200
    except ValueError as e:
        # Treat not found as 404
        msg = str(e)
        if "not found" in msg.lower():
            return not_found_error(account_email, "service account")
        return invalid_argument_error(msg)
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@service_accounts_bp.route('/v1/projects/<project_id>/serviceAccounts/<account_email>', methods=['DELETE'])
def delete_service_account(project_id: str, account_email: str):
    """Delete a service account"""
    try:
        if '@' not in account_email:
            account_email = f"{account_email}@{project_id}.iam.gserviceaccount.com"
        
        sa_service.delete_service_account(account_email)
        return '', 204
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            return not_found_error(account_email, "service account")
        return invalid_argument_error(msg)
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@service_accounts_bp.route('/v1/projects/<project_id>/serviceAccounts/<account_email>:disable', methods=['POST'])
def disable_service_account(project_id: str, account_email: str):
    """Disable a service account"""
    try:
        if '@' not in account_email:
            account_email = f"{account_email}@{project_id}.iam.gserviceaccount.com"
        
        service_account = sa_service.disable_service_account(account_email)
        return jsonify(ServiceAccountSerializer.to_dict(service_account)), 200
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            return not_found_error(account_email, "service account")
        return invalid_argument_error(msg)
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@service_accounts_bp.route('/v1/projects/<project_id>/serviceAccounts/<account_email>:enable', methods=['POST'])
def enable_service_account(project_id: str, account_email: str):
    """Enable a service account"""
    try:
        if '@' not in account_email:
            account_email = f"{account_email}@{project_id}.iam.gserviceaccount.com"
        
        service_account = sa_service.enable_service_account(account_email)
        return jsonify(ServiceAccountSerializer.to_dict(service_account)), 200
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            return not_found_error(account_email, "service account")
        return invalid_argument_error(msg)
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


# ============================================================================
# Service Account Key Endpoints
# ============================================================================

@service_accounts_bp.route('/v1/projects/<project_id>/serviceAccounts/<account_email>/keys', methods=['POST'])
def create_service_account_key(project_id: str, account_email: str):
    """Create a service account key"""
    try:
        if '@' not in account_email:
            account_email = f"{account_email}@{project_id}.iam.gserviceaccount.com"
        
        data = request.get_json() or {}
        key = sa_service.create_key(
            email=account_email,
            key_algorithm=data.get('keyAlgorithm', 'KEY_ALG_RSA_2048'),
            private_key_type=data.get('privateKeyType', 'TYPE_GOOGLE_CREDENTIALS_FILE')
        )
        
        return jsonify(ServiceAccountKeySerializer.to_dict(key, include_private_key=True)), 201
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            return not_found_error(account_email, "service account")
        return invalid_argument_error(msg)
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@service_accounts_bp.route('/v1/projects/<project_id>/serviceAccounts/<account_email>/keys', methods=['GET'])
def list_service_account_keys(project_id: str, account_email: str):
    """List service account keys"""
    try:
        if '@' not in account_email:
            account_email = f"{account_email}@{project_id}.iam.gserviceaccount.com"
        
        keys = sa_service.list_keys(account_email)
        return jsonify({
            "keys": [ServiceAccountKeySerializer.to_dict(key, include_private_key=False) for key in keys]
        }), 200
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@service_accounts_bp.route('/v1/projects/<project_id>/serviceAccounts/<account_email>/keys/<key_id>', methods=['GET'])
def get_service_account_key(project_id: str, account_email: str, key_id: str):
    """Get a service account key"""
    try:
        if '@' not in account_email:
            account_email = f"{account_email}@{project_id}.iam.gserviceaccount.com"
        
        key_name = f"projects/{project_id}/serviceAccounts/{account_email}/keys/{key_id}"
        key = sa_service.get_key(key_name)
        
        if not key:
            return not_found_error(key_id, "key")
        
        return jsonify(ServiceAccountKeySerializer.to_dict(key, include_private_key=False)), 200
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@service_accounts_bp.route('/v1/projects/<project_id>/serviceAccounts/<account_email>/keys/<key_id>', methods=['DELETE'])
def delete_service_account_key(project_id: str, account_email: str, key_id: str):
    """Delete a service account key"""
    try:
        if '@' not in account_email:
            account_email = f"{account_email}@{project_id}.iam.gserviceaccount.com"
        
        key_name = f"projects/{project_id}/serviceAccounts/{account_email}/keys/{key_id}"
        sa_service.delete_key(key_name)
        return '', 204
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            return not_found_error(key_id, "key")
        return invalid_argument_error(msg)
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


# ============================================================================
# IAM Policy Endpoints
# ============================================================================

@iam_policies_bp.route('/v1/<path:resource>:getIamPolicy', methods=['GET', 'POST'])
def get_iam_policy(resource: str):
    """Get IAM policy for a resource"""
    try:
        # Determine resource type from path
        resource_type = _determine_resource_type(resource)
        
        policy = policy_service.get_iam_policy(resource, resource_type)
        return jsonify(IAMPolicySerializer.to_dict(policy)), 200
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@iam_policies_bp.route('/v1/<path:resource>:setIamPolicy', methods=['POST'])
def set_iam_policy(resource: str):
    """Set IAM policy for a resource"""
    try:
        data = request.get_json()
        policy_data = data.get('policy', {})
        
        resource_type = _determine_resource_type(resource)
        
        policy = policy_service.set_iam_policy(
            resource_name=resource,
            resource_type=resource_type,
            bindings=policy_data.get('bindings', []),
            version=policy_data.get('version', 1),
            etag=policy_data.get('etag')
        )
        
        return jsonify(IAMPolicySerializer.to_dict(policy)), 200
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@iam_policies_bp.route('/v1/<path:resource>:testIamPermissions', methods=['POST'])
def test_iam_permissions(resource: str):
    """Test IAM permissions for a resource"""
    try:
        data = request.get_json()
        permissions = data.get('permissions', [])
        
        granted_permissions = policy_service.test_iam_permissions(resource, permissions)
        return jsonify({"permissions": granted_permissions}), 200
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


# ============================================================================
# Role Endpoints
# ============================================================================

@roles_bp.route('/v1/projects/<project_id>/roles', methods=['POST'])
def create_role(project_id: str):
    """Create a custom role"""
    try:
        data = request.get_json()
        role_id = data.get('roleId')
        
        if not role_id:
            return invalid_argument_error("roleId is required")
        
        role = role_service.create_role(
            project_id=project_id,
            role_id=role_id,
            title=data.get('title', role_id),
            description=data.get('description'),
            included_permissions=data.get('includedPermissions', []),
            stage=data.get('stage', 'GA')
        )
        
        return jsonify(RoleSerializer.to_dict(role)), 201
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@roles_bp.route('/v1/projects/<project_id>/roles', methods=['GET'])
@roles_bp.route('/v1/roles', methods=['GET'])
def list_roles(project_id: str = None):
    """List roles"""
    try:
        roles = role_service.list_roles(project_id)
        return jsonify({
            "roles": [RoleSerializer.to_list_item(role) for role in roles]
        }), 200
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@roles_bp.route('/v1/<path:role_name>', methods=['GET'])
def get_role(role_name: str):
    """Get a role"""
    try:
        role = role_service.get_role(role_name)
        if not role:
            return not_found_error(role_name, "role")
        
        return jsonify(RoleSerializer.to_dict(role)), 200
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@roles_bp.route('/v1/<path:role_name>', methods=['PATCH'])
def update_role(role_name: str):
    """Update a custom role"""
    try:
        data = request.get_json()
        role = role_service.update_role(
            role_name=role_name,
            title=data.get('title'),
            description=data.get('description'),
            included_permissions=data.get('includedPermissions'),
            stage=data.get('stage')
        )
        
        return jsonify(RoleSerializer.to_dict(role)), 200
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@roles_bp.route('/v1/<path:role_name>', methods=['DELETE'])
def delete_role(role_name: str):
    """Delete a custom role"""
    try:
        role = role_service.delete_role(role_name)
        return jsonify(RoleSerializer.to_dict(role)), 200
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


@roles_bp.route('/v1/<path:role_name>:undelete', methods=['POST'])
def undelete_role(role_name: str):
    """Undelete a custom role"""
    try:
        role = role_service.undelete_role(role_name)
        return jsonify(RoleSerializer.to_dict(role)), 200
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal error: {str(e)}")


# ============================================================================
# Helper Functions
# ============================================================================

def _determine_resource_type(resource: str) -> str:
    """Determine resource type from resource path"""
    if 'projects' in resource and 'buckets' in resource:
        return 'bucket'
    elif 'projects' in resource and 'serviceAccounts' in resource:
        return 'service_account'
    elif resource.startswith('projects/'):
        return 'project'
    else:
        return 'unknown'
