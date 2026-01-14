"""
VPN Handler - VPN Gateway and Tunnel operations

Simplified VPN implementation for emulator (metadata only).
"""

from flask import request, jsonify
from app.models.vpc import Network
from app.models.router import Router
from app.models.vpn import VPNGateway, VPNTunnel
from app.factory import db
from app.utils.operation_utils import create_operation
import uuid
import random


def generate_vpn_ip():
    """Generate a fake VPN gateway IP (35.x.x.x range)"""
    return f"35.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


# ==================== VPN Gateway Operations ====================

def create_vpn_gateway(project_id: str, region: str):
    """
    Create a VPN gateway
    
    Request body:
    {
        "name": "vpn-gateway-1",
        "network": "projects/{project}/global/networks/{network}",
        "description": "VPN gateway for on-prem connectivity"
    }
    """
    try:
        data = request.get_json()
        
        if not data or "name" not in data or "network" not in data:
            return jsonify({
                "error": {"message": "VPN gateway name and network are required"}
            }), 400
        
        name = data["name"]
        network_url = data["network"]
        
        # Validate name
        if not name or len(name) > 63:
            return jsonify({
                "error": {"message": "VPN gateway name must be 1-63 characters"}
            }), 400
        
        # Extract network name from URL
        network_name = network_url.split('/')[-1]
        
        # Find network
        network = Network.query.filter_by(
            project_id=project_id,
            name=network_name
        ).first()
        
        if not network:
            return jsonify({
                "error": {"message": f"Network '{network_name}' not found"}
            }), 404
        
        # Check if gateway already exists
        existing = VPNGateway.query.filter_by(
            project_id=project_id,
            region=region,
            name=name
        ).first()
        
        if existing:
            return jsonify({
                "error": {"message": f"VPN gateway '{name}' already exists in region '{region}'"}
            }), 409
        
        # Create VPN gateway
        gateway = VPNGateway(
            id=str(uuid.uuid4()),
            name=name,
            project_id=project_id,
            region=region,
            network_id=network.id,
            description=data.get('description'),
            vpn_gateway_type='CLASSIC',
            vpn_interface_0_ip_address=generate_vpn_ip(),
            status='READY'
        )
        
        db.session.add(gateway)
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='insert',
            target_link=gateway.get_self_link(project_id),
            target_id=str(gateway.id),
            region=region
        )
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": f"Failed to create VPN gateway: {str(e)}"}
        }), 500


def list_vpn_gateways(project_id: str, region: str):
    """List VPN gateways in a region"""
    try:
        gateways = VPNGateway.query.filter_by(
            project_id=project_id,
            region=region
        ).all()
        
        items = [gateway.to_dict(project_id) for gateway in gateways]
        
        response = {
            "kind": "compute#vpnGatewayList",
            "id": f"projects/{project_id}/regions/{region}/vpnGateways",
            "items": items
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "error": {"message": f"Failed to list VPN gateways: {str(e)}"}
        }), 500


def get_vpn_gateway(project_id: str, region: str, gateway_name: str):
    """Get a specific VPN gateway"""
    try:
        gateway = VPNGateway.query.filter_by(
            project_id=project_id,
            region=region,
            name=gateway_name
        ).first()
        
        if not gateway:
            return jsonify({
                "error": {"message": f"VPN gateway '{gateway_name}' not found"}
            }), 404
        
        return jsonify(gateway.to_dict(project_id)), 200
        
    except Exception as e:
        return jsonify({
            "error": {"message": f"Failed to get VPN gateway: {str(e)}"}
        }), 500


def delete_vpn_gateway(project_id: str, region: str, gateway_name: str):
    """Delete a VPN gateway"""
    try:
        gateway = VPNGateway.query.filter_by(
            project_id=project_id,
            region=region,
            name=gateway_name
        ).first()
        
        if not gateway:
            return jsonify({
                "error": {"message": f"VPN gateway '{gateway_name}' not found"}
            }), 404
        
        # Check for tunnels
        tunnels = VPNTunnel.query.filter_by(vpn_gateway_id=gateway.id).all()
        if tunnels:
            return jsonify({
                "error": {"message": f"Cannot delete VPN gateway with {len(tunnels)} active tunnel(s)"}
            }), 400
        
        db.session.delete(gateway)
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='delete',
            target_link=gateway.get_self_link(project_id),
            target_id=str(gateway.id),
            region=region
        )
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": f"Failed to delete VPN gateway: {str(e)}"}
        }), 500


# ==================== VPN Tunnel Operations ====================

def create_vpn_tunnel(project_id: str, region: str):
    """
    Create a VPN tunnel
    
    Request body:
    {
        "name": "vpn-tunnel-1",
        "targetVpnGateway": "projects/{project}/regions/{region}/vpnGateways/{gateway}",
        "peerIp": "203.0.113.1",
        "sharedSecret": "secret123",
        "ikeVersion": 2,
        "localTrafficSelector": ["10.128.0.0/20"],
        "remoteTrafficSelector": ["192.168.0.0/16"]
    }
    """
    try:
        data = request.get_json()
        
        if not data or "name" not in data:
            return jsonify({
                "error": {"message": "VPN tunnel name is required"}
            }), 400
        
        name = data["name"]
        
        # Validate name
        if not name or len(name) > 63:
            return jsonify({
                "error": {"message": "VPN tunnel name must be 1-63 characters"}
            }), 400
        
        # Validate required fields
        if "targetVpnGateway" not in data:
            return jsonify({
                "error": {"message": "targetVpnGateway is required"}
            }), 400
        
        if "peerIp" not in data:
            return jsonify({
                "error": {"message": "peerIp is required"}
            }), 400
        
        if "sharedSecret" not in data:
            return jsonify({
                "error": {"message": "sharedSecret is required"}
            }), 400
        
        # Extract gateway name from URL
        gateway_url = data["targetVpnGateway"]
        gateway_name = gateway_url.split('/')[-1]
        
        # Find VPN gateway
        gateway = VPNGateway.query.filter_by(
            project_id=project_id,
            region=region,
            name=gateway_name
        ).first()
        
        if not gateway:
            return jsonify({
                "error": {"message": f"VPN gateway '{gateway_name}' not found"}
            }), 404
        
        # Check if tunnel already exists
        existing = VPNTunnel.query.filter_by(
            project_id=project_id,
            region=region,
            name=name
        ).first()
        
        if existing:
            return jsonify({
                "error": {"message": f"VPN tunnel '{name}' already exists"}
            }), 409
        
        # Optional router
        router_id = None
        if "router" in data:
            router_url = data["router"]
            router_name = router_url.split('/')[-1]
            router = Router.query.filter_by(region=region, name=router_name).first()
            if router:
                router_id = router.id
        
        # Create VPN tunnel
        tunnel = VPNTunnel(
            id=str(uuid.uuid4()),
            name=name,
            project_id=project_id,
            region=region,
            vpn_gateway_id=gateway.id,
            peer_ip=data["peerIp"],
            peer_external_gateway=data.get("peerExternalGateway"),
            router_id=router_id,
            ike_version=data.get("ikeVersion", 2),
            shared_secret=data["sharedSecret"],
            local_traffic_selector=data.get("localTrafficSelector", []),
            remote_traffic_selector=data.get("remoteTrafficSelector", []),
            description=data.get("description"),
            status='ESTABLISHED',
            detailed_status='Tunnel is up and passing traffic.'
        )
        
        db.session.add(tunnel)
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='insert',
            target_link=tunnel.get_self_link(project_id),
            target_id=str(tunnel.id),
            region=region
        )
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": f"Failed to create VPN tunnel: {str(e)}"}
        }), 500


def list_vpn_tunnels(project_id: str, region: str):
    """List VPN tunnels in a region"""
    try:
        tunnels = VPNTunnel.query.filter_by(
            project_id=project_id,
            region=region
        ).all()
        
        items = [tunnel.to_dict(project_id) for tunnel in tunnels]
        
        response = {
            "kind": "compute#vpnTunnelList",
            "id": f"projects/{project_id}/regions/{region}/vpnTunnels",
            "items": items
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "error": {"message": f"Failed to list VPN tunnels: {str(e)}"}
        }), 500


def get_vpn_tunnel(project_id: str, region: str, tunnel_name: str):
    """Get a specific VPN tunnel"""
    try:
        tunnel = VPNTunnel.query.filter_by(
            project_id=project_id,
            region=region,
            name=tunnel_name
        ).first()
        
        if not tunnel:
            return jsonify({
                "error": {"message": f"VPN tunnel '{tunnel_name}' not found"}
            }), 404
        
        return jsonify(tunnel.to_dict(project_id)), 200
        
    except Exception as e:
        return jsonify({
            "error": {"message": f"Failed to get VPN tunnel: {str(e)}"}
        }), 500


def delete_vpn_tunnel(project_id: str, region: str, tunnel_name: str):
    """Delete a VPN tunnel"""
    try:
        tunnel = VPNTunnel.query.filter_by(
            project_id=project_id,
            region=region,
            name=tunnel_name
        ).first()
        
        if not tunnel:
            return jsonify({
                "error": {"message": f"VPN tunnel '{tunnel_name}' not found"}
            }), 404
        
        db.session.delete(tunnel)
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='delete',
            target_link=tunnel.get_self_link(project_id),
            target_id=str(tunnel.id),
            region=region
        )
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": f"Failed to delete VPN tunnel: {str(e)}"}
        }), 500
