"""
VPC Service - Manages VPC networks (control plane only).
Phase 1: Network identity, no actual packet routing or firewall enforcement.
"""
import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.models.vpc import Network, Subnetwork, NetworkInterface
from app.services.subnet_service import SubnetService

logger = logging.getLogger(__name__)


class VPCService:
    """
    VPC Network management service.
    Control plane only - manages network identity and metadata.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.subnet_service = SubnetService(db)
    
    def create_network(
        self,
        project_id: str,
        name: str,
        auto_create_subnetworks: bool = False,
        description: str = None,
        routing_mode: str = 'REGIONAL',
        mtu: int = 1460
    ) -> Network:
        """
        Create a new VPC network.
        
        Args:
            project_id: GCP project ID
            name: Network name (must be unique within project)
            auto_create_subnetworks: If True, auto-create subnets in all regions
            description: Optional description
            routing_mode: REGIONAL or GLOBAL
            mtu: Maximum transmission unit (1460 or 1500)
        
        Returns:
            Network object
        """
        # Check if network already exists
        existing = self.db.query(Network).filter_by(
            project_id=project_id,
            name=name
        ).first()
        
        if existing:
            raise ValueError(f"Network '{name}' already exists in project '{project_id}'")
        
        # Validate MTU
        if mtu not in [1460, 1500]:
            raise ValueError(f"Invalid MTU: {mtu}. Must be 1460 or 1500")
        
        # Create network
        network = Network(
            name=name,
            project_id=project_id,
            description=description,
            auto_create_subnetworks=auto_create_subnetworks,
            routing_mode=routing_mode,
            mtu=mtu
        )
        
        self.db.add(network)
        self.db.flush()  # Get network.id before creating subnets
        
        # If auto-create, create default subnets in common regions
        if auto_create_subnetworks:
            self._create_auto_subnets(network)
        
        self.db.commit()
        self.db.refresh(network)
        
        logger.info(f"Created VPC network: {name} in project {project_id} (auto_create={auto_create_subnetworks})")
        return network
    
    def _create_auto_subnets(self, network: Network):
        """
        Create automatic subnets in default regions.
        Uses standard GCP CIDR ranges.
        """
        # Default regions and CIDR ranges (similar to GCP auto mode)
        default_subnets = [
            ('us-central1', '10.128.0.0/20'),
            ('us-east1', '10.132.0.0/20'),
            ('us-west1', '10.136.0.0/20'),
            ('europe-west1', '10.140.0.0/20'),
            ('asia-east1', '10.144.0.0/20'),
        ]
        
        for region, cidr in default_subnets:
            try:
                self.subnet_service.create_subnetwork(
                    network_id=network.id,
                    name=f"{network.name}-{region}",
                    region=region,
                    ip_cidr_range=cidr,
                    description=f"Auto-created subnet for {network.name}"
                )
            except Exception as e:
                logger.warning(f"Failed to create auto subnet in {region}: {e}")
    
    def get_network(self, project_id: str, name: str) -> Optional[Network]:
        """Get network by name"""
        return self.db.query(Network).filter_by(
            project_id=project_id,
            name=name
        ).first()
    
    def get_network_by_id(self, network_id: int) -> Optional[Network]:
        """Get network by ID"""
        return self.db.query(Network).filter_by(id=network_id).first()
    
    def list_networks(self, project_id: str) -> List[Network]:
        """List all networks in a project"""
        return self.db.query(Network).filter_by(project_id=project_id).order_by(Network.created_at.desc()).all()
    
    def delete_network(self, project_id: str, name: str) -> bool:
        """
        Delete a VPC network.
        Cascades to subnetworks and network interfaces.
        """
        network = self.get_network(project_id, name)
        if not network:
            return False
        
        # Check if any instances are using this network
        interface_count = self.db.query(NetworkInterface).filter_by(network_id=network.id).count()
        if interface_count > 0:
            raise ValueError(f"Cannot delete network '{name}': {interface_count} instances are attached")
        
        self.db.delete(network)
        self.db.commit()
        
        logger.info(f"Deleted VPC network: {name} from project {project_id}")
        return True
    
    def ensure_default_network(self, project_id: str) -> Network:
        """
        Ensure default network exists for a project.
        Creates it if it doesn't exist.
        
        Returns:
            Default network
        """
        default_name = 'default'
        network = self.get_network(project_id, default_name)
        
        if not network:
            logger.info(f"Creating default network for project {project_id}")
            network = self.create_network(
                project_id=project_id,
                name=default_name,
                auto_create_subnetworks=True,
                description='Default network created automatically'
            )
        
        return network
    
    def get_default_subnet_for_region(self, project_id: str, region: str) -> Optional[Subnetwork]:
        """
        Get the default subnet for a region.
        Creates default network if it doesn't exist.
        """
        network = self.ensure_default_network(project_id)
        
        # Find subnet in this region
        subnet = self.db.query(Subnetwork).filter_by(
            network_id=network.id,
            region=region
        ).first()
        
        if not subnet:
            # If auto-create network but no subnet for this region, create one
            logger.info(f"Creating default subnet for region {region} in project {project_id}")
            # Use a CIDR range based on region hash (simple approach)
            base_octet = hash(region) % 200 + 10
            cidr = f"10.{base_octet}.0.0/20"
            
            subnet = self.subnet_service.create_subnetwork(
                network_id=network.id,
                name=f"default-{region}",
                region=region,
                ip_cidr_range=cidr,
                description=f"Default subnet for {region}"
            )
        
        return subnet
