"""Firewall Rules API - Network Security"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Firewall, Network
from pydantic import BaseModel
from typing import List, Optional, Dict
import random

router = APIRouter()


class FirewallAllowedDenied(BaseModel):
    """Allowed or denied protocol/port configuration"""
    IPProtocol: str
    ports: Optional[List[str]] = None


class FirewallRequest(BaseModel):
    """Request to create firewall rule"""
    name: str
    network: str
    description: Optional[str] = None
    direction: Optional[str] = "INGRESS"
    priority: Optional[int] = 1000
    sourceRanges: Optional[List[str]] = None
    destinationRanges: Optional[List[str]] = None
    sourceTags: Optional[List[str]] = None
    targetTags: Optional[List[str]] = None
    allowed: Optional[List[Dict]] = None
    denied: Optional[List[Dict]] = None
    disabled: Optional[bool] = False


@router.get("/projects/{project}/global/firewalls")
def list_firewalls(project: str, db: Session = Depends(get_db)):
    """List all firewall rules in project"""
    firewalls = db.query(Firewall).filter_by(project_id=project).all()
    
    return {
        "kind": "compute#firewallList",
        "items": [{
            "kind": "compute#firewall",
            "id": str(fw.id),
            "name": fw.name,
            "network": fw.network,
            "description": fw.description,
            "direction": fw.direction,
            "priority": fw.priority,
            "sourceRanges": fw.source_ranges,
            "destinationRanges": fw.destination_ranges,
            "sourceTags": fw.source_tags,
            "targetTags": fw.target_tags,
            "allowed": fw.allowed,
            "denied": fw.denied,
            "disabled": fw.disabled,
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/firewalls/{fw.name}",
            "creationTimestamp": fw.created_at.isoformat() + "Z" if fw.created_at else None
        } for fw in firewalls]
    }


@router.get("/projects/{project}/global/firewalls/{firewall_name}")
def get_firewall(project: str, firewall_name: str, db: Session = Depends(get_db)):
    """Get firewall rule details"""
    firewall = db.query(Firewall).filter_by(name=firewall_name, project_id=project).first()
    
    if not firewall:
        raise HTTPException(status_code=404, detail=f"Firewall {firewall_name} not found")
    
    return {
        "kind": "compute#firewall",
        "id": str(firewall.id),
        "name": firewall.name,
        "network": firewall.network,
        "description": firewall.description,
        "direction": firewall.direction,
        "priority": firewall.priority,
        "sourceRanges": firewall.source_ranges,
        "destinationRanges": firewall.destination_ranges,
        "sourceTags": firewall.source_tags,
        "targetTags": firewall.target_tags,
        "allowed": firewall.allowed,
        "denied": firewall.denied,
        "disabled": firewall.disabled,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/firewalls/{firewall.name}",
        "creationTimestamp": firewall.created_at.isoformat() + "Z" if firewall.created_at else None
    }


@router.post("/projects/{project}/global/firewalls")
def create_firewall(project: str, request: FirewallRequest, db: Session = Depends(get_db)):
    """Create firewall rule"""
    # Check if firewall already exists
    existing = db.query(Firewall).filter_by(name=request.name, project_id=project).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Firewall {request.name} already exists")
    
    # Verify network exists
    network_name = request.network.split('/')[-1] if '/' in request.network else request.network
    network = db.query(Network).filter_by(name=network_name, project_id=project).first()
    if not network:
        raise HTTPException(status_code=404, detail=f"Network {network_name} not found")
    
    # Create firewall rule
    firewall = Firewall(
        name=request.name,
        network=f"projects/{project}/global/networks/{network_name}",
        project_id=project,
        description=request.description,
        direction=request.direction,
        priority=request.priority,
        source_ranges=request.sourceRanges,
        destination_ranges=request.destinationRanges,
        source_tags=request.sourceTags,
        target_tags=request.targetTags,
        allowed=request.allowed,
        denied=request.denied,
        disabled=request.disabled
    )
    
    db.add(firewall)
    db.commit()
    db.refresh(firewall)
    
    print(f"✅ Created firewall rule {request.name} for network {network_name}")
    
    operation_id = str(random.randint(1000000000000, 9999999999999))
    return {
        "kind": "compute#operation",
        "id": operation_id,
        "name": operation_id,
        "operationType": "insert",
        "targetLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/firewalls/{request.name}",
        "status": "DONE",
        "progress": 100,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/operations/{operation_id}"
    }


@router.patch("/projects/{project}/global/firewalls/{firewall_name}")
def update_firewall(project: str, firewall_name: str, request: FirewallRequest, db: Session = Depends(get_db)):
    """Update firewall rule"""
    firewall = db.query(Firewall).filter_by(name=firewall_name, project_id=project).first()
    
    if not firewall:
        raise HTTPException(status_code=404, detail=f"Firewall {firewall_name} not found")
    
    # Update fields
    if request.description is not None:
        firewall.description = request.description
    if request.direction is not None:
        firewall.direction = request.direction
    if request.priority is not None:
        firewall.priority = request.priority
    if request.sourceRanges is not None:
        firewall.source_ranges = request.sourceRanges
    if request.destinationRanges is not None:
        firewall.destination_ranges = request.destinationRanges
    if request.sourceTags is not None:
        firewall.source_tags = request.sourceTags
    if request.targetTags is not None:
        firewall.target_tags = request.targetTags
    if request.allowed is not None:
        firewall.allowed = request.allowed
    if request.denied is not None:
        firewall.denied = request.denied
    if request.disabled is not None:
        firewall.disabled = request.disabled
    
    db.commit()
    
    print(f"✅ Updated firewall rule {firewall_name}")
    
    operation_id = str(random.randint(1000000000000, 9999999999999))
    return {
        "kind": "compute#operation",
        "id": operation_id,
        "name": operation_id,
        "operationType": "update",
        "targetLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/firewalls/{firewall_name}",
        "status": "DONE",
        "progress": 100,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/operations/{operation_id}"
    }


@router.delete("/projects/{project}/global/firewalls/{firewall_name}")
def delete_firewall(project: str, firewall_name: str, db: Session = Depends(get_db)):
    """Delete firewall rule"""
    firewall = db.query(Firewall).filter_by(name=firewall_name, project_id=project).first()
    
    if not firewall:
        raise HTTPException(status_code=404, detail=f"Firewall {firewall_name} not found")
    
    db.delete(firewall)
    db.commit()
    
    print(f"✅ Deleted firewall rule {firewall_name}")
    
    operation_id = str(random.randint(1000000000000, 9999999999999))
    return {
        "kind": "compute#operation",
        "id": operation_id,
        "name": operation_id,
        "operationType": "delete",
        "targetLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/firewalls/{firewall_name}",
        "status": "DONE",
        "progress": 100,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/operations/{operation_id}"
    }
