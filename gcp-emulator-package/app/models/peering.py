"""
VPC Network Peering Model

Enables private RFC 1918 connectivity between two VPC networks.
"""

from app.factory import db
from datetime import datetime
import uuid


class VPCPeering(db.Model):
    """VPC Network Peering connection"""
    __tablename__ = 'vpc_peerings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(63), nullable=False)
    
    # Source network (the network this peering belongs to)
    network_id = db.Column(db.String(36), db.ForeignKey('networks.id', ondelete='CASCADE'), nullable=False)
    
    # Peer network (the network being peered with)
    peer_network = db.Column(db.String(255), nullable=False)  # Format: projects/{project}/global/networks/{network}
    peer_project_id = db.Column(db.String(255))  # Extracted from peer_network
    peer_network_name = db.Column(db.String(63))  # Extracted from peer_network
    
    # State
    state = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, INACTIVE
    state_details = db.Column(db.Text)
    
    # Configuration
    auto_create_routes = db.Column(db.Boolean, default=True)
    exchange_subnet_routes = db.Column(db.Boolean, default=True)
    export_custom_routes = db.Column(db.Boolean, default=False)
    import_custom_routes = db.Column(db.Boolean, default=False)
    export_subnet_routes_with_public_ip = db.Column(db.Boolean, default=True)
    import_subnet_routes_with_public_ip = db.Column(db.Boolean, default=False)
    
    # Metadata
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: one peering per network pair
    __table_args__ = (
        db.UniqueConstraint('network_id', 'name', name='unique_peering_per_network'),
    )
    
    # Relationship
    network = db.relationship('Network', foreign_keys=[network_id], backref='peerings')
    
    def to_dict(self, project_id: str = None) -> dict:
        """Convert to GCP peering format"""
        return {
            "kind": "compute#networkPeering",
            "name": self.name,
            "network": self.get_network_link(project_id),
            "peerNetwork": self.peer_network,
            "state": self.state,
            "stateDetails": self.state_details,
            "autoCreateRoutes": self.auto_create_routes,
            "exchangeSubnetRoutes": self.exchange_subnet_routes,
            "exportCustomRoutes": self.export_custom_routes,
            "importCustomRoutes": self.import_custom_routes,
            "exportSubnetRoutesWithPublicIp": self.export_subnet_routes_with_public_ip,
            "importSubnetRoutesWithPublicIp": self.import_subnet_routes_with_public_ip
        }
    
    def get_network_link(self, project_id: str) -> str:
        """Get the network self link"""
        if self.network:
            return f"https://www.googleapis.com/compute/v1/projects/{project_id}/global/networks/{self.network.name}"
        return ""
