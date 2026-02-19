"""
Compute Engine service router.
Includes all existing instance/zone/machine-type endpoints plus
Sprint 1 additions: static addresses, persistent disks, instance tags,
instance metadata, and serial port output.
"""
import random
import ipaddress
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import (
    get_db, Instance, Zone, MachineType, Network, Subnet,
    Address, Disk,
)
from docker_manager import (
    create_container, stop_container, start_container,
    delete_container, get_container_status, ip_in_docker_network,
)
from ip_manager import get_ip_at_offset

from .models import (
    CreateInstanceRequest, SetTagsRequest, SetMetadataRequest,
    CreateAddressRequest, CreateDiskRequest, AttachDiskRequest,
)

router = APIRouter()


# ────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────

def _op(project: str, zone: str, op_type: str, target: str, extra: dict = None) -> dict:
    """Build a DONE compute#operation response."""
    oid = str(random.randint(10 ** 12, 10 ** 13 - 1))
    base = {
        "kind": "compute#operation",
        "id": oid,
        "name": oid,
        "zone": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}",
        "operationType": op_type,
        "targetLink": target,
        "status": "DONE",
        "user": "user@example.com",
        "progress": 100,
        "selfLink": (
            f"https://www.googleapis.com/compute/v1/projects/{project}"
            f"/zones/{zone}/operations/{oid}"
        ),
    }
    if extra:
        base.update(extra)
    return base


def _global_op(project: str, region: str, op_type: str, target: str) -> dict:
    """Build a DONE operation for regional/global resources."""
    oid = str(random.randint(10 ** 12, 10 ** 13 - 1))
    return {
        "kind": "compute#operation",
        "id": oid,
        "name": oid,
        "region": f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}",
        "operationType": op_type,
        "targetLink": target,
        "status": "DONE",
        "user": "user@example.com",
        "progress": 100,
    }


def _instance_resource(i: Instance, project: str) -> dict:
    return {
        "kind": "compute#instance",
        "name": i.name,
        "id": str(i.id),
        "status": i.status,
        "machineType": f"zones/{i.zone}/machineTypes/{i.machine_type}",
        "zone": f"zones/{i.zone}",
        "tags": {"items": i.tags or [], "fingerprint": ""},
        "metadata": {"items": i.metadata_items or [], "fingerprint": ""},
        "labels": i.labels or {},
        "networkInterfaces": [{
            "network": f"https://www.googleapis.com/compute/v1/projects/{project}/{i.network_url}",
            "networkIP": i.internal_ip,
            "name": "nic0",
            "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "natIP": i.external_ip or ""}],
        }] if i.internal_ip else [],
        "disks": [{
            "source": f"projects/{project}/zones/{i.zone}/disks/{i.name}",
            "deviceName": i.name,
            "boot": True,
        }],
        "dockerContainerId": i.container_id,
        "dockerContainerName": i.container_name,
        "selfLink": (
            f"https://www.googleapis.com/compute/v1/projects/{project}"
            f"/zones/{i.zone}/instances/{i.name}"
        ),
        "creationTimestamp": i.created_at.isoformat() + "Z",
    }


# ────────────────────────────────────────────────────────
# Internet Gateway (control-plane only)
# ────────────────────────────────────────────────────────

@router.get("/projects/{project}/global/internetGateways")
def list_internet_gateways(project: str):
    return {
        "kind": "compute#internetGatewayList",
        "items": [{
            "kind": "compute#internetGateway",
            "id": "default-internet-gateway",
            "name": "default-internet-gateway",
            "network": f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/default",
            "status": "ACTIVE",
            "backing": "docker-bridge-nat",
        }],
    }


@router.get("/projects/{project}/global/internetGateways/default-internet-gateway")
def get_internet_gateway(project: str):
    return {
        "kind": "compute#internetGateway",
        "id": "default-internet-gateway",
        "name": "default-internet-gateway",
        "status": "ACTIVE",
    }


# ────────────────────────────────────────────────────────
# Operations
# ────────────────────────────────────────────────────────

@router.post("/projects/{project}/zones/{zone}/operations/{operation}/wait")
def wait_operation(project: str, zone: str, operation: str):
    return {
        "kind": "compute#operation",
        "id": operation,
        "name": operation,
        "status": "DONE",
        "progress": 100,
    }


# ────────────────────────────────────────────────────────
# Project & Zone validation (for gcloud CLI)
# ────────────────────────────────────────────────────────

@router.get("/projects/{project}")
def get_project(project: str):
    """Return project info - gcloud CLI uses this for validation."""
    return {
        "kind": "compute#project",
        "id": project,
        "name": project,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}",
        "defaultServiceAccount": f"{project}@developer.gserviceaccount.com",
        "commonInstanceMetadata": {"kind": "compute#metadata", "fingerprint": ""},
    }


@router.get("/projects/{project}/zones/{zone}")
def get_zone(project: str, zone: str, db: Session = Depends(get_db)):
    """Return zone info - gcloud CLI uses this for validation."""
    z = db.query(Zone).filter_by(name=zone).first()
    if not z:
        raise HTTPException(status_code=404, detail=f"Zone {zone} not found")
    return {
        "kind": "compute#zone",
        "name": z.name,
        "region": z.region,
        "status": z.status,
        "description": z.description or "",
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{z.name}",
    }


# ────────────────────────────────────────────────────────
# Zones & Machine Types
# ────────────────────────────────────────────────────────

@router.get("/projects/{project}/zones")
def list_zones(project: str, db: Session = Depends(get_db)):
    zones = db.query(Zone).all()
    return {
        "kind": "compute#zoneList",
        "items": [{
            "name": z.name,
            "region": z.region,
            "status": z.status,
            "description": z.description or "",
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{z.name}",
        } for z in zones],
    }


@router.get("/projects/{project}/zones/{zone}/machineTypes")
def list_machine_types(project: str, zone: str, db: Session = Depends(get_db)):
    types = db.query(MachineType).filter_by(zone=zone).all()
    return {
        "kind": "compute#machineTypeList",
        "items": [{
            "name": t.name,
            "guestCpus": t.guest_cpus,
            "memoryMb": t.memory_mb,
            "zone": t.zone,
        } for t in types],
    }


# ────────────────────────────────────────────────────────
# Instances — CRUD + start/stop
# ────────────────────────────────────────────────────────

@router.get("/projects/{project}/zones/{zone}/instances")
def list_instances(project: str, zone: str, db: Session = Depends(get_db)):
    instances = db.query(Instance).filter_by(project_id=project, zone=zone).all()
    for i in instances:
        if i.container_id:
            st = get_container_status(i.container_id)
            i.status = "RUNNING" if st == "running" else "TERMINATED" if st == "exited" else i.status
    db.commit()
    return {
        "kind": "compute#instanceList",
        "items": [_instance_resource(i, project) for i in instances],
    }


@router.get("/projects/{project}/aggregated/instances")
def list_instances_aggregated(project: str, db: Session = Depends(get_db)):
    """Return all instances grouped by zone (aggregated list) — used by gcloud."""
    instances = db.query(Instance).filter_by(project_id=project).all()
    items: dict = {}
    for i in instances:
        key = f"zones/{i.zone}"
        items.setdefault(key, {"instances": []})
        items[key]["instances"].append(_instance_resource(i, project))
    return {"kind": "compute#instanceAggregatedList", "items": items}


@router.get("/projects/{project}/zones/{zone}/instances/{instance_name}")
def get_instance(project: str, zone: str, instance_name: str, db: Session = Depends(get_db)):
    i = db.query(Instance).filter_by(project_id=project, zone=zone, name=instance_name).first()
    if not i:
        raise HTTPException(404, "Instance not found")
    if i.container_id:
        st = get_container_status(i.container_id)
        i.status = "RUNNING" if st == "running" else "TERMINATED" if st == "exited" else i.status
        db.commit()
    return _instance_resource(i, project)


@router.post("/projects/{project}/zones/{zone}/instances")
async def create_instance(project: str, zone: str, body: dict, db: Session = Depends(get_db)):
    name = body["name"]
    machine_type = body.get("machineType", "e2-medium").split("/")[-1]

    existing = db.query(Instance).filter_by(project_id=project, zone=zone, name=name).first()
    if existing:
        raise HTTPException(409, f"Instance {name} already exists")

    # Resolve network/subnet
    network_name, subnet_name = "default", "default"
    if body.get("networkInterfaces"):
        net = body["networkInterfaces"][0].get("network", "")
        if net:
            network_name = net.split("/")[-1]
        sub = body["networkInterfaces"][0].get("subnetwork", "")
        if sub:
            subnet_name = sub.split("/")[-1]

    # Resolve subnet by name or default to the subnet in the zone's region
    region = zone.rsplit('-', 1)[0]
    if subnet_name == "default":
        subnet_record = db.query(Subnet).filter_by(network=network_name, region=region).first()
    else:
        subnet_record = db.query(Subnet).filter_by(name=subnet_name).first()

    if not subnet_record:
        raise HTTPException(404, f"Subnet '{subnet_name}' not found")

    allocated_ip = get_ip_at_offset(subnet_record.ip_cidr_range, subnet_record.next_available_ip)
    if not allocated_ip:
        raise HTTPException(400, f"No IPs available in subnet {subnet_name}")

    net_record = db.query(Network).filter_by(project_id=project, name=network_name).first()
    if not net_record:
        raise HTTPException(404, f"Network '{network_name}' not found")

    # Validate allocated IP is within Docker network IPAM to avoid Docker API errors
    if not ip_in_docker_network(net_record.docker_network_name, allocated_ip):
        raise HTTPException(400, f"Allocated IP {allocated_ip} is not contained in Docker network '{net_record.docker_network_name}' IPAM pools")

    container = create_container(name, network=net_record.docker_network_name, ip_address=allocated_ip)
    subnet_record.next_available_ip += 1

    # Extract tags, metadata, labels from request body
    tags_body = body.get("tags", {})
    meta_body = body.get("metadata", {})

    instance = Instance(
        name=name,
        project_id=project,
        zone=zone,
        machine_type=machine_type,
        status="RUNNING",
        internal_ip=allocated_ip,
        container_id=container["container_id"],
        container_name=container["container_name"],
        network_url=f"global/networks/{network_name}",
        subnetwork_url=f"regions/{zone.rsplit('-', 1)[0]}/subnetworks/{subnet_name}",
        subnet=subnet_name,
        tags=tags_body.get("items", []),
        metadata_items=meta_body.get("items", []),
        labels=body.get("labels", {}),
        description=body.get("description"),
        source_image=body.get("disks", [{}])[0].get("initializeParams", {}).get("sourceImage", "debian-11"),
        disk_size_gb=int(body.get("disks", [{}])[0].get("initializeParams", {}).get("diskSizeGb", 10)),
    )
    db.add(instance)
    db.commit()
    db.refresh(instance)

    return _op(project, zone, "insert",
               f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{name}",
               {"targetId": str(instance.id),
                "insertTime": instance.created_at.isoformat() + "Z",
                "startTime": instance.created_at.isoformat() + "Z",
                "endTime": instance.created_at.isoformat() + "Z"})


@router.post("/projects/{project}/zones/{zone}/instances/{instance_name}/stop")
async def stop_instance(project: str, zone: str, instance_name: str, db: Session = Depends(get_db)):
    i = db.query(Instance).filter_by(project_id=project, zone=zone, name=instance_name).first()
    if not i:
        raise HTTPException(404, "Instance not found")
    if i.container_id:
        stop_container(i.container_id)
    i.status = "TERMINATED"
    db.commit()
    return _op(project, zone, "stop",
               f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{instance_name}")


@router.post("/projects/{project}/zones/{zone}/instances/{instance_name}/start")
async def start_instance(project: str, zone: str, instance_name: str, db: Session = Depends(get_db)):
    i = db.query(Instance).filter_by(project_id=project, zone=zone, name=instance_name).first()
    if not i:
        raise HTTPException(404, "Instance not found")
    if i.container_id:
        start_container(i.container_id)
    i.status = "RUNNING"
    db.commit()
    return _op(project, zone, "start",
               f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{instance_name}")


@router.delete("/projects/{project}/zones/{zone}/instances/{instance_name}")
async def delete_instance(project: str, zone: str, instance_name: str, db: Session = Depends(get_db)):
    i = db.query(Instance).filter_by(project_id=project, zone=zone, name=instance_name).first()
    if not i:
        raise HTTPException(404, "Instance not found")
    if i.container_id:
        delete_container(i.container_id)
    # Release disk users
    for d in db.query(Disk).filter_by(project_id=project, zone=zone).all():
        if d.users and instance_name in d.users:
            d.users = [u for u in d.users if u != instance_name]
    db.delete(i)
    db.commit()
    return _op(project, zone, "delete",
               f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{instance_name}")


# ────────────────────────────────────────────────────────
# Sprint 1 — Instance tags & metadata
# ────────────────────────────────────────────────────────

@router.post("/projects/{project}/zones/{zone}/instances/{instance_name}/setTags")
async def set_tags(project: str, zone: str, instance_name: str,
                   body: SetTagsRequest, db: Session = Depends(get_db)):
    i = db.query(Instance).filter_by(project_id=project, zone=zone, name=instance_name).first()
    if not i:
        raise HTTPException(404, "Instance not found")
    i.tags = body.items
    db.commit()
    return _op(project, zone, "setTags",
               f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{instance_name}")


@router.post("/projects/{project}/zones/{zone}/instances/{instance_name}/setMetadata")
async def set_metadata(project: str, zone: str, instance_name: str,
                       body: SetMetadataRequest, db: Session = Depends(get_db)):
    i = db.query(Instance).filter_by(project_id=project, zone=zone, name=instance_name).first()
    if not i:
        raise HTTPException(404, "Instance not found")
    i.metadata_items = body.items
    db.commit()
    return _op(project, zone, "setMetadata",
               f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{instance_name}")


# ────────────────────────────────────────────────────────
# Sprint 1 — Serial port output (stub)
# ────────────────────────────────────────────────────────

@router.get("/projects/{project}/zones/{zone}/instances/{instance_name}/serialPort")
def get_serial_port(project: str, zone: str, instance_name: str,
                    port: int = 1, db: Session = Depends(get_db)):
    i = db.query(Instance).filter_by(project_id=project, zone=zone, name=instance_name).first()
    if not i:
        raise HTTPException(404, "Instance not found")
    # Simulated boot log output
    lines = [
        f"[    0.000000] GCP Stimulator VM — {instance_name}",
        f"[    0.100000] Machine type: {i.machine_type}",
        f"[    0.200000] Network: {i.network_url}",
        f"[    0.500000] Starting Docker container {i.container_name} ...",
        f"[    1.200000] Container ID: {i.container_id or 'N/A'}",
        f"[    2.000000] Internal IP: {i.internal_ip}",
        f"[    3.000000] System booted successfully.",
        "",
    ]
    return {
        "kind": "compute#serialPortOutput",
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{instance_name}/serialPort",
        "contents": "\n".join(lines),
        "next": 0,
    }


# ────────────────────────────────────────────────────────
# Sprint 1 — Static addresses (regional)
# ────────────────────────────────────────────────────────

def _address_resource(a: Address, project: str) -> dict:
    return {
        "kind": "compute#address",
        "id": str(a.id),
        "name": a.name,
        "address": a.address or "",
        "addressType": a.address_type,
        "status": a.status,
        "region": f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{a.region}",
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{a.region}/addresses/{a.name}",
        "description": a.description or "",
        "users": a.users or [],
        "creationTimestamp": a.created_at.isoformat() + "Z",
    }


def _next_address(region: str, db: Session) -> str:
    """Allocate a fake regional static IP (192.0.2.x range)."""
    existing = db.query(Address).filter_by(region=region).count()
    return f"192.0.2.{(existing + 1) % 256}"


@router.get("/projects/{project}/regions/{region}/addresses")
def list_addresses(project: str, region: str, db: Session = Depends(get_db)):
    items = db.query(Address).filter_by(project_id=project, region=region).all()
    return {
        "kind": "compute#addressList",
        "items": [_address_resource(a, project) for a in items],
    }


@router.get("/projects/{project}/regions/{region}/addresses/{address_name}")
def get_address(project: str, region: str, address_name: str, db: Session = Depends(get_db)):
    a = db.query(Address).filter_by(project_id=project, region=region, name=address_name).first()
    if not a:
        raise HTTPException(404, "Address not found")
    return _address_resource(a, project)


@router.post("/projects/{project}/regions/{region}/addresses")
async def create_address(project: str, region: str,
                         body: CreateAddressRequest, db: Session = Depends(get_db)):
    existing = db.query(Address).filter_by(project_id=project, region=region, name=body.name).first()
    if existing:
        raise HTTPException(409, f"Address {body.name} already exists")

    ip = body.address or _next_address(region, db)
    addr = Address(
        name=body.name,
        project_id=project,
        region=region,
        address=ip,
        address_type=body.addressType,
        status="RESERVED",
        description=body.description,
        users=[],
    )
    db.add(addr)
    db.commit()
    return _global_op(project, region, "insert",
                      f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/addresses/{body.name}")


@router.delete("/projects/{project}/regions/{region}/addresses/{address_name}")
async def delete_address(project: str, region: str, address_name: str, db: Session = Depends(get_db)):
    a = db.query(Address).filter_by(project_id=project, region=region, name=address_name).first()
    if not a:
        raise HTTPException(404, "Address not found")
    if a.status == "IN_USE":
        raise HTTPException(400, "Cannot delete an address that is in use")
    db.delete(a)
    db.commit()
    return _global_op(project, region, "delete",
                      f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/addresses/{address_name}")


# ────────────────────────────────────────────────────────
# Sprint 1 — Persistent disks (zonal)
# ────────────────────────────────────────────────────────

def _disk_resource(d: Disk, project: str) -> dict:
    return {
        "kind": "compute#disk",
        "id": str(d.id),
        "name": d.name,
        "zone": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{d.zone}",
        "sizeGb": str(d.size_gb),
        "type": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{d.zone}/diskTypes/{d.type}",
        "status": d.status,
        "sourceImage": d.source_image or "",
        "description": d.description or "",
        "labels": d.labels or {},
        "users": d.users or [],
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{d.zone}/disks/{d.name}",
        "creationTimestamp": d.created_at.isoformat() + "Z",
    }


@router.get("/projects/{project}/zones/{zone}/disks")
def list_disks(project: str, zone: str, db: Session = Depends(get_db)):
    disks = db.query(Disk).filter_by(project_id=project, zone=zone).all()
    return {
        "kind": "compute#diskList",
        "items": [_disk_resource(d, project) for d in disks],
    }


@router.get("/projects/{project}/zones/{zone}/disks/{disk_name}")
def get_disk(project: str, zone: str, disk_name: str, db: Session = Depends(get_db)):
    d = db.query(Disk).filter_by(project_id=project, zone=zone, name=disk_name).first()
    if not d:
        raise HTTPException(404, "Disk not found")
    return _disk_resource(d, project)


@router.post("/projects/{project}/zones/{zone}/disks")
async def create_disk(project: str, zone: str,
                      body: CreateDiskRequest, db: Session = Depends(get_db)):
    existing = db.query(Disk).filter_by(project_id=project, zone=zone, name=body.name).first()
    if existing:
        raise HTTPException(409, f"Disk {body.name} already exists")
    d = Disk(
        name=body.name,
        project_id=project,
        zone=zone,
        size_gb=body.sizeGb,
        type=body.type,
        status="READY",
        source_image=body.sourceImage,
        description=body.description,
        labels=body.labels or {},
        users=[],
    )
    db.add(d)
    db.commit()
    return _op(project, zone, "insert",
               f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/disks/{body.name}")


@router.delete("/projects/{project}/zones/{zone}/disks/{disk_name}")
async def delete_disk(project: str, zone: str, disk_name: str, db: Session = Depends(get_db)):
    d = db.query(Disk).filter_by(project_id=project, zone=zone, name=disk_name).first()
    if not d:
        raise HTTPException(404, "Disk not found")
    if d.users:
        raise HTTPException(400, f"Disk {disk_name} is still in use by: {d.users}")
    db.delete(d)
    db.commit()
    return _op(project, zone, "delete",
               f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/disks/{disk_name}")


@router.post("/projects/{project}/zones/{zone}/instances/{instance_name}/attachDisk")
async def attach_disk(project: str, zone: str, instance_name: str,
                      body: AttachDiskRequest, db: Session = Depends(get_db)):
    i = db.query(Instance).filter_by(project_id=project, zone=zone, name=instance_name).first()
    if not i:
        raise HTTPException(404, "Instance not found")
    disk_name = body.source.split("/")[-1]
    d = db.query(Disk).filter_by(project_id=project, zone=zone, name=disk_name).first()
    if not d:
        raise HTTPException(404, f"Disk {disk_name} not found")
    users = list(d.users or [])
    if instance_name not in users:
        users.append(instance_name)
        d.users = users
    db.commit()
    return _op(project, zone, "attachDisk",
               f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{instance_name}")


@router.post("/projects/{project}/zones/{zone}/instances/{instance_name}/detachDisk")
async def detach_disk(project: str, zone: str, instance_name: str,
                      deviceName: str, db: Session = Depends(get_db)):
    i = db.query(Instance).filter_by(project_id=project, zone=zone, name=instance_name).first()
    if not i:
        raise HTTPException(404, "Instance not found")
    d = db.query(Disk).filter_by(project_id=project, zone=zone, name=deviceName).first()
    if d and d.users:
        d.users = [u for u in d.users if u != instance_name]
    db.commit()
    return _op(project, zone, "detachDisk",
               f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{instance_name}")
