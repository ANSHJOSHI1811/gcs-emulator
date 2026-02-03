"""VPC Network API - Network Management"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Network
import docker
import uuid

router = APIRouter()
client = docker.from_env()

@router.get("/projects/{project}/global/networks")
def list_networks(project: str, db: Session = Depends(get_db)):
    """List all VPC networks in project"""
    networks = db.query(Network).filter_by(project_id=project).all()
    
    return {
        "kind": "compute#networkList",
        "items": [{
            "name": n.name,
            "id": n.id,
            "description": n.description or "",
            "autoCreateSubnetworks": n.auto_create_subnetworks,
            "routingMode": n.routing_mode,
            "dockerNetworkId": n.docker_network_id,
            "dockerNetworkName": n.docker_network_name,
            "selfLink": f"global/networks/{n.name}"
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
        "name": network.name,
        "id": network.id,
        "description": network.description or "",
        "autoCreateSubnetworks": network.auto_create_subnetworks,
        "routingMode": network.routing_mode,
        "dockerNetworkId": network.docker_network_id,
        "dockerNetworkName": network.docker_network_name,
        "selfLink": f"global/networks/{network.name}"
    }

@router.post("/projects/{project}/global/networks")
async def create_network(project: str, body: dict, db: Session = Depends(get_db)):
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
        docker_network_id = docker_network.id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create Docker network: {e}")
    
    # Create network record
    network = Network(
        id=str(uuid.uuid4()),
        name=name,
        project_id=project,
        description=body.get("description", ""),
        auto_create_subnetworks=body.get("autoCreateSubnetworks", True),
        routing_mode=body.get("routingMode", "REGIONAL"),
        docker_network_id=docker_network_id,
        docker_network_name=docker_network_name
    )
    
    db.add(network)
    db.commit()
    
    print(f"✅ Created VPC network {name} with Docker network {docker_network_name}")
    
    return {
        "kind": "compute#operation",
        "status": "DONE",
        "targetLink": f"projects/{project}/global/networks/{name}",
        "operationType": "insert"
    }

@router.delete("/projects/{project}/global/networks/{network_name}")
async def delete_network(project: str, network_name: str, db: Session = Depends(get_db)):
    """Delete VPC network (deletes Docker network)"""
    network = db.query(Network).filter_by(
        project_id=project,
        name=network_name
    ).first()
    
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    
    # Delete Docker network
    if network.docker_network_id:
        try:
            docker_net = client.networks.get(network.docker_network_id)
            docker_net.remove()
            print(f"✅ Deleted Docker network {network.docker_network_name}")
        except Exception as e:
            print(f"Warning: Failed to delete Docker network: {e}")
    
    db.delete(network)
    db.commit()
    
    return {
        "kind": "compute#operation",
        "status": "DONE",
        "operationType": "delete"
    }
