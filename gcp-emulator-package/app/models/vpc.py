"""
VPC Network and Subnetwork models for GCP Compute Engine emulation.
Phase 1: Control plane only - network identity and fake IP allocation.
"""
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.factory import db


class Network(db.Model):
    """
    VPC Network model - represents a virtual network (control plane only).
    No actual packet routing or firewall enforcement in Phase 1.
    """
    __tablename__ = 'networks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), nullable=False)  # GCP network name constraints
    project_id = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    auto_create_subnetworks = db.Column(db.Boolean, default=False, nullable=False)
    routing_mode = db.Column(db.String(20), default='REGIONAL')  # REGIONAL or GLOBAL
    mtu = db.Column(db.Integer, default=1460)  # Maximum transmission unit
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subnetworks = relationship('Subnetwork', back_populates='network', cascade='all, delete-orphan')
    network_interfaces = relationship('NetworkInterface', back_populates='network')
    
    def __repr__(self):
        return f"<Network(id={self.id}, name={self.name}, project={self.project_id})>"
    
    def to_dict(self):
        """Convert to GCP Compute API v1 format"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description or '',
            'selfLink': f'projects/{self.project_id}/global/networks/{self.name}',
            'autoCreateSubnetworks': self.auto_create_subnetworks,
            'subnetworks': [
                f'projects/{self.project_id}/regions/{sub.region}/subnetworks/{sub.name}'
                for sub in self.subnetworks
            ] if not self.auto_create_subnetworks else [],
            'routingConfig': {
                'routingMode': self.routing_mode
            },
            'mtu': self.mtu,
            'kind': 'compute#network',
            'creationTimestamp': self.created_at.isoformat() + 'Z' if self.created_at else None
        }


class Subnetwork(db.Model):
    """
    Subnet model - regional subdivision of a VPC network.
    Controls fake IP allocation from CIDR range.
    """
    __tablename__ = 'subnetworks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), nullable=False)
    network_id = db.Column(db.Integer, db.ForeignKey('networks.id', ondelete='CASCADE'), nullable=False, index=True)
    region = db.Column(db.String(50), nullable=False, index=True)
    ip_cidr_range = db.Column(db.String(50), nullable=False)  # e.g., "10.0.0.0/24"
    gateway_address = db.Column(db.String(45), nullable=True)  # First usable IP in range
    description = db.Column(db.Text, nullable=True)
    private_ip_google_access = db.Column(db.Boolean, default=False)
    
    # IP allocation tracking - simple counter for fake IPs
    next_ip_index = db.Column(db.Integer, default=2, nullable=False)  # Start at .2 (.1 is gateway)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    network = relationship('Network', back_populates='subnetworks')
    network_interfaces = relationship('NetworkInterface', back_populates='subnetwork')
    
    def __repr__(self):
        return f"<Subnetwork(id={self.id}, name={self.name}, region={self.region}, cidr={self.ip_cidr_range})>"
    
    def to_dict(self, project_id=None):
        """Convert to GCP Compute API v1 format"""
        if not project_id and self.network:
            project_id = self.network.project_id
            
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description or '',
            'selfLink': f'projects/{project_id}/regions/{self.region}/subnetworks/{self.name}',
            'network': f'projects/{project_id}/global/networks/{self.network.name}' if self.network else None,
            'ipCidrRange': self.ip_cidr_range,
            'gatewayAddress': self.gateway_address,
            'region': self.region,
            'privateIpGoogleAccess': self.private_ip_google_access,
            'kind': 'compute#subnetwork',
            'creationTimestamp': self.created_at.isoformat() + 'Z' if self.created_at else None
        }


class NetworkInterface(db.Model):
    """
    Network interface attachment for compute instances.
    Phase 1: Single NIC only, stores fake private IP.
    """
    __tablename__ = 'network_interfaces'
    
    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.String(36), db.ForeignKey('instances.id', ondelete='CASCADE'), nullable=False, index=True)
    network_id = db.Column(db.Integer, db.ForeignKey('networks.id', ondelete='CASCADE'), nullable=False, index=True)
    subnetwork_id = db.Column(db.Integer, db.ForeignKey('subnetworks.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Fake IP allocation (control plane only - no actual networking)
    network_ip = db.Column(db.String(45), nullable=False)  # Private IP from subnet CIDR
    name = db.Column(db.String(63), default='nic0')  # Interface name
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    instance = relationship('Instance', back_populates='network_interfaces')
    network = relationship('Network', back_populates='network_interfaces')
    subnetwork = relationship('Subnetwork', back_populates='network_interfaces')
    
    def __repr__(self):
        return f"<NetworkInterface(id={self.id}, instance_id={self.instance_id}, ip={self.network_ip})>"
    
    def to_dict(self, project_id=None):
        """Convert to GCP Compute API v1 format"""
        if not project_id and self.network:
            project_id = self.network.project_id
            
        result = {
            'name': self.name,
            'network': f'projects/{project_id}/global/networks/{self.network.name}' if self.network else None,
            'subnetwork': f'projects/{project_id}/regions/{self.subnetwork.region}/subnetworks/{self.subnetwork.name}' if self.subnetwork else None,
            'networkIP': self.network_ip,
            'kind': 'compute#networkInterface'
        }
        
        # Phase 1: No external IPs, no access configs
        # Future phases can add accessConfigs for external IPs
        
        return result
