"""
PHASE 1: Docker Driver for Compute Service
Manages Docker container lifecycle for VM simulation (WSL Linux compatible)
"""
import docker
from docker.errors import DockerException, ImageNotFound, APIError, NotFound
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class DockerDriver:
    """
    PHASE 1: Thread-safe Docker wrapper for compute instances
    - Creates fresh docker client per method call (thread safety)
    - Works on WSL Linux with /var/run/docker.sock
    - No Windows paths, no bind mounts
    """
    
    def __init__(self, socket_path: str = "/var/run/docker.sock"):
        """
        Initialize Docker driver (verifies Docker is accessible)
        
        Args:
            socket_path: Path to Docker socket (default: /var/run/docker.sock)
        """
        self.socket_path = socket_path
        
        # Verify Docker is accessible
        try:
            client = self._get_client()
            client.ping()
            logger.info(f"DockerDriver initialized (socket: {socket_path})")
        except DockerException as e:
            logger.error(f"Failed to connect to Docker: {e}")
            raise
    
    def _get_client(self):
        """
        Get fresh Docker client (thread-safe pattern)
        
        Returns:
            docker.DockerClient instance
        """
        return docker.from_env()
    
    def create_container(
        self,
        image: str,
        name: Optional[str] = None,
        cpu: int = 1,
        memory: int = 512
    ) -> Optional[str]:
        """
        Create and start a Docker container
        
        Args:
            image: Docker image to use (e.g., 'alpine:latest')
            name: Optional container name
            cpu: Number of CPU cores
            memory: Memory limit in MB
        
        Returns:
            Container ID if successful, None otherwise
        """
        client = self._get_client()
        
        try:
            # Pull image if not present
            logger.info(f"Ensuring image is available: {image}")
            try:
                client.images.get(image)
            except ImageNotFound:
                logger.info(f"Pulling image: {image}")
                client.images.pull(image)
            
            # Calculate resource limits
            nano_cpus = int(cpu * 1e9)  # Convert cores to nanocpus
            mem_limit = f"{memory}m"
            
            # Create container
            logger.info(f"Creating container (image={image}, cpu={cpu}, memory={memory}MB)")
            
            container = client.containers.run(
                image=image,
                name=name,
                detach=True,
                remove=False,
                nano_cpus=nano_cpus,
                mem_limit=mem_limit,
                stdin_open=True,
                tty=True,
                command="/bin/sh"  # Keep container running
            )
            
            container_id = container.id
            logger.info(f"Container created and started: {container_id[:12]} (name={name})")
            return container_id
            
        except APIError as e:
            logger.error(f"Failed to create container: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating container: {e}", exc_info=True)
            return None
    
    def start_container(self, container_id: str) -> bool:
        """
        Start a stopped container
        
        Args:
            container_id: Container ID
        
        Returns:
            True if successful, False otherwise
        """
        client = self._get_client()
        
        try:
            container = client.containers.get(container_id)
            container.start()
            logger.info(f"Started container: {container_id[:12]}")
            return True
        except NotFound:
            logger.error(f"Container not found: {container_id[:12]}")
            return False
        except APIError as e:
            logger.error(f"Failed to start container {container_id[:12]}: {e}")
            return False
    
    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """
        Stop a running container
        
        Args:
            container_id: Container ID
            timeout: Seconds to wait before force kill
        
        Returns:
            True if successful, False otherwise
        """
        client = self._get_client()
        
        try:
            container = client.containers.get(container_id)
            container.stop(timeout=timeout)
            logger.info(f"Stopped container: {container_id[:12]}")
            return True
        except NotFound:
            logger.error(f"Container not found: {container_id[:12]}")
            return False
        except APIError as e:
            logger.error(f"Failed to stop container {container_id[:12]}: {e}")
            return False
    
    def remove_container(self, container_id: str, force: bool = True) -> bool:
        """
        Remove a container
        
        Args:
            container_id: Container ID
            force: Force removal even if running
        
        Returns:
            True if successful, False otherwise
        """
        client = self._get_client()
        
        try:
            container = client.containers.get(container_id)
            container.remove(force=force)
            logger.info(f"Removed container: {container_id[:12]}")
            return True
        except NotFound:
            logger.warning(f"Container already removed: {container_id[:12]}")
            return True  # Already gone, consider success
        except APIError as e:
            logger.error(f"Failed to remove container {container_id[:12]}: {e}")
            return False
    
    def get_container_state(self, container_id: str) -> Optional[str]:
        """
        Get container state
        
        Args:
            container_id: Container ID
        
        Returns:
            Container state string ('running', 'exited', 'paused', 'dead', etc.) or None if not found
        """
        client = self._get_client()
        
        try:
            container = client.containers.get(container_id)
            state = container.status  # 'running', 'exited', 'paused', 'restarting', 'dead', 'created'
            logger.debug(f"Container {container_id[:12]} state: {state}")
            return state
        except NotFound:
            logger.debug(f"Container not found: {container_id[:12]}")
            return None
        except APIError as e:
            logger.error(f"Failed to get state for container {container_id[:12]}: {e}")
            return None
    
    def remove_container(self, container_id: str, force: bool = True) -> bool:
        """
        Remove a container
        
        Args:
            container_id: Docker container ID
            force: Force removal even if running
        
        Returns:
            True if successful, False otherwise
        """
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            logger.info(f"Removed container: {container_id[:12]}")
            return True
        except APIError as e:
            logger.error(f"Failed to remove container {container_id}: {e}")
            return False
    
    def get_container_status(self, container_id: str) -> Optional[Dict]:
        """
        Get container status and details
        
        Args:
            container_id: Docker container ID
        
        Returns:
            Dictionary with status info or None if not found
        """
        try:
            container = self.client.containers.get(container_id)
            container.reload()  # Refresh container data
            
            # Get network info
            networks = container.attrs.get('NetworkSettings', {}).get('Networks', {})
            compute_network = networks.get(self.network_name, {})
            
            return {
                'id': container.id,
                'name': container.name,
                'status': container.status,  # created, running, paused, restarting, removing, exited, dead
                'state': container.attrs['State'],
                'ip_address': compute_network.get('IPAddress'),
                'created': container.attrs.get('Created'),
            }
        except docker.errors.NotFound:
            logger.warning(f"Container not found: {container_id}")
            return None
        except APIError as e:
            logger.error(f"Failed to get container status {container_id}: {e}")
            return None
    
    def list_managed_containers(self) -> List[Dict]:
        """
        List all containers managed by GCS emulator
        
        Returns:
            List of container info dictionaries
        """
        try:
            containers = self.client.containers.list(
                all=True,
                filters={'label': 'gcs-compute=true'}
            )
            return [
                {
                    'id': c.id,
                    'name': c.name,
                    'status': c.status,
                    'image': c.image.tags[0] if c.image.tags else c.image.id
                }
                for c in containers
            ]
        except APIError as e:
            logger.error(f"Failed to list containers: {e}")
            return []
    
    def cleanup_orphaned_containers(self) -> int:
        """
        Remove containers that are no longer tracked in database
        
        Returns:
            Number of containers cleaned up
        """
        try:
            containers = self.client.containers.list(
                all=True,
                filters={
                    'label': 'gcs-compute=true',
                    'status': 'exited'
                }
            )
            count = 0
            for container in containers:
                try:
                    container.remove()
                    count += 1
                    logger.info(f"Cleaned up orphaned container: {container.name}")
                except APIError:
                    pass
            return count
        except APIError as e:
            logger.error(f"Failed to cleanup orphaned containers: {e}")
            return 0
    
    def list_images(self) -> List[Dict[str, str]]:
        """
        List available Docker images
        
        Returns:
            List of dicts with image info (name, tags, size)
        """
        client = self._get_client()
        
        try:
            images = []
            for image in client.images.list():
                # Skip images without tags
                if not image.tags:
                    continue
                
                for tag in image.tags:
                    images.append({
                        'name': tag,
                        'id': image.short_id.replace('sha256:', ''),
                        'size': self._format_size(image.attrs.get('Size', 0))
                    })
            
            logger.info(f"Found {len(images)} Docker images")
            return images
        except APIError as e:
            logger.error(f"Failed to list images: {e}")
            return []
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
