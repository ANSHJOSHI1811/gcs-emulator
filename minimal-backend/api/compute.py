"""Compute Engine API - VM Instances"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Instance, Zone, MachineType, Project, Network, Subnet
from docker_manager import create_container, stop_container, start_container, delete_container, get_container_status
from ip_manager import get_ip_at_offset
import uuid
import random

router = APIRouter()


def _internet_gateway_resource(project: str) -> dict:
    """Return static control-plane internet gateway representation.

    This is a demo-only resource used for visibility. Data-plane NAT
    is still provided by Docker bridge on the host.
    """
    self_link = (
        f"https://www.googleapis.com/compute/v1/projects/"
        f"{project}/global/internetGateways/default-internet-gateway"
    )
    return {
        "kind": "compute#internetGateway",
        "id": "default-internet-gateway",
        "name": "default-internet-gateway",
        "network": (
            f"https://www.googleapis.com/compute/v1/projects/"
            f"{project}/global/networks/default"
        ),
        "status": "ACTIVE",
        "backing": "docker-bridge-nat",
        "selfLink": self_link,
    }


@router.get("/projects/{project}/global/internetGateways")
def list_internet_gateways(project: str):
    """List demo internet gateways (control-plane only).

    Always returns a single default-internet-gateway backed by Docker NAT.
    """
    return {
        "kind": "compute#internetGatewayList",
        "items": [
            _internet_gateway_resource(project)
        ],
    }


@router.get("/projects/{project}/global/internetGateways/default-internet-gateway")
def get_internet_gateway(project: str):
    """Get the default demo internet gateway (control-plane only)."""
    return _internet_gateway_resource(project)

@router.post("/projects/{project}/zones/{zone}/operations/{operation}/wait")
def wait_operation(project: str, zone: str, operation: str):
    """Operation wait endpoint - all operations complete immediately"""
    return {
        "kind": "compute#operation",
        "id": operation,
        "name": operation,
        "zone": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}",
        "status": "DONE",
        "progress": 100,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/operations/{operation}"
    }

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
            "description": z.description or "",
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{z.name}"
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
    
    # Commit status changes to database
    db.commit()
    
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
                "network": i.network_url,
                "accessConfigs": [
                    {
                        "type": "ONE_TO_ONE_NAT",
                        "natIP": "127.0.0.1",
                    }
                ],
            }] if i.internal_ip else [],
            "dockerContainerId": i.container_id,  # Show in UI
            "dockerContainerName": i.container_name,
        } for i in instances],
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
        "kind": "compute#instance",
        "name": instance.name,
        "id": str(instance.id),
        "status": instance.status,
        "machineType": f"zones/{instance.zone}/machineTypes/{instance.machine_type}",
        "zone": f"zones/{instance.zone}",
        "networkInterfaces": [{
            "network": f"https://www.googleapis.com/compute/v1/projects/{project}/{instance.network_url}",
            "networkIP": instance.internal_ip,
            "name": "nic0",
            "accessConfigs": [
                {
                    "type": "ONE_TO_ONE_NAT",
                    "natIP": "127.0.0.1",
                }
            ],
        }] if instance.internal_ip else [],
        "dockerContainerId": instance.container_id,
        "dockerContainerName": instance.container_name,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{instance.zone}/instances/{instance.name}"
    }

@router.post("/projects/{project}/zones/{zone}/instances")
async def create_instance(project: str, zone: str, body: dict, db: Session = Depends(get_db)):
    """Create VM instance (creates Docker container) with IP allocated from subnet"""
    name = body["name"]
    machine_type = body.get("machineType", "e2-medium").split("/")[-1]
    
    # Check if instance exists
    existing = db.query(Instance).filter_by(project_id=project, zone=zone, name=name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Instance {name} already exists")
    
    # Extract network and subnet from request or use default
    network_name = "default"
    network_url = "global/networks/default"
    subnet_name = "default"
    subnetwork_url = None
    
    if "networkInterfaces" in body and body["networkInterfaces"]:
        network = body["networkInterfaces"][0].get("network", "")
        if network:
            network_name = network.split("/")[-1] if "/" in network else network
            network_url = f"global/networks/{network_name}"
        
        # Extract subnetwork if provided
        subnetwork = body["networkInterfaces"][0].get("subnetwork", "")
        if subnetwork:
            subnet_name = subnetwork.split("/")[-1] if "/" in subnetwork else subnetwork
            subnetwork_url = f"regions/{zone.rsplit('-', 1)[0]}/subnetworks/{subnet_name}"
    
    # Lookup subnet for IP allocation
    subnet_record = db.query(Subnet).filter_by(name=subnet_name).first()
    if not subnet_record:
        raise HTTPException(status_code=404, detail=f"Subnet {subnet_name} not found")
    
    # Allocate IP from subnet CIDR range
    next_offset = subnet_record.next_available_ip
    allocated_ip = get_ip_at_offset(subnet_record.ip_cidr_range, next_offset)
    
    if not allocated_ip:
        raise HTTPException(
            status_code=400, 
            detail=f"Subnet {subnet_name} has no available IPs. CIDR: {subnet_record.ip_cidr_range}"
        )
    
    # Lookup Docker network name from database
    network_record = db.query(Network).filter_by(
        project_id=project,
        name=network_name
    ).first()
    
    if not network_record:
        raise HTTPException(status_code=404, detail=f"Network {network_name} not found")
    
    docker_network_name = network_record.docker_network_name
    print(f"Creating instance {name} on network {network_name}, subnet {subnet_name} with IP {allocated_ip}")
    
    # Create Docker container with allocated IP
    container = create_container(name, network=docker_network_name, ip_address=allocated_ip)
    
    # Increment subnet's next available IP
    subnet_record.next_available_ip = next_offset + 1
    db.add(subnet_record)  # Explicitly add to session
    
    # Create instance record (ID will be auto-generated as integer)
    instance = Instance(
        name=name,
        project_id=project,
        zone=zone,
        machine_type=machine_type,
        status="RUNNING",
        internal_ip=allocated_ip,
        container_id=container["container_id"],
        container_name=container["container_name"],
        network_url=network_url,
        subnetwork_url=subnetwork_url,
        subnet=subnet_name
    )
    
    db.add(instance)
    db.commit()
    db.refresh(instance)  # Get the auto-generated ID
    
    print(f"✅ Created instance {name} (ID: {instance.id}) with container {container['container_id'][:12]} on network {docker_network_name}")
    
    import random
    operation_id = str(random.randint(1000000000000, 9999999999999))
    return {
        "kind": "compute#operation",
        "id": operation_id,
        "name": operation_id,
        "zone": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}",
        "operationType": "insert",
        "targetLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{name}",
        "targetId": str(instance.id),
        "status": "DONE",
        "user": "user@example.com",
        "progress": 100,
        "insertTime": instance.created_at.isoformat() + "Z",
        "startTime": instance.created_at.isoformat() + "Z",
        "endTime": instance.created_at.isoformat() + "Z",
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/operations/{operation_id}"
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
    
    import random
    operation_id = str(random.randint(1000000000000, 9999999999999))
    return {
        "kind": "compute#operation",
        "id": operation_id,
        "name": operation_id,
        "zone": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}",
        "operationType": "stop",
        "targetLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{instance_name}",
        "status": "DONE",
        "user": "user@example.com",
        "progress": 100,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/operations/{operation_id}"
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
    
    import random
    operation_id = str(random.randint(1000000000000, 9999999999999))
    return {
        "kind": "compute#operation",
        "id": operation_id,
        "name": operation_id,
        "zone": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}",
        "operationType": "start",
        "targetLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{instance_name}",
        "status": "DONE",
        "user": "user@example.com",
        "progress": 100,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/operations/{operation_id}"
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
    
    import random
    operation_id = str(random.randint(1000000000000, 9999999999999))
    return {
        "kind": "compute#operation",
        "id": operation_id,
        "name": operation_id,
        "zone": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}",
        "operationType": "delete",
        "targetLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{instance_name}",
        "status": "DONE",
        "user": "user@example.com",
        "progress": 100,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/operations/{operation_id}"
    }
