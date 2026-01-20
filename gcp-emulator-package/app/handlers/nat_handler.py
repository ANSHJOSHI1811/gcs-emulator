"""
Cloud NAT Handler - Network Address Translation

Handles Cloud NAT CRUD operations for Cloud Routers.
Cloud NAT enables instances without external IPs to access the internet.

Endpoints:
- POST   /compute/v1/projects/{project}/regions/{region}/routers/{router}/nats
- GET    /compute/v1/projects/{project}/regions/{region}/routers/{router}/nats  
- GET    /compute/v1/projects/{project}/regions/{region}/routers/{router}/nats/{nat}
- PATCH  /compute/v1/projects/{project}/regions/{region}/routers/{router}/nats/{nat}
- DELETE /compute/v1/projects/{project}/regions/{region}/routers/{router}/nats/{nat}
"""

from flask import request, jsonify
from app.models.router import Router, CloudNAT
from app.models.vpc import Network
from app.factory import db
from app.utils.operation_utils import create_operation
from sqlalchemy.exc import IntegrityError
import uuid


def create_nat(project_id: str, region: str, router_name: str):
    """
    Create a Cloud NAT configuration on a router
    
    Request body:
    {
        "name": "nat-config-1",
        "natIpAllocateOption": "AUTO_ONLY",
        "sourceSubnetworkIpRangesToNat": "ALL_SUBNETWORKS_ALL_IP_RANGES",
        "natIps": [],
        "minPortsPerVm": 64,
        "maxPortsPerVm": 65536,
        "logConfig": {
            "enable": true,
            "filter": "ALL"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or "name" not in data:
            return jsonify({"error": {"message": "NAT configuration name is required"}}), 400
        
        # Validate NAT name
        name = data["name"]
        if not name or len(name) > 63:
            return jsonify({"error": {"message": "NAT name must be 1-63 characters"}}), 400
        
        # Find the router
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        if not network_ids:
            return jsonify({
                "error": {"message": f"Router '{router_name}' not found in region '{region}'"}
            }), 404
        
        router = Router.query.filter(
            Router.network_id.in_(network_ids),
            Router.region == region,
            Router.name == router_name
        ).first()
        
        if not router:
            return jsonify({
                "error": {"message": f"Router '{router_name}' not found in region '{region}'"}
            }), 404
        
        # Validate natIpAllocateOption
        nat_ip_option = data.get("natIpAllocateOption", "AUTO_ONLY")
        if nat_ip_option not in ["AUTO_ONLY", "MANUAL_ONLY"]:
            return jsonify({
                "error": {"message": "natIpAllocateOption must be AUTO_ONLY or MANUAL_ONLY"}
            }), 400
        
        # Validate sourceSubnetworkIpRangesToNat
        source_ranges = data.get("sourceSubnetworkIpRangesToNat", "ALL_SUBNETWORKS_ALL_IP_RANGES")
        valid_options = [
            "ALL_SUBNETWORKS_ALL_IP_RANGES",
            "ALL_SUBNETWORKS_ALL_PRIMARY_IP_RANGES",
            "LIST_OF_SUBNETWORKS"
        ]
        if source_ranges not in valid_options:
            return jsonify({
                "error": {"message": f"Invalid sourceSubnetworkIpRangesToNat. Must be one of: {', '.join(valid_options)}"}
            }), 400
        
        # Validate port ranges
        min_ports = data.get("minPortsPerVm", 64)
        max_ports = data.get("maxPortsPerVm", 65536)
        
        if min_ports < 64 or min_ports > 65536:
            return jsonify({
                "error": {"message": "minPortsPerVm must be between 64 and 65536"}
            }), 400
        
        if max_ports < min_ports or max_ports > 65536:
            return jsonify({
                "error": {"message": f"maxPortsPerVm must be between {min_ports} and 65536"}
            }), 400
        
        # Check if NAT config already exists on this router
        existing_nat = CloudNAT.query.filter_by(
            router_id=router.id,
            name=name
        ).first()
        
        if existing_nat:
            return jsonify({
                "error": {
                    "message": f"NAT configuration '{name}' already exists on router '{router_name}'"
                }
            }), 409
        
        # Extract log config
        log_config = data.get("logConfig", {})
        enable_logging = log_config.get("enable", False)
        log_filter = log_config.get("filter", "ALL")
        
        if log_filter not in ["ALL", "ERRORS_ONLY", "TRANSLATIONS_ONLY"]:
            log_filter = "ALL"
        
        # Create NAT configuration
        nat = CloudNAT(
            id=str(uuid.uuid4()),
            name=name,
            router_id=router.id,
            nat_ip_allocate_option=nat_ip_option,
            source_subnetwork_ip_ranges_to_nat=source_ranges,
            nat_ips=data.get("natIps", []),
            min_ports_per_vm=min_ports,
            max_ports_per_vm=max_ports,
            enable_logging=enable_logging,
            log_filter=log_filter
        )
        
        db.session.add(nat)
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='insert',
            target_link=router.get_self_link(project_id),
            target_id=str(nat.id),
            region=region
        )
        return jsonify(operation.to_dict()), 200
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": f"Database constraint violation: {str(e)}"}
        }), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": f"Failed to create NAT configuration: {str(e)}"}
        }), 500


def list_nats(project_id: str, region: str, router_name: str):
    """List Cloud NAT configurations on a router"""
    try:
        # Find the router
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        if not network_ids:
            return jsonify({
                "error": {"message": f"Router '{router_name}' not found in region '{region}'"}
            }), 404
        
        router = Router.query.filter(
            Router.network_id.in_(network_ids),
            Router.region == region,
            Router.name == router_name
        ).first()
        
        if not router:
            return jsonify({
                "error": {"message": f"Router '{router_name}' not found in region '{region}'"}
            }), 404
        
        # Get NAT configs for this router
        nats = CloudNAT.query.filter_by(router_id=router.id).all()
        
        items = [nat.to_dict(project_id=project_id) for nat in nats]
        
        response = {
            "kind": "compute#routerNatList",
            "id": f"projects/{project_id}/regions/{region}/routers/{router_name}/nats",
            "items": items
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "error": {"message": f"Failed to list NAT configurations: {str(e)}"}
        }), 500


def get_nat(project_id: str, region: str, router_name: str, nat_name: str):
    """Get details of a specific Cloud NAT configuration"""
    try:
        # Find the router
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        if not network_ids:
            return jsonify({
                "error": {"message": f"Router '{router_name}' not found in region '{region}'"}
            }), 404
        
        router = Router.query.filter(
            Router.network_id.in_(network_ids),
            Router.region == region,
            Router.name == router_name
        ).first()
        
        if not router:
            return jsonify({
                "error": {"message": f"Router '{router_name}' not found in region '{region}'"}
            }), 404
        
        # Find the NAT config
        nat = CloudNAT.query.filter_by(
            router_id=router.id,
            name=nat_name
        ).first()
        
        if not nat:
            return jsonify({
                "error": {"message": f"NAT configuration '{nat_name}' not found on router '{router_name}'"}
            }), 404
        
        return jsonify(nat.to_dict(project_id=project_id)), 200
        
    except Exception as e:
        return jsonify({
            "error": {"message": f"Failed to get NAT configuration: {str(e)}"}
        }), 500


def update_nat(project_id: str, region: str, router_name: str, nat_name: str):
    """
    Update a Cloud NAT configuration (PATCH)
    
    Supports updating:
    - natIpAllocateOption
    - sourceSubnetworkIpRangesToNat
    - natIps
    - minPortsPerVm, maxPortsPerVm
    - logConfig
    """
    try:
        data = request.get_json()
        
        # Find the router
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        if not network_ids:
            return jsonify({
                "error": {"message": f"Router '{router_name}' not found in region '{region}'"}
            }), 404
        
        router = Router.query.filter(
            Router.network_id.in_(network_ids),
            Router.region == region,
            Router.name == router_name
        ).first()
        
        if not router:
            return jsonify({
                "error": {"message": f"Router '{router_name}' not found in region '{region}'"}
            }), 404
        
        # Find the NAT config
        nat = CloudNAT.query.filter_by(
            router_id=router.id,
            name=nat_name
        ).first()
        
        if not nat:
            return jsonify({
                "error": {"message": f"NAT configuration '{nat_name}' not found on router '{router_name}'"}
            }), 404
        
        # Update fields
        if "natIpAllocateOption" in data:
            if data["natIpAllocateOption"] not in ["AUTO_ONLY", "MANUAL_ONLY"]:
                return jsonify({
                    "error": {"message": "natIpAllocateOption must be AUTO_ONLY or MANUAL_ONLY"}
                }), 400
            nat.nat_ip_allocate_option = data["natIpAllocateOption"]
        
        if "sourceSubnetworkIpRangesToNat" in data:
            nat.source_subnetwork_ip_ranges_to_nat = data["sourceSubnetworkIpRangesToNat"]
        
        if "natIps" in data:
            nat.nat_ips = data["natIps"]
        
        if "minPortsPerVm" in data:
            min_ports = data["minPortsPerVm"]
            if min_ports < 64 or min_ports > 65536:
                return jsonify({
                    "error": {"message": "minPortsPerVm must be between 64 and 65536"}
                }), 400
            nat.min_ports_per_vm = min_ports
        
        if "maxPortsPerVm" in data:
            max_ports = data["maxPortsPerVm"]
            if max_ports < nat.min_ports_per_vm or max_ports > 65536:
                return jsonify({
                    "error": {"message": f"maxPortsPerVm must be between {nat.min_ports_per_vm} and 65536"}
                }), 400
            nat.max_ports_per_vm = max_ports
        
        if "logConfig" in data:
            log_config = data["logConfig"]
            if "enable" in log_config:
                nat.enable_logging = log_config["enable"]
            if "filter" in log_config:
                nat.log_filter = log_config["filter"]
        
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='update',
            target_link=router.get_self_link(project_id),
            target_id=str(nat.id),
            region=region
        )
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": f"Failed to update NAT configuration: {str(e)}"}
        }), 500


def delete_nat(project_id: str, region: str, router_name: str, nat_name: str):
    """Delete a Cloud NAT configuration"""
    try:
        # Find the router
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        if not network_ids:
            return jsonify({
                "error": {"message": f"Router '{router_name}' not found in region '{region}'"}
            }), 404
        
        router = Router.query.filter(
            Router.network_id.in_(network_ids),
            Router.region == region,
            Router.name == router_name
        ).first()
        
        if not router:
            return jsonify({
                "error": {"message": f"Router '{router_name}' not found in region '{region}'"}
            }), 404
        
        # Find the NAT config
        nat = CloudNAT.query.filter_by(
            router_id=router.id,
            name=nat_name
        ).first()
        
        if not nat:
            return jsonify({
                "error": {"message": f"NAT configuration '{nat_name}' not found on router '{router_name}'"}
            }), 404
        
        # Delete the NAT config
        db.session.delete(nat)
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='delete',
            target_link=router.get_self_link(project_id),
            target_id=str(nat.id),
            region=region
        )
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {"message": f"Failed to delete NAT configuration: {str(e)}"}
        }), 500
