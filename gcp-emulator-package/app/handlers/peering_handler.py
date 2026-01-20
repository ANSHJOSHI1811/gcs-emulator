"""
VPC Peering Handler

Handles VPC network peering operations.
"""

from flask import request, jsonify
from app.models.vpc import Network
from app.models.peering import VPCPeering
from app.factory import db
from app.utils.operation_utils import create_operation
import uuid
import re


def add_peering(project_id: str, network_name: str):
    """
    Add a peering connection to a network
    
    Request body:
    {
        "name": "peering-to-network-b",
        "peerNetwork": "projects/peer-project/global/networks/network-b",
        "autoCreateRoutes": true,
        "exchangeSubnetRoutes": true,
        "exportCustomRoutes": false,
        "importCustomRoutes": false
    }
    """
    try:
        data = request.get_json()
        
        if not data or "name" not in data or "peerNetwork" not in data:
            return jsonify({
                "error": {"message": "Peering name and peerNetwork are required"}
            }), 400
        
        peering_name = data["name"]
        peer_network = data["peerNetwork"]
        
        # Validate peering name
        if not peering_name or len(peering_name) > 63:
            return jsonify({
                "error": {"message": "Peering name must be 1-63 characters"}
            }), 400
        
        # Find source network
        network = Network.query.filter_by(
            project_id=project_id,
            name=network_name
        ).first()
        
        if not network:
            return jsonify({
                "error": {"message": f"Network '{network_name}' not found"}
            }), 404
        
        # Parse peer network URL
        # Format: projects/{project}/global/networks/{network}
        peer_pattern = r'projects/([^/]+)/global/networks/([^/]+)'
        match = re.match(peer_pattern, peer_network)
        
        if not match:
            return jsonify({
                "error": {"message": "Invalid peerNetwork format. Expected: projects/{project}/global/networks/{network}"}
            }), 400
        
        peer_project_id = match.group(1)
        peer_network_name = match.group(2)
        
        # Check if peering already exists
        existing_peering = VPCPeering.query.filter_by(
            network_id=network.id,
            name=peering_name
        ).first()
        
        if existing_peering:
            return jsonify({
                "error": {"message": f"Peering '{peering_name}' already exists on network '{network_name}'"}
            }), 409
        
        # Check for duplicate peer network (can't peer same networks twice)
        duplicate_peer = VPCPeering.query.filter_by(
            network_id=network.id,
            peer_network=peer_network
        ).first()
        
        if duplicate_peer:
            return jsonify({
                "error": {"message": f"Network '{network_name}' is already peered with '{peer_network}'"}
            }), 409
        
        # Create peering
        peering = VPCPeering(
            id=str(uuid.uuid4()),
            name=peering_name,
            network_id=network.id,
            peer_network=peer_network,
            peer_project_id=peer_project_id,
            peer_network_name=peer_network_name,
            state='ACTIVE',
            auto_create_routes=data.get('autoCreateRoutes', True),
            exchange_subnet_routes=data.get('exchangeSubnetRoutes', True),
            export_custom_routes=data.get('exportCustomRoutes', False),
            import_custom_routes=data.get('importCustomRoutes', False),
            export_subnet_routes_with_public_ip=data.get('exportSubnetRoutesWithPublicIp', True),
            import_subnet_routes_with_public_ip=data.get('importSubnetRoutesWithPublicIp', False)
        )
        
        db.session.add(peering)
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='addPeering',
            target_link=network.get_self_link(project_id),
            target_id=str(peering.id),
            scope='global'
        )
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": f"Failed to add peering: {str(e)}"}
        }), 500


def remove_peering(project_id: str, network_name: str, peering_name: str):
    """Remove a peering connection from a network"""
    try:
        # Find network
        network = Network.query.filter_by(
            project_id=project_id,
            name=network_name
        ).first()
        
        if not network:
            return jsonify({
                "error": {"message": f"Network '{network_name}' not found"}
            }), 404
        
        # Find peering
        peering = VPCPeering.query.filter_by(
            network_id=network.id,
            name=peering_name
        ).first()
        
        if not peering:
            return jsonify({
                "error": {"message": f"Peering '{peering_name}' not found on network '{network_name}'"}
            }), 404
        
        # Delete peering
        db.session.delete(peering)
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='removePeering',
            target_link=network.get_self_link(project_id),
            target_id=str(peering.id),
            scope='global'
        )
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": f"Failed to remove peering: {str(e)}"}
        }), 500


def list_peerings(project_id: str, network_name: str):
    """List all peering connections for a network"""
    try:
        # Find network
        network = Network.query.filter_by(
            project_id=project_id,
            name=network_name
        ).first()
        
        if not network:
            return jsonify({
                "error": {"message": f"Network '{network_name}' not found"}
            }), 404
        
        # Get all peerings for this network
        peerings = VPCPeering.query.filter_by(network_id=network.id).all()
        
        items = [peering.to_dict(project_id) for peering in peerings]
        
        response = {
            "kind": "compute#peeringList",
            "id": f"projects/{project_id}/global/networks/{network_name}/peerings",
            "items": items
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "error": {"message": f"Failed to list peerings: {str(e)}"}
        }), 500


def get_peering(project_id: str, network_name: str, peering_name: str):
    """Get details of a specific peering connection"""
    try:
        # Find network
        network = Network.query.filter_by(
            project_id=project_id,
            name=network_name
        ).first()
        
        if not network:
            return jsonify({
                "error": {"message": f"Network '{network_name}' not found"}
            }), 404
        
        # Find peering
        peering = VPCPeering.query.filter_by(
            network_id=network.id,
            name=peering_name
        ).first()
        
        if not peering:
            return jsonify({
                "error": {"message": f"Peering '{peering_name}' not found"}
            }), 404
        
        return jsonify(peering.to_dict(project_id)), 200
        
    except Exception as e:
        return jsonify({
            "error": {"message": f"Failed to get peering: {str(e)}"}
        }), 500


def update_peering(project_id: str, network_name: str, peering_name: str):
    """
    Update a peering connection (PATCH)
    
    Can update: exportCustomRoutes, importCustomRoutes,
                exportSubnetRoutesWithPublicIp, importSubnetRoutesWithPublicIp
    """
    try:
        data = request.get_json()
        
        # Find network
        network = Network.query.filter_by(
            project_id=project_id,
            name=network_name
        ).first()
        
        if not network:
            return jsonify({
                "error": {"message": f"Network '{network_name}' not found"}
            }), 404
        
        # Find peering
        peering = VPCPeering.query.filter_by(
            network_id=network.id,
            name=peering_name
        ).first()
        
        if not peering:
            return jsonify({
                "error": {"message": f"Peering '{peering_name}' not found"}
            }), 404
        
        # Update mutable fields
        if "exportCustomRoutes" in data:
            peering.export_custom_routes = data["exportCustomRoutes"]
        
        if "importCustomRoutes" in data:
            peering.import_custom_routes = data["importCustomRoutes"]
        
        if "exportSubnetRoutesWithPublicIp" in data:
            peering.export_subnet_routes_with_public_ip = data["exportSubnetRoutesWithPublicIp"]
        
        if "importSubnetRoutesWithPublicIp" in data:
            peering.import_subnet_routes_with_public_ip = data["importSubnetRoutesWithPublicIp"]
        
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='updatePeering',
            target_link=network.get_self_link(project_id),
            target_id=str(peering.id),
            scope='global'
        )
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": f"Failed to update peering: {str(e)}"}
        }), 500
