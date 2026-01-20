"""
Route Handler - VPC Route Management

Handles:
- Create route (custom routing rules)
- List routes (all routes in project)
- Get route details
- Delete route
- Update route properties
"""

from flask import jsonify, request
from sqlalchemy.exc import IntegrityError
from app.factory import db
from app.models.vpc import Network, Route
from app.validators.vpc_validators import validate_route_config, validate_network_tags
from datetime import datetime
import uuid


def create_route(project_id: str):
    """
    Create a new route in a VPC network
    
    Request body:
    {
        "name": "route-name",
        "network": "projects/PROJECT/global/networks/NETWORK",
        "destRange": "0.0.0.0/0",
        "priority": 1000,
        "nextHopGateway": "default-internet-gateway",  # OR
        "nextHopIp": "10.0.0.1",  # OR
        "nextHopInstance": "zones/ZONE/instances/INSTANCE",  # OR
        "nextHopVpnTunnel": "regions/REGION/vpnTunnels/TUNNEL",
        "description": "Optional description",
        "tags": ["tag1", "tag2"]
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or "name" not in data:
            return jsonify({"error": {"message": "Route name is required"}}), 400
        
        if "network" not in data:
            return jsonify({"error": {"message": "Network is required"}}), 400
        
        if "destRange" not in data:
            return jsonify({"error": {"message": "Destination range is required"}}), 400
        
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
            return jsonify({"error": {"message": f"Network '{network_name}' not found"}}), 404
        
        # Determine next hop type and value
        next_hop_type = None
        next_hop_value = None
        
        if "nextHopGateway" in data:
            next_hop_type = "gateway"
            next_hop_value = data["nextHopGateway"]
        elif "nextHopIp" in data:
            next_hop_type = "ip"
            next_hop_value = data["nextHopIp"]
        elif "nextHopInstance" in data:
            next_hop_type = "instance"
            next_hop_value = data["nextHopInstance"]
        elif "nextHopVpnTunnel" in data:
            next_hop_type = "vpn_tunnel"
            next_hop_value = data["nextHopVpnTunnel"]
        elif "nextHopInterconnect" in data:
            next_hop_type = "interconnect"
            next_hop_value = data["nextHopInterconnect"]
        else:
            return jsonify({"error": {"message": "At least one nextHop* field is required"}}), 400
        
        # Get priority (default 1000)
        priority = data.get("priority", 1000)
        
        # Validate route configuration
        is_valid, error_msg = validate_route_config(
            name=data["name"],
            dest_range=data["destRange"],
            priority=priority,
            next_hop_type=next_hop_type,
            next_hop_value=next_hop_value
        )
        if not is_valid:
            return jsonify({"error": {"message": error_msg}}), 400
        
        # Validate tags if provided
        tags = data.get("tags", [])
        if tags:
            is_valid, error_msg = validate_network_tags(tags)
            if not is_valid:
                return jsonify({"error": {"message": error_msg}}), 400
        
        # Check if route with this name already exists in network
        existing = Route.query.filter_by(
            network_id=network.id,
            name=data["name"]
        ).first()
        
        if existing:
            return jsonify({"error": {"message": f"Route '{data['name']}' already exists in network '{network_name}'"}}), 409
        
        # Create the route
        route = Route(
            id=uuid.uuid4(),
            name=data["name"],
            network_id=network.id,
            description=data.get("description", ""),
            dest_range=data["destRange"],
            priority=priority,
            next_hop_type=next_hop_type,
            next_hop_value=next_hop_value,
            tags=tags if tags else None,
            creation_timestamp=datetime.utcnow()
        )
        
        db.session.add(route)
        db.session.commit()
        
        return jsonify(route.to_dict(project_id)), 201
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": {"message": f"Database error: {str(e)}"}}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"message": f"Failed to create route: {str(e)}"}}), 500


def list_routes(project_id: str):
    """
    List all routes in a project
    
    Query parameters:
    - filter: Optional filter string (e.g., "network=NETWORK_NAME")
    - maxResults: Maximum number of results
    - orderBy: Order by field (e.g., "priority" or "creationTimestamp")
    """
    try:
        # Get all networks for this project
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        # Query routes for all networks
        query = Route.query.filter(Route.network_id.in_(network_ids))
        
        # Apply filter if provided
        filter_param = request.args.get('filter')
        if filter_param:
            # Simple network filter: "network=network-name"
            if filter_param.startswith("network="):
                network_name = filter_param.split("=", 1)[1].strip()
                network = Network.query.filter_by(
                    project_id=project_id,
                    name=network_name
                ).first()
                if network:
                    query = query.filter(Route.network_id == network.id)
        
        # Apply ordering
        order_by = request.args.get('orderBy', 'priority')
        if order_by == 'priority':
            query = query.order_by(Route.priority)
        elif order_by == 'creationTimestamp':
            query = query.order_by(Route.creation_timestamp)
        elif order_by == 'name':
            query = query.order_by(Route.name)
        else:
            query = query.order_by(Route.priority)
        
        # Apply maxResults
        max_results = request.args.get('maxResults', type=int)
        if max_results:
            query = query.limit(max_results)
        
        routes = query.all()
        
        return jsonify({
            "kind": "compute#routeList",
            "items": [route.to_dict(project_id) for route in routes],
            "selfLink": f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/global/routes"
        }), 200
        
    except Exception as e:
        return jsonify({"error": {"message": f"Failed to list routes: {str(e)}"}}), 500


def get_route(project_id: str, route_name: str):
    """
    Get details of a specific route
    """
    try:
        # Get all networks for this project
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        # Find the route
        route = Route.query.filter(
            Route.network_id.in_(network_ids),
            Route.name == route_name
        ).first()
        
        if not route:
            return jsonify({"error": {"message": f"Route '{route_name}' not found"}}), 404
        
        return jsonify(route.to_dict(project_id)), 200
        
    except Exception as e:
        return jsonify({"error": {"message": f"Failed to get route: {str(e)}"}}), 500


def delete_route(project_id: str, route_name: str):
    """
    Delete a route
    """
    try:
        # Get all networks for this project
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        # Find the route
        route = Route.query.filter(
            Route.network_id.in_(network_ids),
            Route.name == route_name
        ).first()
        
        if not route:
            return jsonify({"error": {"message": f"Route '{route_name}' not found"}}), 404
        
        # Check if this is a system-generated route (e.g., default routes)
        # In GCP, routes with priority 1000 and destRange 0.0.0.0/0 created by system cannot be deleted
        # For now, we'll allow deletion of all routes in the emulator
        
        db.session.delete(route)
        db.session.commit()
        
        return jsonify({
            "kind": "compute#operation",
            "operationType": "delete",
            "targetLink": f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/global/routes/{route_name}",
            "status": "DONE"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"message": f"Failed to delete route: {str(e)}"}}), 500


def update_route(project_id: str, route_name: str):
    """
    Update route properties (PUT - full update)
    
    Updates:
    - priority
    - tags
    - description
    - next hop (type and value)
    
    Note: destRange and network cannot be changed after creation
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": {"message": "Request body is required"}}), 400
        
        # Get all networks for this project
        networks = Network.query.filter_by(project_id=project_id).all()
        network_ids = [n.id for n in networks]
        
        # Find the route
        route = Route.query.filter(
            Route.network_id.in_(network_ids),
            Route.name == route_name
        ).first()
        
        if not route:
            return jsonify({"error": {"message": f"Route '{route_name}' not found"}}), 404
        
        # Update priority if provided
        if "priority" in data:
            priority = data["priority"]
            if not isinstance(priority, int) or priority < 0 or priority > 65535:
                return jsonify({"error": {"message": "Priority must be between 0 and 65535"}}), 400
            route.priority = priority
        
        # Update description if provided
        if "description" in data:
            route.description = data["description"]
        
        # Update tags if provided
        if "tags" in data:
            tags = data["tags"]
            is_valid, error_msg = validate_network_tags(tags)
            if not is_valid:
                return jsonify({"error": {"message": error_msg}}), 400
            route.tags = tags if tags else None
        
        # Update next hop if provided
        next_hop_updated = False
        if "nextHopGateway" in data:
            route.next_hop_type = "gateway"
            route.next_hop_value = data["nextHopGateway"]
            next_hop_updated = True
        elif "nextHopIp" in data:
            route.next_hop_type = "ip"
            route.next_hop_value = data["nextHopIp"]
            next_hop_updated = True
        elif "nextHopInstance" in data:
            route.next_hop_type = "instance"
            route.next_hop_value = data["nextHopInstance"]
            next_hop_updated = True
        elif "nextHopVpnTunnel" in data:
            route.next_hop_type = "vpn_tunnel"
            route.next_hop_value = data["nextHopVpnTunnel"]
            next_hop_updated = True
        elif "nextHopInterconnect" in data:
            route.next_hop_type = "interconnect"
            route.next_hop_value = data["nextHopInterconnect"]
            next_hop_updated = True
        
        # Validate next hop if updated
        if next_hop_updated:
            is_valid, error_msg = validate_route_config(
                name=route.name,
                dest_range=route.dest_range,
                priority=route.priority,
                next_hop_type=route.next_hop_type,
                next_hop_value=route.next_hop_value
            )
            if not is_valid:
                return jsonify({"error": {"message": error_msg}}), 400
        
        db.session.commit()
        
        return jsonify(route.to_dict(project_id)), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"message": f"Failed to update route: {str(e)}"}}), 500


def patch_route(project_id: str, route_name: str):
    """
    Partially update route properties (PATCH)
    
    Same as update_route but only updates provided fields
    """
    return update_route(project_id, route_name)
