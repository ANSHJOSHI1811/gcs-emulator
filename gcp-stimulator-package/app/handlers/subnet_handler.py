"""
Subnetwork Handler - VPC Subnet Management

Handles:
- Create subnetwork (regional IP ranges)
- List subnetworks (regional or all)
- Get subnetwork details
- Delete subnetwork
- Expand subnetwork CIDR range
- IP allocation tracking
"""

from flask import jsonify, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_
from app.factory import db
from app.models.vpc import Network, Subnetwork
from app.models.compute import Zone
from app.validators.vpc_validators import validate_subnet_config
from app.utils.operation_utils import create_operation
from app.utils.ip_utils import (
    validate_cidr,
    is_private_range,
    calculate_gateway,
    get_usable_ip_count,
    cidr_overlaps,
    validate_ip_in_range
)
from datetime import datetime
import uuid


def create_subnetwork(project_id: str, region: str):
    """
    Create a new subnetwork in a VPC network
    
    Request body:
    {
        "name": "subnet-name",
        "network": "projects/PROJECT/global/networks/NETWORK",
        "ipCidrRange": "10.0.0.0/24",
        "description": "Optional description",
        "privateIpGoogleAccess": false,
        "enableFlowLogs": false
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or "name" not in data:
            return jsonify({"error": {"message": "Subnetwork name is required"}}), 400
        
        if "network" not in data:
            return jsonify({"error": {"message": "Network is required"}}), 400
        
        if "ipCidrRange" not in data:
            return jsonify({"error": {"message": "IP CIDR range is required"}}), 400
        
        # Validate subnet configuration
        is_valid, error_msg = validate_subnet_config(
            name=data["name"],
            cidr=data["ipCidrRange"],
            region=region
        )
        if not is_valid:
            return jsonify({"error": {"message": error_msg}}), 400
        
        # Extract network name from URL
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
            return jsonify({
                "error": {
                    "message": f"Network '{network_name}' not found in project '{project_id}'"
                }
            }), 404
        
        # Check if network is in auto mode (can't manually add subnets)
        if network.auto_create_subnetworks:
            return jsonify({
                "error": {
                    "message": "Cannot create subnetwork in auto-mode network. Use custom mode network."
                }
            }), 400
        
        # Validate region exists
        zones_in_region = Zone.query.filter(Zone.region == region).all()
        if not zones_in_region:
            return jsonify({
                "error": {
                    "message": f"Region '{region}' not found"
                }
            }), 404
        
        # Validate CIDR
        ip_cidr_range = data["ipCidrRange"]
        if not validate_cidr(ip_cidr_range):
            return jsonify({
                "error": {
                    "message": f"Invalid CIDR range: {ip_cidr_range}"
                }
            }), 400
        
        # Check if CIDR is private
        if not is_private_range(ip_cidr_range):
            return jsonify({
                "error": {
                    "message": f"CIDR range must be private (RFC 1918): {ip_cidr_range}"
                }
            }), 400
        
        # Check for overlapping subnets in the same network
        existing_subnets = Subnetwork.query.filter_by(
            network_id=network.id
        ).all()
        
        for existing_subnet in existing_subnets:
            if cidr_overlaps(ip_cidr_range, existing_subnet.ip_cidr_range):
                return jsonify({
                    "error": {
                        "message": f"CIDR range {ip_cidr_range} overlaps with existing subnet '{existing_subnet.name}' ({existing_subnet.ip_cidr_range})"
                    }
                }), 400
        
        # Check for duplicate name in region
        existing_subnet = Subnetwork.query.filter(
            and_(
                Subnetwork.network_id == network.id,
                Subnetwork.region == region,
                Subnetwork.name == data["name"]
            )
        ).first()
        
        if existing_subnet:
            return jsonify({
                "error": {
                    "message": f"Subnetwork '{data['name']}' already exists in region '{region}'"
                }
            }), 409
        
        # Calculate gateway IP
        gateway_address = calculate_gateway(ip_cidr_range)
        
        # Create subnetwork
        subnet_id = str(uuid.uuid4())
        subnet = Subnetwork(
            id=subnet_id,
            network_id=network.id,
            name=data["name"],
            region=region,
            ip_cidr_range=ip_cidr_range,
            gateway_address=gateway_address,
            description=data.get("description", ""),
            private_ip_google_access=data.get("privateIpGoogleAccess", False),
            enable_flow_logs=data.get("enableFlowLogs", False)
        )
        
        db.session.add(subnet)
        db.session.commit()
        
        # Convert UUID to integer for gcloud CLI compatibility
        id_as_int = int(subnet.id.hex[:16], 16) % (10**19)
        
        # Return operation instead of subnet object
        operation = create_operation(
            project_id=project_id,
            operation_type='insert',
            target_link=subnet.get_self_link(project_id),
            target_id=str(id_as_int),
            region=region
        )
        return jsonify(operation.to_dict()), 200
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            "error": {
                "message": f"Database constraint violation: {str(e)}"
            }
        }), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {
                "message": f"Failed to create subnetwork: {str(e)}"
            }
        }), 500


def list_subnetworks(project_id: str, region: str = None):
    """
    List subnetworks in a project/region
    
    Query parameters:
    - filter: Optional filter string
    - maxResults: Maximum number of results (default: 500)
    - pageToken: Pagination token
    """
    try:
        # Get all networks in the project first
        from app.models.vpc import Network
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        # Build query for subnetworks in those networks
        query = Subnetwork.query.filter(Subnetwork.network_id.in_(network_ids))
        
        # Filter by region if specified
        if region:
            query = query.filter_by(region=region)
        
        # Apply filter if provided
        filter_param = request.args.get("filter")
        if filter_param:
            # Simple name filter for now
            if "name=" in filter_param:
                name_filter = filter_param.split("name=")[1].strip('"')
                query = query.filter(Subnetwork.name.ilike(f"%{name_filter}%"))
        
        # Get results
        subnets = query.all()
        
        # Build response based on whether region is specified
        base_url = request.host_url.rstrip("/")
        
        if region:
            # Regional list - simple items array
            items = [subnet.to_dict(project_id=project_id) for subnet in subnets]
            response = {
                "kind": "compute#subnetworkList",
                "id": f"projects/{project_id}/regions/{region}/subnetworks",
                "items": items,
                "selfLink": f"{base_url}/compute/v1/projects/{project_id}/regions/{region}/subnetworks"
            }
        else:
            # Aggregated list - items as dict keyed by region
            items_by_region = {}
            for subnet in subnets:
                region_key = f"regions/{subnet.region}"
                if region_key not in items_by_region:
                    items_by_region[region_key] = {
                        "subnetworks": []
                    }
                items_by_region[region_key]["subnetworks"].append(subnet.to_dict(project_id=project_id))
            
            response = {
                "kind": "compute#subnetworkAggregatedList",
                "id": f"projects/{project_id}/aggregated/subnetworks",
                "items": items_by_region,
                "selfLink": f"{base_url}/compute/v1/projects/{project_id}/aggregated/subnetworks"
            }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "error": {
                "message": f"Failed to list subnetworks: {str(e)}"
            }
        }), 500


def get_subnetwork(project_id: str, region: str, subnet_name: str):
    """Get details of a specific subnetwork"""
    try:
        # Get networks in project
        from app.models.vpc import Network
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        subnet = Subnetwork.query.filter(
            and_(
                Subnetwork.network_id.in_(network_ids),
                Subnetwork.region == region,
                Subnetwork.name == subnet_name
            )
        ).first()
        
        if not subnet:
            return jsonify({
                "error": {
                    "message": f"Subnetwork '{subnet_name}' not found in region '{region}'"
                }
            }), 404
        
        return jsonify(subnet.to_dict(project_id=project_id)), 200
        
    except Exception as e:
        return jsonify({
            "error": {
                "message": f"Failed to get subnetwork: {str(e)}"
            }
        }), 500


def delete_subnetwork(project_id: str, region: str, subnet_name: str):
    """
    Delete a subnetwork
    
    Checks:
    - Subnetwork exists
    - No instances are using the subnetwork
    """
    try:
        # Get networks in project
        from app.models.vpc import Network
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        subnet = Subnetwork.query.filter(
            and_(
                Subnetwork.network_id.in_(network_ids),
                Subnetwork.region == region,
                Subnetwork.name == subnet_name
            )
        ).first()
        
        if not subnet:
            return jsonify({
                "error": {
                    "message": f"Subnetwork '{subnet_name}' not found in region '{region}'"
                }
            }), 404
        
        # Check if any instances are using this subnetwork
        from app.models.compute import Instance
        instances_using_subnet = Instance.query.filter(
            and_(
                Instance.project_id == project_id,
                or_(
                    Instance.subnetwork_url.ilike(f"%/subnetworks/{subnet_name}"),
                    Instance.subnetwork_url == subnet.get_self_link(project_id)
                )
            )
        ).count()
        
        if instances_using_subnet > 0:
            return jsonify({
                "error": {
                    "message": f"Cannot delete subnetwork '{subnet_name}'. {instances_using_subnet} instance(s) are using it."
                }
            }), 400
        
        # Delete the subnetwork
        db.session.delete(subnet)
        db.session.commit()
        
        # Convert UUID to integer for gcloud CLI compatibility
        id_as_int = int(subnet.id.hex[:16], 16) % (10**19)
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='delete',
            target_link=subnet.get_self_link(project_id),
            target_id=str(id_as_int),
            region=region
        )
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {
                "message": f"Failed to delete subnetwork: {str(e)}"
            }
        }), 500


def expand_subnetwork(project_id: str, region: str, subnet_name: str):
    """
    Expand IP CIDR range of an existing subnetwork
    
    Request body:
    {
        "ipCidrRange": "10.0.0.0/20"  # Must be larger than current range
    }
    """
    try:
        data = request.get_json()
        
        if not data or "ipCidrRange" not in data:
            return jsonify({
                "error": {
                    "message": "New IP CIDR range is required"
                }
            }), 400
        
        # Get networks in project
        from app.models.vpc import Network
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        subnet = Subnetwork.query.filter(
            and_(
                Subnetwork.network_id.in_(network_ids),
                Subnetwork.region == region,
                Subnetwork.name == subnet_name
            )
        ).first()
        
        if not subnet:
            return jsonify({
                "error": {
                    "message": f"Subnetwork '{subnet_name}' not found in region '{region}'"
                }
            }), 404
        
        new_cidr = data["ipCidrRange"]
        
        # Validate new CIDR
        if not validate_cidr(new_cidr):
            return jsonify({
                "error": {
                    "message": f"Invalid CIDR range: {new_cidr}"
                }
            }), 400
        
        # Check if new CIDR is private
        if not is_private_range(new_cidr):
            return jsonify({
                "error": {
                    "message": f"CIDR range must be private (RFC 1918): {new_cidr}"
                }
            }), 400
        
        # Get network and prefix sizes
        import ipaddress
        old_network = ipaddress.ip_network(subnet.ip_cidr_range, strict=False)
        new_network = ipaddress.ip_network(new_cidr, strict=False)
        
        # Validate expansion rules
        if new_network.prefixlen >= old_network.prefixlen:
            return jsonify({
                "error": {
                    "message": f"New CIDR range must be larger (smaller prefix). Current: /{old_network.prefixlen}, New: /{new_network.prefixlen}"
                }
            }), 400
        
        # Check if old range is subnet of new range
        if not old_network.subnet_of(new_network):
            return jsonify({
                "error": {
                    "message": f"New CIDR range must include the existing range. Existing: {subnet.ip_cidr_range}, New: {new_cidr}"
                }
            }), 400
        
        # Check for overlaps with other subnets in the network
        network = Network.query.get(subnet.network_id)
        other_subnets = Subnetwork.query.filter(
            and_(
                Subnetwork.network_id == network.id,
                Subnetwork.id != subnet.id
            )
        ).all()
        
        for other_subnet in other_subnets:
            if cidr_overlaps(new_cidr, other_subnet.ip_cidr_range):
                return jsonify({
                    "error": {
                        "message": f"Expanded CIDR {new_cidr} overlaps with subnet '{other_subnet.name}' ({other_subnet.ip_cidr_range})"
                    }
                }), 400
        
        # Update the subnet
        subnet.ip_cidr_range = new_cidr
        subnet.gateway_address = calculate_gateway(new_cidr)
        subnet.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(subnet.to_dict(project_id=project_id)), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {
                "message": f"Failed to expand subnetwork: {str(e)}"
            }
        }), 500


def patch_subnetwork(project_id: str, region: str, subnet_name: str):
    """
    Update subnetwork properties
    
    Updatable fields:
    - privateIpGoogleAccess
    - enableFlowLogs
    - description
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": {
                    "message": "Request body is required"
                }
            }), 400
        
        # Get networks in project
        from app.models.vpc import Network
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        subnet = Subnetwork.query.filter(
            and_(
                Subnetwork.network_id.in_(network_ids),
                Subnetwork.region == region,
                Subnetwork.name == subnet_name
            )
        ).first()
        
        if not subnet:
            return jsonify({
                "error": {
                    "message": f"Subnetwork '{subnet_name}' not found in region '{region}'"
                }
            }), 404
        
        # Update allowed fields
        if "privateIpGoogleAccess" in data:
            subnet.private_ip_google_access = data["privateIpGoogleAccess"]
        
        if "enableFlowLogs" in data:
            subnet.enable_flow_logs = data["enableFlowLogs"]
        
        if "description" in data:
            subnet.description = data["description"]
        
        subnet.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(subnet.to_dict(project_id=project_id)), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {
                "message": f"Failed to update subnetwork: {str(e)}"
            }
        }), 500
