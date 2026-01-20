"""
Router Routes - Cloud Router and Cloud NAT endpoints
"""

from flask import Blueprint
from app.handlers import router_handler, nat_handler

router_bp = Blueprint('router', __name__)


# Cloud Router endpoints
@router_bp.route('/compute/v1/projects/<project_id>/regions/<region>/routers', methods=['POST'])
def create_router(project_id, region):
    """Create a Cloud Router"""
    return router_handler.create_router(project_id, region)


@router_bp.route('/compute/v1/projects/<project_id>/regions/<region>/routers', methods=['GET'])
def list_routers(project_id, region):
    """List Cloud Routers in a region"""
    return router_handler.list_routers(project_id, region)


@router_bp.route('/compute/v1/projects/<project_id>/regions/<region>/routers/<router_name>', methods=['GET'])
def get_router(project_id, region, router_name):
    """Get a specific Cloud Router"""
    return router_handler.get_router(project_id, region, router_name)


@router_bp.route('/compute/v1/projects/<project_id>/regions/<region>/routers/<router_name>', methods=['PATCH'])
def update_router(project_id, region, router_name):
    """Update a Cloud Router"""
    return router_handler.update_router(project_id, region, router_name)


@router_bp.route('/compute/v1/projects/<project_id>/regions/<region>/routers/<router_name>', methods=['DELETE'])
def delete_router(project_id, region, router_name):
    """Delete a Cloud Router"""
    return router_handler.delete_router(project_id, region, router_name)


# Cloud NAT endpoints
@router_bp.route('/compute/v1/projects/<project_id>/regions/<region>/routers/<router_name>/nats', methods=['POST'])
def create_nat(project_id, region, router_name):
    """Create a Cloud NAT configuration on a router"""
    return nat_handler.create_nat(project_id, region, router_name)


@router_bp.route('/compute/v1/projects/<project_id>/regions/<region>/routers/<router_name>/nats', methods=['GET'])
def list_nats(project_id, region, router_name):
    """List Cloud NAT configurations on a router"""
    return nat_handler.list_nats(project_id, region, router_name)


@router_bp.route('/compute/v1/projects/<project_id>/regions/<region>/routers/<router_name>/nats/<nat_name>', methods=['GET'])
def get_nat(project_id, region, router_name, nat_name):
    """Get a specific Cloud NAT configuration"""
    return nat_handler.get_nat(project_id, region, router_name, nat_name)


@router_bp.route('/compute/v1/projects/<project_id>/regions/<region>/routers/<router_name>/nats/<nat_name>', methods=['PATCH'])
def update_nat(project_id, region, router_name, nat_name):
    """Update a Cloud NAT configuration"""
    return nat_handler.update_nat(project_id, region, router_name, nat_name)


@router_bp.route('/compute/v1/projects/<project_id>/regions/<region>/routers/<router_name>/nats/<nat_name>', methods=['DELETE'])
def delete_nat(project_id, region, router_name, nat_name):
    """Delete a Cloud NAT configuration"""
    return nat_handler.delete_nat(project_id, region, router_name, nat_name)
