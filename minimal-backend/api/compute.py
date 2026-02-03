"""Compute Engine API - VM Instances"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Instance, Zone, MachineType, Project
from docker_manager import create_container, stop_container, start_container, delete_container, get_container_status
import uuid

router = APIRouter()

@router.get("/projects/{project}/zones")
def list_zones(project: str, db: Session = Depends(get_db)):
    """List all zones"""
    zones = db.query(Zone).all()
    return {
        "kind": "compute#zoneList",
        "items": [{
            "name": z.name,
            "region": z.region,
            "status": z.status,
            "description": z.description or ""
        } for z in zones]
    }

@router.get("/projects/{project}/zones/{zone}/machineTypes")
def list_machine_types(project: str, zone: str, db: Session = Depends(get_db)):
    """List machine types in zone"""
    types = db.query(MachineType).filter_by(zone=zone).all()
    return {
        "kind": "compute#machineTypeList",
        "items": [{
            "name": t.name,
            "guestCpus": t.guest_cpus,
            "memoryMb": t.memory_mb,
            "zone": t.zone
        } for t in types]
    }

@router.get("/projects/{project}/zones/{zone}/instances")
def list_instances(project: str, zone: str, db: Session = Depends(get_db)):
    """List VM instances in zone"""
    instances = db.query(Instance).filter_by(project_id=project, zone=zone).all()
    
    items = []
    for i in instances:
        # Update status from Docker
        if i.container_id:
            docker_status = get_container_status(i.container_id)
            if docker_status == "running":
                i.status = "RUNNING"
            elif docker_status == "exited":
                i.status = "TERMINATED"
    
    return {
        "kind": "compute#instanceList",
        "items": [{
            "name": i.name,
            "id": i.id,
            "status": i.status,
            "machineType": f"zones/{i.zone}/machineTypes/{i.machine_type}",
            "zone": f"zones/{i.zone}",
            "networkInterfaces": [{
                "networkIP": i.internal_ip,
                "network": i.network_url
            }] if i.internal_ip else [],
            "dockerContainerId": i.container_id,  # Show in UI
            "dockerContainerName": i.container_name
        } for i in instances]
    }

@router.get("/projects/{project}/zones/{zone}/instances/{instance_name}")
def get_instance(project: str, zone: str, instance_name: str, db: Session = Depends(get_db)):
    """Get VM instance details"""
    instance = db.query(Instance).filter_by(
        project_id=project,
        zone=zone,
        name=instance_name
    ).first()
    
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Update status from Docker
    if instance.container_id:
        docker_status = get_container_status(instance.container_id)
        if docker_status == "running":
            instance.status = "RUNNING"
        elif docker_status == "exited":
            instance.status = "TERMINATED"
        db.commit()
    
    return {
        "name": instance.name,
        "id": instance.id,
        "status": instance.status,
        "machineType": f"zones/{instance.zone}/machineTypes/{instance.machine_type}",
        "zone": f"zones/{instance.zone}",
        "networkInterfaces": [{
            "networkIP": instance.internal_ip,
            "network": instance.network_url
        }] if instance.internal_ip else [],
        "dockerContainerId": instance.container_id,
        "dockerContainerName": instance.container_name
    }

@router.post("/projects/{project}/zones/{zone}/instances")
async def create_instance(project: str, zone: str, body: dict, db: Session = Depends(get_db)):
    """Create VM instance (creates Docker container)"""
    name = body["name"]
    machine_type = body.get("machineType", "e2-medium").split("/")[-1]
    
    # Check if instance exists
    existing = db.query(Instance).filter_by(project_id=project, zone=zone, name=name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Instance {name} already exists")
    
    # Create Docker container
    print(f"Creating Docker container for {name}...")
    container = create_container(name)
    
    # Create instance record
    instance = Instance(
        id=str(uuid.uuid4()),
        name=name,
        project_id=project,
        zone=zone,
        machine_type=machine_type,
        status="RUNNING",
        internal_ip=container["internal_ip"],
        container_id=container["container_id"],
        container_name=container["container_name"]
    )
    
    db.add(instance)
    db.commit()
    
    print(f"✅ Created instance {name} with container {container['container_id'][:12]}")
    
    return {
        "kind": "compute#operation",
        "status": "DONE",
        "targetLink": f"projects/{project}/zones/{zone}/instances/{name}",
        "operationType": "insert"
    }

@router.post("/projects/{project}/zones/{zone}/instances/{instance_name}/stop")
async def stop_instance(project: str, zone: str, instance_name: str, db: Session = Depends(get_db)):
    """Stop VM instance (stops Docker container)"""
    instance = db.query(Instance).filter_by(
        project_id=project,
        zone=zone,
        name=instance_name
    ).first()
    
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    if instance.container_id:
        stop_container(instance.container_id)
    
    instance.status = "TERMINATED"
    db.commit()
    
    print(f"✅ Stopped instance {instance_name}")
    
    return {
        "kind": "compute#operation",
        "status": "DONE",
        "operationType": "stop"
    }

@router.post("/projects/{project}/zones/{zone}/instances/{instance_name}/start")
async def start_instance(project: str, zone: str, instance_name: str, db: Session = Depends(get_db)):
    """Start VM instance (starts Docker container)"""
    instance = db.query(Instance).filter_by(
        project_id=project,
        zone=zone,
        name=instance_name
    ).first()
    
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    if instance.container_id:
        start_container(instance.container_id)
    
    instance.status = "RUNNING"
    db.commit()
    
    print(f"✅ Started instance {instance_name}")
    
    return {
        "kind": "compute#operation",
        "status": "DONE",
        "operationType": "start"
    }

@router.delete("/projects/{project}/zones/{zone}/instances/{instance_name}")
async def delete_instance(project: str, zone: str, instance_name: str, db: Session = Depends(get_db)):
    """Delete VM instance (deletes Docker container)"""
    instance = db.query(Instance).filter_by(
        project_id=project,
        zone=zone,
        name=instance_name
    ).first()
    
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Delete Docker container
    if instance.container_id:
        delete_container(instance.container_id)
    
    db.delete(instance)
    db.commit()
    
    print(f"✅ Deleted instance {instance_name}")
    
    return {
        "kind": "compute#operation",
        "status": "DONE",
        "operationType": "delete"
    }
