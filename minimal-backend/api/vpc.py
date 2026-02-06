"""VPC Network API - Network Management"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Network, Instance, Subnet
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
            "IPv4Range": n.cidr_range if hasattr(n, 'cidr_range') else "10.128.0.0/16",
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
        "IPv4Range": network.cidr_range if hasattr(network, 'cidr_range') else "10.128.0.0/16",
        "autoCreateSubnetworks": network.auto_create_subnetworks,
        "creationTimestamp": network.creation_timestamp.isoformat() + "Z" if network.creation_timestamp else None,
        "dockerNetworkName": network.docker_network_name
    }

@router.post("/projects/{project}/global/networks")
def create_network(project: str, body: dict, db: Session = Depends(get_db)):
    """
    Create VPC network with custom CIDR (creates Docker network with IPAM)
    Auto-mode uses 10.128.0.0/9 and auto-creates subnets per region
    Example: {"name": "my-vpc", "IPv4Range": "10.99.0.0/16", "autoCreateSubnetworks": false}
    """
    import sys
    sys.path.insert(0, '/home/ubuntu/gcs-stimulator/minimal-backend')
    from docker_manager import create_docker_network_with_cidr
    from ip_manager import validate_cidr, get_gateway_ip
    from region_subnets import get_auto_mode_subnets, is_auto_mode_cidr
    
    name = body["name"]
    auto_create = body.get("autoCreateSubnetworks", True)
    
    # Auto-mode uses 10.128.0.0/9, custom mode uses provided CIDR
    if auto_create:
        cidr = "10.128.0.0/9"  # Fixed CIDR for auto-mode
    else:
        cidr = body.get("IPv4Range", "10.128.0.0/16")
    
    # Validate CIDR
    if not validate_cidr(cidr):
        raise HTTPException(status_code=400, detail=f"Invalid CIDR format: {cidr}")
    
    # Check if network exists
    existing = db.query(Network).filter_by(project_id=project, name=name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Network {name} already exists")
    
    # Create Docker network with custom CIDR
    # For auto-mode, use a unique Docker network CIDR
    if auto_create:
        docker_cidr = f"172.{16 + hash(project + name) % 16}.0.0/16"  # Unique per VPC
    else:
        docker_cidr = cidr
    
    docker_network_name = f"gcp-vpc-{project}-{name}"
    print(f"Creating Docker network: {docker_network_name} with CIDR {docker_cidr}")
    
    try:
        docker_network_id = create_docker_network_with_cidr(name, docker_cidr, project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create Docker network: {e}")
    
    # Create network record
    network = Network(
        name=name,
        project_id=project,
        docker_network_name=docker_network_name,
        cidr_range=cidr,
        auto_create_subnetworks=auto_create
    )
    
    db.add(network)
    db.commit()
    db.refresh(network)
    
    print(f"✅ Created VPC network {name} (ID: {network.id}) with Docker network {docker_network_name}")
    
    # Auto-create subnets if auto-mode is enabled
    if auto_create and is_auto_mode_cidr(cidr):
        print(f"Auto-mode enabled, creating subnets for all regions...")
        regions_data = get_auto_mode_subnets()
        
        for region_info in regions_data:
            region_name = region_info["name"]
            subnet_cidr = region_info["cidr"]
            subnet_name = f"{name}-{region_name}"
            
            # Create subnet record
            subnet = Subnet(
                name=subnet_name,
                network=f"projects/{project}/global/networks/{name}",
                region=region_name,
                ip_cidr_range=subnet_cidr,
                gateway_ip=get_gateway_ip(subnet_cidr),
                next_available_ip=2  # Start from .2 (.0=network, .1=gateway)
            )
            db.add(subnet)
        
        db.commit()
        print(f"✅ Auto-created {len(regions_data)} subnets for {name}")
    
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

# ============================================================================
# SUBNET MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/projects/{project}/regions/{region}/subnetworks")
def create_subnet(project: str, region: str, body: dict, db: Session = Depends(get_db)):
    """
    Create subnet in VPC network
    Example: {"name": "web-subnet", "network": "custom-vpc", "ipCidrRange": "10.99.1.0/24"}
    """
    import sys
    sys.path.insert(0, '/home/ubuntu/gcs-stimulator/minimal-backend')
    from ip_manager import validate_cidr, subnet_within_vpc, get_gateway_ip
    
    name = body.get("name")
    network_name = body.get("network", "").split("/")[-1]  # Extract name from URL
    cidr = body.get("ipCidrRange")
    
    if not name or not network_name or not cidr:
        raise HTTPException(status_code=400, detail="Missing required fields: name, network, ipCidrRange")
    
    # Validate CIDR
    if not validate_cidr(cidr):
        raise HTTPException(status_code=400, detail=f"Invalid CIDR format: {cidr}")
    
    # Get parent network
    network = db.query(Network).filter_by(project_id=project, name=network_name).first()
    if not network:
        raise HTTPException(status_code=404, detail=f"Network {network_name} not found")
    
    # Validate subnet is within VPC CIDR
    vpc_cidr = network.cidr_range if hasattr(network, 'cidr_range') and network.cidr_range else "10.128.0.0/16"
    if not subnet_within_vpc(vpc_cidr, cidr):
        raise HTTPException(
            status_code=400,
            detail=f"Subnet {cidr} is not within VPC range {vpc_cidr}"
        )
    
    # Check for existing subnet with same name
    existing = db.query(Subnet).filter_by(name=name, region=region).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Subnet {name} already exists in {region}")
    
    # Check for overlapping subnets
    existing_subnets = db.query(Subnet).filter_by(network=network_name).all()
    import ipaddress
    for existing in existing_subnets:
        # Check if ranges overlap
        try:
            new_net = ipaddress.ip_network(cidr, strict=False)
            exist_net = ipaddress.ip_network(existing.ip_cidr_range, strict=False)
            if new_net.overlaps(exist_net):
                raise HTTPException(
                    status_code=400,
                    detail=f"Subnet {cidr} overlaps with existing subnet {existing.name} ({existing.ip_cidr_range})"
                )
        except HTTPException:
            # Re-raise HTTPException (don't swallow validation errors!)
            raise
        except Exception as e:
            # Log but continue if there's a parsing error
            print(f"Warning: Could not validate overlap for {existing.name}: {e}")
            pass
    
    # Calculate gateway IP
    gateway = get_gateway_ip(cidr)
    
    # Create subnet (ID will be auto-generated as integer)
    subnet = Subnet(
        name=name,
        network=network_name,
        region=region,
        ip_cidr_range=cidr,
        gateway_ip=gateway,
        next_available_ip=2  # Start at .2 (skip .0 and .1)
    )
    db.add(subnet)
    db.commit()
    db.refresh(subnet)
    
    print(f"✅ Created subnet {name} in {network_name}: {cidr}, gateway {gateway}")
    
    operation_id = str(random.randint(1000000000000, 9999999999999))
    return {
        "kind": "compute#operation",
        "id": operation_id,
        "name": operation_id,
        "operationType": "insert",
        "targetLink": f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/subnetworks/{name}",
        "status": "DONE",
        "progress": 100,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/operations/{operation_id}"
    }

@router.get("/projects/{project}/aggregated/subnetworks")
def list_subnets_aggregated(project: str, db: Session = Depends(get_db)):
    """List all subnets across all regions (aggregated)"""
    # Get all networks for this project
    project_networks = db.query(Network).filter(Network.project_id == project).all()
    network_names = [net.name for net in project_networks]
    
    # Get all subnets for those networks
    subnets = db.query(Subnet).filter(Subnet.network.in_(network_names)).all()
    
    # Group by region
    items = {}
    for s in subnets:
        region_key = f"regions/{s.region}"
        if region_key not in items:
            items[region_key] = {
                "subnetworks": []
            }
        items[region_key]["subnetworks"].append({
            "kind": "compute#subnetwork",
            "name": s.name,
            "id": s.id,
            "network": s.network,
            "ipCidrRange": s.ip_cidr_range,
            "gatewayAddress": s.gateway_ip,
            "region": s.region,
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{s.region}/subnetworks/{s.name}",
            "creationTimestamp": s.created_at.isoformat() + "Z" if s.created_at else None
        })
    
    return {
        "kind": "compute#subnetworkAggregatedList",
        "items": items
    }

@router.get("/projects/{project}/regions/{region}/subnetworks")
def list_subnets(project: str, region: str, db: Session = Depends(get_db)):
    """List all subnets in a region"""
    subnets = db.query(Subnet).filter_by(region=region).all()
    
    return {
        "kind": "compute#subnetworkList",
        "items": [{
            "kind": "compute#subnetwork",
            "name": s.name,
            "id": s.id,
            "network": s.network,
            "ipCidrRange": s.ip_cidr_range,
            "gatewayAddress": s.gateway_ip,
            "region": s.region,
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/subnetworks/{s.name}",
            "creationTimestamp": s.created_at.isoformat() + "Z" if s.created_at else None
        } for s in subnets]
    }

@router.get("/projects/{project}/regions/{region}/subnetworks/{subnet_name}")
def get_subnet(project: str, region: str, subnet_name: str, db: Session = Depends(get_db)):
    """Get subnet details"""
    subnet = db.query(Subnet).filter_by(name=subnet_name, region=region).first()
    
    if not subnet:
        raise HTTPException(status_code=404, detail=f"Subnet {subnet_name} not found")
    
    return {
        "kind": "compute#subnetwork",
        "name": subnet.name,
        "id": subnet.id,
        "network": subnet.network,
        "ipCidrRange": subnet.ip_cidr_range,
        "gatewayAddress": subnet.gateway_ip,
        "region": subnet.region,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/subnetworks/{subnet.name}",
        "creationTimestamp": subnet.created_at.isoformat() + "Z" if subnet.created_at else None
    }

@router.delete("/projects/{project}/regions/{region}/subnetworks/{subnet_name}")
def delete_subnet(project: str, region: str, subnet_name: str, db: Session = Depends(get_db)):
    """Delete subnet"""
    subnet = db.query(Subnet).filter_by(name=subnet_name, region=region).first()
    
    if not subnet:
        raise HTTPException(status_code=404, detail=f"Subnet {subnet_name} not found")
    
    # Check if any instances are using this subnet
    instances = db.query(Instance).filter(Instance.subnet == subnet_name).first()
    if instances:
        raise HTTPException(
            status_code=400,
            detail=f"Subnet {subnet_name} is in use by instances. Delete instances first."
        )
    
    db.delete(subnet)
    db.commit()
    
    operation_id = str(random.randint(1000000000000, 9999999999999))
    return {
        "kind": "compute#operation",
        "id": operation_id,
        "name": operation_id,
        "operationType": "delete",
        "status": "DONE",
        "progress": 100,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/operations/{operation_id}"
    }
