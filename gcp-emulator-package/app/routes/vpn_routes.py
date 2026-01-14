"""
VPN Routes - VPN Gateway and Tunnel endpoints
"""

from flask import Blueprint
from app.handlers import vpn_handler

vpn_bp = Blueprint('vpn', __name__)


# VPN Gateway endpoints
@vpn_bp.route('/compute/v1/projects/<project_id>/regions/<region>/vpnGateways', methods=['POST'])
def create_vpn_gateway(project_id, region):
    """Create a VPN gateway"""
    return vpn_handler.create_vpn_gateway(project_id, region)


@vpn_bp.route('/compute/v1/projects/<project_id>/regions/<region>/vpnGateways', methods=['GET'])
def list_vpn_gateways(project_id, region):
    """List VPN gateways in a region"""
    return vpn_handler.list_vpn_gateways(project_id, region)


@vpn_bp.route('/compute/v1/projects/<project_id>/regions/<region>/vpnGateways/<gateway_name>', methods=['GET'])
def get_vpn_gateway(project_id, region, gateway_name):
    """Get a specific VPN gateway"""
    return vpn_handler.get_vpn_gateway(project_id, region, gateway_name)


@vpn_bp.route('/compute/v1/projects/<project_id>/regions/<region>/vpnGateways/<gateway_name>', methods=['DELETE'])
def delete_vpn_gateway(project_id, region, gateway_name):
    """Delete a VPN gateway"""
    return vpn_handler.delete_vpn_gateway(project_id, region, gateway_name)


# VPN Tunnel endpoints
@vpn_bp.route('/compute/v1/projects/<project_id>/regions/<region>/vpnTunnels', methods=['POST'])
def create_vpn_tunnel(project_id, region):
    """Create a VPN tunnel"""
    return vpn_handler.create_vpn_tunnel(project_id, region)


@vpn_bp.route('/compute/v1/projects/<project_id>/regions/<region>/vpnTunnels', methods=['GET'])
def list_vpn_tunnels(project_id, region):
    """List VPN tunnels in a region"""
    return vpn_handler.list_vpn_tunnels(project_id, region)


@vpn_bp.route('/compute/v1/projects/<project_id>/regions/<region>/vpnTunnels/<tunnel_name>', methods=['GET'])
def get_vpn_tunnel(project_id, region, tunnel_name):
    """Get a specific VPN tunnel"""
    return vpn_handler.get_vpn_tunnel(project_id, region, tunnel_name)


@vpn_bp.route('/compute/v1/projects/<project_id>/regions/<region>/vpnTunnels/<tunnel_name>', methods=['DELETE'])
def delete_vpn_tunnel(project_id, region, tunnel_name):
    """Delete a VPN tunnel"""
    return vpn_handler.delete_vpn_tunnel(project_id, region, tunnel_name)
