"""
IAM handler - Service Accounts, Roles, and Policies management
"""
import secrets
import json
import base64
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from app.factory import db
from app.models.service_account import ServiceAccount, ServiceAccountKey
from app.models.iam_policy import IamPolicy, Role, get_role_permissions
from app.models.project import Project
from app.handlers.errors import error_response

iam_bp = Blueprint("iam", __name__)


# ========== Service Accounts ==========

@iam_bp.route("/v1/projects/<project_id>/serviceAccounts", methods=["POST"])
def create_service_account(project_id):
    """Create a service account"""
    data = request.get_json()
    account_id = data.get("accountId")
    
    if not account_id:
        return error_response(400, "INVALID_ARGUMENT", "accountId is required")
    
    # Check if project exists
    project = Project.query.filter_by(id=project_id).first()
    if not project:
        return error_response(404, "NOT_FOUND", f"Project {project_id} not found")
    
    # Generate unique ID and email
    unique_id = str(secrets.randbelow(10**21)).zfill(21)
    email = f"{account_id}@{project_id}.iam.gserviceaccount.com"
    resource_name = f"projects/{project_id}/serviceAccounts/{email}"
    
    # Check if already exists
    existing = ServiceAccount.query.filter_by(email=email).first()
    if existing:
        return error_response(409, "ALREADY_EXISTS", f"Service account {email} already exists")
    
    sa = ServiceAccount(
        id=resource_name,
        project_id=project_id,
        email=email,
        unique_id=unique_id,
        display_name=data.get("displayName", account_id),
        description=data.get("description", ""),
    )
    
    db.session.add(sa)
    db.session.commit()
    
    return jsonify(sa.to_dict()), 201


@iam_bp.route("/v1/projects/<project_id>/serviceAccounts", methods=["GET"])
def list_service_accounts(project_id):
    """List service accounts in a project"""
    accounts = ServiceAccount.query.filter_by(project_id=project_id).all()
    
    return jsonify({
        "accounts": [sa.to_dict() for sa in accounts]
    })


@iam_bp.route("/v1/<path:resource_name>", methods=["GET"])
def get_service_account(resource_name):
    """Get a service account by resource name"""
    if not resource_name.startswith("projects/") or "/serviceAccounts/" not in resource_name:
        return error_response(400, "INVALID_ARGUMENT", "Invalid resource name")
    
    sa = ServiceAccount.query.filter_by(id=resource_name).first()
    if not sa:
        return error_response(404, "NOT_FOUND", f"Service account {resource_name} not found")
    
    return jsonify(sa.to_dict())


@iam_bp.route("/v1/<path:resource_name>", methods=["DELETE"])
def delete_service_account(resource_name):
    """Delete a service account"""
    if not resource_name.startswith("projects/") or "/serviceAccounts/" not in resource_name:
        return error_response(400, "INVALID_ARGUMENT", "Invalid resource name")
    
    sa = ServiceAccount.query.filter_by(id=resource_name).first()
    if not sa:
        return error_response(404, "NOT_FOUND", f"Service account {resource_name} not found")
    
    db.session.delete(sa)
    db.session.commit()
    
    return "", 204


# ========== Service Account Keys ==========

@iam_bp.route("/v1/<path:resource_name>/keys", methods=["POST"])
def create_service_account_key(resource_name):
    """Create a service account key"""
    if not resource_name.startswith("projects/") or "/serviceAccounts/" not in resource_name:
        return error_response(400, "INVALID_ARGUMENT", "Invalid resource name")
    
    sa = ServiceAccount.query.filter_by(id=resource_name).first()
    if not sa:
        return error_response(404, "NOT_FOUND", f"Service account {resource_name} not found")
    
    data = request.get_json() or {}
    private_key_type = data.get("privateKeyType", "TYPE_GOOGLE_CREDENTIALS_FILE")
    
    # Generate key ID
    key_id = secrets.token_hex(20)
    key_name = f"{resource_name}/keys/{key_id}"
    
    # Generate mock JSON key file
    json_key = {
        "type": "service_account",
        "project_id": sa.project_id,
        "private_key_id": key_id,
        "private_key": f"-----BEGIN PRIVATE KEY-----\n{secrets.token_urlsafe(512)}\n-----END PRIVATE KEY-----\n",
        "client_email": sa.email,
        "client_id": sa.unique_id,
        "auth_uri": "http://localhost:8080/o/oauth2/auth",
        "token_uri": "http://localhost:8080/token",
        "auth_provider_x509_cert_url": "http://localhost:8080/oauth2/v1/certs",
    }
    
    key = ServiceAccountKey(
        id=key_name,
        service_account_id=sa.id,
        name=key_name,
        private_key_type=private_key_type,
        private_key_data=base64.b64encode(json.dumps(json_key).encode()).decode(),
    )
    
    db.session.add(key)
    db.session.commit()
    
    return jsonify(key.to_dict(include_private=True)), 201


@iam_bp.route("/v1/<path:resource_name>/keys", methods=["GET"])
def list_service_account_keys(resource_name):
    """List service account keys"""
    if not resource_name.startswith("projects/") or "/serviceAccounts/" not in resource_name:
        return error_response(400, "INVALID_ARGUMENT", "Invalid resource name")
    
    sa = ServiceAccount.query.filter_by(id=resource_name).first()
    if not sa:
        return error_response(404, "NOT_FOUND", f"Service account {resource_name} not found")
    
    return jsonify({
        "keys": [key.to_dict() for key in sa.keys]
    })


@iam_bp.route("/v1/<path:key_name>", methods=["DELETE"])
def delete_service_account_key(key_name):
    """Delete a service account key"""
    if "/keys/" not in key_name:
        return error_response(400, "INVALID_ARGUMENT", "Invalid key name")
    
    key = ServiceAccountKey.query.filter_by(id=key_name).first()
    if not key:
        return error_response(404, "NOT_FOUND", f"Key {key_name} not found")
    
    db.session.delete(key)
    db.session.commit()
    
    return "", 204


# ========== IAM Policies ==========

@iam_bp.route("/v1/<path:resource_path>:getIamPolicy", methods=["POST", "GET"])
def get_iam_policy(resource_path):
    """Get IAM policy for a resource"""
    # Parse resource type and ID
    resource_type, resource_id = parse_resource_path(resource_path)
    
    policy = IamPolicy.query.filter_by(
        resource_type=resource_type,
        resource_id=resource_id
    ).first()
    
    if not policy:
        # Return empty policy
        return jsonify({
            "version": 1,
            "bindings": [],
            "etag": "",
        })
    
    return jsonify(policy.to_dict())


@iam_bp.route("/v1/<path:resource_path>:setIamPolicy", methods=["POST"])
def set_iam_policy(resource_path):
    """Set IAM policy for a resource"""
    data = request.get_json()
    new_policy_data = data.get("policy", {})
    
    # Parse resource type and ID
    resource_type, resource_id = parse_resource_path(resource_path)
    
    policy = IamPolicy.query.filter_by(
        resource_type=resource_type,
        resource_id=resource_id
    ).first()
    
    if not policy:
        policy = IamPolicy(
            resource_type=resource_type,
            resource_id=resource_id,
        )
        db.session.add(policy)
    
    policy.version = new_policy_data.get("version", 1)
    policy.bindings = new_policy_data.get("bindings", [])
    policy.etag = secrets.token_hex(8)
    
    db.session.commit()
    
    return jsonify(policy.to_dict())


@iam_bp.route("/v1/<path:resource_path>:testIamPermissions", methods=["POST"])
def test_iam_permissions(resource_path):
    """Test which permissions the caller has on a resource"""
    data = request.get_json()
    permissions = data.get("permissions", [])
    
    # In emulator mode, grant all permissions by default
    # In real implementation, this would check actual IAM policies
    
    return jsonify({
        "permissions": permissions  # Grant all requested permissions
    })


def parse_resource_path(path: str) -> tuple:
    """Parse resource path into type and ID"""
    if path.startswith("projects/"):
        if "/buckets/" in path:
            parts = path.split("/buckets/")
            return "bucket", parts[1]
        elif "/instances/" in path:
            parts = path.split("/instances/")
            return "instance", parts[1]
        else:
            # Project itself
            project_id = path.replace("projects/", "").split("/")[0]
            return "project", project_id
    
    return "unknown", path
