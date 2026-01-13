"""
Subnetwork Routes - VPC Subnet API Endpoints

GCP-compatible endpoints:
- POST   /compute/v1/projects/{project}/regions/{region}/subnetworks
- GET    /compute/v1/projects/{project}/regions/{region}/subnetworks
- GET    /compute/v1/projects/{project}/regions/{region}/subnetworks/{subnetwork}
- DELETE /compute/v1/projects/{project}/regions/{region}/subnetworks/{subnetwork}
- POST   /compute/v1/projects/{project}/regions/{region}/subnetworks/{subnetwork}/expandIpCidrRange
- PATCH  /compute/v1/projects/{project}/regions/{region}/subnetworks/{subnetwork}
- GET    /compute/v1/projects/{project}/aggregated/subnetworks (list all)
"""

from flask import Blueprint
from app.handlers import subnet_handler

subnet_bp = Blueprint("subnetworks", __name__)


@subnet_bp.route("/compute/v1/projects/<project_id>/regions/<region>/subnetworks", methods=["POST"])
def create_subnet(project_id: str, region: str):
    """Create a new subnetwork"""
    return subnet_handler.create_subnetwork(project_id, region)


@subnet_bp.route("/compute/v1/projects/<project_id>/regions/<region>/subnetworks", methods=["GET"])
def list_subnets_in_region(project_id: str, region: str):
    """List subnetworks in a specific region"""
    return subnet_handler.list_subnetworks(project_id, region)


@subnet_bp.route("/compute/v1/projects/<project_id>/aggregated/subnetworks", methods=["GET"])
def list_all_subnets(project_id: str):
    """List all subnetworks across all regions"""
    return subnet_handler.list_subnetworks(project_id)


@subnet_bp.route("/compute/v1/projects/<project_id>/regions/<region>/subnetworks/<subnet_name>", methods=["GET"])
def get_subnet(project_id: str, region: str, subnet_name: str):
    """Get details of a specific subnetwork"""
    return subnet_handler.get_subnetwork(project_id, region, subnet_name)


@subnet_bp.route("/compute/v1/projects/<project_id>/regions/<region>/subnetworks/<subnet_name>", methods=["DELETE"])
def delete_subnet(project_id: str, region: str, subnet_name: str):
    """Delete a subnetwork"""
    return subnet_handler.delete_subnetwork(project_id, region, subnet_name)


@subnet_bp.route("/compute/v1/projects/<project_id>/regions/<region>/subnetworks/<subnet_name>/expandIpCidrRange", methods=["POST"])
def expand_subnet(project_id: str, region: str, subnet_name: str):
    """Expand the IP CIDR range of a subnetwork"""
    return subnet_handler.expand_subnetwork(project_id, region, subnet_name)


@subnet_bp.route("/compute/v1/projects/<project_id>/regions/<region>/subnetworks/<subnet_name>", methods=["PATCH"])
def patch_subnet(project_id: str, region: str, subnet_name: str):
    """Update subnetwork properties"""
    return subnet_handler.patch_subnetwork(project_id, region, subnet_name)
