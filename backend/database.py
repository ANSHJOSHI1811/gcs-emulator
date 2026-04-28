"""
Backward-compatibility shim — all DB models live in app/models/database.py.
Old imports like 'from database import Base' still work via this shim.
"""
from app.models.database import (
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
