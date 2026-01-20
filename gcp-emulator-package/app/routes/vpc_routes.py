"""
VPC Routes - URL routing for VPC networks and subnetworks.
Implements GCP Compute Engine API v1 URL structure.
"""
from flask import Blueprint
from app.handlers.vpc_handler import VPCHandler, SubnetHandler
from app.services.vpc_service import VPCService
from app.services.subnet_service import SubnetService


def create_vpc_routes(db_session) -> Blueprint:
    """
    Create and configure VPC routes.
    Called from factory.py during app initialization.
    
    Args:
        db_session: SQLAlchemy database session
        
    Returns:
        Configured VPC blueprint
    """
    # Create blueprint
    vpc_bp = Blueprint('vpc', __name__)
    
    # Initialize services
    subnet_service = SubnetService(db_session)
    vpc_service = VPCService(db_session)
    
    # Initialize handlers
    vpc_handler = VPCHandler(vpc_service)
    subnet_handler = SubnetHandler(subnet_service, vpc_service)
    
    # Networks endpoints
    # List networks: GET /compute/v1/projects/{project}/global/networks
    vpc_bp.add_url_rule(
        '/compute/v1/projects/<project_id>/global/networks',
        endpoint='list_networks',
        view_func=lambda project_id: vpc_handler.list_networks(project_id),
        methods=['GET']
    )
    
    # Get network: GET /compute/v1/projects/{project}/global/networks/{network}
    vpc_bp.add_url_rule(
        '/compute/v1/projects/<project_id>/global/networks/<network_name>',
        endpoint='get_network',
        view_func=lambda project_id, network_name: vpc_handler.get_network(project_id, network_name),
        methods=['GET']
    )
    
    # Create network: POST /compute/v1/projects/{project}/global/networks
    vpc_bp.add_url_rule(
        '/compute/v1/projects/<project_id>/global/networks',
        endpoint='create_network',
        view_func=lambda project_id: vpc_handler.create_network(project_id),
        methods=['POST']
    )
    
    # Delete network: DELETE /compute/v1/projects/{project}/global/networks/{network}
    vpc_bp.add_url_rule(
        '/compute/v1/projects/<project_id>/global/networks/<network_name>',
        endpoint='delete_network',
        view_func=lambda project_id, network_name: vpc_handler.delete_network(project_id, network_name),
        methods=['DELETE']
    )
    
    # Subnetworks endpoints
    # List subnets: GET /compute/v1/projects/{project}/regions/{region}/subnetworks
    vpc_bp.add_url_rule(
        '/compute/v1/projects/<project_id>/regions/<region>/subnetworks',
        endpoint='list_subnetworks',
        view_func=lambda project_id, region: subnet_handler.list_subnetworks(project_id, region),
        methods=['GET']
    )
    
    # Get subnet: GET /compute/v1/projects/{project}/regions/{region}/subnetworks/{subnetwork}
    vpc_bp.add_url_rule(
        '/compute/v1/projects/<project_id>/regions/<region>/subnetworks/<subnetwork_name>',
        endpoint='get_subnetwork',
        view_func=lambda project_id, region, subnetwork_name: subnet_handler.get_subnetwork(project_id, region, subnetwork_name),
        methods=['GET']
    )
    
    # Create subnet: POST /compute/v1/projects/{project}/regions/{region}/subnetworks
    vpc_bp.add_url_rule(
        '/compute/v1/projects/<project_id>/regions/<region>/subnetworks',
        endpoint='create_subnetwork',
        view_func=lambda project_id, region: subnet_handler.create_subnetwork(project_id, region),
        methods=['POST']
    )
    
    # Delete subnet: DELETE /compute/v1/projects/{project}/regions/{region}/subnetworks/{subnetwork}
    vpc_bp.add_url_rule(
        '/compute/v1/projects/<project_id>/regions/<region>/subnetworks/<subnetwork_name>',
        endpoint='delete_subnetwork',
        view_func=lambda project_id, region, subnetwork_name: subnet_handler.delete_subnetwork(project_id, region, subnetwork_name),
        methods=['DELETE']
    )
    
    return vpc_bp
