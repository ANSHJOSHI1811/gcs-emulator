"""
VPC Handlers - HTTP request handlers for VPC networks and subnetworks.
Implements GCP Compute Engine API v1 endpoints.
"""
import logging
from flask import jsonify, request
from app.services.vpc_service import VPCService
from app.services.subnet_service import SubnetService

logger = logging.getLogger(__name__)


class VPCHandler:
    """
    Handles VPC network API requests.
    Endpoints: /compute/v1/projects/{project}/global/networks
    """
    
    def __init__(self, vpc_service: VPCService):
        self.vpc_service = vpc_service
    
    def list_networks(self, project_id: str):
        """
        List VPC networks in a project.
        GET /compute/v1/projects/{project}/global/networks
        """
        try:
            networks = self.vpc_service.list_networks(project_id)
            
            return jsonify({
                'kind': 'compute#networkList',
                'id': f'projects/{project_id}/global/networks',
                'items': [net.to_dict() for net in networks],
                'selfLink': f'projects/{project_id}/global/networks'
            }), 200
        except Exception as e:
            logger.error(f"Error listing networks: {e}", exc_info=True)
            return jsonify({
                'error': {
                    'code': 500,
                    'message': str(e)
                }
            }), 500
    
    def get_network(self, project_id: str, network_name: str):
        """
        Get a specific VPC network.
        GET /compute/v1/projects/{project}/global/networks/{network}
        """
        try:
            network = self.vpc_service.get_network(project_id, network_name)
            
            if not network:
                return jsonify({
                    'error': {
                        'code': 404,
                        'message': f"Network '{network_name}' not found"
                    }
                }), 404
            
            return jsonify(network.to_dict()), 200
        except Exception as e:
            logger.error(f"Error getting network: {e}", exc_info=True)
            return jsonify({
                'error': {
                    'code': 500,
                    'message': str(e)
                }
            }), 500
    
    def create_network(self, project_id: str):
        """
        Create a new VPC network.
        POST /compute/v1/projects/{project}/global/networks
        """
        try:
            data = request.get_json()
            
            if not data or 'name' not in data:
                return jsonify({
                    'error': {
                        'code': 400,
                        'message': 'Missing required field: name'
                    }
                }), 400
            
            name = data['name']
            auto_create = data.get('autoCreateSubnetworks', False)
            description = data.get('description', '')
            routing_mode = data.get('routingConfig', {}).get('routingMode', 'REGIONAL')
            mtu = data.get('mtu', 1460)
            
            network = self.vpc_service.create_network(
                project_id=project_id,
                name=name,
                auto_create_subnetworks=auto_create,
                description=description,
                routing_mode=routing_mode,
                mtu=mtu
            )
            
            return jsonify({
                'kind': 'compute#operation',
                'operationType': 'insert',
                'status': 'DONE',
                'targetLink': f'projects/{project_id}/global/networks/{name}',
                'insertTime': network.created_at.isoformat() + 'Z'
            }), 200
        except ValueError as e:
            return jsonify({
                'error': {
                    'code': 409,
                    'message': str(e)
                }
            }), 409
        except Exception as e:
            logger.error(f"Error creating network: {e}", exc_info=True)
            return jsonify({
                'error': {
                    'code': 500,
                    'message': str(e)
                }
            }), 500
    
    def delete_network(self, project_id: str, network_name: str):
        """
        Delete a VPC network.
        DELETE /compute/v1/projects/{project}/global/networks/{network}
        """
        try:
            success = self.vpc_service.delete_network(project_id, network_name)
            
            if not success:
                return jsonify({
                    'error': {
                        'code': 404,
                        'message': f"Network '{network_name}' not found"
                    }
                }), 404
            
            return jsonify({
                'kind': 'compute#operation',
                'operationType': 'delete',
                'status': 'DONE',
                'targetLink': f'projects/{project_id}/global/networks/{network_name}'
            }), 200
        except ValueError as e:
            return jsonify({
                'error': {
                    'code': 400,
                    'message': str(e)
                }
            }), 400
        except Exception as e:
            logger.error(f"Error deleting network: {e}", exc_info=True)
            return jsonify({
                'error': {
                    'code': 500,
                    'message': str(e)
                }
            }), 500


class SubnetHandler:
    """
    Handles subnetwork API requests.
    Endpoints: /compute/v1/projects/{project}/regions/{region}/subnetworks
    """
    
    def __init__(self, subnet_service: SubnetService, vpc_service: VPCService):
        self.subnet_service = subnet_service
        self.vpc_service = vpc_service
    
    def list_subnetworks(self, project_id: str, region: str):
        """
        List subnetworks in a region.
        GET /compute/v1/projects/{project}/regions/{region}/subnetworks
        """
        try:
            # Get all networks for this project
            networks = self.vpc_service.list_networks(project_id)
            network_ids = [net.id for net in networks]
            
            # Get subnets for these networks in this region
            all_subnets = []
            for net_id in network_ids:
                subnets = self.subnet_service.list_subnetworks(network_id=net_id, region=region)
                all_subnets.extend(subnets)
            
            return jsonify({
                'kind': 'compute#subnetworkList',
                'id': f'projects/{project_id}/regions/{region}/subnetworks',
                'items': [subnet.to_dict(project_id) for subnet in all_subnets],
                'selfLink': f'projects/{project_id}/regions/{region}/subnetworks'
            }), 200
        except Exception as e:
            logger.error(f"Error listing subnetworks: {e}", exc_info=True)
            return jsonify({
                'error': {
                    'code': 500,
                    'message': str(e)
                }
            }), 500
    
    def get_subnetwork(self, project_id: str, region: str, subnetwork_name: str):
        """
        Get a specific subnetwork.
        GET /compute/v1/projects/{project}/regions/{region}/subnetworks/{subnetwork}
        """
        try:
            # Find the subnet by name in this region
            networks = self.vpc_service.list_networks(project_id)
            
            for network in networks:
                subnet = self.subnet_service.get_subnetwork(network.id, subnetwork_name)
                if subnet and subnet.region == region:
                    return jsonify(subnet.to_dict(project_id)), 200
            
            return jsonify({
                'error': {
                    'code': 404,
                    'message': f"Subnetwork '{subnetwork_name}' not found in region '{region}'"
                }
            }), 404
        except Exception as e:
            logger.error(f"Error getting subnetwork: {e}", exc_info=True)
            return jsonify({
                'error': {
                    'code': 500,
                    'message': str(e)
                }
            }), 500
    
    def create_subnetwork(self, project_id: str, region: str):
        """
        Create a new subnetwork.
        POST /compute/v1/projects/{project}/regions/{region}/subnetworks
        """
        try:
            data = request.get_json()
            
            if not data or 'name' not in data or 'network' not in data or 'ipCidrRange' not in data:
                return jsonify({
                    'error': {
                        'code': 400,
                        'message': 'Missing required fields: name, network, ipCidrRange'
                    }
                }), 400
            
            # Extract network name from URL (format: projects/{project}/global/networks/{network})
            network_url = data['network']
            network_name = network_url.split('/')[-1]
            
            # Get network
            network = self.vpc_service.get_network(project_id, network_name)
            if not network:
                return jsonify({
                    'error': {
                        'code': 404,
                        'message': f"Network '{network_name}' not found"
                    }
                }), 404
            
            name = data['name']
            ip_cidr_range = data['ipCidrRange']
            description = data.get('description', '')
            private_ip_google_access = data.get('privateIpGoogleAccess', False)
            
            subnet = self.subnet_service.create_subnetwork(
                network_id=network.id,
                name=name,
                region=region,
                ip_cidr_range=ip_cidr_range,
                description=description,
                private_ip_google_access=private_ip_google_access
            )
            
            return jsonify({
                'kind': 'compute#operation',
                'operationType': 'insert',
                'status': 'DONE',
                'targetLink': f'projects/{project_id}/regions/{region}/subnetworks/{name}',
                'insertTime': subnet.created_at.isoformat() + 'Z'
            }), 200
        except ValueError as e:
            return jsonify({
                'error': {
                    'code': 400,
                    'message': str(e)
                }
            }), 400
        except Exception as e:
            logger.error(f"Error creating subnetwork: {e}", exc_info=True)
            return jsonify({
                'error': {
                    'code': 500,
                    'message': str(e)
                }
            }), 500
    
    def delete_subnetwork(self, project_id: str, region: str, subnetwork_name: str):
        """
        Delete a subnetwork.
        DELETE /compute/v1/projects/{project}/regions/{region}/subnetworks/{subnetwork}
        """
        try:
            # Find the subnet
            networks = self.vpc_service.list_networks(project_id)
            
            for network in networks:
                subnet = self.subnet_service.get_subnetwork(network.id, subnetwork_name)
                if subnet and subnet.region == region:
                    success = self.subnet_service.delete_subnetwork(network.id, subnetwork_name)
                    
                    if success:
                        return jsonify({
                            'kind': 'compute#operation',
                            'operationType': 'delete',
                            'status': 'DONE',
                            'targetLink': f'projects/{project_id}/regions/{region}/subnetworks/{subnetwork_name}'
                        }), 200
            
            return jsonify({
                'error': {
                    'code': 404,
                    'message': f"Subnetwork '{subnetwork_name}' not found in region '{region}'"
                }
            }), 404
        except ValueError as e:
            return jsonify({
                'error': {
                    'code': 400,
                    'message': str(e)
                }
            }), 400
        except Exception as e:
            logger.error(f"Error deleting subnetwork: {e}", exc_info=True)
            return jsonify({
                'error': {
                    'code': 500,
                    'message': str(e)
                }
            }), 500
