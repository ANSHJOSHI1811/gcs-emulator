"""
Cloud Router Model - VPC Networking

Cloud Router enables dynamic route exchange via BGP for hybrid connectivity.
In the emulator, this is metadata-only (no actual routing).

Attributes:
- name: Router name (unique per region)
- network_id: Associated VPC network
- region: GCP region (us-central1, europe-west1, etc.)
- description: Optional description
- bgp_asn: BGP Autonomous System Number (ASN) for the router
- bgp_keepalive_interval: BGP keepalive interval in seconds
- interfaces: BGP interfaces (future: for VPN/Interconnect)
- bgp_peers: BGP peering sessions (future)
"""

import uuid
from datetime import datetime
from app.factory import db


class Router(db.Model):
    __tablename__ = 'routers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(63), nullable=False)
    network_id = db.Column(db.String(36), db.ForeignKey('networks.id', ondelete='CASCADE'), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    
    # BGP Configuration
    bgp_asn = db.Column(db.Integer, nullable=False)  # 64512-65534 (private) or 1-64511 (public)
    bgp_keepalive_interval = db.Column(db.Integer, default=20)  # seconds
    
    # Timestamps
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('network_id', 'region', 'name', name='unique_router_per_region'),
    )
    
    # Relationship
    network = db.relationship('Network', backref=db.backref('routers', lazy=True, cascade='all, delete-orphan'))
    
    def to_dict(self, project_id: str = None) -> dict:
        """
        Convert router to GCP API format
        
        Returns:
            dict: GCP-compatible router representation
        """
        base_url = "http://127.0.0.1:8080"
        
        router_dict = {
            "kind": "compute#router",
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "network": f"{base_url}/compute/v1/projects/{project_id}/global/networks/{self.network.name}" if project_id else self.network.name,
            "region": f"{base_url}/compute/v1/projects/{project_id}/regions/{self.region}" if project_id else self.region,
            "selfLink": self.get_self_link(project_id),
            "creationTimestamp": self.creation_timestamp.isoformat() + "Z" if self.creation_timestamp else None,
            "bgp": {
                "asn": self.bgp_asn,
                "keepaliveInterval": self.bgp_keepalive_interval
            },
            "interfaces": [],  # Future: VPN/Interconnect interfaces
            "bgpPeers": []     # Future: BGP peers
        }
        
        return router_dict
    
    def get_self_link(self, project_id: str) -> str:
        """Generate self link URL"""
        base_url = "http://127.0.0.1:8080"
        return f"{base_url}/compute/v1/projects/{project_id}/regions/{self.region}/routers/{self.name}"
    
    def __repr__(self):
        return f"<Router {self.name} in {self.region} (ASN: {self.bgp_asn})>"


class CloudNAT(db.Model):
    """
    Cloud NAT Configuration
    
    Enables instances without external IPs to access the internet.
    Attached to a Cloud Router.
    """
    __tablename__ = 'cloud_nat'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(63), nullable=False)
    router_id = db.Column(db.String(36), db.ForeignKey('routers.id', ondelete='CASCADE'), nullable=False)
    
    # NAT Configuration
    nat_ip_allocate_option = db.Column(db.String(50), default='AUTO_ONLY')  # AUTO_ONLY, MANUAL_ONLY
    source_subnetwork_ip_ranges_to_nat = db.Column(db.String(50), default='ALL_SUBNETWORKS_ALL_IP_RANGES')
    nat_ips = db.Column(db.JSON, default=list)  # List of external IP self-links
    
    # Port allocation
    min_ports_per_vm = db.Column(db.Integer, default=64)
    max_ports_per_vm = db.Column(db.Integer, default=65536)
    
    # Logging
    enable_logging = db.Column(db.Boolean, default=False)
    log_filter = db.Column(db.String(50), default='ALL')  # ALL, ERRORS_ONLY, TRANSLATIONS_ONLY
    
    # Timestamps
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('router_id', 'name', name='unique_nat_per_router'),
    )
    
    # Relationship
    router = db.relationship('Router', backref=db.backref('nat_configs', lazy=True, cascade='all, delete-orphan'))
    
    def to_dict(self, project_id: str = None) -> dict:
        """
        Convert Cloud NAT to GCP API format
        
        Returns:
            dict: GCP-compatible NAT configuration
        """
        nat_dict = {
            "kind": "compute#routerNat",
            "name": self.name,
            "natIpAllocateOption": self.nat_ip_allocate_option,
            "sourceSubnetworkIpRangesToNat": self.source_subnetwork_ip_ranges_to_nat,
            "natIps": self.nat_ips or [],
            "minPortsPerVm": self.min_ports_per_vm,
            "maxPortsPerVm": self.max_ports_per_vm,
            "enableEndpointIndependentMapping": False,  # Simplified for emulator
            "logConfig": {
                "enable": self.enable_logging,
                "filter": self.log_filter
            }
        }
        
        return nat_dict
    
    def __repr__(self):
        return f"<CloudNAT {self.name} on Router {self.router_id}>"
