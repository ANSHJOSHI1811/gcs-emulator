"""
GCP Compute Engine API v1 Routes
SDK-compatible REST endpoints matching official Compute Engine API
"""
from flask import Blueprint
from app.handlers.compute_v1_handler import ComputeV1Handler


def create_compute_v1_blueprint(compute_service) -> Blueprint:
    """
    Create GCP Compute Engine API v1 blueprint
    URL pattern: /compute/v1/projects/{project}/zones/{zone}/...
    """
    compute_v1_bp = Blueprint('compute_v1', __name__, url_prefix='/compute/v1')
    handler = ComputeV1Handler(compute_service)
    
    # POST /compute/v1/projects/{project}/zones/{zone}/instances
    # SDK: InstancesClient.insert(project, zone, instance_resource)
    compute_v1_bp.add_url_rule(
        '/projects/<project>/zones/<zone>/instances',
        view_func=handler.insert_instance,
        methods=['POST']
    )
    
    # GET /compute/v1/projects/{project}/zones/{zone}/instances
    # SDK: InstancesClient.list(project, zone)
    compute_v1_bp.add_url_rule(
        '/projects/<project>/zones/<zone>/instances',
        view_func=handler.list_instances,
        methods=['GET']
    )
    
    # GET /compute/v1/projects/{project}/zones/{zone}/instances/{instance}
    # SDK: InstancesClient.get(project, zone, instance)
    compute_v1_bp.add_url_rule(
        '/projects/<project>/zones/<zone>/instances/<instance_name>',
        view_func=handler.get_instance,
        methods=['GET']
    )
    
    # DELETE /compute/v1/projects/{project}/zones/{zone}/instances/{instance}
    # SDK: InstancesClient.delete(project, zone, instance)
    compute_v1_bp.add_url_rule(
        '/projects/<project>/zones/<zone>/instances/<instance_name>',
        view_func=handler.delete_instance,
        methods=['DELETE']
    )
    
    # POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/start
    # SDK: InstancesClient.start(project, zone, instance)
    compute_v1_bp.add_url_rule(
        '/projects/<project>/zones/<zone>/instances/<instance_name>/start',
        view_func=handler.start_instance,
        methods=['POST']
    )
    
    # POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/stop
    # SDK: InstancesClient.stop(project, zone, instance)
    compute_v1_bp.add_url_rule(
        '/projects/<project>/zones/<zone>/instances/<instance_name>/stop',
        view_func=handler.stop_instance,
        methods=['POST']
    )
    
    # GET /compute/v1/projects/{project}/zones/{zone}/operations/{operation}
    # SDK: ZoneOperationsClient.get(project, zone, operation)
    compute_v1_bp.add_url_rule(
        '/projects/<project>/zones/<zone>/operations/<operation_name>',
        view_func=handler.get_operation,
        methods=['GET']
    )
    
    return compute_v1_bp
