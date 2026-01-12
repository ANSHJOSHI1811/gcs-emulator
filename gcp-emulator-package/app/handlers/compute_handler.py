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
from app.handlers.errors import error_response

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
            
            # Create container
            container = client.containers.run(
                docker_image,
                name=container_name,
                detach=True,
                command="tail -f /dev/null",  # Keep container running
                labels={
                    "gcp-emulator": "true",
                    "project": project_id,
                    "zone": zone_name,
                    "instance": name,
                },
                remove=False,
            )
            
            # Update instance with container info
            instance.container_id = container.id
            instance.container_name = container_name
            instance.status = "RUNNING"
            
            # Generate fake IPs
            instance.internal_ip = f"10.128.0.{secrets.randbelow(254) + 1}"
            instance.external_ip = f"35.{secrets.randbelow(256)}.{secrets.randbelow(256)}.{secrets.randbelow(256)}"
            
            db.session.commit()
    except Exception as e:
        # If Docker fails, still create instance but mark as TERMINATED
        print(f"Failed to create Docker container: {e}")
        instance.status = "TERMINATED"
        db.session.commit()
    
    return jsonify(instance.to_dict()), 201


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
    
    return jsonify({"kind": "compute#operation"}), 200


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
    
    return jsonify({"kind": "compute#operation"}), 200


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
    
    return jsonify({"kind": "compute#operation"}), 200
