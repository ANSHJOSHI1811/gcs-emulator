"""
Firewall Routes - VPC Firewall Rule API Endpoints

GCP-compatible endpoints:
- POST   /compute/v1/projects/{project}/global/firewalls
- GET    /compute/v1/projects/{project}/global/firewalls
- GET    /compute/v1/projects/{project}/global/firewalls/{firewall}
- DELETE /compute/v1/projects/{project}/global/firewalls/{firewall}
- PUT    /compute/v1/projects/{project}/global/firewalls/{firewall}
- PATCH  /compute/v1/projects/{project}/global/firewalls/{firewall}
"""

from flask import Blueprint
from app.handlers import firewall_handler

firewall_bp = Blueprint("firewalls", __name__)


@firewall_bp.route("/compute/v1/projects/<project_id>/global/firewalls", methods=["POST"])
def create_firewall(project_id: str):
    """Create a new firewall rule"""
    return firewall_handler.create_firewall_rule(project_id)


@firewall_bp.route("/compute/v1/projects/<project_id>/global/firewalls", methods=["GET"])
def list_firewalls(project_id: str):
    """List firewall rules"""
    return firewall_handler.list_firewall_rules(project_id)


@firewall_bp.route("/compute/v1/projects/<project_id>/global/firewalls/<firewall_name>", methods=["GET"])
def get_firewall(project_id: str, firewall_name: str):
    """Get details of a specific firewall rule"""
    return firewall_handler.get_firewall_rule(project_id, firewall_name)


@firewall_bp.route("/compute/v1/projects/<project_id>/global/firewalls/<firewall_name>", methods=["DELETE"])
def delete_firewall(project_id: str, firewall_name: str):
    """Delete a firewall rule"""
    return firewall_handler.delete_firewall_rule(project_id, firewall_name)


@firewall_bp.route("/compute/v1/projects/<project_id>/global/firewalls/<firewall_name>", methods=["PUT"])
def update_firewall(project_id: str, firewall_name: str):
    """Update a firewall rule"""
    return firewall_handler.update_firewall_rule(project_id, firewall_name)


@firewall_bp.route("/compute/v1/projects/<project_id>/global/firewalls/<firewall_name>", methods=["PATCH"])
def patch_firewall(project_id: str, firewall_name: str):
    """Patch a firewall rule"""
    return firewall_handler.patch_firewall_rule(project_id, firewall_name)
