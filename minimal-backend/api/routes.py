"""VPC Routes API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime
from database import get_db, Route

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
