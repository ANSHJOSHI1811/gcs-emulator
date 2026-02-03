"""VPC Network API - Network Management"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Network, Instance
import docker
import uuid
import random

router = APIRouter()
client = docker.from_env()

def ensure_default_network(db: Session, project: str):
    """Ensure default network exists for project"""
    default = db.query(Network).filter_by(project_id=project, name="default").first()
    if not default:
        # Create default network record (maps to Docker bridge)
        default = Network(
            name="default",
            project_id=project,
            docker_network_name="bridge",  # Use Docker's default bridge
            auto_create_subnetworks=True
        )
        db.add(default)
        db.commit()
        db.refresh(default)
        print(f"✅ Created default network for project {project} (ID: {default.id})")
    return default

@router.get("/projects/{project}/global/networks")
def list_networks(project: str, db: Session = Depends(get_db)):
    """List all VPC networks in project"""
    # Ensure default network exists
    ensure_default_network(db, project)
    
    networks = db.query(Network).filter_by(project_id=project).all()
    
    return {
        "kind": "compute#networkList",
        "items": [{
            "kind": "compute#network",
            "name": n.name,
            "id": n.id,
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{n.name}",
            "autoCreateSubnetworks": n.auto_create_subnetworks,
            "creationTimestamp": n.creation_timestamp.isoformat() + "Z" if n.creation_timestamp else None,
            "dockerNetworkName": n.docker_network_name
        } for n in networks]
    }

@router.get("/projects/{project}/global/networks/{network_name}")
def get_network(project: str, network_name: str, db: Session = Depends(get_db)):
    """Get VPC network details"""
    network = db.query(Network).filter_by(
        project_id=project,
        name=network_name
    ).first()
    
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    
    return {
        "kind": "compute#network",
        "name": network.name,
        "id": network.id,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{network.name}",
        "autoCreateSubnetworks": network.auto_create_subnetworks,
        "creationTimestamp": network.creation_timestamp.isoformat() + "Z" if network.creation_timestamp else None,
        "dockerNetworkName": network.docker_network_name
    }

@router.post("/projects/{project}/global/networks")
def create_network(project: str, body: dict, db: Session = Depends(get_db)):
    """
    Create VPC network (creates Docker network)
    Example: {"name": "my-vpc", "autoCreateSubnetworks": false}
    """
    name = body["name"]
    
    # Check if network exists
    existing = db.query(Network).filter_by(project_id=project, name=name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Network {name} already exists")
    
    # Create Docker network
    docker_network_name = f"gcp-vpc-{project}-{name}"
    print(f"Creating Docker network: {docker_network_name}")
    
    try:
        docker_network = client.networks.create(
            docker_network_name,
            driver="bridge",
            labels={
                "gcp-project": project,
                "gcp-network": name
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create Docker network: {e}")
    
    # Create network record
    network = Network(
        name=name,
        project_id=project,
        docker_network_name=docker_network_name,
        auto_create_subnetworks=body.get("autoCreateSubnetworks", True)
    )
    
    db.add(network)
    db.commit()
    db.refresh(network)
    
    print(f"✅ Created VPC network {name} (ID: {network.id}) with Docker network {docker_network_name}")
    
    operation_id = str(random.randint(1000000000000, 9999999999999))
    return {
        "kind": "compute#operation",
        "id": operation_id,
        "name": operation_id,
        "operationType": "insert",
        "targetLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{name}",
        "status": "DONE",
        "progress": 100,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/operations/{operation_id}"
    }

@router.delete("/projects/{project}/global/networks/{network_name}")
def delete_network(project: str, network_name: str, db: Session = Depends(get_db)):
    """Delete VPC network (deletes Docker network)"""
    network = db.query(Network).filter_by(
        project_id=project,
        name=network_name
    ).first()
    
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    
    # Cannot delete default network
    if network.name == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default network")
    
    # Check if any instances are using this network
    instances = db.query(Instance).filter(
        Instance.project_id == project,
        Instance.network_url.like(f"%{network_name}%")
    ).first()
    
    if instances:
        raise HTTPException(
            status_code=400, 
            detail=f"Network {network_name} is in use by instances. Delete instances first."
        )
    
    # Delete Docker network
    if network.docker_network_name and network.docker_network_name != "bridge":
        try:
            docker_net = client.networks.get(network.docker_network_name)
            docker_net.remove()
            print(f"✅ Deleted Docker network {network.docker_network_name}")
        except docker.errors.NotFound:
            print(f"Warning: Docker network {network.docker_network_name} not found")
        except Exception as e:
            print(f"Warning: Failed to delete Docker network: {e}")
    
    db.delete(network)
    db.commit()
    
    operation_id = str(random.randint(1000000000000, 9999999999999))
    return {
        "kind": "compute#operation",
        "id": operation_id,
        "name": operation_id,
        "operationType": "delete",
        "status": "DONE",
        "progress": 100,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/operations/{operation_id}"
    }
