"""VPC Peering Manager - Handles Docker network operations for VPC peering"""
import docker
import logging
from ipaddress import ip_network, AddressValueError, IPv4Network
from typing import List, Tuple, Optional, Any

logger = logging.getLogger(__name__)


class PeeringManager:
    """Manages VPC peering operations using Docker networks"""
    
    def __init__(self):
        self.client = docker.from_env()
    
    def validate_cidrs_dont_overlap(self, cidr1: str, cidr2: str) -> bool:
        """
        Validate that two CIDR ranges don't overlap
        
        Args:
            cidr1: First CIDR range (e.g., "10.0.0.0/16")
            cidr2: Second CIDR range (e.g., "10.1.0.0/16")
        
        Returns:
            True if CIDRs don't overlap, False otherwise
        """
        try:
            net1 = ip_network(cidr1, strict=False)
            net2 = ip_network(cidr2, strict=False)
            return not (net1.overlaps(net2) or net2.overlaps(net1))
        except (AddressValueError, ValueError) as e:
            logger.error(f"Invalid CIDR format: {e}")
            return False
    
    def get_docker_network_name(self, project_id: str, network_name: str) -> str:
        """
        Generate Docker network name from project and network identifiers
        
        Args:
            project_id: GCP project ID
            network_name: VPC network name
        
        Returns:
            Docker-compatible network name
        """
        # Docker network names max 63 chars, alphanumeric + dash/underscore
        name = f"{project_id}-{network_name}".lower().replace("_", "-")
        return name[:63]
    
    def get_docker_network(self, network_name: str) -> Optional[Any]:
        """
        Get Docker network by name
        
        Args:
            network_name: Docker network name
        
        Returns:
            Docker network object or None if not found
        """
        try:
            return self.client.networks.get(network_name)
        except docker.errors.NotFound:
            return None
    
    def get_network_containers(self, docker_network: Any) -> List[str]:
        """
        Get list of container IDs attached to a network
        
        Args:
            docker_network: Docker network object
        
        Returns:
            List of container IDs/names
        """
        try:
            containers = []
            network_info = docker_network.attrs.get("Containers", {})
            for container_id in network_info.keys():
                containers.append(container_id)
            return containers
        except Exception as e:
            logger.error(f"Error getting network containers: {e}")
            return []
    
    def connect_docker_networks(self, local_network_name: str, peer_network_name: str) -> bool:
        """
        Connect two Docker networks by attaching all containers from peer network
        to the local network (enables multi-homing)
        
        Args:
            local_network_name: Docker network name for local VPC
            peer_network_name: Docker network name for peer VPC
        
        Returns:
            True if successful, False otherwise
        """
        try:
            local_network = self.get_docker_network(local_network_name)
            peer_network = self.get_docker_network(peer_network_name)
            
            if not local_network:
                logger.error(f"Local network not found: {local_network_name}")
                return False
            
            if not peer_network:
                logger.error(f"Peer network not found: {peer_network_name}")
                return False
            
            # Get all containers in peer network
            peer_containers = self.get_network_containers(peer_network)
            
            if not peer_containers:
                logger.warning(f"No containers in peer network: {peer_network_name}")
                # Still return True as this is valid - empty VPC
                return True
            
            # Connect each peer container to local network
            for container_id in peer_containers:
                try:
                    container = self.client.containers.get(container_id)
                    
                    # Check if already connected
                    if local_network_name in [net for net in container.attrs.get("NetworkSettings", {}).get("Networks", {}).keys()]:
                        logger.debug(f"Container {container_id} already connected to {local_network_name}")
                        continue
                    
                    local_network.connect(container)
                    logger.info(f"✅ Connected container {container_id} to {local_network_name}")
                
                except docker.errors.APIError as e:
                    if "already exists" in str(e).lower():
                        logger.debug(f"Container {container_id} already connected to {local_network_name}")
                    else:
                        logger.error(f"Error connecting container to network: {e}")
                        return False
            
            # Similarly connect local containers to peer network
            local_containers = self.get_network_containers(local_network)
            for container_id in local_containers:
                try:
                    container = self.client.containers.get(container_id)
                    
                    # Check if already connected
                    if peer_network_name in [net for net in container.attrs.get("NetworkSettings", {}).get("Networks", {}).keys()]:
                        logger.debug(f"Container {container_id} already connected to {peer_network_name}")
                        continue
                    
                    peer_network.connect(container)
                    logger.info(f"✅ Connected container {container_id} to {peer_network_name}")
                
                except docker.errors.APIError as e:
                    if "already exists" in str(e).lower():
                        logger.debug(f"Container {container_id} already connected to {peer_network_name}")
                    else:
                        logger.error(f"Error connecting container to network: {e}")
                        return False
            
            logger.info(f"✅ VPC peering established: {local_network_name} <-> {peer_network_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error connecting Docker networks: {e}")
            return False
    
    def disconnect_docker_networks(self, local_network_name: str, peer_network_name: str) -> bool:
        """
        Disconnect two Docker networks by removing containers from peer network
        
        Args:
            local_network_name: Docker network name for local VPC
            peer_network_name: Docker network name for peer VPC
        
        Returns:
            True if successful, False otherwise
        """
        try:
            local_network = self.get_docker_network(local_network_name)
            peer_network = self.get_docker_network(peer_network_name)
            
            if not local_network:
                logger.error(f"Local network not found: {local_network_name}")
                return False
            
            if not peer_network:
                logger.error(f"Peer network not found: {peer_network_name}")
                return False
            
            # Disconnect peer containers from local network
            peer_containers = self.get_network_containers(peer_network)
            for container_id in peer_containers:
                try:
                    container = self.client.containers.get(container_id)
                    local_network.disconnect(container)
                    logger.info(f"✅ Disconnected container {container_id} from {local_network_name}")
                
                except docker.errors.APIError as e:
                    if "not connected" in str(e).lower():
                        logger.debug(f"Container {container_id} not connected to {local_network_name}")
                    else:
                        logger.error(f"Error disconnecting container: {e}")
                        return False
            
            # Disconnect local containers from peer network
            local_containers = self.get_network_containers(local_network)
            for container_id in local_containers:
                try:
                    container = self.client.containers.get(container_id)
                    peer_network.disconnect(container)
                    logger.info(f"✅ Disconnected container {container_id} from {peer_network_name}")
                
                except docker.errors.APIError as e:
                    if "not connected" in str(e).lower():
                        logger.debug(f"Container {container_id} not connected to {peer_network_name}")
                    else:
                        logger.error(f"Error disconnecting container: {e}")
                        return False
            
            logger.info(f"✅ VPC peering removed: {local_network_name} <-> {peer_network_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error disconnecting Docker networks: {e}")
            return False


# Singleton instance
_peering_manager = None


def get_peering_manager() -> PeeringManager:
    """Get or create singleton peering manager"""
    global _peering_manager
    if _peering_manager is None:
        _peering_manager = PeeringManager()
    return _peering_manager
