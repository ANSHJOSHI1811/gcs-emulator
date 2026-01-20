"""
VPC Network Routes - HTTP endpoint mapping

Maps HTTP methods and paths to network handler functions
"""

from flask import Blueprint
from app.handlers import network_handler

# Create blueprint for VPC network routes
network_bp = Blueprint('networks', __name__)


# VPC Networks
@network_bp.route('/compute/v1/projects/<project_id>/global/networks', methods=['POST'])
def create_network_route(project_id):
    """Create a VPC network"""
    return network_handler.create_network(project_id)


@network_bp.route('/compute/v1/projects/<project_id>/global/networks', methods=['GET'])
def list_networks_route(project_id):
    """List all VPC networks"""
    return network_handler.list_networks(project_id)


@network_bp.route('/compute/v1/projects/<project_id>/global/networks/<network_name>', methods=['GET'])
def get_network_route(project_id, network_name):
    """Get VPC network details"""
    return network_handler.get_network(project_id, network_name)


@network_bp.route('/compute/v1/projects/<project_id>/global/networks/<network_name>', methods=['DELETE'])
def delete_network_route(project_id, network_name):
    """Delete a VPC network"""
    return network_handler.delete_network(project_id, network_name)


@network_bp.route('/compute/v1/projects/<project_id>/global/networks/<network_name>', methods=['PATCH'])
def update_network_route(project_id, network_name):
    """Update VPC network configuration"""
    return network_handler.update_network(project_id, network_name)
