"""
Backward-compatibility shim — all DB models live in core/database.py.
Old api/ modules import from here; new services/ modules import from core.database.
"""
from core.database import (
    Base, engine, SessionLocal, get_db,
    # Compute
    Instance, Zone, MachineType, Address, Disk,
    # Projects
    Project,
    # VPC
    Network, Subnet, Firewall, Route, CloudRouter, CloudNAT, VPCPeering,
    # Storage
    SignedUrlSession, Bucket, Object,
    # IAM
    ServiceAccount, IAMPolicyBinding, CustomRole, ServiceAccountKey,
    # GKE
    GKECluster, GKENodePool, GKEAddon,
)

__all__ = [
    "Base", "engine", "SessionLocal", "get_db",
    "Instance", "Zone", "MachineType", "Address", "Disk",
    "Project",
    "Network", "Subnet", "Firewall", "Route", "CloudRouter", "CloudNAT", "VPCPeering",
    "SignedUrlSession", "Bucket", "Object",
    "ServiceAccount", "IAMPolicyBinding", "CustomRole", "ServiceAccountKey",
    "GKECluster", "GKENodePool", "GKEAddon",
]
