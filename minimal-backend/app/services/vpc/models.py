"""VPC Network service — Pydantic request/response models"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# ── Networks & Subnets ──────────────────────────────────────────────

class CreateNetworkRequest(BaseModel):
    name: str
    IPv4Range: Optional[str] = "10.128.0.0/16"
    autoCreateSubnetworks: Optional[bool] = True
    description: Optional[str] = None


class CreateSubnetRequest(BaseModel):
    name: str
    network: str                             # network selfLink or name
    ipCidrRange: str
    description: Optional[str] = None
    enableFlowLogs: Optional[bool] = False
    privateIpGoogleAccess: Optional[bool] = False


class PatchSubnetRequest(BaseModel):
    """PATCH subnetwork — flow logs toggle, CIDR expand, etc."""
    enableFlowLogs: Optional[bool] = None
    privateIpGoogleAccess: Optional[bool] = None
    ipCidrRange: Optional[str] = None        # expand only (cannot shrink)


# ── Firewall Rules ──────────────────────────────────────────────────

class FirewallRequest(BaseModel):
    name: str
    network: str
    description: Optional[str] = None
    direction: Optional[str] = "INGRESS"
    priority: Optional[int] = 1000
    sourceRanges: Optional[List[str]] = None
    destinationRanges: Optional[List[str]] = None
    sourceTags: Optional[List[str]] = None
    targetTags: Optional[List[str]] = None
    allowed: Optional[List[Dict[str, Any]]] = None
    denied: Optional[List[Dict[str, Any]]] = None
    disabled: Optional[bool] = False


# ── Routes ─────────────────────────────────────────────────────────

class CreateRouteRequest(BaseModel):
    name: str
    network: str
    destRange: str
    description: Optional[str] = None
    nextHopGateway: Optional[str] = None
    nextHopInstance: Optional[str] = None
    nextHopIp: Optional[str] = None
    nextHopNetwork: Optional[str] = None
    priority: Optional[int] = 1000
    tags: Optional[List[str]] = None


# ── Cloud Router ────────────────────────────────────────────────────

class CreateRouterRequest(BaseModel):
    name: str
    network: str
    description: Optional[str] = None
    bgpAsn: Optional[int] = 64512


# ── Cloud NAT ───────────────────────────────────────────────────────

class CreateNATRequest(BaseModel):
    name: str
    natIpAllocateOption: Optional[str] = "AUTO_ONLY"
    sourceSubnetworkIpRangesToNat: Optional[str] = "ALL_SUBNETWORKS_ALL_IP_RANGES"
    minPortsPerVm: Optional[int] = 64


# ── VPC Peering ─────────────────────────────────────────────────────

class AddPeeringRequest(BaseModel):
    name: str
    peerNetwork: str                         # full selfLink of peer network
    exchangeSubnetRoutes: Optional[bool] = True
    exportCustomRoutes: Optional[bool] = False
    importCustomRoutes: Optional[bool] = False


class RemovePeeringRequest(BaseModel):
    name: str
