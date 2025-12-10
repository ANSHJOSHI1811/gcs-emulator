"""PHASE 1: Compute Routes Blueprint"""
from flask import Blueprint
from app.handlers.compute_handler import ComputeHandler


def create_compute_blueprint(compute_service) -> Blueprint:
    """Create and configure the Compute blueprint for PHASE 1"""
    compute_bp = Blueprint('compute', __name__, url_prefix='/compute')
    handler = ComputeHandler(compute_service)
    
    # POST /compute/instances - Create instance
    compute_bp.add_url_rule(
        '/instances',
        view_func=handler.run_instance,
        methods=['POST']
    )
    
    # GET /compute/instances - List instances
    compute_bp.add_url_rule(
        '/instances',
        view_func=handler.describe_instances,
        methods=['GET']
    )
    
    # GET /compute/instances/<instance_id> - Get single instance
    compute_bp.add_url_rule(
        '/instances/<instance_id>',
        view_func=handler.get_instance,
        methods=['GET']
    )
    
    # POST /compute/instances/<instance_id>/stop - Stop instance
    compute_bp.add_url_rule(
        '/instances/<instance_id>/stop',
        view_func=handler.stop_instance,
        methods=['POST']
    )
    
    # POST /compute/instances/<instance_id>/terminate - Terminate instance
    compute_bp.add_url_rule(
        '/instances/<instance_id>/terminate',
        view_func=handler.terminate_instance,
        methods=['POST']
    )
    
    return compute_bp
