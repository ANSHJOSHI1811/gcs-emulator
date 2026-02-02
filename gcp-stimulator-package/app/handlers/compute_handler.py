"""
Compute Engine handler - Instance management with Docker integration
"""
import secrets
import docker
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.factory import db
from app.models.compute import Instance, Zone, MachineType
from app.models.project import Project
from app.models.vpc import NetworkInterface, Network, Subnetwork, Address
from app.services.ip_allocation_service import IPAllocationService
from app.services.external_ip_service import ExternalIPPoolService
from app.utils.operation_utils import create_operation
from app.handlers.errors import error_response
import uuid

compute_bp = Blueprint("compute", __name__)

# Docker client (will be initialized lazily)
docker_client = None


def get_docker_client():
    """Get or initialize Docker client"""
    global docker_client
    if docker_client is None:
        try:
            docker_client = docker.from_env()
        except Exception as e:
            print(f"Warning: Docker not available: {e}")
            docker_client = None
    return docker_client


def _create_default_network_interface(instance: Instance, project_id: str):
    """Create default network interface for an instance"""
    try:
        # Get default or auto network
        network = Network.query.filter_by(project_id=project_id, name="default").first()
        if not network:
            network = Network.query.filter_by(project_id=project_id, name="auto-network").first()
        
        if not network:
            print(f"No default/auto-network found for project {project_id}")
            return None
        
        # Get zone region
        zone = instance.zone
        region = "-".join(zone.split("-")[:-1])
        
        # Get subnet in instance's region
        subnetwork = Subnetwork.query.filter_by(network_id=network.id, region=region).first()
        if not subnetwork:
            print(f"No subnet found for network in region {region}")
            return None
        
        # Allocate IP
        network_ip = IPAllocationService.allocate_ip(subnetwork)
        if not network_ip:
            print(f"No available IPs in subnet {subnetwork.name}")
            return None
        
        # Create interface
        interface = NetworkInterface(
            id=uuid.uuid4(),
            instance_id=instance.id,
            network_id=network.id,
            subnetwork_id=subnetwork.id,
            name="nic0",
            network_ip=network_ip,
            network_tier="PREMIUM",
            nic_index=0,
            creation_timestamp=datetime.utcnow()
        )
        
        db.session.add(interface)
        db.session.commit()
        return interface
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating default network interface: {e}")
        return None


# ========== Zones ==========

@compute_bp.route("/compute/v1/projects/<project_id>/zones", methods=["GET"])
def list_zones(project_id):
    """List all zones"""
    zones = Zone.query.all()
    
    return jsonify({
        "kind": "compute#zoneList",
        "items": [zone.to_dict(project_id) for zone in zones]
    })


@compute_bp.route("/compute/v1/projects/<project_id>/zones/<zone_name>", methods=["GET"])
def get_zone(project_id, zone_name):
    """Get zone details"""
    zone = Zone.query.filter_by(name=zone_name).first()
    if not zone:
        return error_response(404, "NOT_FOUND", f"Zone {zone_name} not found")
    
    return jsonify(zone.to_dict(project_id))


# ========== Machine Types ==========

@compute_bp.route("/compute/v1/projects/<project_id>/zones/<zone_name>/machineTypes", methods=["GET"])
def list_machine_types(project_id, zone_name):
    """List machine types in a zone"""
    machine_types = MachineType.query.filter_by(zone=zone_name).all()
    
    return jsonify({
        "kind": "compute#machineTypeList",
        "items": [mt.to_dict(project_id) for mt in machine_types]
    })


@compute_bp.route("/compute/v1/projects/<project_id>/zones/<zone_name>/machineTypes/<machine_type_name>", methods=["GET"])
def get_machine_type(project_id, zone_name, machine_type_name):
    """Get details of a specific machine type"""
    machine_type = MachineType.query.filter_by(zone=zone_name, name=machine_type_name).first()
    
    if not machine_type:
        from app.handlers.errors import error_response
        return error_response(404, "NOT_FOUND", f"Machine type {machine_type_name} not found in zone {zone_name}")
    
    return jsonify(machine_type.to_dict(project_id))


# ========== Instances ==========

@compute_bp.route("/compute/v1/projects/<project_id>/zones/<zone_name>/instances", methods=["POST"])
def create_instance(project_id, zone_name):
    """
    Create a compute instance
    This will spawn a Docker container as the backing "VM"
    """
    data = request.get_json()
    name = data.get("name")
    machine_type = data.get("machineType", "e2-micro")
    
    if not name:
        return error_response(400, "INVALID_ARGUMENT", "Instance name is required")
    
    # Check if project and zone exist
    project = Project.query.filter_by(id=project_id).first()
    if not project:
        return error_response(404, "NOT_FOUND", f"Project {project_id} not found")
    
    zone = Zone.query.filter_by(name=zone_name).first()
    if not zone:
        return error_response(404, "NOT_FOUND", f"Zone {zone_name} not found")
    
    # Check if instance already exists
    existing = Instance.query.filter_by(
        project_id=project_id,
        zone=zone_name,
        name=name
    ).first()
    
    if existing:
        return error_response(409, "ALREADY_EXISTS", f"Instance {name} already exists in zone {zone_name}")
    
    # Generate unique ID
    instance_id = str(secrets.randbelow(10**19))
    
    # Extract disk and network info
    disks = data.get("disks", [])
    source_image = disks[0].get("initializeParams", {}).get("sourceImage", "debian-11") if disks else "debian-11"
    disk_size_gb = int(disks[0].get("initializeParams", {}).get("diskSizeGb", 10)) if disks else 10
    
    network_interfaces = data.get("networkInterfaces", [{}])
    
    # Check for external IP request in access configs
    request_external_ip = False
    static_external_ip = None
    if network_interfaces and len(network_interfaces) > 0:
        access_configs = network_interfaces[0].get("accessConfigs", [])
        if access_configs and len(access_configs) > 0:
            request_external_ip = True
            # Check if user specified a static IP
            static_external_ip = access_configs[0].get("natIP")
    
    # Service account
    service_accounts = data.get("serviceAccounts", [])
    service_account_email = service_accounts[0].get("email") if service_accounts else None
    service_account_scopes = service_accounts[0].get("scopes", []) if service_accounts else []
    
    # Create instance record
    instance = Instance(
        id=instance_id,
        project_id=project_id,
        name=name,
        zone=zone_name,
        machine_type=machine_type,
        status="PROVISIONING",
        source_image=source_image,
        disk_size_gb=disk_size_gb,
        instance_metadata=data.get("metadata", {}),
        labels=data.get("labels", {}),
        tags=data.get("tags", {}).get("items", []),
        service_account_email=service_account_email,
        service_account_scopes=service_account_scopes,
    )
    
    db.session.add(instance)
    db.session.commit()
    
    # Spawn Docker container (async in real implementation)
    try:
        container_name = f"gce-{project_id}-{zone_name}-{name}"
        client = get_docker_client()
        
        if client:
            # Determine image based on source_image
            docker_image = "ubuntu:22.04"  # Default
            if "debian" in source_image.lower():
                docker_image = "debian:11"
            elif "ubuntu" in source_image.lower():
                docker_image = "ubuntu:22.04"
            elif "alpine" in source_image.lower():
                docker_image = "alpine:latest"
            
            # Get VPC network for Docker network attachment (REQUIRED)
            docker_network = None
            network_name = None
            
            if network_interfaces and len(network_interfaces) > 0:
                network_url = network_interfaces[0].get('network', '')
                # Extract network name from URL like "global/networks/default"
                if 'networks/' in network_url:
                    network_name = network_url.split('networks/')[-1]
            
            # If no network specified, use default
            if not network_name:
                network_name = 'default'
            
            # Get VPC network and ensure it has a Docker network
            vpc_network = Network.query.filter_by(project_id=project_id, name=network_name).first()
            
            if not vpc_network:
                # Create default network if it doesn't exist
                from app.handlers.network_handler import create_default_network
                vpc_network = create_default_network(project_id)
            
            # Ensure the VPC has a Docker network
            if not vpc_network.docker_network_name:
                # Create Docker network for this VPC
                from app.handlers.network_handler import _create_docker_network_for_vpc
                docker_net_id, docker_net_name = _create_docker_network_for_vpc(
                    vpc_network.name, 
                    project_id, 
                    None
                )
                if docker_net_id:
                    vpc_network.docker_network_id = docker_net_id
                    vpc_network.docker_network_name = docker_net_name
                    db.session.commit()
            
            docker_network = vpc_network.docker_network_name
            
            # Validate Docker network exists
            if not docker_network:
                raise Exception(f"Failed to get or create Docker network for VPC '{network_name}'. All instances must be in a VPC network.")
            
            # Create container with VPC network attachment
            container = client.containers.run(
                docker_image,
                name=container_name,
                detach=True,
                command="tail -f /dev/null",  # Keep container running
                network=docker_network,  # Attach to VPC Docker network
                labels={
                    "gcp-stimulator": "true",
                    "project": project_id,
                    "zone": zone_name,
                    "instance": name,
                    "vpc-network": docker_network or "default",
                },
                remove=False,
            )
            
            # Update instance with container info
            instance.container_id = container.id
            instance.container_name = container_name
            instance.status = "RUNNING"
            
            db.session.commit()
            
            # Create default network interface with real IP allocation
            interface = _create_default_network_interface(instance, project_id)
            if interface:
                # Update instance with allocated IP (for backward compatibility)
                instance.internal_ip = interface.network_ip
                db.session.commit()
            
            # Handle external IP if requested
            if request_external_ip:
                region = "-".join(zone_name.split("-")[:-1])
                try:
                    if static_external_ip:
                        # Use the specified static IP
                        addr_obj = Address.query.filter_by(
                            project_id=project_id,
                            address=static_external_ip
                        ).first()
                        if addr_obj and addr_obj.status == 'RESERVED':
                            ExternalIPPoolService.mark_in_use(addr_obj, instance.id, interface.id if interface else None)
                            instance.external_ip = static_external_ip
                        else:
                            print(f"Static IP {static_external_ip} not available")
                    else:
                        # Allocate ephemeral external IP
                        external_ip = ExternalIPPoolService.allocate_ephemeral_ip(
                            project_id=project_id,
                            region=region,
                            network_tier='PREMIUM'
                        )
                        instance.external_ip = external_ip
                    db.session.commit()
                except Exception as ext_ip_error:
                    print(f"Failed to allocate external IP: {ext_ip_error}")
            
    except Exception as e:
        # If Docker fails, still create instance but mark as TERMINATED
        print(f"Failed to create Docker container: {e}")
        instance.status = "TERMINATED"
        db.session.commit()
        
        # Still try to create network interface
        try:
            interface = _create_default_network_interface(instance, project_id)
            if interface:
                instance.internal_ip = interface.network_ip
                db.session.commit()
            
            # Handle external IP even if Docker failed
            if request_external_ip:
                region = "-".join(zone_name.split("-")[:-1])
                try:
                    if static_external_ip:
                        addr_obj = Address.query.filter_by(
                            project_id=project_id,
                            address=static_external_ip
                        ).first()
                        if addr_obj and addr_obj.status == 'RESERVED':
                            ExternalIPPoolService.mark_in_use(addr_obj, instance.id, interface.id if interface else None)
                            instance.external_ip = static_external_ip
                    else:
                        external_ip = ExternalIPPoolService.allocate_ephemeral_ip(
                            project_id=project_id,
                            region=region,
                            network_tier='PREMIUM'
                        )
                        instance.external_ip = external_ip
                    db.session.commit()
                except Exception as ext_ip_error:
                    print(f"Failed to allocate external IP: {ext_ip_error}")
        except Exception as net_error:
            print(f"Failed to create network interface: {net_error}")
    
    # Convert UUID to integer for gcloud CLI compatibility
    id_as_int = int(instance.id.hex[:16], 16) % (10**19)
    
    # Return operation instead of instance object
    operation = create_operation(
        project_id=project_id,
        operation_type='insert',
        target_link=f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/zones/{zone_name}/instances/{name}",
        target_id=str(id_as_int),
        zone=zone_name
    )
    return jsonify(operation.to_dict()), 200


@compute_bp.route("/compute/v1/projects/<project_id>/zones/<zone_name>/instances", methods=["GET"])
def list_instances(project_id, zone_name):
    """List instances in a zone"""
    instances = Instance.query.filter_by(
        project_id=project_id,
        zone=zone_name
    ).all()
    
    return jsonify({
        "kind": "compute#instanceList",
        "items": [inst.to_dict(project_id) for inst in instances]
    })


@compute_bp.route("/compute/v1/projects/<project_id>/global/images", methods=["GET"])
def list_images(project_id):
    """List images in a project"""
    # Return a mock list of common images
    images = [
        {
            "kind": "compute#image",
            "id": "1",
            "name": "debian-11",
            "description": "Debian 11 (bullseye)",
            "selfLink": f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/global/images/debian-11",
            "sourceType": "RAW",
            "status": "READY",
            "diskSizeGb": "10",
            "family": "debian-11"
        },
        {
            "kind": "compute#image",
            "id": "2",
            "name": "ubuntu-2004-lts",
            "description": "Ubuntu 20.04 LTS",
            "selfLink": f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/global/images/ubuntu-2004-lts",
            "sourceType": "RAW",
            "status": "READY",
            "diskSizeGb": "10",
            "family": "ubuntu-2004-lts"
        },
        {
            "kind": "compute#image",
            "id": "3",
            "name": "centos-7",
            "description": "CentOS 7",
            "selfLink": f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/global/images/centos-7",
            "sourceType": "RAW",
            "status": "READY",
            "diskSizeGb": "10",
            "family": "centos-7"
        }
    ]
    
    return jsonify({
        "kind": "compute#imageList",
        "items": images
    })


@compute_bp.route("/compute/v1/projects/<project_id>/zones/<zone_name>/disks", methods=["GET"])
def list_disks(project_id, zone_name):
    """List persistent disks in a zone"""
    # Get all instances in the zone and return their disk info
    instances = Instance.query.filter_by(
        project_id=project_id,
        zone=zone_name
    ).all()
    
    disks = []
    for instance in instances:
        disk = {
            "kind": "compute#disk",
            "id": str(hash(f"{instance.id}-disk")),
            "name": f"{instance.name}-disk",
            "zone": f"projects/{project_id}/zones/{zone_name}",
            "status": "READY",
            "sizeGb": str(instance.disk_size_gb),
            "type": f"projects/{project_id}/zones/{zone_name}/diskTypes/pd-standard",
            "selfLink": f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/zones/{zone_name}/disks/{instance.name}-disk",
            "sourceImage": instance.source_image,
            "users": [f"projects/{project_id}/zones/{zone_name}/instances/{instance.name}"]
        }
        disks.append(disk)
    
    return jsonify({
        "kind": "compute#diskList",
        "items": disks
    })


@compute_bp.route("/compute/v1/projects/<project_id>/zones/<zone_name>/instances/<instance_name>", methods=["GET"])
def get_instance(project_id, zone_name, instance_name):
    """Get instance details"""
    instance = Instance.query.filter_by(
        project_id=project_id,
        zone=zone_name,
        name=instance_name
    ).first()
    
    if not instance:
        return error_response(404, "NOT_FOUND", f"Instance {instance_name} not found")
    
    return jsonify(instance.to_dict(project_id))


@compute_bp.route("/compute/v1/projects/<project_id>/zones/<zone_name>/instances/<instance_name>", methods=["DELETE"])
def delete_instance(project_id, zone_name, instance_name):
    """Delete an instance and its Docker container"""
    instance = Instance.query.filter_by(
        project_id=project_id,
        zone=zone_name,
        name=instance_name
    ).first()
    
    if not instance:
        return error_response(404, "NOT_FOUND", f"Instance {instance_name} not found")
    
    # Stop and remove Docker container
    if instance.container_id:
        try:
            client = get_docker_client()
            if client:
                container = client.containers.get(instance.container_id)
                container.stop(timeout=10)
                container.remove()
        except Exception as e:
            print(f"Failed to remove Docker container: {e}")
    
    db.session.delete(instance)
    db.session.commit()
    
    # Convert UUID to integer for gcloud CLI compatibility
    id_as_int = int(instance.id.hex[:16], 16) % (10**19)
    
    # Return operation
    operation = create_operation(
        project_id=project_id,
        operation_type='delete',
        target_link=f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/zones/{zone_name}/instances/{instance_name}",
        target_id=str(id_as_int),
        zone=zone_name
    )
    return jsonify(operation.to_dict()), 200


@compute_bp.route("/compute/v1/projects/<project_id>/zones/<zone_name>/instances/<instance_name>/start", methods=["POST"])
def start_instance(project_id, zone_name, instance_name):
    """Start a stopped instance"""
    instance = Instance.query.filter_by(
        project_id=project_id,
        zone=zone_name,
        name=instance_name
    ).first()
    
    if not instance:
        return error_response(404, "NOT_FOUND", f"Instance {instance_name} not found")
    
    if instance.status == "RUNNING":
        return error_response(400, "INVALID_STATE", "Instance is already running")
    
    # Start Docker container
    if instance.container_id:
        try:
            client = get_docker_client()
            if client:
                container = client.containers.get(instance.container_id)
                container.start()
                instance.status = "RUNNING"
                db.session.commit()
        except Exception as e:
            return error_response(500, "INTERNAL", f"Failed to start container: {e}")
    
    # Convert UUID to integer for gcloud CLI compatibility
    id_as_int = int(instance.id.hex[:16], 16) % (10**19)
    
    # Return operation
    operation = create_operation(
        project_id=project_id,
        operation_type='start',
        target_link=f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/zones/{zone_name}/instances/{instance_name}",
        target_id=str(id_as_int),
        zone=zone_name
    )
    return jsonify(operation.to_dict()), 200


@compute_bp.route("/compute/v1/projects/<project_id>/zones/<zone_name>/instances/<instance_name>/stop", methods=["POST"])
def stop_instance(project_id, zone_name, instance_name):
    """Stop a running instance"""
    instance = Instance.query.filter_by(
        project_id=project_id,
        zone=zone_name,
        name=instance_name
    ).first()
    
    if not instance:
        return error_response(404, "NOT_FOUND", f"Instance {instance_name} not found")
    
    if instance.status == "STOPPED":
        return error_response(400, "INVALID_STATE", "Instance is already stopped")
    
    # Stop Docker container
    if instance.container_id:
        try:
            client = get_docker_client()
            if client:
                container = client.containers.get(instance.container_id)
                container.stop(timeout=10)
                instance.status = "STOPPED"
                db.session.commit()
        except Exception as e:
            return error_response(500, "INTERNAL", f"Failed to stop container: {e}")
    
    # Convert UUID to integer for gcloud CLI compatibility
    id_as_int = int(instance.id.hex[:16], 16) % (10**19)
    
    # Return operation
    operation = create_operation(
        project_id=project_id,
        operation_type='stop',
        target_link=f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/zones/{zone_name}/instances/{instance_name}",
        target_id=str(id_as_int),
        zone=zone_name
    )
    return jsonify(operation.to_dict()), 200


# ========== Disks ==========

@compute_bp.route("/compute/v1/projects/<project_id>/zones/<zone_name>/disks", methods=["POST"])
def create_disk(project_id, zone_name):
    """Create a persistent disk"""
    data = request.get_json()
    name = data.get("name")
    size_gb = data.get("sizeGb", 100)
    disk_type = data.get("type", "pd-standard")
    
    if not name:
        return error_response(400, "INVALID_ARGUMENT", "Disk name is required")
    
    # Check if disk already exists
    result = db.session.execute(
        db.text("SELECT id FROM disks WHERE project_id = :project_id AND zone = :zone AND name = :name"),
        {"project_id": project_id, "zone": zone_name, "name": name}
    ).fetchone()
    
    if result:
        return error_response(409, "ALREADY_EXISTS", f"Disk {name} already exists in zone {zone_name}")
    
    # Generate disk ID
    disk_id = str(secrets.randbelow(10**18))  # Smaller to avoid bigint overflow
    
    # Insert disk
    db.session.execute(
        db.text("""
            INSERT INTO disks (id, project_id, name, zone, size_gb, disk_type, status)
            VALUES (:id, :project_id, :name, :zone, :size_gb, :disk_type, 'READY')
        """),
        {
            "id": disk_id,
            "project_id": project_id,
            "name": name,
            "zone": zone_name,
            "size_gb": size_gb,
            "disk_type": disk_type
        }
    )
    db.session.commit()
    
    # Return operation
    operation = create_operation(
        project_id=project_id,
        operation_type='insert',
        target_link=f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/zones/{zone_name}/disks/{name}",
        target_id=disk_id,
        zone=zone_name
    )
    return jsonify(operation.to_dict()), 200


@compute_bp.route("/compute/v1/projects/<project_id>/zones/<zone_name>/disks/<disk_name>", methods=["GET"])
def get_disk(project_id, zone_name, disk_name):
    """Get disk details"""
    result = db.session.execute(
        db.text("SELECT * FROM disks WHERE project_id = :project_id AND zone = :zone AND name = :name"),
        {"project_id": project_id, "zone": zone_name, "name": disk_name}
    ).fetchone()
    
    if not result:
        return error_response(404, "NOT_FOUND", f"Disk {disk_name} not found")
    
    disk = {
        "kind": "compute#disk",
        "id": result.id,
        "name": result.name,
        "zone": f"projects/{project_id}/zones/{zone_name}",
        "status": result.status,
        "sizeGb": str(result.size_gb),
        "type": f"projects/{project_id}/zones/{zone_name}/diskTypes/{result.disk_type}",
        "selfLink": f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/zones/{zone_name}/disks/{disk_name}",
    }
    
    if result.attached_to:
        disk["users"] = [f"projects/{project_id}/zones/{zone_name}/instances/{result.attached_to}"]
    
    return jsonify(disk), 200


@compute_bp.route("/compute/v1/projects/<project_id>/zones/<zone_name>/instances/<instance_name>/attachDisk", methods=["POST"])
def attach_disk(project_id, zone_name, instance_name):
    """Attach a disk to an instance"""
    data = request.get_json()
    disk_name = data.get("source", "").split("/")[-1]  # Extract disk name from URL
    
    if not disk_name:
        return error_response(400, "INVALID_ARGUMENT", "Disk source is required")
    
    # Check if instance exists
    instance = Instance.query.filter_by(
        project_id=project_id,
        zone=zone_name,
        name=instance_name
    ).first()
    
    if not instance:
        return error_response(404, "NOT_FOUND", f"Instance {instance_name} not found")
    
    # Check if disk exists
    disk_result = db.session.execute(
        db.text("SELECT id, attached_to FROM disks WHERE project_id = :project_id AND zone = :zone AND name = :name"),
        {"project_id": project_id, "zone": zone_name, "name": disk_name}
    ).fetchone()
    
    if not disk_result:
        return error_response(404, "NOT_FOUND", f"Disk {disk_name} not found")
    
    if disk_result.attached_to:
        return error_response(400, "INVALID_STATE", f"Disk {disk_name} is already attached")
    
    # Attach disk
    db.session.execute(
        db.text("UPDATE disks SET attached_to = :instance_name WHERE project_id = :project_id AND zone = :zone AND name = :name"),
        {"instance_name": instance_name, "project_id": project_id, "zone": zone_name, "name": disk_name}
    )
    db.session.commit()
    
    # Return operation  
    operation = create_operation(
        project_id=project_id,
        operation_type='attachDisk',
        target_link=f"http://127.0.0.1:8080/compute/v1/projects/{project_id}/zones/{zone_name}/instances/{instance_name}",
        target_id=disk_result.id,
        zone=zone_name
    )
    return jsonify(operation.to_dict()), 200
