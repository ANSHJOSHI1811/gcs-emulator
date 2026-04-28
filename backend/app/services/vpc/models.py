"""VPC Network service — Pydantic request/response models"""
from ipaddress import ip_network
from pydantic import BaseModel, Field, field_validator, model_validator
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

class FirewallRuleConfig(BaseModel):
    IPProtocol: str
    ports: Optional[List[str]] = None

    @field_validator("IPProtocol")
    @classmethod
    def validate_protocol(cls, value: str) -> str:
        protocol = (value or "").lower()
        if protocol not in {"tcp", "udp", "icmp", "all", "esp", "ah", "sctp"}:
            raise ValueError("IPProtocol must be one of: tcp, udp, icmp, all, esp, ah, sctp")
        return value


class CreateFirewallRequest(BaseModel):
    name: str
    network: str
    description: Optional[str] = None
    direction: Optional[str] = "INGRESS"
    priority: Optional[int] = Field(default=1000, ge=0, le=65535)
    sourceRanges: Optional[List[str]] = None
    destinationRanges: Optional[List[str]] = None
    sourceTags: Optional[List[str]] = None
    targetTags: Optional[List[str]] = None
    allowed: Optional[List[FirewallRuleConfig]] = None
    denied: Optional[List[FirewallRuleConfig]] = None
    disabled: Optional[bool] = False

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        upper = value.upper()
        if upper not in {"INGRESS", "EGRESS"}:
            raise ValueError("direction must be INGRESS or EGRESS")
        return upper

    @field_validator("sourceRanges", "destinationRanges")
    @classmethod
    def validate_cidrs(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if not value:
            return value
        for cidr in value:
            try:
                ip_network(cidr, strict=False)
            except ValueError as exc:
                raise ValueError(f"Invalid CIDR block: {cidr}") from exc
        return value

    @model_validator(mode="after")
    def validate_rule_presence(self) -> "CreateFirewallRequest":
        if not self.allowed and not self.denied:
            raise ValueError("At least one of allowed or denied must be provided")
        return self


class PatchFirewallRequest(BaseModel):
    description: Optional[str] = None
    direction: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=0, le=65535)
    sourceRanges: Optional[List[str]] = None
    destinationRanges: Optional[List[str]] = None
    sourceTags: Optional[List[str]] = None
    targetTags: Optional[List[str]] = None
    allowed: Optional[List[FirewallRuleConfig]] = None
    denied: Optional[List[FirewallRuleConfig]] = None
    disabled: Optional[bool] = None

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        upper = value.upper()
        if upper not in {"INGRESS", "EGRESS"}:
            raise ValueError("direction must be INGRESS or EGRESS")
        return upper

    @field_validator("sourceRanges", "destinationRanges")
    @classmethod
    def validate_cidrs(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if not value:
            return value
        for cidr in value:
            try:
                ip_network(cidr, strict=False)
            except ValueError as exc:
                raise ValueError(f"Invalid CIDR block: {cidr}") from exc
        return value


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
