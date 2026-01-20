"""
VPN Gateway and Tunnel Models

Simplified VPN implementation for emulator (metadata only).
"""

from app.factory import db
from datetime import datetime
import uuid


class VPNGateway(db.Model):
    """VPN Gateway for hybrid connectivity"""
    __tablename__ = 'vpn_gateways'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(63), nullable=False)
    project_id = db.Column(db.String(255), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    
    # Network
    network_id = db.Column(db.String(36), db.ForeignKey('networks.id', ondelete='CASCADE'), nullable=False)
    
    # Description
    description = db.Column(db.Text)
    
    # VPN type
    vpn_gateway_type = db.Column(db.String(20), default='CLASSIC')  # CLASSIC or HA (High Availability)
    
    # IP address (for classic VPN)
    vpn_interface_0_ip_address = db.Column(db.String(50))  # Generated fake external IP
    vpn_interface_1_ip_address = db.Column(db.String(50))  # For HA VPN
    
    # Status
    status = db.Column(db.String(20), default='READY')  # PENDING, READY, DELETING
    
    # Metadata
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('project_id', 'region', 'name', name='unique_vpn_gateway'),
    )
    
    # Relationships
    network = db.relationship('Network', foreign_keys=[network_id], backref='vpn_gateways')
    tunnels = db.relationship('VPNTunnel', back_populates='gateway', cascade='all, delete-orphan')
    
    def to_dict(self, project_id: str = None) -> dict:
        """Convert to GCP VPN gateway format"""
        result = {
            "kind": "compute#vpnGateway",
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "region": f"https://www.googleapis.com/compute/v1/projects/{project_id or self.project_id}/regions/{self.region}",
            "network": self.network.get_self_link(project_id or self.project_id) if self.network else "",
            "status": self.status,
            "selfLink": self.get_self_link(project_id or self.project_id),
            "creationTimestamp": self.creation_timestamp.isoformat() + "Z" if self.creation_timestamp else None
        }
        
        # Add IP addresses
        if self.vpn_gateway_type == 'CLASSIC':
            result["ipAddress"] = self.vpn_interface_0_ip_address
        else:  # HA VPN
            result["vpnInterfaces"] = [
                {"id": 0, "ipAddress": self.vpn_interface_0_ip_address},
                {"id": 1, "ipAddress": self.vpn_interface_1_ip_address}
            ]
        
        return result
    
    def get_self_link(self, project_id: str) -> str:
        """Get the VPN gateway self link"""
        return f"https://www.googleapis.com/compute/v1/projects/{project_id}/regions/{self.region}/vpnGateways/{self.name}"


class VPNTunnel(db.Model):
    """VPN Tunnel connecting to external gateway"""
    __tablename__ = 'vpn_tunnels'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(63), nullable=False)
    project_id = db.Column(db.String(255), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    
    # VPN Gateway
    vpn_gateway_id = db.Column(db.String(36), db.ForeignKey('vpn_gateways.id', ondelete='CASCADE'))
    
    # Peer/Target
    peer_ip = db.Column(db.String(50), nullable=False)  # External peer gateway IP
    peer_external_gateway = db.Column(db.String(255))  # For HA VPN
    
    # Routing
    router_id = db.Column(db.String(36), db.ForeignKey('routers.id', ondelete='SET NULL'))
    
    # IKE settings
    ike_version = db.Column(db.Integer, default=2)
    shared_secret = db.Column(db.String(255), nullable=False)
    
    # Traffic selectors (local and remote IP ranges)
    local_traffic_selector = db.Column(db.JSON, default=list)  # List of local CIDR ranges
    remote_traffic_selector = db.Column(db.JSON, default=list)  # List of remote CIDR ranges
    
    # Description
    description = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(20), default='ESTABLISHED')  # PENDING, ESTABLISHED, FAILED
    detailed_status = db.Column(db.Text)
    
    # Metadata
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('project_id', 'region', 'name', name='unique_vpn_tunnel'),
    )
    
    # Relationships
    gateway = db.relationship('VPNGateway', back_populates='tunnels')
    router = db.relationship('Router', foreign_keys=[router_id])
    
    def to_dict(self, project_id: str = None) -> dict:
        """Convert to GCP VPN tunnel format"""
        return {
            "kind": "compute#vpnTunnel",
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "region": f"https://www.googleapis.com/compute/v1/projects/{project_id or self.project_id}/regions/{self.region}",
            "targetVpnGateway": self.gateway.get_self_link(project_id or self.project_id) if self.gateway else None,
            "peerIp": self.peer_ip,
            "peerExternalGateway": self.peer_external_gateway,
            "router": self.router.get_self_link(project_id or self.project_id) if self.router else None,
            "ikeVersion": self.ike_version,
            "localTrafficSelector": self.local_traffic_selector or [],
            "remoteTrafficSelector": self.remote_traffic_selector or [],
            "status": self.status,
            "detailedStatus": self.detailed_status,
            "selfLink": self.get_self_link(project_id or self.project_id),
            "creationTimestamp": self.creation_timestamp.isoformat() + "Z" if self.creation_timestamp else None
        }
    
    def get_self_link(self, project_id: str) -> str:
        """Get the VPN tunnel self link"""
        return f"https://www.googleapis.com/compute/v1/projects/{project_id}/regions/{self.region}/vpnTunnels/{self.name}"
