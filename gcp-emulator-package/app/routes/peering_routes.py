"""
Peering Routes - VPC Network Peering endpoints
"""

from flask import Blueprint
from app.handlers import peering_handler

peering_bp = Blueprint('peering', __name__)


@peering_bp.route('/compute/v1/projects/<project_id>/global/networks/<network_name>/addPeering', methods=['POST'])
def add_peering(project_id, network_name):
    """Add a peering connection to a network"""
    return peering_handler.add_peering(project_id, network_name)


@peering_bp.route('/compute/v1/projects/<project_id>/global/networks/<network_name>/removePeering', methods=['POST'])
def remove_peering(project_id, network_name):
    """Remove a peering connection from a network"""
    # Peering name should be in request body
    from flask import request
    data = request.get_json()
    peering_name = data.get('name') if data else None
    
    if not peering_name:
        from flask import jsonify
        return jsonify({"error": {"message": "Peering name required in request body"}}), 400
    
    return peering_handler.remove_peering(project_id, network_name, peering_name)


@peering_bp.route('/compute/v1/projects/<project_id>/global/networks/<network_name>/peerings', methods=['GET'])
def list_peerings(project_id, network_name):
    """List all peering connections for a network"""
    return peering_handler.list_peerings(project_id, network_name)


@peering_bp.route('/compute/v1/projects/<project_id>/global/networks/<network_name>/peerings/<peering_name>', methods=['GET'])
def get_peering(project_id, network_name, peering_name):
    """Get a specific peering connection"""
    return peering_handler.get_peering(project_id, network_name, peering_name)


@peering_bp.route('/compute/v1/projects/<project_id>/global/networks/<network_name>/peerings/<peering_name>', methods=['PATCH'])
def update_peering(project_id, network_name, peering_name):
    """Update a peering connection"""
    return peering_handler.update_peering(project_id, network_name, peering_name)
