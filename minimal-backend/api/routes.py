"""VPC Routes API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime
from database import get_db, Route, RouteTable, SubnetRouteTableAssociation

router = APIRouter()


@router.get("/compute/v1/projects/{project}/global/routes")
def list_routes(project: str, db: Session = Depends(get_db)):
    """List all routes in a project"""
    routes = db.query(Route).filter(Route.project_id == project).all()
    
    return {
        "kind": "compute#routeList",
        "id": f"projects/{project}/global/routes",
        "items": [
            {
                "kind": "compute#route",
                "id": str(route.id),
                "name": route.name,
                "network": f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{route.network}",
                "destRange": route.dest_range,
                "priority": route.priority,
                "description": route.description or "",
                "nextHopGateway": route.next_hop_gateway,
                "nextHopInstance": route.next_hop_instance,
                "nextHopIp": route.next_hop_ip,
                "nextHopNetwork": route.next_hop_network,
                "tags": route.tags or [],
                "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/routes/{route.name}",
                "creationTimestamp": route.created_at.isoformat() + "Z" if route.created_at else ""
            }
            for route in routes
        ]
    }


@router.get("/compute/v1/projects/{project}/global/routes/{route_name}")
def get_route(project: str, route_name: str, db: Session = Depends(get_db)):
    """Get a specific route"""
    route = db.query(Route).filter(
        Route.project_id == project,
        Route.name == route_name
    ).first()
    
    if not route:
        raise HTTPException(status_code=404, detail=f"Route '{route_name}' not found")
    
    return {
        "kind": "compute#route",
        "id": str(route.id),
        "name": route.name,
        "network": f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{route.network}",
        "destRange": route.dest_range,
        "priority": route.priority,
        "description": route.description or "",
        "nextHopGateway": route.next_hop_gateway,
        "nextHopInstance": route.next_hop_instance,
        "nextHopIp": route.next_hop_ip,
        "nextHopNetwork": route.next_hop_network,
        "tags": route.tags or [],
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/routes/{route.name}",
        "creationTimestamp": route.created_at.isoformat() + "Z" if route.created_at else ""
    }


@router.post("/compute/v1/projects/{project}/global/routes")
def create_route(project: str, body: Dict[str, Any], db: Session = Depends(get_db)):
    """Create a new route"""
    name = body.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Route name is required")
    
    # Check if route already exists
    existing = db.query(Route).filter(
        Route.project_id == project,
        Route.name == name
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail=f"Route '{name}' already exists")
    
    # Extract network name from URL
    network_url = body.get("network", "")
    network_name = network_url.split("/")[-1] if network_url else "default"
    
    # Validate destination range
    dest_range = body.get("destRange")
    if not dest_range:
        raise HTTPException(status_code=400, detail="destRange is required")
    
    # Create route
    route = Route(
        name=name,
        network=network_name,
        project_id=project,
        description=body.get("description", ""),
        dest_range=dest_range,
        next_hop_gateway=body.get("nextHopGateway"),
        next_hop_instance=body.get("nextHopInstance"),
        next_hop_ip=body.get("nextHopIp"),
        next_hop_network=body.get("nextHopNetwork"),
        priority=body.get("priority", 1000),
        tags=body.get("tags", []),
        created_at=datetime.utcnow()
    )
    
    db.add(route)
    db.commit()
    db.refresh(route)
    
    return {
        "kind": "compute#operation",
        "name": f"operation-{route.id}",
        "operationType": "insert",
        "status": "DONE",
        "progress": 100,
        "targetLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/routes/{name}"
    }


@router.patch("/compute/v1/projects/{project}/global/routes/{route_name}")
def update_route(project: str, route_name: str, body: Dict[str, Any], db: Session = Depends(get_db)):
    """Update an existing route"""
    route = db.query(Route).filter(
        Route.project_id == project,
        Route.name == route_name
    ).first()
    
    if not route:
        raise HTTPException(status_code=404, detail=f"Route '{route_name}' not found")
    
    # Update fields
    if "description" in body:
        route.description = body["description"]
    if "priority" in body:
        route.priority = body["priority"]
    if "tags" in body:
        route.tags = body["tags"]
    if "nextHopGateway" in body:
        route.next_hop_gateway = body["nextHopGateway"]
    if "nextHopInstance" in body:
        route.next_hop_instance = body["nextHopInstance"]
    if "nextHopIp" in body:
        route.next_hop_ip = body["nextHopIp"]
    
    db.commit()
    db.refresh(route)
    
    return {
        "kind": "compute#operation",
        "name": f"operation-update-{route.id}",
        "operationType": "update",
        "status": "DONE",
        "progress": 100
    }


@router.delete("/compute/v1/projects/{project}/global/routes/{route_name}")
def delete_route(project: str, route_name: str, db: Session = Depends(get_db)):
    """Delete a route"""
    route = db.query(Route).filter(
        Route.project_id == project,
        Route.name == route_name
    ).first()
    
    if not route:
        raise HTTPException(status_code=404, detail=f"Route '{route_name}' not found")
    
    db.delete(route)
    db.commit()
    
    return {
        "kind": "compute#operation",
        "name": f"operation-delete-{route.name}",
        "operationType": "delete",
        "status": "DONE",
        "progress": 100
    }


# ============================================================================
# ROUTE TABLE MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/compute/v1/projects/{project}/global/routeTables")
def list_route_tables(project: str, db: Session = Depends(get_db)):
    """List all route tables in a project"""
    route_tables = db.query(RouteTable).filter(RouteTable.project_id == project).all()
    
    items = []
    for rt in route_tables:
        # Get routes for this table
        routes_in_table = db.query(Route).filter(Route.route_table_id == rt.id).all()
        # Get associated subnets
        associations = db.query(SubnetRouteTableAssociation).filter(
            SubnetRouteTableAssociation.route_table_id == rt.id
        ).all()
        
        items.append({
            "kind": "compute#routeTable",
            "id": str(rt.id),
            "name": rt.name,
            "network": f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{rt.network}",
            "description": rt.description or "",
            "isDefault": rt.is_default,
            "routeCount": len(routes_in_table),
            "subnetCount": len(associations),
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/routeTables/{rt.name}",
            "creationTimestamp": rt.created_at.isoformat() + "Z" if rt.created_at else ""
        })
    
    return {
        "kind": "compute#routeTableList",
        "items": items
    }


@router.get("/compute/v1/projects/{project}/global/routeTables/{route_table_name}")
def get_route_table(project: str, route_table_name: str, db: Session = Depends(get_db)):
    """Get a specific route table"""
    rt = db.query(RouteTable).filter(
        RouteTable.project_id == project,
        RouteTable.name == route_table_name
    ).first()
    
    if not rt:
        raise HTTPException(status_code=404, detail=f"Route table '{route_table_name}' not found")
    
    # Get routes for this table
    routes_in_table = db.query(Route).filter(Route.route_table_id == rt.id).all()
    # Get associated subnets
    associations = db.query(SubnetRouteTableAssociation).filter(
        SubnetRouteTableAssociation.route_table_id == rt.id
    ).all()
    
    return {
        "kind": "compute#routeTable",
        "id": str(rt.id),
        "name": rt.name,
        "network": f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{rt.network}",
        "description": rt.description or "",
        "isDefault": rt.is_default,
        "routes": [
            {
                "kind": "compute#route",
                "name": route.name,
                "destRange": route.dest_range,
                "priority": route.priority,
                "nextHopGateway": route.next_hop_gateway,
                "nextHopInstance": route.next_hop_instance,
                "nextHopIp": route.next_hop_ip,
                "nextHopNetwork": route.next_hop_network
            }
            for route in routes_in_table
        ],
        "associations": [
            {
                "subnetName": assoc.subnet_name
            }
            for assoc in associations
        ],
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/routeTables/{rt.name}",
        "creationTimestamp": rt.created_at.isoformat() + "Z" if rt.created_at else ""
    }


@router.post("/compute/v1/projects/{project}/global/routeTables")
def create_route_table(project: str, body: Dict[str, Any], db: Session = Depends(get_db)):
    """Create a new route table"""
    name = body.get("name")
    network = body.get("network", "default")
    
    if not name:
        raise HTTPException(status_code=400, detail="Route table name is required")
    
    # Check if route table already exists
    existing = db.query(RouteTable).filter(
        RouteTable.project_id == project,
        RouteTable.name == name
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail=f"Route table '{name}' already exists")
    
    # Create route table
    rt = RouteTable(
        name=name,
        project_id=project,
        network=network,
        description=body.get("description", ""),
        is_default=body.get("isDefault", False),
        created_at=datetime.utcnow()
    )
    
    db.add(rt)
    db.commit()
    db.refresh(rt)
    
    return {
        "kind": "compute#operation",
        "name": f"operation-{rt.id}",
        "operationType": "insert",
        "status": "DONE",
        "progress": 100,
        "targetLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/routeTables/{name}"
    }


@router.post("/compute/v1/projects/{project}/global/routeTables/{route_table_name}/addRoute")
def add_route_to_table(project: str, route_table_name: str, body: Dict[str, Any], db: Session = Depends(get_db)):
    """Add a route to a route table"""
    rt = db.query(RouteTable).filter(
        RouteTable.project_id == project,
        RouteTable.name == route_table_name
    ).first()
    
    if not rt:
        raise HTTPException(status_code=404, detail=f"Route table '{route_table_name}' not found")
    
    # Generate a route name if not provided
    dest_range = body.get("destRange")
    route_name = body.get("name") or f"{route_table_name}-route-{dest_range.replace('/', '-')}"
    
    # Create and add route
    route = Route(
        name=route_name,
        network=rt.network,
        project_id=project,
        description=body.get("description", ""),
        dest_range=dest_range,
        next_hop_gateway=body.get("nextHopGateway"),
        next_hop_instance=body.get("nextHopInstance"),
        next_hop_ip=body.get("nextHopIp"),
        next_hop_network=body.get("nextHopNetwork"),
        priority=body.get("priority", 1000),
        route_table_id=rt.id,
        created_at=datetime.utcnow()
    )
    
    db.add(route)
    db.commit()
    
    return {
        "kind": "compute#operation",
        "operationType": "insert",
        "status": "DONE",
        "progress": 100
    }


@router.delete("/compute/v1/projects/{project}/global/routeTables/{route_table_name}")
def delete_route_table(project: str, route_table_name: str, db: Session = Depends(get_db)):
    """Delete a route table"""
    rt = db.query(RouteTable).filter(
        RouteTable.project_id == project,
        RouteTable.name == route_table_name
    ).first()
    
    if not rt:
        raise HTTPException(status_code=404, detail=f"Route table '{route_table_name}' not found")
    
    # Cannot delete if subnets are associated
    associations = db.query(SubnetRouteTableAssociation).filter(
        SubnetRouteTableAssociation.route_table_id == rt.id
    ).all()
    
    if associations:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete route table with {len(associations)} associated subnets. Disassociate subnets first."
        )
    
    # Delete routes in this table
    routes = db.query(Route).filter(Route.route_table_id == rt.id).all()
    for route in routes:
        db.delete(route)
    
    # Delete the route table
    db.delete(rt)
    db.commit()
    
    return {
        "kind": "compute#operation",
        "name": f"operation-delete-{rt.name}",
        "operationType": "delete",
        "status": "DONE",
        "progress": 100
    }
