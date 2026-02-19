"""
VPC Network service router.
Consolidates: Networks, Subnets, Firewall Rules, Routes (existing)
Sprint 2 additions: Cloud Router, Cloud NAT, VPC Peering, Flow Logs toggle.
"""
import random
import ipaddress
import docker

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import (
    get_db, Network, Subnet, Instance,
    Firewall, Route, CloudRouter, CloudNAT, VPCPeering,
)
from ip_manager import validate_cidr, get_gateway_ip, get_ip_at_offset

from .models import (
    CreateNetworkRequest, CreateSubnetRequest, PatchSubnetRequest,
    FirewallRequest, CreateRouteRequest,
    CreateRouterRequest, CreateNATRequest,
    AddPeeringRequest, RemovePeeringRequest,
)

router = APIRouter()

try:
    _docker = docker.from_env()
except Exception:
    _docker = None


# ────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────

def _op(project: str, op_type: str, target: str, scope: str = "global") -> dict:
    oid = str(random.randint(10 ** 12, 10 ** 13 - 1))
    return {
        "kind": "compute#operation",
        "id": oid, "name": oid,
        "operationType": op_type,
        "targetLink": target,
        "status": "DONE",
        "progress": 100,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/{scope}/operations/{oid}",
    }


def _subnet_resource(s: Subnet, project: str) -> dict:
    enable_flow = getattr(s, "enable_flow_logs", False)
    return {
        "kind": "compute#subnetwork",
        "id": str(s.id),
        "name": s.name,
        "network": s.network,
        "ipCidrRange": s.ip_cidr_range,
        "gatewayAddress": s.gateway_ip,
        "region": s.region,
        "enableFlowLogs": enable_flow or False,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{s.region}/subnetworks/{s.name}",
        "creationTimestamp": s.created_at.isoformat() + "Z" if s.created_at else None,
    }


def _fw_resource(fw: Firewall, project: str) -> dict:
    return {
        "kind": "compute#firewall",
        "id": str(fw.id), "name": fw.name,
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
        "creationTimestamp": fw.created_at.isoformat() + "Z" if fw.created_at else None,
    }


def _route_resource(r: Route, project: str) -> dict:
    return {
        "kind": "compute#route",
        "id": str(r.id), "name": r.name,
        "network": r.network, "project_id": r.project_id,
        "description": r.description,
        "destRange": r.dest_range,
        "nextHopGateway": r.next_hop_gateway,
        "nextHopInstance": r.next_hop_instance,
        "nextHopIp": r.next_hop_ip,
        "nextHopNetwork": r.next_hop_network,
        "priority": r.priority,
        "tags": r.tags,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/routes/{r.name}",
        "creationTimestamp": r.created_at.isoformat() + "Z" if r.created_at else None,
    }


# ────────────────────────────────────────────────────────
# Default network bootstrap helpers
# ────────────────────────────────────────────────────────

def _create_igw_route(db, project, network_name):
    name = f"default-route-{network_name}"
    if db.query(Route).filter_by(project_id=project, name=name).first():
        return
    route = Route(
        name=name, network=network_name, project_id=project,
        description=f"Default to Internet Gateway for {network_name}",
        dest_range="0.0.0.0/0",
        next_hop_gateway=f"projects/{project}/global/gateways/default-internet-gateway",
        priority=1000,
    )
    db.add(route)
    db.commit()


def _create_subnet_route(db, project, network_name, subnet_name, subnet_cidr):
    name = f"route-{subnet_name}"
    if db.query(Route).filter_by(project_id=project, name=name).first():
        return
    route = Route(
        name=name, network=network_name, project_id=project,
        description=f"Auto route for subnet {subnet_name}",
        dest_range=subnet_cidr,
        next_hop_network=f"projects/{project}/global/networks/{network_name}",
        priority=1000,
    )
    db.add(route)
    db.commit()


def ensure_default_network(db: Session, project: str):
    """Bootstrap default VPC + subnet if missing."""
    default = db.query(Network).filter_by(project_id=project, name="default").first()
    if not default:
        default = Network(
            name="default", project_id=project,
            docker_network_name="bridge",
            auto_create_subnetworks=True,
            cidr_range="10.128.0.0/16",
        )
        db.add(default)
        db.commit()
        db.refresh(default)
        _create_igw_route(db, project, "default")

    # Ensure at least one subnet
    sn = db.query(Subnet).filter_by(network="default", region="us-central1").first()
    if not sn:
        subnet_cidr = "10.128.0.0/20"
        sn = Subnet(
            name="default-subnet-us-central1", network="default",
            region="us-central1", ip_cidr_range=subnet_cidr,
            gateway_ip=get_gateway_ip(subnet_cidr), next_available_ip=2,
        )
        db.add(sn)
        db.commit()
        _create_subnet_route(db, project, "default", "default-subnet-us-central1", subnet_cidr)
    return default


# ────────────────────────────────────────────────────────
# Networks
# ────────────────────────────────────────────────────────

@router.get("/projects/{project}/global/networks")
def list_networks(project: str, db: Session = Depends(get_db)):
    ensure_default_network(db, project)
    networks = db.query(Network).filter_by(project_id=project).all()
    return {
        "kind": "compute#networkList",
        "items": [{
            "kind": "compute#network",
            "name": n.name, "id": n.id,
            "IPv4Range": n.cidr_range or "10.128.0.0/16",
            "autoCreateSubnetworks": n.auto_create_subnetworks,
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{n.name}",
            "creationTimestamp": n.creation_timestamp.isoformat() + "Z" if n.creation_timestamp else None,
        } for n in networks],
    }


@router.get("/projects/{project}/global/networks/{network_name}")
def get_network(project: str, network_name: str, db: Session = Depends(get_db)):
    n = db.query(Network).filter_by(project_id=project, name=network_name).first()
    if not n:
        raise HTTPException(404, "Network not found")
    return {
        "kind": "compute#network",
        "name": n.name, "id": n.id,
        "IPv4Range": n.cidr_range or "10.128.0.0/16",
        "autoCreateSubnetworks": n.auto_create_subnetworks,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{n.name}",
        "creationTimestamp": n.creation_timestamp.isoformat() + "Z" if n.creation_timestamp else None,
    }


@router.post("/projects/{project}/global/networks")
def create_network(project: str, body: CreateNetworkRequest, db: Session = Depends(get_db)):
    from docker_manager import create_docker_network_with_cidr
    from region_subnets import get_auto_mode_subnets, is_auto_mode_cidr

    if not validate_cidr(body.IPv4Range):
        raise HTTPException(400, f"Invalid CIDR: {body.IPv4Range}")
    if db.query(Network).filter_by(project_id=project, name=body.name).first():
        raise HTTPException(409, f"Network {body.name} already exists")

    cidr = "10.128.0.0/9" if body.autoCreateSubnetworks else body.IPv4Range
    docker_net_name = f"gcp-vpc-{project}-{body.name}"

    try:
        create_docker_network_with_cidr(body.name, cidr, project)
    except Exception as e:
        raise HTTPException(500, f"Docker network creation failed: {e}")

    net = Network(
        name=body.name, project_id=project,
        docker_network_name=docker_net_name,
        cidr_range=cidr, auto_create_subnetworks=body.autoCreateSubnetworks,
    )
    db.add(net)
    db.commit()
    db.refresh(net)
    _create_igw_route(db, project, body.name)

    if body.autoCreateSubnetworks and is_auto_mode_cidr(cidr):
        for ri in get_auto_mode_subnets():
            sn = Subnet(
                name=f"{body.name}-{ri['name']}", network=body.name,
                region=ri["name"], ip_cidr_range=ri["cidr"],
                gateway_ip=get_gateway_ip(ri["cidr"]), next_available_ip=2,
            )
            db.add(sn)
            _create_subnet_route(db, project, body.name, sn.name, ri["cidr"])
        db.commit()

    return _op(project, "insert",
               f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{body.name}")


@router.delete("/projects/{project}/global/networks/{network_name}")
def delete_network(project: str, network_name: str, db: Session = Depends(get_db)):
    n = db.query(Network).filter_by(project_id=project, name=network_name).first()
    if not n:
        raise HTTPException(404, "Network not found")
    if n.name == "default":
        raise HTTPException(400, "Cannot delete the default network")
    if db.query(Instance).filter(Instance.project_id == project,
                                  Instance.network_url.like(f"%{network_name}%")).first():
        raise HTTPException(400, f"Network {network_name} is in use by instances")

    if n.docker_network_name and n.docker_network_name != "bridge" and _docker:
        try:
            _docker.networks.get(n.docker_network_name).remove()
        except Exception:
            pass

    db.query(Route).filter_by(project_id=project, network=network_name).delete()
    db.query(Subnet).filter_by(network=network_name).delete()
    db.delete(n)
    db.commit()
    return _op(project, "delete",
               f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{network_name}")


# ────────────────────────────────────────────────────────
# Subnets
# ────────────────────────────────────────────────────────

@router.get("/projects/{project}/aggregated/subnetworks")
def list_subnets_aggregated(project: str, db: Session = Depends(get_db)):
    nets = {n.name for n in db.query(Network).filter_by(project_id=project).all()}
    subnets = db.query(Subnet).filter(Subnet.network.in_(nets)).all()
    items: dict = {}
    for s in subnets:
        key = f"regions/{s.region}"
        items.setdefault(key, {"subnetworks": []})
        items[key]["subnetworks"].append(_subnet_resource(s, project))
    return {"kind": "compute#subnetworkAggregatedList", "items": items}


@router.get("/projects/{project}/regions/{region}/subnetworks")
def list_subnets(project: str, region: str, db: Session = Depends(get_db)):
    subnets = db.query(Subnet).filter_by(region=region).all()
    return {"kind": "compute#subnetworkList",
            "items": [_subnet_resource(s, project) for s in subnets]}


@router.get("/projects/{project}/regions/{region}/subnetworks/{subnet_name}")
def get_subnet(project: str, region: str, subnet_name: str, db: Session = Depends(get_db)):
    s = db.query(Subnet).filter_by(name=subnet_name, region=region).first()
    if not s:
        raise HTTPException(404, f"Subnet {subnet_name} not found")
    return _subnet_resource(s, project)


@router.post("/projects/{project}/regions/{region}/subnetworks")
def create_subnet(project: str, region: str, body: CreateSubnetRequest, db: Session = Depends(get_db)):
    network_name = body.network.split("/")[-1]
    if not validate_cidr(body.ipCidrRange):
        raise HTTPException(400, f"Invalid CIDR: {body.ipCidrRange}")

    net = db.query(Network).filter_by(project_id=project, name=network_name).first()
    if not net:
        raise HTTPException(404, f"Network {network_name} not found")

    vpc_cidr = net.cidr_range or "10.128.0.0/16"
    try:
        if not ipaddress.ip_network(body.ipCidrRange, strict=False).subnet_of(
                ipaddress.ip_network(vpc_cidr, strict=False)):
            raise HTTPException(400, f"Subnet {body.ipCidrRange} not within VPC {vpc_cidr}")
    except TypeError:
        raise HTTPException(400, "CIDR version mismatch")

    # overlap check
    for existing in db.query(Subnet).filter_by(network=network_name).all():
        if ipaddress.ip_network(body.ipCidrRange, strict=False).overlaps(
                ipaddress.ip_network(existing.ip_cidr_range, strict=False)):
            raise HTTPException(400, f"Overlaps with subnet {existing.name} ({existing.ip_cidr_range})")

    if db.query(Subnet).filter_by(name=body.name, region=region).first():
        raise HTTPException(409, f"Subnet {body.name} already exists")

    sn = Subnet(
        name=body.name, network=network_name, region=region,
        ip_cidr_range=body.ipCidrRange,
        gateway_ip=get_gateway_ip(body.ipCidrRange), next_available_ip=2,
    )
    db.add(sn)
    db.commit()
    _create_subnet_route(db, project, network_name, body.name, body.ipCidrRange)
    return _op(project, "insert",
               f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/subnetworks/{body.name}",
               scope=f"regions/{region}")


@router.patch("/projects/{project}/regions/{region}/subnetworks/{subnet_name}")
def patch_subnet(project: str, region: str, subnet_name: str,
                 body: PatchSubnetRequest, db: Session = Depends(get_db)):
    """Toggle flow logs, expand CIDR, toggle Private Google Access."""
    s = db.query(Subnet).filter_by(name=subnet_name, region=region).first()
    if not s:
        raise HTTPException(404, f"Subnet {subnet_name} not found")

    if body.enableFlowLogs is not None:
        # Store on a JSON column if present; else silently accept
        if hasattr(s, "enable_flow_logs"):
            s.enable_flow_logs = body.enableFlowLogs

    if body.ipCidrRange is not None:
        # Validate expansion (cannot shrink)
        try:
            old = ipaddress.ip_network(s.ip_cidr_range, strict=False)
            new = ipaddress.ip_network(body.ipCidrRange, strict=False)
            if new.prefixlen > old.prefixlen:
                raise HTTPException(400, "Cannot shrink a subnet CIDR range")
            if not old.subnet_of(new):
                raise HTTPException(400, "New CIDR must be a supernet of the existing CIDR")
        except TypeError:
            raise HTTPException(400, "CIDR version mismatch")
        s.ip_cidr_range = body.ipCidrRange

    db.commit()
    return _subnet_resource(s, project)


@router.delete("/projects/{project}/regions/{region}/subnetworks/{subnet_name}")
def delete_subnet(project: str, region: str, subnet_name: str, db: Session = Depends(get_db)):
    s = db.query(Subnet).filter_by(name=subnet_name, region=region).first()
    if not s:
        raise HTTPException(404, f"Subnet {subnet_name} not found")
    if db.query(Instance).filter_by(subnet=subnet_name).first():
        raise HTTPException(400, f"Subnet {subnet_name} is in use by instances")
    db.delete(s)
    db.commit()
    return _op(project, "delete",
               f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/subnetworks/{subnet_name}",
               scope=f"regions/{region}")


# ────────────────────────────────────────────────────────
# Firewall Rules
# ────────────────────────────────────────────────────────

@router.get("/projects/{project}/global/firewalls")
def list_firewalls(project: str, db: Session = Depends(get_db)):
    fws = db.query(Firewall).filter_by(project_id=project).all()
    return {"kind": "compute#firewallList",
            "items": [_fw_resource(fw, project) for fw in fws]}


@router.get("/projects/{project}/global/firewalls/{firewall_name}")
def get_firewall(project: str, firewall_name: str, db: Session = Depends(get_db)):
    fw = db.query(Firewall).filter_by(name=firewall_name, project_id=project).first()
    if not fw:
        raise HTTPException(404, f"Firewall {firewall_name} not found")
    return _fw_resource(fw, project)


@router.post("/projects/{project}/global/firewalls")
def create_firewall(project: str, body: FirewallRequest, db: Session = Depends(get_db)):
    if db.query(Firewall).filter_by(name=body.name, project_id=project).first():
        raise HTTPException(409, f"Firewall {body.name} already exists")
    network_name = body.network.split("/")[-1]
    if not db.query(Network).filter_by(name=network_name, project_id=project).first():
        raise HTTPException(404, f"Network {network_name} not found")
    fw = Firewall(
        name=body.name, network=f"projects/{project}/global/networks/{network_name}",
        project_id=project, description=body.description,
        direction=body.direction, priority=body.priority,
        source_ranges=body.sourceRanges, destination_ranges=body.destinationRanges,
        source_tags=body.sourceTags, target_tags=body.targetTags,
        allowed=body.allowed, denied=body.denied, disabled=body.disabled,
    )
    db.add(fw)
    db.commit()
    return _op(project, "insert",
               f"https://www.googleapis.com/compute/v1/projects/{project}/global/firewalls/{body.name}")


@router.patch("/projects/{project}/global/firewalls/{firewall_name}")
def patch_firewall(project: str, firewall_name: str, body: FirewallRequest, db: Session = Depends(get_db)):
    fw = db.query(Firewall).filter_by(name=firewall_name, project_id=project).first()
    if not fw:
        raise HTTPException(404, f"Firewall {firewall_name} not found")
    for field, attr in [("description", "description"), ("direction", "direction"),
                         ("priority", "priority"), ("sourceRanges", "source_ranges"),
                         ("destinationRanges", "destination_ranges"), ("sourceTags", "source_tags"),
                         ("targetTags", "target_tags"), ("allowed", "allowed"),
                         ("denied", "denied"), ("disabled", "disabled")]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(fw, attr, val)
    db.commit()
    return _op(project, "patch",
               f"https://www.googleapis.com/compute/v1/projects/{project}/global/firewalls/{firewall_name}")


@router.delete("/projects/{project}/global/firewalls/{firewall_name}")
def delete_firewall(project: str, firewall_name: str, db: Session = Depends(get_db)):
    fw = db.query(Firewall).filter_by(name=firewall_name, project_id=project).first()
    if not fw:
        raise HTTPException(404, f"Firewall {firewall_name} not found")
    db.delete(fw)
    db.commit()
    return _op(project, "delete",
               f"https://www.googleapis.com/compute/v1/projects/{project}/global/firewalls/{firewall_name}")


# ────────────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────────────

@router.get("/compute/v1/projects/{project}/global/routes")
def list_routes(project: str, db: Session = Depends(get_db)):
    routes = db.query(Route).filter_by(project_id=project).all()
    return {"kind": "compute#routeList",
            "items": [_route_resource(r, project) for r in routes]}


@router.get("/compute/v1/projects/{project}/global/routes/{route_name}")
def get_route(project: str, route_name: str, db: Session = Depends(get_db)):
    r = db.query(Route).filter_by(project_id=project, name=route_name).first()
    if not r:
        raise HTTPException(404, f"Route {route_name} not found")
    return _route_resource(r, project)


@router.post("/compute/v1/projects/{project}/global/routes")
def create_route(project: str, body: CreateRouteRequest, db: Session = Depends(get_db)):
    if db.query(Route).filter_by(project_id=project, name=body.name).first():
        raise HTTPException(409, f"Route {body.name} already exists")
    r = Route(
        name=body.name, network=body.network, project_id=project,
        description=body.description, dest_range=body.destRange,
        next_hop_gateway=body.nextHopGateway, next_hop_instance=body.nextHopInstance,
        next_hop_ip=body.nextHopIp, next_hop_network=body.nextHopNetwork,
        priority=body.priority, tags=body.tags,
    )
    db.add(r)
    db.commit()
    return _op(project, "insert",
               f"https://www.googleapis.com/compute/v1/projects/{project}/global/routes/{body.name}")


@router.patch("/compute/v1/projects/{project}/global/routes/{route_name}")
def patch_route(project: str, route_name: str, body: CreateRouteRequest, db: Session = Depends(get_db)):
    r = db.query(Route).filter_by(project_id=project, name=route_name).first()
    if not r:
        raise HTTPException(404, f"Route {route_name} not found")
    for f, a in [("destRange", "dest_range"), ("nextHopGateway", "next_hop_gateway"),
                  ("nextHopInstance", "next_hop_instance"), ("nextHopIp", "next_hop_ip"),
                  ("priority", "priority"), ("description", "description")]:
        val = getattr(body, f, None)
        if val is not None:
            setattr(r, a, val)
    db.commit()
    return _op(project, "patch",
               f"https://www.googleapis.com/compute/v1/projects/{project}/global/routes/{route_name}")


@router.delete("/compute/v1/projects/{project}/global/routes/{route_name}")
def delete_route(project: str, route_name: str, db: Session = Depends(get_db)):
    r = db.query(Route).filter_by(project_id=project, name=route_name).first()
    if not r:
        raise HTTPException(404, f"Route {route_name} not found")
    db.delete(r)
    db.commit()
    return _op(project, "delete",
               f"https://www.googleapis.com/compute/v1/projects/{project}/global/routes/{route_name}")


# ────────────────────────────────────────────────────────
# Sprint 2 — Cloud Router
# ────────────────────────────────────────────────────────

def _router_resource(cr: CloudRouter, project: str) -> dict:
    return {
        "kind": "compute#router",
        "id": str(cr.id),
        "name": cr.name,
        "region": f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{cr.region}",
        "network": f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{cr.network}",
        "description": cr.description or "",
        "bgp": {"asn": cr.bgp_asn},
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{cr.region}/routers/{cr.name}",
        "creationTimestamp": cr.created_at.isoformat() + "Z",
    }


@router.get("/projects/{project}/regions/{region}/routers")
def list_routers(project: str, region: str, db: Session = Depends(get_db)):
    routers = db.query(CloudRouter).filter_by(project_id=project, region=region).all()
    return {"kind": "compute#routerList",
            "items": [_router_resource(r, project) for r in routers]}


@router.get("/projects/{project}/regions/{region}/routers/{router_name}")
def get_router(project: str, region: str, router_name: str, db: Session = Depends(get_db)):
    r = db.query(CloudRouter).filter_by(project_id=project, region=region, name=router_name).first()
    if not r:
        raise HTTPException(404, f"Router {router_name} not found")
    return _router_resource(r, project)


@router.post("/projects/{project}/regions/{region}/routers")
def create_router(project: str, region: str, body: CreateRouterRequest, db: Session = Depends(get_db)):
    network_name = body.network.split("/")[-1]
    if not db.query(Network).filter_by(project_id=project, name=network_name).first():
        raise HTTPException(404, f"Network {network_name} not found")
    if db.query(CloudRouter).filter_by(project_id=project, region=region, name=body.name).first():
        raise HTTPException(409, f"Router {body.name} already exists")
    cr = CloudRouter(
        name=body.name, project_id=project, region=region,
        network=network_name, description=body.description, bgp_asn=body.bgpAsn,
    )
    db.add(cr)
    db.commit()
    return _op(project, "insert",
               f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/routers/{body.name}",
               scope=f"regions/{region}")


@router.delete("/projects/{project}/regions/{region}/routers/{router_name}")
def delete_router(project: str, region: str, router_name: str, db: Session = Depends(get_db)):
    r = db.query(CloudRouter).filter_by(project_id=project, region=region, name=router_name).first()
    if not r:
        raise HTTPException(404, f"Router {router_name} not found")
    # Delete associated NATs first
    db.query(CloudNAT).filter_by(project_id=project, region=region, router_name=router_name).delete()
    db.delete(r)
    db.commit()
    return _op(project, "delete",
               f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/routers/{router_name}",
               scope=f"regions/{region}")


# ────────────────────────────────────────────────────────
# Sprint 2 — Cloud NAT
# ────────────────────────────────────────────────────────

def _nat_resource(n: CloudNAT, project: str) -> dict:
    return {
        "kind": "compute#routerNat",
        "name": n.name,
        "routerName": n.router_name,
        "region": n.region,
        "natIpAllocateOption": n.nat_ip_allocate_option,
        "sourceSubnetworkIpRangesToNat": n.source_subnetwork_option,
        "minPortsPerVm": n.min_ports_per_vm,
        "selfLink": (
            f"https://www.googleapis.com/compute/v1/projects/{project}"
            f"/regions/{n.region}/routers/{n.router_name}/nats/{n.name}"
        ),
        "creationTimestamp": n.created_at.isoformat() + "Z",
    }


@router.get("/projects/{project}/regions/{region}/routers/{router_name}/nats")
def list_nats(project: str, region: str, router_name: str, db: Session = Depends(get_db)):
    nats = db.query(CloudNAT).filter_by(project_id=project, region=region, router_name=router_name).all()
    return {"kind": "compute#routerNatList",
            "items": [_nat_resource(n, project) for n in nats]}


@router.post("/projects/{project}/regions/{region}/routers/{router_name}/nats")
def create_nat(project: str, region: str, router_name: str,
               body: CreateNATRequest, db: Session = Depends(get_db)):
    if not db.query(CloudRouter).filter_by(project_id=project, region=region, name=router_name).first():
        raise HTTPException(404, f"Router {router_name} not found")
    if db.query(CloudNAT).filter_by(project_id=project, region=region,
                                     router_name=router_name, name=body.name).first():
        raise HTTPException(409, f"NAT {body.name} already exists on router {router_name}")
    nat = CloudNAT(
        name=body.name, router_name=router_name,
        project_id=project, region=region,
        nat_ip_allocate_option=body.natIpAllocateOption,
        source_subnetwork_option=body.sourceSubnetworkIpRangesToNat,
        min_ports_per_vm=body.minPortsPerVm,
    )
    db.add(nat)
    db.commit()
    return _op(project, "patch",
               f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/routers/{router_name}",
               scope=f"regions/{region}")


@router.delete("/projects/{project}/regions/{region}/routers/{router_name}/nats/{nat_name}")
def delete_nat(project: str, region: str, router_name: str, nat_name: str, db: Session = Depends(get_db)):
    n = db.query(CloudNAT).filter_by(project_id=project, region=region,
                                      router_name=router_name, name=nat_name).first()
    if not n:
        raise HTTPException(404, f"NAT {nat_name} not found")
    db.delete(n)
    db.commit()
    return _op(project, "patch",
               f"https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/routers/{router_name}",
               scope=f"regions/{region}")


# ────────────────────────────────────────────────────────
# Sprint 2 — VPC Peering
# ────────────────────────────────────────────────────────

def _peering_resource(p: VPCPeering, project: str) -> dict:
    return {
        "name": p.name,
        "network": p.network,
        "peerNetwork": p.peer_network,
        "state": p.state,
        "stateDetails": "Connected" if p.state == "ACTIVE" else "Disconnected",
        "exchangeSubnetRoutes": p.exchange_subnet_routes,
        "selfLink": (
            f"https://www.googleapis.com/compute/v1/projects/{project}"
            f"/global/networks/{p.network}/peerings/{p.name}"
        ),
        "creationTimestamp": p.created_at.isoformat() + "Z",
    }


@router.get("/projects/{project}/global/networks/{network_name}/peerings")
def list_peerings(project: str, network_name: str, db: Session = Depends(get_db)):
    peerings = db.query(VPCPeering).filter_by(project_id=project, network=network_name).all()
    return {"kind": "compute#peeringList",
            "items": [_peering_resource(p, project) for p in peerings]}


@router.post("/projects/{project}/global/networks/{network_name}/addPeering")
def add_peering(project: str, network_name: str,
                body: AddPeeringRequest, db: Session = Depends(get_db)):
    if not db.query(Network).filter_by(project_id=project, name=network_name).first():
        raise HTTPException(404, f"Network {network_name} not found")
    if db.query(VPCPeering).filter_by(project_id=project, network=network_name, name=body.name).first():
        raise HTTPException(409, f"Peering {body.name} already exists")
    p = VPCPeering(
        name=body.name, project_id=project, network=network_name,
        peer_network=body.peerNetwork, state="ACTIVE",
        exchange_subnet_routes=body.exchangeSubnetRoutes,
    )
    db.add(p)
    db.commit()
    return _op(project, "addPeering",
               f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{network_name}")


@router.post("/projects/{project}/global/networks/{network_name}/removePeering")
def remove_peering(project: str, network_name: str,
                   body: RemovePeeringRequest, db: Session = Depends(get_db)):
    p = db.query(VPCPeering).filter_by(project_id=project, network=network_name, name=body.name).first()
    if not p:
        raise HTTPException(404, f"Peering {body.name} not found")
    db.delete(p)
    db.commit()
    return _op(project, "removePeering",
               f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{network_name}")
