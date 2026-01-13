"""
VPC Networking Models

Models for:
- Network (VPC Network)
- Subnetwork (Subnet)
- FirewallRule
- FirewallAllowedDenied
- Route
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from app.factory import db


class Network(db.Model):
    """VPC Network model"""
    __tablename__ = 'networks'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(63), nullable=False)
    project_id = db.Column(db.String(255), db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    description = db.Column(db.Text)
    auto_create_subnetworks = db.Column(db.Boolean, default=False)
    routing_mode = db.Column(db.String(20), default='REGIONAL')  # REGIONAL or GLOBAL
    mtu = db.Column(db.Integer, default=1460)  # 1460 or 1500
    self_link = db.Column(db.Text)
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subnetworks = db.relationship('Subnetwork', back_populates='network', cascade='all, delete-orphan')
    firewall_rules = db.relationship('FirewallRule', back_populates='network', cascade='all, delete-orphan')
    routes = db.relationship('Route', back_populates='network', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('project_id', 'name', name='uq_network_project_name'),
    )
    
    def to_dict(self, project_id=None):
        """Convert to GCP API format"""
        pid = project_id or self.project_id
        self_link = f"http://127.0.0.1:8080/compute/v1/projects/{pid}/global/networks/{self.name}"
        
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description or '',
            'selfLink': self_link,
            'autoCreateSubnetworks': self.auto_create_subnetworks,
            'routingConfig': {
                'routingMode': self.routing_mode
            },
            'mtu': self.mtu,
            'creationTimestamp': self.creation_timestamp.isoformat() + 'Z',
            'kind': 'compute#network'
        }


class Subnetwork(db.Model):
    """Subnet model"""
    __tablename__ = 'subnetworks'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(63), nullable=False)
    network_id = db.Column(UUID(as_uuid=True), db.ForeignKey('networks.id', ondelete='CASCADE'), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    ip_cidr_range = db.Column(db.String(50), nullable=False)
    gateway_address = db.Column(db.String(50))
    description = db.Column(db.Text)
    private_ip_google_access = db.Column(db.Boolean, default=False)
    enable_flow_logs = db.Column(db.Boolean, default=False)
    secondary_ip_ranges = db.Column(JSONB)
    self_link = db.Column(db.Text)
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    network = db.relationship('Network', back_populates='subnetworks')
    
    __table_args__ = (
        db.UniqueConstraint('network_id', 'name', name='uq_subnetwork_network_name'),
    )
    
    def get_self_link(self, project_id=None):
        """Get the selfLink for this subnetwork"""
        # Get project_id from network
        from app.models.vpc import Network
        network = Network.query.get(self.network_id)
        pid = project_id or network.project_id
        return f"http://127.0.0.1:8080/compute/v1/projects/{pid}/regions/{self.region}/subnetworks/{self.name}"
    
    def to_dict(self, project_id=None):
        """Convert to GCP API format"""
        # Get project_id from network
        from app.models.vpc import Network
        network = Network.query.get(self.network_id)
        pid = project_id or network.project_id
        
        self_link = self.get_self_link(pid)
        network_link = f"http://127.0.0.1:8080/compute/v1/projects/{pid}/global/networks/{network.name}"
        
        result = {
            'id': str(self.id),
            'name': self.name,
            'network': network_link,
            'selfLink': self_link,
            'region': f"http://127.0.0.1:8080/compute/v1/projects/{pid}/regions/{self.region}",
            'ipCidrRange': self.ip_cidr_range,
            'gatewayAddress': self.gateway_address,
            'privateIpGoogleAccess': self.private_ip_google_access,
            'enableFlowLogs': self.enable_flow_logs,
            'creationTimestamp': self.creation_timestamp.isoformat() + 'Z',
            'kind': 'compute#subnetwork'
        }
        
        # Add description if it exists
        if self.description:
            result['description'] = self.description
        
        if self.secondary_ip_ranges:
            result['secondaryIpRanges'] = self.secondary_ip_ranges
            
        return result


class FirewallRule(db.Model):
    """Firewall Rule model"""
    __tablename__ = 'firewall_rules'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(63), nullable=False)
    network_id = db.Column(UUID(as_uuid=True), db.ForeignKey('networks.id', ondelete='CASCADE'), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.Integer, default=1000)
    direction = db.Column(db.String(10), default='INGRESS')
    action = db.Column(db.String(10), default='ALLOW')
    disabled = db.Column(db.Boolean, default=False)
    
    # Match criteria
    source_ranges = db.Column(ARRAY(db.Text))
    destination_ranges = db.Column(ARRAY(db.Text))
    source_tags = db.Column(ARRAY(db.Text))
    target_tags = db.Column(ARRAY(db.Text))
    source_service_accounts = db.Column(ARRAY(db.Text))
    target_service_accounts = db.Column(ARRAY(db.Text))
    
    self_link = db.Column(db.Text)
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    network = db.relationship('Network', back_populates='firewall_rules')
    allowed_protocols = db.relationship('FirewallAllowedDenied', back_populates='firewall_rule', 
                                       cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('network_id', 'name', name='uq_firewall_network_name'),
    )
    
    def get_self_link(self, project_id=None):
        """Get the selfLink for this firewall rule"""
        from app.models.vpc import Network
        network = Network.query.get(self.network_id)
        pid = project_id or network.project_id
        return f"http://127.0.0.1:8080/compute/v1/projects/{pid}/global/firewalls/{self.name}"
    
    def to_dict(self, project_id=None):
        """Convert to GCP API format"""
        from app.models.vpc import Network
        network = Network.query.get(self.network_id)
        pid = project_id or network.project_id
        
        self_link = f"http://127.0.0.1:8080/compute/v1/projects/{pid}/global/firewalls/{self.name}"
        network_link = f"http://127.0.0.1:8080/compute/v1/projects/{pid}/global/networks/{network.name}"
        
        result = {
            'id': str(self.id),
            'name': self.name,
            'description': self.description or '',
            'network': network_link,
            'selfLink': self_link,
            'priority': self.priority,
            'direction': self.direction,
            'disabled': self.disabled,
            'creationTimestamp': self.creation_timestamp.isoformat() + 'Z',
            'kind': 'compute#firewall'
        }
        
        # Add allowed or denied protocols based on action
        protocols_list = []
        for p in self.allowed_protocols:
            protocols_list.append(p.to_dict())
        
        if self.action == 'ALLOW' and protocols_list:
            result['allowed'] = protocols_list
        elif self.action == 'DENY' and protocols_list:
            result['denied'] = protocols_list
        
        # Add match criteria
        if self.source_ranges:
            result['sourceRanges'] = self.source_ranges
        if self.destination_ranges:
            result['destinationRanges'] = self.destination_ranges
        if self.source_tags:
            result['sourceTags'] = self.source_tags
        if self.target_tags:
            result['targetTags'] = self.target_tags
        if self.source_service_accounts:
            result['sourceServiceAccounts'] = self.source_service_accounts
        if self.target_service_accounts:
            result['targetServiceAccounts'] = self.target_service_accounts
            
        return result


class FirewallAllowedDenied(db.Model):
    """Firewall Allowed/Denied Protocols"""
    __tablename__ = 'firewall_allowed_denied'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firewall_rule_id = db.Column(UUID(as_uuid=True), db.ForeignKey('firewall_rules.id', ondelete='CASCADE'), nullable=False)
    ip_protocol = db.Column(db.String(20), nullable=False)
    ports = db.Column(ARRAY(db.Text))
    
    # Relationships
    firewall_rule = db.relationship('FirewallRule', back_populates='allowed_protocols')
    
    def to_dict(self):
        """Convert to GCP API format"""
        result = {
            'IPProtocol': self.ip_protocol
        }
        if self.ports:
            result['ports'] = self.ports
        return result


class Route(db.Model):
    """Route model"""
    __tablename__ = 'routes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(63), nullable=False)
    network_id = db.Column(UUID(as_uuid=True), db.ForeignKey('networks.id', ondelete='CASCADE'), nullable=False)
    description = db.Column(db.Text)
    dest_range = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.Integer, default=1000)
    next_hop_type = db.Column(db.String(30))
    next_hop_value = db.Column(db.Text)
    tags = db.Column(ARRAY(db.Text))
    self_link = db.Column(db.Text)
    creation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    network = db.relationship('Network', back_populates='routes')
    
    __table_args__ = (
        db.UniqueConstraint('network_id', 'name', name='uq_route_network_name'),
    )
    
    def to_dict(self, project_id=None):
        """Convert to GCP API format"""
        from app.models.vpc import Network
        network = Network.query.get(self.network_id)
        pid = project_id or network.project_id
        
        self_link = f"http://127.0.0.1:8080/compute/v1/projects/{pid}/global/routes/{self.name}"
        network_link = f"http://127.0.0.1:8080/compute/v1/projects/{pid}/global/networks/{network.name}"
        
        result = {
            'id': str(self.id),
            'name': self.name,
            'description': self.description or '',
            'network': network_link,
            'selfLink': self_link,
            'destRange': self.dest_range,
            'priority': self.priority,
            'creationTimestamp': self.creation_timestamp.isoformat() + 'Z',
            'kind': 'compute#route'
        }
        
        # Add next hop based on type
        if self.next_hop_type == 'gateway':
            result['nextHopGateway'] = self.next_hop_value
        elif self.next_hop_type == 'instance':
            result['nextHopInstance'] = self.next_hop_value
        elif self.next_hop_type == 'ip':
            result['nextHopIp'] = self.next_hop_value
        elif self.next_hop_type == 'vpn_tunnel':
            result['nextHopVpnTunnel'] = self.next_hop_value
        
        if self.tags:
            result['tags'] = self.tags
            
        return result
