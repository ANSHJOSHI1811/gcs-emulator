"""
Subnet Service - Manages VPC subnetworks and IP allocation.
Phase 1: Fake IP allocation from CIDR, no actual networking.
"""
import logging
import ipaddress
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.vpc import Subnetwork, NetworkInterface

logger = logging.getLogger(__name__)


class SubnetService:
    """
    Subnetwork management and IP allocation service.
    Control plane only - allocates fake IPs from CIDR range.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_subnetwork(
        self,
        network_id: int,
        name: str,
        region: str,
        ip_cidr_range: str,
        description: str = None,
        private_ip_google_access: bool = False
    ) -> Subnetwork:
        """
        Create a new subnetwork.
        
        Args:
            network_id: Parent network ID
            name: Subnetwork name
            region: GCP region (e.g., 'us-central1')
            ip_cidr_range: CIDR notation (e.g., '10.0.0.0/24')
            description: Optional description
            private_ip_google_access: Enable private Google access
        
        Returns:
            Subnetwork object
        """
        # Validate CIDR range
        try:
            network = ipaddress.ip_network(ip_cidr_range, strict=True)
        except ValueError as e:
            raise ValueError(f"Invalid CIDR range '{ip_cidr_range}': {e}")
        
        # Check for overlapping subnets in the same network
        existing_subnets = self.db.query(Subnetwork).filter_by(network_id=network_id).all()
        for existing in existing_subnets:
            existing_network = ipaddress.ip_network(existing.ip_cidr_range)
            if network.overlaps(existing_network):
                raise ValueError(
                    f"CIDR range {ip_cidr_range} overlaps with existing subnet "
                    f"'{existing.name}' ({existing.ip_cidr_range})"
                )
        
        # Check if subnet name already exists in this network
        existing = self.db.query(Subnetwork).filter_by(
            network_id=network_id,
            name=name
        ).first()
        
        if existing:
            raise ValueError(f"Subnetwork '{name}' already exists in this network")
        
        # Calculate gateway address (first usable IP)
        gateway_address = str(network.network_address + 1)
        
        # Create subnetwork
        subnetwork = Subnetwork(
            network_id=network_id,
            name=name,
            region=region,
            ip_cidr_range=ip_cidr_range,
            gateway_address=gateway_address,
            description=description,
            private_ip_google_access=private_ip_google_access,
            next_ip_index=2  # Start at .2 (.1 is gateway)
        )
        
        self.db.add(subnetwork)
        self.db.commit()
        self.db.refresh(subnetwork)
        
        logger.info(f"Created subnetwork: {name} in region {region} with CIDR {ip_cidr_range}")
        return subnetwork
    
    def get_subnetwork(self, network_id: int, name: str) -> Optional[Subnetwork]:
        """Get subnetwork by name within a network"""
        return self.db.query(Subnetwork).filter_by(
            network_id=network_id,
            name=name
        ).first()
    
    def get_subnetwork_by_id(self, subnetwork_id: int) -> Optional[Subnetwork]:
        """Get subnetwork by ID"""
        return self.db.query(Subnetwork).filter_by(id=subnetwork_id).first()
    
    def list_subnetworks(self, network_id: int = None, region: str = None) -> List[Subnetwork]:
        """
        List subnetworks, optionally filtered by network and/or region.
        """
        query = self.db.query(Subnetwork)
        
        if network_id:
            query = query.filter_by(network_id=network_id)
        
        if region:
            query = query.filter_by(region=region)
        
        return query.order_by(Subnetwork.created_at.desc()).all()
    
    def delete_subnetwork(self, network_id: int, name: str) -> bool:
        """
        Delete a subnetwork.
        Fails if instances are attached.
        """
        subnetwork = self.get_subnetwork(network_id, name)
        if not subnetwork:
            return False
        
        # Check if any instances are using this subnet
        interface_count = self.db.query(NetworkInterface).filter_by(subnetwork_id=subnetwork.id).count()
        if interface_count > 0:
            raise ValueError(f"Cannot delete subnetwork '{name}': {interface_count} instances are attached")
        
        self.db.delete(subnetwork)
        self.db.commit()
        
        logger.info(f"Deleted subnetwork: {name}")
        return True
    
    def allocate_ip(self, subnetwork_id: int) -> str:
        """
        Allocate next available IP from subnet's CIDR range.
        Phase 1: Simple incremental allocation (fake IPs, no actual networking).
        
        Args:
            subnetwork_id: Subnetwork to allocate from
        
        Returns:
            Allocated IP address as string
        """
        subnetwork = self.get_subnetwork_by_id(subnetwork_id)
        if not subnetwork:
            raise ValueError(f"Subnetwork {subnetwork_id} not found")
        
        # Parse CIDR range
        network = ipaddress.ip_network(subnetwork.ip_cidr_range)
        
        # Calculate next IP
        # network[0] is network address, network[1] is gateway, start from network[2]
        next_ip = network.network_address + subnetwork.next_ip_index
        
        # Check if we've exhausted the range
        if next_ip >= network.broadcast_address:
            raise ValueError(f"Subnetwork {subnetwork.name} has no available IPs")
        
        # Increment the counter
        subnetwork.next_ip_index += 1
        self.db.commit()
        
        allocated_ip = str(next_ip)
        logger.debug(f"Allocated IP {allocated_ip} from subnet {subnetwork.name}")
        
        return allocated_ip
    
    def release_ip(self, network_ip: str):
        """
        Release an IP address.
        Phase 1: No-op (we don't reuse IPs in simple incremental allocation).
        Future phases can implement IP pool management.
        """
        # Phase 1: Simple incremental allocation, no reuse
        logger.debug(f"IP {network_ip} released (not reused in Phase 1)")
        pass
    
    def validate_cidr(self, cidr_range: str) -> bool:
        """
        Validate CIDR notation.
        
        Returns:
            True if valid, raises ValueError otherwise
        """
        try:
            network = ipaddress.ip_network(cidr_range, strict=True)
            
            # GCP constraints: minimum /29, maximum /8
            if network.prefixlen < 8 or network.prefixlen > 29:
                raise ValueError(f"CIDR prefix must be between /8 and /29, got /{network.prefixlen}")
            
            return True
        except ValueError as e:
            raise ValueError(f"Invalid CIDR range: {e}")
