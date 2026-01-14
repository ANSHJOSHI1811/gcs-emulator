"""
Network Handler - VPC Network Management

Handles:
- Create VPC network (custom/auto mode)
- List VPC networks
- Get VPC network details
- Delete VPC network
- Update VPC network
- Default network creation
"""

from flask import jsonify, request
from sqlalchemy.exc import IntegrityError
from app.factory import db
from app.models.vpc import Network, Subnetwork, FirewallRule, FirewallAllowedDenied
from app.validators.vpc_validators import validate_network_config
from app.utils.ip_utils import get_auto_subnet_range
from app.utils.operation_utils import create_operation
from app.models.compute import Zone
import uuid
import docker
import ipaddress


def create_network(project_id):
    """
    Create a new VPC network
    
    POST /compute/v1/projects/{project}/global/networks
    """
    try:
        data = request.get_json() or {}
        
        # Extract network configuration
        name = data.get('name')
        description = data.get('description', '')
        auto_create_subnetworks = data.get('autoCreateSubnetworks', False)
        routing_mode = data.get('routingConfig', {}).get('routingMode', 'REGIONAL')
        mtu = data.get('mtu', 1460)
        
        # Validate network configuration
        is_valid, error = validate_network_config(name, routing_mode, mtu, auto_create_subnetworks)
        if not is_valid:
            return jsonify({'error': {'message': error}}), 400
        
        # Check if network already exists
        existing = Network.query.filter_by(project_id=project_id, name=name).first()
        if existing:
            return jsonify({
                'error': {
                    'message': f'Network {name} already exists in project {project_id}'
                }
            }), 409
        
        # Create network
        network = Network(
            id=uuid.uuid4(),
            name=name,
            project_id=project_id,
            description=description,
            auto_create_subnetworks=auto_create_subnetworks,
            routing_mode=routing_mode,
            mtu=mtu
        )
        
        db.session.add(network)
        db.session.flush()  # Get network ID
        
        # If auto mode, create subnets in all regions
        if auto_create_subnetworks:
            _create_auto_subnets(network.id, project_id)
        
        # Create Docker network for VPC (for container networking)
        # Use first subnet's CIDR if available, otherwise use default
        subnet_cidr = None
        if auto_create_subnetworks:
            # Get first subnet for Docker network CIDR
            first_subnet = Subnetwork.query.filter_by(network_id=network.id).first()
            if first_subnet:
                subnet_cidr = first_subnet.ip_cidr_range
        
        docker_net_id, docker_net_name = _create_docker_network_for_vpc(name, project_id, subnet_cidr)
        if docker_net_id:
            network.docker_network_id = docker_net_id
            network.docker_network_name = docker_net_name
        
        # Create default firewall rules
        _create_default_firewall_rules(network.id, project_id)
        
        db.session.commit()
        
        # Create operation
        operation = create_operation(
            project_id=project_id,
            operation_type='insert',
            target_link=f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/global/networks/{name}",
            target_id=str(network.id)
        )
        
        return jsonify(operation.to_dict()), 200
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'error': {'message': f'Database error: {str(e)}'}}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': {'message': str(e)}}), 500


def list_networks(project_id):
    """
    List all VPC networks in a project
    
    GET /compute/v1/projects/{project}/global/networks
    """
    try:
        networks = Network.query.filter_by(project_id=project_id).all()
        
        return jsonify({
            'kind': 'compute#networkList',
            'items': [net.to_dict(project_id) for net in networks],
            'selfLink': f'http://127.0.0.1:8080/compute/v1/projects/{project_id}/global/networks'
        }), 200
        
    except Exception as e:
        return jsonify({'error': {'message': str(e)}}), 500


def get_network(project_id, network_name):
    """
    Get VPC network details
    
    GET /compute/v1/projects/{project}/global/networks/{network}
    """
    try:
        network = Network.query.filter_by(project_id=project_id, name=network_name).first()
        
        if not network:
            return jsonify({
                'error': {
                    'message': f'Network {network_name} not found'
                }
            }), 404
        
        return jsonify(network.to_dict(project_id)), 200
        
    except Exception as e:
        return jsonify({'error': {'message': str(e)}}), 500


def delete_network(project_id, network_name):
    """
    Delete a VPC network
    
    DELETE /compute/v1/projects/{project}/global/networks/{network}
    """
    try:
        network = Network.query.filter_by(project_id=project_id, name=network_name).first()
        
        if not network:
            return jsonify({
                'error': {
                    'message': f'Network {network_name} not found'
                }
            }), 404
        
        # Delete associated Docker network
        if network.docker_network_id:
            _delete_docker_network(network.docker_network_id, network.docker_network_name)
        
        # Check if network is in use by instances
        from app.models.compute import Instance
        network_url = f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/global/networks/{network_name}"
        instances_using_network = Instance.query.filter_by(network_url=network_url).count()
        
        if instances_using_network > 0:
            return jsonify({
                'error': {
                    'message': f'Cannot delete network {network_name}: {instances_using_network} instances are using it'
                }
            }), 400
        
        # Delete network (cascade will delete subnets, firewall rules, routes)
        db.session.delete(network)
        db.session.commit()
        
        # Create operation
        operation = create_operation(
            project_id=project_id,
            operation_type='delete',
            target_link=f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/global/networks/{network_name}",
            target_id=str(network.id)
        )
        
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': {'message': str(e)}}), 500


def update_network(project_id, network_name):
    """
    Update VPC network configuration
    
    PATCH /compute/v1/projects/{project}/global/networks/{network}
    """
    try:
        network = Network.query.filter_by(project_id=project_id, name=network_name).first()
        
        if not network:
            return jsonify({
                'error': {
                    'message': f'Network {network_name} not found'
                }
            }), 404
        
        data = request.get_json() or {}
        
        # Update allowed fields
        if 'routingConfig' in data:
            routing_mode = data['routingConfig'].get('routingMode')
            if routing_mode and routing_mode in ['REGIONAL', 'GLOBAL']:
                network.routing_mode = routing_mode
        
        if 'mtu' in data:
            mtu = data['mtu']
            if mtu in [1460, 1500]:
                network.mtu = mtu
        
        if 'description' in data:
            network.description = data['description']
        
        db.session.commit()
        
        return jsonify(network.to_dict(project_id)), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': {'message': str(e)}}), 500


def _create_auto_subnets(network_id, project_id):
    """
    Create subnets automatically for all regions
    
    Internal helper function for auto-mode networks
    """
    # Get all regions from zones
    zones = Zone.query.all()
    regions = list(set([zone.region for zone in zones if zone.region]))
    
    for region in regions:
        cidr = get_auto_subnet_range(region)
        if not cidr:
            continue
        
        # Calculate gateway (first IP + 1)
        from app.utils.ip_utils import calculate_gateway
        gateway = calculate_gateway(cidr)
        
        subnet = Subnetwork(
            id=uuid.uuid4(),
            name=f'{project_id}-{region}',
            network_id=network_id,
            region=region,
            ip_cidr_range=cidr,
            gateway_address=gateway,
            private_ip_google_access=True
        )
        db.session.add(subnet)


def _create_default_firewall_rules(network_id, project_id):
    """
    Create default firewall rules for a network
    
    Rules created:
    - default-allow-internal (Allow all traffic within network)
    - default-allow-ssh (Allow SSH from anywhere)
    - default-allow-rdp (Allow RDP from anywhere)  
    - default-allow-icmp (Allow ICMP from anywhere)
    """
    # Get network for name
    network = Network.query.get(network_id)
    network_name = network.name
    
    # Rule 1: Allow internal traffic (all protocols within 10.128.0.0/9)
    rule_internal = FirewallRule(
        id=uuid.uuid4(),
        name=f'{network_name}-allow-internal',
        network_id=network_id,
        description='Allow internal traffic on the network',
        priority=65534,
        direction='INGRESS',
        action='ALLOW',
        source_ranges=['10.128.0.0/9']
    )
    db.session.add(rule_internal)
    db.session.flush()
    
    # Add allowed protocols for internal rule (all)
    protocol_internal = FirewallAllowedDenied(
        id=uuid.uuid4(),
        firewall_rule_id=rule_internal.id,
        ip_protocol='all'
    )
    db.session.add(protocol_internal)
    
    # Rule 2: Allow SSH (tcp:22)
    rule_ssh = FirewallRule(
        id=uuid.uuid4(),
        name=f'{network_name}-allow-ssh',
        network_id=network_id,
        description='Allow SSH from anywhere',
        priority=65534,
        direction='INGRESS',
        action='ALLOW',
        source_ranges=['0.0.0.0/0']
    )
    db.session.add(rule_ssh)
    db.session.flush()
    
    protocol_ssh = FirewallAllowedDenied(
        id=uuid.uuid4(),
        firewall_rule_id=rule_ssh.id,
        ip_protocol='tcp',
        ports=['22']
    )
    db.session.add(protocol_ssh)
    
    # Rule 3: Allow RDP (tcp:3389)
    rule_rdp = FirewallRule(
        id=uuid.uuid4(),
        name=f'{network_name}-allow-rdp',
        network_id=network_id,
        description='Allow RDP from anywhere',
        priority=65534,
        direction='INGRESS',
        action='ALLOW',
        source_ranges=['0.0.0.0/0']
    )
    db.session.add(rule_rdp)
    db.session.flush()
    
    protocol_rdp = FirewallAllowedDenied(
        id=uuid.uuid4(),
        firewall_rule_id=rule_rdp.id,
        ip_protocol='tcp',
        ports=['3389']
    )
    db.session.add(protocol_rdp)
    
    # Rule 4: Allow ICMP
    rule_icmp = FirewallRule(
        id=uuid.uuid4(),
        name=f'{network_name}-allow-icmp',
        network_id=network_id,
        description='Allow ICMP from anywhere',
        priority=65534,
        direction='INGRESS',
        action='ALLOW',
        source_ranges=['0.0.0.0/0']
    )
    db.session.add(rule_icmp)
    db.session.flush()
    
    protocol_icmp = FirewallAllowedDenied(
        id=uuid.uuid4(),
        firewall_rule_id=rule_icmp.id,
        ip_protocol='icmp'
    )
    db.session.add(protocol_icmp)


def create_default_network(project_id):
    """
    Create default network for a project
    
    Called automatically when a project is created
    """
    try:
        # Check if default network exists
        existing = Network.query.filter_by(project_id=project_id, name='default').first()
        if existing:
            return existing
        
        # Create default network in auto mode
        network = Network(
            id=uuid.uuid4(),
            name='default',
            project_id=project_id,
            description='Default network for the project',
            auto_create_subnetworks=True,
            routing_mode='REGIONAL',
            mtu=1460
        )
        
        db.session.add(network)
        db.session.flush()
        
        # Create auto subnets
        _create_auto_subnets(network.id, project_id)
        
        # Create default firewall rules
        _create_default_firewall_rules(network.id, project_id)
        
        db.session.commit()
        
        return network
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating default network: {str(e)}")
        return None
