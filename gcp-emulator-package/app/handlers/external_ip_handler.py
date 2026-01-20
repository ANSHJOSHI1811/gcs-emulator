"""
External IP Address Handler

Handles address (external IP) operations:
- Reserve static external IPs
- Release external IPs
- List addresses
- Get address details
- Add/delete access configs (attach/detach external IPs to instances)
"""

from flask import jsonify, request
from app.factory import db
from app.models.vpc import Address, NetworkInterface, Network, Subnetwork
from app.models.compute import Instance
from app.services.external_ip_service import ExternalIPPoolService
import uuid


def reserve_address(project, region):
    """
    Reserve a static external IP address.
    
    POST /compute/v1/projects/{project}/regions/{region}/addresses
    
    Request body:
    {
        "name": "my-static-ip",
        "address": "34.123.45.67"  # optional, auto-assigned if omitted
        "description": "My static IP",  # optional
        "networkTier": "PREMIUM"  # optional, PREMIUM or STANDARD
    }
    """
    data = request.get_json() or {}
    
    # Validate required fields
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Field "name" is required'}), 400
    
    # Optional fields
    address = data.get('address')
    description = data.get('description')
    network_tier = data.get('networkTier', 'PREMIUM')
    
    # Validate network tier
    if network_tier not in ['PREMIUM', 'STANDARD']:
        return jsonify({'error': 'Invalid networkTier. Must be PREMIUM or STANDARD'}), 400
    
    try:
        # Allocate the static IP
        address_obj = ExternalIPPoolService.allocate_static_ip(
            project_id=project,
            region=region,
            name=name,
            network_tier=network_tier,
            address=address,
            description=description
        )
        
        return jsonify(address_obj.to_dict(project)), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to reserve address: {str(e)}'}), 500


def list_addresses(project, region):
    """
    List all static external IP addresses in a region.
    
    GET /compute/v1/projects/{project}/regions/{region}/addresses
    """
    addresses = Address.query.filter_by(
        project_id=project,
        region=region
    ).all()
    
    return jsonify({
        'items': [addr.to_dict(project) for addr in addresses],
        'kind': 'compute#addressList'
    }), 200


def get_address(project, region, address):
    """
    Get details of a specific static external IP address.
    
    GET /compute/v1/projects/{project}/regions/{region}/addresses/{address}
    """
    addr_obj = Address.query.filter_by(
        project_id=project,
        region=region,
        name=address
    ).first()
    
    if not addr_obj:
        return jsonify({
            'error': f"Address '{address}' not found in region '{region}'"
        }), 404
    
    return jsonify(addr_obj.to_dict(project)), 200


def delete_address(project, region, address):
    """
    Delete (release) a static external IP address.
    
    DELETE /compute/v1/projects/{project}/regions/{region}/addresses/{address}
    """
    addr_obj = Address.query.filter_by(
        project_id=project,
        region=region,
        name=address
    ).first()
    
    if not addr_obj:
        return jsonify({
            'error': f"Address '{address}' not found in region '{region}'"
        }), 404
    
    try:
        # Check if address is in use
        if addr_obj.status == 'IN_USE':
            return jsonify({
                'error': f"Address '{address}' is currently in use and cannot be deleted"
            }), 400
        
        ExternalIPPoolService.release_static_ip(addr_obj)
        
        return jsonify({
            'kind': 'compute#operation',
            'operationType': 'delete',
            'status': 'DONE'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to delete address: {str(e)}'}), 500


def add_access_config(project, zone, instance_name):
    """
    Add an external IP (access config) to an instance's network interface.
    
    POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/addAccessConfig
    
    Request body:
    {
        "name": "External NAT",  # Name for the access config
        "type": "ONE_TO_ONE_NAT",  # Always ONE_TO_ONE_NAT for now
        "natIP": "34.123.45.67",  # Optional: specific static IP to use
        "networkTier": "PREMIUM",  # Optional
        "networkInterface": "nic0"  # Optional, defaults to nic0
    }
    """
    data = request.get_json() or {}
    
    # Get the instance
    instance = Instance.query.filter_by(name=instance_name, zone=zone).first()
    if not instance:
        return jsonify({'error': f"Instance '{instance_name}' not found"}), 404
    
    # Get network interface (default to nic0)
    nic_name = data.get('networkInterface', 'nic0')
    network_interface = NetworkInterface.query.filter_by(
        instance_id=instance.id,
        name=nic_name
    ).first()
    
    if not network_interface:
        return jsonify({'error': f"Network interface '{nic_name}' not found on instance"}), 404
    
    # Check if interface already has an external IP
    # In simplified version, we'll store this in the instance model
    if instance.external_ip:
        return jsonify({'error': 'Instance already has an external IP'}), 400
    
    # Get access config details
    nat_ip = data.get('natIP')
    network_tier = data.get('networkTier', 'PREMIUM')
    access_config_name = data.get('name', 'External NAT')
    
    try:
        # Determine region from zone
        region = '-'.join(zone.split('-')[:-1])
        
        if nat_ip:
            # User specified a static IP - find it
            addr_obj = Address.query.filter_by(
                project_id=project,
                region=region,
                address=nat_ip
            ).first()
            
            if not addr_obj:
                return jsonify({'error': f"Static IP '{nat_ip}' not found in region"}), 404
            
            if addr_obj.status == 'IN_USE':
                return jsonify({'error': f"Static IP '{nat_ip}' is already in use"}), 400
            
            # Mark the static IP as in use
            ExternalIPPoolService.mark_in_use(addr_obj, instance.id, network_interface.id)
            external_ip = nat_ip
        else:
            # Allocate ephemeral IP
            external_ip = ExternalIPPoolService.allocate_ephemeral_ip(
                project_id=project,
                region=region,
                network_tier=network_tier
            )
        
        # Update instance with external IP
        instance.external_ip = external_ip
        db.session.commit()
        
        return jsonify({
            'kind': 'compute#operation',
            'operationType': 'addAccessConfig',
            'status': 'DONE',
            'natIP': external_ip
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to add access config: {str(e)}'}), 500


def delete_access_config(project, zone, instance_name):
    """
    Remove an external IP (access config) from an instance's network interface.
    
    POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/deleteAccessConfig
    
    Request parameters:
    - accessConfig: Name of the access config to delete (default "External NAT")
    - networkInterface: Name of the network interface (default "nic0")
    """
    # Get query parameters
    access_config_name = request.args.get('accessConfig', 'External NAT')
    nic_name = request.args.get('networkInterface', 'nic0')
    
    # Get the instance
    instance = Instance.query.filter_by(name=instance_name, zone=zone).first()
    if not instance:
        return jsonify({'error': f"Instance '{instance_name}' not found"}), 404
    
    # Check if instance has an external IP
    if not instance.external_ip:
        return jsonify({'error': 'Instance does not have an external IP'}), 400
    
    try:
        # Determine region from zone
        region = '-'.join(zone.split('-')[:-1])
        
        # Check if this is a static IP
        addr_obj = Address.query.filter_by(
            project_id=project,
            address=instance.external_ip
        ).first()
        
        if addr_obj:
            # It's a static IP - mark as RESERVED (not in use)
            ExternalIPPoolService.mark_reserved(addr_obj)
        
        # Note: Ephemeral IPs are just removed, no tracking needed
        
        # Remove external IP from instance
        instance.external_ip = None
        db.session.commit()
        
        return jsonify({
            'kind': 'compute#operation',
            'operationType': 'deleteAccessConfig',
            'status': 'DONE'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete access config: {str(e)}'}), 500


def list_addresses_aggregated(project):
    """
    List all addresses across all regions (aggregated list).
    
    GET /compute/v1/projects/{project}/aggregated/addresses
    """
    addresses = Address.query.filter_by(project_id=project).all()
    
    # Group by region
    items_by_region = {}
    for addr in addresses:
        region_key = f"regions/{addr.region}"
        if region_key not in items_by_region:
            items_by_region[region_key] = {
                'addresses': []
            }
        items_by_region[region_key]['addresses'].append(addr.to_dict(project))
    
    return jsonify({
        'items': items_by_region,
        'kind': 'compute#addressAggregatedList'
    }), 200
