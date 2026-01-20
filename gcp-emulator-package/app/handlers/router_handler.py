"""
Cloud Router Handler - Dynamic Route Exchange via BGP

Handles Cloud Router CRUD operations for VPC networking.
Cloud Routers enable dynamic route exchange via BGP for hybrid connectivity.

Endpoints:
- POST   /compute/v1/projects/{project}/regions/{region}/routers
- GET    /compute/v1/projects/{project}/regions/{region}/routers
- GET    /compute/v1/projects/{project}/regions/{region}/routers/{router}
- PATCH  /compute/v1/projects/{project}/regions/{region}/routers/{router}
- DELETE /compute/v1/projects/{project}/regions/{region}/routers/{router}
"""

from flask import request, jsonify
from app.models.router import Router, CloudNAT
from app.models.vpc import Network
from app.factory import db
from app.utils.operation_utils import create_operation
from sqlalchemy.exc import IntegrityError
import uuid


def create_router(project_id: str, region: str):
    """
    Create a new Cloud Router
    
    Request body:
    {
        "name": "router-1",
        "network": "projects/PROJECT/global/networks/NETWORK",
        "description": "Optional description",
        "bgp": {
            "asn": 64512,
            "keepaliveInterval": 20
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or "name" not in data:
            return jsonify({"error": {"message": "Router name is required"}}), 400
        
        if "network" not in data:
            return jsonify({"error": {"message": "Network is required"}}), 400
        
        if "bgp" not in data or "asn" not in data["bgp"]:
            return jsonify({"error": {"message": "BGP ASN is required"}}), 400
        
        # Validate router name (RFC 1035)
        name = data["name"]
        if not name or len(name) > 63:
            return jsonify({"error": {"message": "Router name must be 1-63 characters"}}), 400
        
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
        
        # Validate BGP ASN (64512-65534 for private, 1-4294967295 for public)
        bgp_asn = data["bgp"]["asn"]
        if not isinstance(bgp_asn, int) or bgp_asn < 1 or bgp_asn > 4294967295:
            return jsonify({
                "error": {"message": "BGP ASN must be between 1 and 4294967295"}
            }), 400
        
        # BGP keepalive interval (default 20 seconds)
        bgp_keepalive = data["bgp"].get("keepaliveInterval", 20)
        if bgp_keepalive < 1 or bgp_keepalive > 60:
            return jsonify({
                "error": {"message": "BGP keepalive interval must be between 1 and 60 seconds"}
            }), 400
        
        # Check if router already exists
        existing_router = Router.query.filter_by(
            network_id=network.id,
            region=region,
            name=name
        ).first()
        
        if existing_router:
            return jsonify({
                "error": {
                    "message": f"Router '{name}' already exists in region '{region}' for network '{network_name}'"
                }
            }), 409
        
        # Create router
        router = Router(
            id=str(uuid.uuid4()),
            name=name,
            network_id=network.id,
            region=region,
            description=data.get("description", ""),
            bgp_asn=bgp_asn,
            bgp_keepalive_interval=bgp_keepalive
        )
        
        db.session.add(router)
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='insert',
            target_link=router.get_self_link(project_id),
            target_id=str(router.id),
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
                "message": f"Failed to create router: {str(e)}"
            }
        }), 500


def list_routers(project_id: str, region: str):
    """
    List Cloud Routers in a region
    
    Query parameters:
    - filter: Optional filter string
    - maxResults: Maximum number of results
    - pageToken: Pagination token
    """
    try:
        # Get all networks in the project
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        if not network_ids:
            # No networks, no routers
            response = {
                "kind": "compute#routerList",
                "id": f"projects/{project_id}/regions/{region}/routers",
                "items": [],
                "selfLink": f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/regions/{region}/routers"
            }
            return jsonify(response), 200
        
        # Get routers in this region for these networks
        routers = Router.query.filter(
            Router.network_id.in_(network_ids),
            Router.region == region
        ).all()
        
        items = [router.to_dict(project_id=project_id) for router in routers]
        
        response = {
            "kind": "compute#routerList",
            "id": f"projects/{project_id}/regions/{region}/routers",
            "items": items,
            "selfLink": f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/regions/{region}/routers"
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "error": {
                "message": f"Failed to list routers: {str(e)}"
            }
        }), 500


def get_router(project_id: str, region: str, router_name: str):
    """Get details of a specific Cloud Router"""
    try:
        # Get all networks in the project
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        if not network_ids:
            return jsonify({
                "error": {
                    "message": f"Router '{router_name}' not found in region '{region}'"
                }
            }), 404
        
        # Find the router
        router = Router.query.filter(
            Router.network_id.in_(network_ids),
            Router.region == region,
            Router.name == router_name
        ).first()
        
        if not router:
            return jsonify({
                "error": {
                    "message": f"Router '{router_name}' not found in region '{region}'"
                }
            }), 404
        
        return jsonify(router.to_dict(project_id=project_id)), 200
        
    except Exception as e:
        return jsonify({
            "error": {
                "message": f"Failed to get router: {str(e)}"
            }
        }), 500


def update_router(project_id: str, region: str, router_name: str):
    """
    Update a Cloud Router (PATCH)
    
    Supports updating:
    - description
    - bgp.asn
    - bgp.keepaliveInterval
    """
    try:
        data = request.get_json()
        
        # Get all networks in the project
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        if not network_ids:
            return jsonify({
                "error": {
                    "message": f"Router '{router_name}' not found in region '{region}'"
                }
            }), 404
        
        # Find the router
        router = Router.query.filter(
            Router.network_id.in_(network_ids),
            Router.region == region,
            Router.name == router_name
        ).first()
        
        if not router:
            return jsonify({
                "error": {
                    "message": f"Router '{router_name}' not found in region '{region}'"
                }
            }), 404
        
        # Update fields
        if "description" in data:
            router.description = data["description"]
        
        if "bgp" in data:
            if "asn" in data["bgp"]:
                bgp_asn = data["bgp"]["asn"]
                if not isinstance(bgp_asn, int) or bgp_asn < 1 or bgp_asn > 4294967295:
                    return jsonify({
                        "error": {"message": "BGP ASN must be between 1 and 4294967295"}
                    }), 400
                router.bgp_asn = bgp_asn
            
            if "keepaliveInterval" in data["bgp"]:
                interval = data["bgp"]["keepaliveInterval"]
                if interval < 1 or interval > 60:
                    return jsonify({
                        "error": {"message": "BGP keepalive interval must be between 1 and 60 seconds"}
                    }), 400
                router.bgp_keepalive_interval = interval
        
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='update',
            target_link=router.get_self_link(project_id),
            target_id=str(router.id),
            region=region
        )
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {
                "message": f"Failed to update router: {str(e)}"
            }
        }), 500


def delete_router(project_id: str, region: str, router_name: str):
    """Delete a Cloud Router"""
    try:
        # Get all networks in the project
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        if not network_ids:
            return jsonify({
                "error": {
                    "message": f"Router '{router_name}' not found in region '{region}'"
                }
            }), 404
        
        # Find the router
        router = Router.query.filter(
            Router.network_id.in_(network_ids),
            Router.region == region,
            Router.name == router_name
        ).first()
        
        if not router:
            return jsonify({
                "error": {
                    "message": f"Router '{router_name}' not found in region '{region}'"
                }
            }), 404
        
        # Check if router has NAT configs (optional: could allow cascade delete)
        nat_count = CloudNAT.query.filter_by(router_id=router.id).count()
        if nat_count > 0:
            return jsonify({
                "error": {
                    "message": f"Cannot delete router '{router_name}'. It has {nat_count} Cloud NAT configuration(s). Delete them first."
                }
            }), 400
        
        # Delete the router
        db.session.delete(router)
        db.session.commit()
        
        # Return operation
        operation = create_operation(
            project_id=project_id,
            operation_type='delete',
            target_link=router.get_self_link(project_id),
            target_id=str(router.id),
            region=region
        )
        return jsonify(operation.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": {
                "message": f"Failed to delete router: {str(e)}"
            }
        }), 500
