"""
Route Routes Blueprint - VPC Route Management Endpoints

Endpoints:
- POST   /compute/v1/projects/{project}/global/routes
- GET    /compute/v1/projects/{project}/global/routes
- GET    /compute/v1/projects/{project}/global/routes/{route}
- DELETE /compute/v1/projects/{project}/global/routes/{route}
- PUT    /compute/v1/projects/{project}/global/routes/{route}
- PATCH  /compute/v1/projects/{project}/global/routes/{route}
"""

from flask import Blueprint
from app.handlers import route_handler

route_bp = Blueprint('routes', __name__)


@route_bp.route('/compute/v1/projects/<project_id>/global/routes', methods=['POST'])
def create_route(project_id):
    """Create a new route"""
    return route_handler.create_route(project_id)


@route_bp.route('/compute/v1/projects/<project_id>/global/routes', methods=['GET'])
def list_routes(project_id):
    """List all routes in project"""
    return route_handler.list_routes(project_id)


@route_bp.route('/compute/v1/projects/<project_id>/global/routes/<route_name>', methods=['GET'])
def get_route(project_id, route_name):
    """Get specific route details"""
    return route_handler.get_route(project_id, route_name)


@route_bp.route('/compute/v1/projects/<project_id>/global/routes/<route_name>', methods=['DELETE'])
def delete_route(project_id, route_name):
    """Delete a route"""
    return route_handler.delete_route(project_id, route_name)


@route_bp.route('/compute/v1/projects/<project_id>/global/routes/<route_name>', methods=['PUT'])
def update_route(project_id, route_name):
    """Update route (full update)"""
    return route_handler.update_route(project_id, route_name)


@route_bp.route('/compute/v1/projects/<project_id>/global/routes/<route_name>', methods=['PATCH'])
def patch_route(project_id, route_name):
    """Partially update route"""
    return route_handler.patch_route(project_id, route_name)
