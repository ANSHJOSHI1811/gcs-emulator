"""Instance Groups API Router"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.database import get_db, InstanceGroup, InstanceGroupMember, Instance

router = APIRouter()


class NamedPort(BaseModel):
    name: str
    port: int


class InstanceGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    network: Optional[str] = "default"
    namedPorts: Optional[List[NamedPort]] = None
    labels: Optional[dict] = None


class InstanceGroupUpdate(BaseModel):
    description: Optional[str] = None
    namedPorts: Optional[List[NamedPort]] = None
    labels: Optional[dict] = None


def _to_dict(ig: InstanceGroup, project: str, zone: str) -> dict:
    """Convert InstanceGroup model to GCP API response format"""
    return {
        "kind": "compute#instanceGroup",
        "id": str(ig.id),
        "creationTimestamp": ig.created_at.isoformat() + "Z" if ig.created_at else None,
        "name": ig.name,
        "description": ig.description or "",
        "selfLink": (
            f"https://www.googleapis.com/compute/v1/projects/{project}"
            f"/zones/{zone}/instanceGroups/{ig.name}"
        ),
        "network": f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{ig.network}",
        "zone": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}",
        "status": ig.status,
        "size": 0,  # Will update with member count
        "namedPorts": ig.named_ports or [],
        "fingerprint": "",
        "labels": ig.labels or {},
    }


# ────────────────────────────────────────────────────────
# Instance Group endpoints
# ────────────────────────────────────────────────────────

@router.post("/projects/{project}/zones/{zone}/instanceGroups")
def create_instance_group(
    project: str,
    zone: str,
    body: InstanceGroupCreate,
    db: Session = Depends(get_db),
):
    """Create a new instance group"""
    # Check if group already exists
    existing = db.query(InstanceGroup).filter_by(
        project_id=project, zone=zone, name=body.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Instance group '{body.name}' already exists"
        )

    ig = InstanceGroup(
        name=body.name,
        project_id=project,
        zone=zone,
        description=body.description,
        network=body.network or "default",
        named_ports=[p.dict() for p in (body.namedPorts or [])],
        labels=body.labels or {},
        status="AVAILABLE",
    )
    db.add(ig)
    db.commit()
    db.refresh(ig)

    return _to_dict(ig, project, zone)


@router.get("/projects/{project}/zones/{zone}/instanceGroups")
def list_instance_groups(
    project: str,
    zone: str,
    filter: Optional[str] = Query(None),
    maxResults: Optional[int] = Query(500),
    pageToken: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List instance groups in a zone"""
    query = db.query(InstanceGroup).filter_by(project_id=project, zone=zone)
    
    groups = query.limit(maxResults).all()
    member_counts = {}
    
    for ig in groups:
        count = db.query(InstanceGroupMember).filter_by(
            instance_group_id=ig.id, project_id=project, zone=zone
        ).count()
        member_counts[ig.id] = count

    items = []
    for ig in groups:
        item = _to_dict(ig, project, zone)
        item["size"] = member_counts.get(ig.id, 0)
        items.append(item)

    return {
        "kind": "compute#instanceGroupList",
        "items": items,
        "selfLink": (
            f"https://www.googleapis.com/compute/v1/projects/{project}"
            f"/zones/{zone}/instanceGroups"
        ),
    }


@router.get("/projects/{project}/zones/{zone}/instanceGroups/{group_name}")
def get_instance_group(
    project: str,
    zone: str,
    group_name: str,
    db: Session = Depends(get_db),
):
    """Get a specific instance group"""
    ig = db.query(InstanceGroup).filter_by(
        project_id=project, zone=zone, name=group_name
    ).first()
    
    if not ig:
        raise HTTPException(status_code=404, detail="Instance group not found")

    result = _to_dict(ig, project, zone)
    
    # Add member count
    member_count = db.query(InstanceGroupMember).filter_by(
        instance_group_id=ig.id, project_id=project, zone=zone
    ).count()
    result["size"] = member_count

    return result


@router.delete("/projects/{project}/zones/{zone}/instanceGroups/{group_name}")
def delete_instance_group(
    project: str,
    zone: str,
    group_name: str,
    db: Session = Depends(get_db),
):
    """Delete an instance group"""
    ig = db.query(InstanceGroup).filter_by(
        project_id=project, zone=zone, name=group_name
    ).first()
    
    if not ig:
        raise HTTPException(status_code=404, detail="Instance group not found")

    # Remove all members
    db.query(InstanceGroupMember).filter_by(instance_group_id=ig.id).delete()
    
    # Delete the group
    db.delete(ig)
    db.commit()

    return {
        "kind": "compute#operation",
        "name": group_name,
        "operationType": "delete",
        "status": "DONE",
        "targetLink": (
            f"https://www.googleapis.com/compute/v1/projects/{project}"
            f"/zones/{zone}/instanceGroups/{group_name}"
        ),
    }


@router.post("/projects/{project}/zones/{zone}/instanceGroups/{group_name}/addInstances")
def add_instances_to_group(
    project: str,
    zone: str,
    group_name: str,
    body: dict,  # {"instances": [{"instance": "projects/{p}/zones/{z}/instances/{name}"}, ...]}
    db: Session = Depends(get_db),
):
    """Add instances to an instance group"""
    ig = db.query(InstanceGroup).filter_by(
        project_id=project, zone=zone, name=group_name
    ).first()
    
    if not ig:
        raise HTTPException(status_code=404, detail="Instance group not found")

    instances = body.get("instances", [])
    added_count = 0

    for inst_ref in instances:
        # Parse instance reference: "projects/{p}/zones/{z}/instances/{name}"
        inst_path = inst_ref.get("instance", "")
        parts = inst_path.split("/")
        if len(parts) >= 2:
            inst_name = parts[-1]
        else:
            inst_name = inst_ref.get("instance", "")

        # Verify instance exists
        instance = db.query(Instance).filter_by(
            project_id=project, zone=zone, name=inst_name
        ).first()
        
        if not instance:
            continue

        # Check if already a member
        existing = db.query(InstanceGroupMember).filter_by(
            instance_group_id=ig.id,
            instance_name=inst_name,
            project_id=project,
            zone=zone,
        ).first()

        if not existing:
            member = InstanceGroupMember(
                instance_group_id=ig.id,
                instance_name=inst_name,
                project_id=project,
                zone=zone,
                status=instance.status,
            )
            db.add(member)
            added_count += 1

    db.commit()

    return {
        "kind": "compute#operation",
        "name": group_name,
        "operationType": "addInstances",
        "status": "DONE",
    }


@router.post("/projects/{project}/zones/{zone}/instanceGroups/{group_name}/removeInstances")
def remove_instances_from_group(
    project: str,
    zone: str,
    group_name: str,
    body: dict,  # {"instances": [{"instance": "..."}, ...]}
    db: Session = Depends(get_db),
):
    """Remove instances from an instance group"""
    ig = db.query(InstanceGroup).filter_by(
        project_id=project, zone=zone, name=group_name
    ).first()
    
    if not ig:
        raise HTTPException(status_code=404, detail="Instance group not found")

    instances = body.get("instances", [])

    for inst_ref in instances:
        inst_path = inst_ref.get("instance", "")
        parts = inst_path.split("/")
        if len(parts) >= 2:
            inst_name = parts[-1]
        else:
            inst_name = inst_ref.get("instance", "")

        db.query(InstanceGroupMember).filter_by(
            instance_group_id=ig.id,
            instance_name=inst_name,
            project_id=project,
            zone=zone,
        ).delete()

    db.commit()

    return {
        "kind": "compute#operation",
        "name": group_name,
        "operationType": "removeInstances",
        "status": "DONE",
    }


@router.get("/projects/{project}/zones/{zone}/instanceGroups/{group_name}/listInstances")
def list_group_instances(
    project: str,
    zone: str,
    group_name: str,
    maxResults: Optional[int] = Query(500),
    db: Session = Depends(get_db),
):
    """List instances in an instance group"""
    ig = db.query(InstanceGroup).filter_by(
        project_id=project, zone=zone, name=group_name
    ).first()
    
    if not ig:
        raise HTTPException(status_code=404, detail="Instance group not found")

    members = db.query(InstanceGroupMember).filter_by(
        instance_group_id=ig.id, project_id=project, zone=zone
    ).limit(maxResults).all()

    items = []
    for member in members:
        items.append({
            "instance": (
                f"https://www.googleapis.com/compute/v1/projects/{project}"
                f"/zones/{zone}/instances/{member.instance_name}"
            ),
            "status": member.status,
        })

    return {
        "kind": "compute#instanceGroupsListInstances",
        "items": items,
    }
