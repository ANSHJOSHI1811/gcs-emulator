"""
Compute routes - Router stage (HTTP → Endpoint mapping)
Phase 2: Maps HTTP methods and paths to compute handler functions
Phase 5: Added firewall rules endpoints
Following GCE API v1 URL patterns
"""
from flask import Blueprint, jsonify
from app.handlers.compute_handler import (
    handle_create_instance,
    handle_list_instances,
    handle_get_instance,
    handle_start_instance,
    handle_stop_instance,
    handle_delete_instance,
    handle_get_serial_port_output
)
from app.handlers.firewall_handler import FirewallHandler
from app.models.compute import MachineType

compute_bp = Blueprint("compute", __name__)


# ============================================================================
# Instance Routes (Phase 2: Full lifecycle)
# ============================================================================

@compute_bp.route("/v1/projects/<project_id>/zones/<zone>/instances", methods=["POST"])
def create_instance(project_id, zone):
    """
    Create a new compute instance
    
    POST /compute/v1/projects/{project}/zones/{zone}/instances
    """
    return handle_create_instance(project_id, zone)


@compute_bp.route("/v1/projects/<project_id>/zones/<zone>/instances", methods=["GET"])
def list_instances(project_id, zone):
    """
    List all instances in a zone
    
    GET /compute/v1/projects/{project}/zones/{zone}/instances
    """
    return handle_list_instances(project_id, zone)


@compute_bp.route("/v1/projects/<project_id>/zones/<zone>/instances/<instance_name>", methods=["GET"])
def get_instance(project_id, zone, instance_name):
    """
    Get instance details
    
    GET /compute/v1/projects/{project}/zones/{zone}/instances/{instance}
    """
    return handle_get_instance(project_id, zone, instance_name)


@compute_bp.route("/v1/projects/<project_id>/zones/<zone>/instances/<instance_name>/start", methods=["POST"])
def start_instance(project_id, zone, instance_name):
    """
    Start a terminated instance
    
    POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/start
    """
    return handle_start_instance(project_id, zone, instance_name)


@compute_bp.route("/v1/projects/<project_id>/zones/<zone>/instances/<instance_name>/stop", methods=["POST"])
def stop_instance(project_id, zone, instance_name):
    """
    Stop a running instance
    
    POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/stop
    """
    return handle_stop_instance(project_id, zone, instance_name)


@compute_bp.route("/v1/projects/<project_id>/zones/<zone>/instances/<instance_name>", methods=["DELETE"])
def delete_instance(project_id, zone, instance_name):
    """
    Delete an instance
    
    DELETE /compute/v1/projects/{project}/zones/{zone}/instances/{instance}
    """
    return handle_delete_instance(project_id, zone, instance_name)


@compute_bp.route("/v1/projects/<project_id>/zones/<zone>/instances/<instance_name>/serialPort", methods=["GET"])
def get_serial_port_output(project_id, zone, instance_name):
    """
    Get serial port output for an instance
    
    GET /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/serialPort
    """
    return handle_get_serial_port_output(project_id, zone, instance_name)


# ============================================================================
# Machine Type Routes (Read-only catalog)
# ============================================================================

@compute_bp.route("/v1/projects/<project_id>/zones/<zone>/machineTypes", methods=["GET"])
def list_machine_types(project_id, zone):
    """
    List available machine types
    
    GET /compute/v1/projects/{project}/zones/{zone}/machineTypes
    """
    machine_types = MachineType.get_all()
    items = [
        MachineType.to_gce_format(mt_name, project_id, zone)
        for mt_name in machine_types.keys()
    ]
    
    response = {
        "kind": "compute#machineTypeList",
        "id": f"projects/{project_id}/zones/{zone}/machineTypes",
        "items": items,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project_id}/zones/{zone}/machineTypes"
    }
    
    return jsonify(response), 200


@compute_bp.route("/v1/projects/<project_id>/zones/<zone>/machineTypes/<machine_type>", methods=["GET"])
def get_machine_type(project_id, zone, machine_type):
    """
    Get specific machine type details
    
    GET /compute/v1/projects/{project}/zones/{zone}/machineTypes/{machineType}
    """
    if not MachineType.is_valid(machine_type):
        return jsonify({
            "error": {
                "code": 404,
                "message": f"Machine type '{machine_type}' not found"
            }
        }), 404
    
    mt_details = MachineType.to_gce_format(machine_type, project_id, zone)
    return jsonify(mt_details), 200


# ============================================================================
# Firewall Rules Routes (Phase 5)
# ============================================================================

@compute_bp.route("/v1/projects/<project_id>/global/firewalls", methods=["POST"])
def create_firewall_rule(project_id):
    """
    Create a new firewall rule
    
    POST /compute/v1/projects/{project}/global/firewalls
    """
    return FirewallHandler.create_firewall_rule(project_id)


@compute_bp.route("/v1/projects/<project_id>/global/firewalls", methods=["GET"])
def list_firewall_rules(project_id):
    """
    List all firewall rules in a project
    
    GET /compute/v1/projects/{project}/global/firewalls
    """
    return FirewallHandler.list_firewall_rules(project_id)


@compute_bp.route("/v1/projects/<project_id>/global/firewalls/<firewall_name>", methods=["GET"])
def get_firewall_rule(project_id, firewall_name):
    """
    Get a specific firewall rule
    
    GET /compute/v1/projects/{project}/global/firewalls/{firewall}
    """
    return FirewallHandler.get_firewall_rule(project_id, firewall_name)


@compute_bp.route("/v1/projects/<project_id>/global/firewalls/<firewall_name>", methods=["DELETE"])
def delete_firewall_rule(project_id, firewall_name):
    """
    Delete a firewall rule
    
    DELETE /compute/v1/projects/{project}/global/firewalls/{firewall}
    """
    return FirewallHandler.delete_firewall_rule(project_id, firewall_name)


# ============================================================================
# Health Check
# ============================================================================

@compute_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint
    
    GET /compute/health
    """
    return jsonify({
        "service": "compute-engine",
        "status": "healthy",
        "phase": "5 - Networking System",
        "features": [
            "Create instance (PROVISIONING → STAGING → RUNNING)",
            "List instances",
            "Get instance",
            "Start instance (TERMINATED → STAGING → RUNNING)",
            "Stop instance (RUNNING → STOPPING → TERMINATED)",
            "Delete instance (force stop if RUNNING)",
            "Machine type catalog",
            "Internal IP allocation (10.0.0.0/16)",
            "External IP allocation (203.0.113.0/24)",
            "Firewall rules (ALLOW/DENY, INGRESS/EGRESS)",
            "Network metadata in instance responses"
        ]
    }), 200
