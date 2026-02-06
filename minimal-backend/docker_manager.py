"""Docker Manager - Container operations"""
import docker
import ipaddress
from typing import Optional

client = docker.from_env()

def create_docker_network_with_cidr(name: str, cidr: str, project: str) -> str:
    """Create Docker network with custom CIDR range
    
    Args:
        name: Network name
        cidr: CIDR range (e.g., '10.99.0.0/16')
        project: GCP project ID
        
    Returns:
        Docker network ID
    """
    docker_network_name = f"gcp-vpc-{project}-{name}"
    
    try:
        # Check if already exists
        existing = client.networks.get(docker_network_name)
        print(f"✓ Network {docker_network_name} already exists")
        return existing.id
    except docker.errors.NotFound:
        pass
    
    # Parse CIDR to get gateway
    network_obj = ipaddress.ip_network(cidr, strict=False)
    gateway = str(list(network_obj.hosts())[0])
    
    # Create IPAM configuration
    ipam_pool = docker.types.IPAMPool(
        subnet=cidr,
        gateway=gateway
    )
    ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
    
    # Create network
    network = client.networks.create(
        docker_network_name,
        driver="bridge",
        ipam=ipam_config,
        labels={
            "gcp-project": project,
            "gcp-network": name,
            "gcp-cidr": cidr
        }
    )
    
    print(f"✓ Created Docker network {docker_network_name} with CIDR {cidr}, gateway {gateway}")
    return network.id

def create_default_network():
    """Create default GCP Docker network with IPAM configuration"""
    try:
        return client.networks.get("gcp-default")
    except docker.errors.NotFound:
        print("Creating gcp-default Docker network with IPAM...")
        
        # Create IPAM configuration for default network
        ipam_pool = docker.types.IPAMPool(
            subnet='10.128.0.0/20',
            gateway='10.128.0.1'
        )
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
        
        return client.networks.create(
            "gcp-default", 
            driver="bridge",
            ipam=ipam_config
        )

def create_container(name: str, network: str = "gcp-default", image: str = "ubuntu:22.04", ip_address: Optional[str] = None):
    """
    Create Docker container for VM instance with optional static IP assignment
    
    Args:
        name: VM instance name
        network: Docker network name
        image: Container image
        ip_address: Optional static IP to assign (e.g., "10.128.0.2")
    
    Returns: {"container_id": str, "container_name": str, "internal_ip": str}
    """
    container_name = f"gcp-vm-{name}"
    
    # Ensure network exists
    try:
        net = client.networks.get(network)
    except:
        net = create_default_network()
    
    # Create container WITHOUT attaching to network yet (if we need specific IP)
    if ip_address:
        container = client.containers.run(
            image,
            name=container_name,
            command="sleep infinity",
            detach=True,
            network=None,  # Don't attach yet
            hostname=name
        )
        
        # Connect to network with specific IP
        net.connect(container, ipv4_address=ip_address)
        print(f"✓ Assigned IP {ip_address} to container {container_name}")
        
        container.reload()
        final_ip = ip_address
    else:
        # Create with auto-assigned IP
        container = client.containers.run(
            image,
            name=container_name,
            command="sleep infinity",
            detach=True,
            network=network,
            hostname=name
        )
        
        # Get auto-assigned IP
        container.reload()
        final_ip = container.attrs['NetworkSettings']['Networks'][network]['IPAddress']
        print(f"✓ Auto-assigned IP {final_ip} to container {container_name}")
    
    return {
        "container_id": container.id,
        "container_name": container_name,
        "internal_ip": final_ip
    }

def stop_container(container_id: str):
    """Stop Docker container"""
    try:
        container = client.containers.get(container_id)
        container.stop()
        return True
    except Exception as e:
        print(f"Error stopping container: {e}")
        return False

def start_container(container_id: str):
    """Start Docker container"""
    try:
        container = client.containers.get(container_id)
        container.start()
        return True
    except Exception as e:
        print(f"Error starting container: {e}")
        return False

def delete_container(container_id: str):
    """Delete Docker container"""
    try:
        container = client.containers.get(container_id)
        container.remove(force=True)
        return True
    except Exception as e:
        print(f"Error deleting container: {e}")
        return False

def get_container_status(container_id: str) -> Optional[str]:
    """Get container status"""
    try:
        container = client.containers.get(container_id)
        return container.status
    except:
        return None

# Initialize default network
create_default_network()
print("✅ Docker manager initialized")
