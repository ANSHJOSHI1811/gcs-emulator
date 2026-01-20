"""
Network Interface Handler - Manage instance network attachments

Handles:
- Attach network interface to instance
- Detach network interface from instance
- List instance network interfaces
- Update network interface properties
"""

from flask import jsonify, request
from sqlalchemy.exc import IntegrityError
from app.factory import db
from app.models.vpc import Network, Subnetwork, NetworkInterface
from app.models.compute import Instance
from app.services.ip_allocation_service import IPAllocationService
from datetime import datetime
import uuid


def attach_network_interface(project_id: str, zone: str, instance_name: str):
    """
    Attach a network interface to an instance
    
    Request body:
    {
        "network": "projects/PROJECT/global/networks/NETWORK",
        "subnetwork": "projects/PROJECT/regions/REGION/subnetworks/SUBNET",
        "networkIP": "10.128.0.5" (optional - auto-allocated if not provided),
        "name": "nic1" (optional - defaults to nic{N})
    }
    """
    try:
        data = request.get_json()
        
        if not data or "network" not in data:
            return jsonify({"error": {"message": "Network is required"}}), 400
        
        # Find the instance
        instance = Instance.query.filter_by(
            project_id=project_id,
            zone=zone,
            name=instance_name
        ).first()
        
        if not instance:
            return jsonify({"error": {"message": f"Instance '{instance_name}' not found"}}), 404
        
        # Extract network name
        network_url_parts = data["network"].split("/")
        if "networks" in network_url_parts:
            network_name = network_url_parts[network_url_parts.index("networks") + 1]
        else:
            network_name = data["network"]
        
        # Get the network
        network = Network.query.filter_by(
            project_id=project_id,
            name=network_name
        ).first()
        
        if not network:
            return jsonify({"error": {"message": f"Network '{network_name}' not found"}}), 404
        
        # Get subnetwork if specified
        subnetwork = None
        if "subnetwork" in data:
            subnet_url_parts = data["subnetwork"].split("/")
            if "subnetworks" in subnet_url_parts:
                subnet_name = subnet_url_parts[subnet_url_parts.index("subnetworks") + 1]
            else:
                subnet_name = data["subnetwork"]
            
            # Extract region from zone (e.g., us-central1-a -> us-central1)
            region = "-".join(zone.split("-")[:-1])
            
            subnetwork = Subnetwork.query.filter_by(
                network_id=network.id,
                region=region,
                name=subnet_name
            ).first()
            
            if not subnetwork:
                return jsonify({"error": {"message": f"Subnetwork '{subnet_name}' not found in region '{region}'"}}), 404
        else:
            # Auto-select subnet in instance's region
            region = "-".join(zone.split("-")[:-1])
            subnetwork = Subnetwork.query.filter_by(
                network_id=network.id,
                region=region
            ).first()
            
            if not subnetwork:
                return jsonify({"error": {"message": f"No subnetwork found for network '{network_name}' in region '{region}'"}}), 404
        
        # Determine NIC index
        existing_nics = NetworkInterface.query.filter_by(
            instance_id=instance.id
        ).count()
        
        nic_index = existing_nics
        nic_name = data.get("name", f"nic{nic_index}")
        
        # Allocate IP address
        if "networkIP" in data:
            # User specified IP
            requested_ip = data["networkIP"]
            success, error = IPAllocationService.allocate_specific_ip(subnetwork, requested_ip)
            if not success:
                return jsonify({"error": {"message": error}}), 400
            network_ip = requested_ip
        else:
            # Auto-allocate IP
            network_ip = IPAllocationService.allocate_ip(subnetwork)
            if not network_ip:
                return jsonify({"error": {"message": f"No available IPs in subnet '{subnetwork.name}'"}}), 503
        
        # Create network interface
        interface = NetworkInterface(
            id=uuid.uuid4(),
            instance_id=instance.id,
            network_id=network.id,
            subnetwork_id=subnetwork.id,
            name=nic_name,
            network_ip=network_ip,
            network_tier=data.get("networkTier", "PREMIUM"),
            nic_index=nic_index,
            creation_timestamp=datetime.utcnow()
        )
        
        db.session.add(interface)
        db.session.commit()
        
        return jsonify({
            "kind": "compute#operation",
            "operationType": "addNetworkInterface",
            "status": "DONE",
            "targetLink": f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/zones/{zone}/instances/{instance_name}",
            "networkInterface": interface.to_dict(project_id)
        }), 200
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": {"message": f"Network interface already exists or constraint violation: {str(e)}"}}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"message": f"Failed to attach network interface: {str(e)}"}}), 500


def detach_network_interface(project_id: str, zone: str, instance_name: str):
    """
    Detach a network interface from an instance
    
    Query parameters:
    - networkInterface: Name of the network interface (e.g., "nic1")
    """
    try:
        nic_name = request.args.get('networkInterface')
        if not nic_name:
            return jsonify({"error": {"message": "networkInterface parameter is required"}}), 400
        
        # Find the instance
        instance = Instance.query.filter_by(
            project_id=project_id,
            zone=zone,
            name=instance_name
        ).first()
        
        if not instance:
            return jsonify({"error": {"message": f"Instance '{instance_name}' not found"}}), 404
        
        # Find the network interface
        interface = NetworkInterface.query.filter_by(
            instance_id=instance.id,
            name=nic_name
        ).first()
        
        if not interface:
            return jsonify({"error": {"message": f"Network interface '{nic_name}' not found"}}), 404
        
        # Cannot detach nic0 (primary interface)
        if interface.nic_index == 0:
            return jsonify({"error": {"message": "Cannot detach primary network interface (nic0)"}}), 400
        
        # Delete the interface (IP will be released)
        db.session.delete(interface)
        db.session.commit()
        
        return jsonify({
            "kind": "compute#operation",
            "operationType": "removeNetworkInterface",
            "status": "DONE",
            "targetLink": f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/zones/{zone}/instances/{instance_name}"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"message": f"Failed to detach network interface: {str(e)}"}}), 500


def list_network_interfaces(project_id: str, zone: str, instance_name: str):
    """
    List all network interfaces for an instance
    """
    try:
        # Find the instance
        instance = Instance.query.filter_by(
            project_id=project_id,
            zone=zone,
            name=instance_name
        ).first()
        
        if not instance:
            return jsonify({"error": {"message": f"Instance '{instance_name}' not found"}}), 404
        
        # Get all network interfaces
        interfaces = NetworkInterface.query.filter_by(
            instance_id=instance.id
        ).order_by(NetworkInterface.nic_index).all()
        
        return jsonify({
            "kind": "compute#networkInterfaceList",
            "items": [interface.to_dict(project_id) for interface in interfaces]
        }), 200
        
    except Exception as e:
        return jsonify({"error": {"message": f"Failed to list network interfaces: {str(e)}"}}), 500


def get_network_interface(project_id: str, zone: str, instance_name: str, interface_name: str):
    """
    Get details of a specific network interface
    """
    try:
        # Find the instance
        instance = Instance.query.filter_by(
            project_id=project_id,
            zone=zone,
            name=instance_name
        ).first()
        
        if not instance:
            return jsonify({"error": {"message": f"Instance '{instance_name}' not found"}}), 404
        
        # Find the network interface
        interface = NetworkInterface.query.filter_by(
            instance_id=instance.id,
            name=interface_name
        ).first()
        
        if not interface:
            return jsonify({"error": {"message": f"Network interface '{interface_name}' not found"}}), 404
        
        return jsonify(interface.to_dict(project_id)), 200
        
    except Exception as e:
        return jsonify({"error": {"message": f"Failed to get network interface: {str(e)}"}}), 500


def create_default_network_interface(instance: Instance, project_id: str) -> Optional[NetworkInterface]:
    """
    Create default network interface for an instance
    
    Args:
        instance: Instance object
        project_id: GCP project ID
        
    Returns:
        NetworkInterface object or None if failed
    """
    try:
        # Get default network (try "default" first, fallback to "auto-network")
        network = Network.query.filter_by(
            project_id=project_id,
            name="default"
        ).first()
        
        if not network:
            network = Network.query.filter_by(
                project_id=project_id,
                name="auto-network"
            ).first()
        
        if not network:
            print(f"No default or auto-network found for project {project_id}")
            return None
        
        # Get zone region
        zone = instance.zone
        region = "-".join(zone.split("-")[:-1])
        
        # Get subnet in instance's region
        subnetwork = Subnetwork.query.filter_by(
            network_id=network.id,
            region=region
        ).first()
        
        if not subnetwork:
            print(f"No subnet found for default network in region {region}")
            return None
        
        # Allocate IP
        network_ip = IPAllocationService.allocate_ip(subnetwork)
        if not network_ip:
            print(f"No available IPs in subnet {subnetwork.name}")
            return None
        
        # Create interface
        interface = NetworkInterface(
            id=uuid.uuid4(),
            instance_id=instance.id,
            network_id=network.id,
            subnetwork_id=subnetwork.id,
            name="nic0",
            network_ip=network_ip,
            network_tier="PREMIUM",
            nic_index=0,
            creation_timestamp=datetime.utcnow()
        )
        
        db.session.add(interface)
        db.session.commit()
        
        return interface
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating default network interface: {e}")
        return None
