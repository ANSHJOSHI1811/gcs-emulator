"""Docker Manager - Container operations"""
import docker
from typing import Optional

client = docker.from_env()

def create_default_network():
    """Create default GCP Docker network"""
    try:
        return client.networks.get("gcp-default")
    except docker.errors.NotFound:
        print("Creating gcp-default Docker network...")
        return client.networks.create("gcp-default", driver="bridge")

def create_container(name: str, network: str = "gcp-default", image: str = "ubuntu:22.04"):
    """
    Create Docker container for VM instance
    Returns: {"container_id": str, "container_name": str, "internal_ip": str}
    """
    container_name = f"gcp-vm-{name}"
    
    # Ensure network exists
    try:
        net = client.networks.get(network)
    except:
        net = create_default_network()
    
    # Create container
    container = client.containers.run(
        image,
        name=container_name,
        command="sleep infinity",
        detach=True,
        network=network,
        hostname=name
    )
    
    # Get IP address
    container.reload()
    ip = container.attrs['NetworkSettings']['Networks'][network]['IPAddress']
    
    return {
        "container_id": container.id,
        "container_name": container_name,
        "internal_ip": ip
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
