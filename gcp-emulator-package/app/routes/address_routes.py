"""
Address Routes - External IP address operations

Routes for:
- Reserve static external IPs
- List addresses
- Get address details
- Delete addresses
- Add/delete access configs on instances
"""

from flask import Blueprint
from app.handlers import external_ip_handler

addresses_bp = Blueprint("addresses", __name__)


# Regional address operations
@addresses_bp.route("/compute/v1/projects/<project>/regions/<region>/addresses", methods=["POST"])
def reserve_address(project, region):
    """Reserve a static external IP address"""
    return external_ip_handler.reserve_address(project, region)


@addresses_bp.route("/compute/v1/projects/<project>/regions/<region>/addresses", methods=["GET"])
def list_addresses(project, region):
    """List addresses in a region"""
    return external_ip_handler.list_addresses(project, region)


@addresses_bp.route("/compute/v1/projects/<project>/regions/<region>/addresses/<address>", methods=["GET"])
def get_address(project, region, address):
    """Get address details"""
    return external_ip_handler.get_address(project, region, address)


@addresses_bp.route("/compute/v1/projects/<project>/regions/<region>/addresses/<address>", methods=["DELETE"])
def delete_address(project, region, address):
    """Delete a static external IP address"""
    return external_ip_handler.delete_address(project, region, address)


# Aggregated addresses
@addresses_bp.route("/compute/v1/projects/<project>/aggregated/addresses", methods=["GET"])
def list_addresses_aggregated(project):
    """List addresses across all regions"""
    return external_ip_handler.list_addresses_aggregated(project)


# Access config operations (attach/detach external IPs to instances)
@addresses_bp.route("/compute/v1/projects/<project>/zones/<zone>/instances/<instance>/addAccessConfig", methods=["POST"])
def add_access_config(project, zone, instance):
    """Add external IP to instance network interface"""
    return external_ip_handler.add_access_config(project, zone, instance)


@addresses_bp.route("/compute/v1/projects/<project>/zones/<zone>/instances/<instance>/deleteAccessConfig", methods=["POST"])
def delete_access_config(project, zone, instance):
    """Remove external IP from instance network interface"""
    return external_ip_handler.delete_access_config(project, zone, instance)
