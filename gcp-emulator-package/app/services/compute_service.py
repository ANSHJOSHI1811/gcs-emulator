"""
Compute Engine service - Business logic for instance lifecycle
Phase 3: Added Docker-backed execution with COMPUTE_DOCKER_ENABLED feature flag
Phase 5: Added networking (IP allocation, firewall rules)
"""
import uuid
import time
import os
from datetime import datetime, timezone
from typing import List, Optional
from flask import current_app
from app.factory import db
from app.models.compute import Instance, InstanceStatus, MachineType
from app.models.project import Project
from app.repositories.compute_repository import ComputeRepository
from app.compute.docker_runner import DockerRunner, DockerError
from app.services.networking_service import NetworkingService
from app.logging import log_service_stage


# Custom exceptions
class InvalidStateError(Exception):
    """Raised when an operation is attempted on an instance in invalid state"""
    pass


class InstanceNotFoundError(Exception):
    """Raised when an instance is not found"""
    pass


class InstanceAlreadyExistsError(Exception):
    """Raised when trying to create an instance that already exists"""
    pass


class DockerExecutionError(Exception):
    """Raised when Docker operations fail"""
    pass


class ComputeService:
    """Service for Compute Engine instance operations with proper lifecycle"""
    
    @staticmethod
    def _is_docker_enabled() -> bool:
        """Check if Docker integration is enabled via feature flag"""
        try:
            return current_app.config.get("COMPUTE_DOCKER_ENABLED", False)
        except RuntimeError:
            # Outside app context (e.g., in tests without app)
            return os.getenv("COMPUTE_DOCKER_ENABLED", "false").lower() == "true"
    
    @staticmethod
    def _get_docker_runner() -> Optional[DockerRunner]:
        """Get DockerRunner instance if Docker is enabled"""
        if ComputeService._is_docker_enabled():
            return DockerRunner()
        return None
    
    @staticmethod
    def create_instance(
        project_id: str,
        zone: str,
        name: str,
        machine_type: str,
        metadata: dict = None,
        labels: dict = None,
        tags: list = None,
        network_interfaces: list = None,
        disks: list = None
    ) -> Instance:
        """
        Create a new compute instance
        Phase 2: Creates instance with proper state transitions: PROVISIONING → STAGING → RUNNING
        
        Args:
            project_id: GCP project ID
            zone: Zone name (e.g., "us-central1-a")
            name: Instance name
            machine_type: Machine type (e.g., "e2-medium")
            metadata: Instance metadata dict
            labels: Instance labels dict
            tags: Network tags list
            network_interfaces: Network interface configs
            disks: Disk configs
            
        Returns:
            Created Instance object in RUNNING state
            
        Raises:
            ValueError: If validation fails
            InstanceAlreadyExistsError: If instance already exists
        """
        start_time = time.time()
        
        log_service_stage(
            message="Creating compute instance",
            details={
                "project_id": project_id,
                "zone": zone,
                "name": name,
                "machine_type": machine_type
            }
        )
        
        # Validate project exists
        project = Project.query.filter_by(id=project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Validate machine type
        if not MachineType.is_valid(machine_type):
            available = ", ".join(list(MachineType.get_all().keys())[:5])
            raise ValueError(
                f"Invalid machine type: {machine_type}. "
                f"Available types include: {available}, ..."
            )
        
        # Check for duplicate instance in same zone
        if ComputeRepository.instance_exists(project_id, zone, name):
            raise InstanceAlreadyExistsError(
                f"Instance '{name}' already exists in zone '{zone}'"
            )
        
        # Create instance with PROVISIONING status
        instance = Instance(
            id=str(uuid.uuid4()),
            name=name,
            project_id=project_id,
            zone=zone,
            machine_type=machine_type,
            status=InstanceStatus.PROVISIONING,
            status_message="Instance is being provisioned",
            instance_metadata=metadata or {},
            labels=labels or {},
            tags=tags or [],
            network_interfaces=network_interfaces or [],
            disks=disks or [],
            creation_timestamp=datetime.now(timezone.utc)
        )
        
        # Save to database
        instance = ComputeRepository.create_instance(instance)
        
        # Phase 5: Configure networking (allocate internal IP, optionally external IP)
        NetworkingService.configure_instance_networking(instance, allocate_external=True)
        
        # Phase 3: Docker integration
        docker_runner = ComputeService._get_docker_runner()
        container_id = None
        
        if docker_runner:
            try:
                # Get Docker image for machine type
                image = DockerRunner.get_image_for_machine_type(machine_type)
                
                # Build container name (unique per instance)
                container_name = f"gce-{project_id}-{zone}-{name}".replace("_", "-")
                
                # Prepare environment variables from metadata
                env = {}
                if metadata:
                    for key, value in metadata.items():
                        # Prefix metadata keys to avoid conflicts
                        env[f"GCE_METADATA_{key.upper()}"] = str(value)
                
                # Add instance info to env
                env["GCE_INSTANCE_NAME"] = name
                env["GCE_ZONE"] = zone
                env["GCE_PROJECT"] = project_id
                env["GCE_MACHINE_TYPE"] = machine_type
                
                log_service_stage(
                    message="Creating Docker container for instance",
                    details={
                        "instance_id": instance.id,
                        "image": image,
                        "container_name": container_name
                    }
                )
                
                # Create and start container
                container_id = docker_runner.create_container(
                    image=image,
                    name=container_name,
                    env=env
                )
                
                docker_runner.start_container(container_id)
                
                # Update instance with container ID
                instance.container_id = container_id
                db.session.commit()
                
                log_service_stage(
                    message="Docker container created and started",
                    details={
                        "instance_id": instance.id,
                        "container_id": container_id
                    }
                )
                
            except DockerError as e:
                log_service_stage(
                    message="Docker operation failed during instance creation",
                    details={"instance_id": instance.id, "error": str(e)},
                    level="ERROR"
                )
                # Clean up: delete instance from DB since Docker failed
                ComputeRepository.delete_instance(instance)
                raise DockerExecutionError(f"Failed to create Docker container: {str(e)}")
        
        # Simulate async state transitions: PROVISIONING → STAGING → RUNNING
        instance = ComputeRepository.update_instance_status(
            instance,
            InstanceStatus.STAGING,
            "Instance is being staged"
        )
        
        instance = ComputeRepository.update_instance_status(
            instance,
            InstanceStatus.RUNNING,
            "Instance is running"
        )
        
        # Set start timestamp
        instance = ComputeRepository.update_start_timestamp(instance)
        
        log_service_stage(
            message="Instance created and transitioned to RUNNING",
            details={
                "instance_id": instance.id,
                "instance_name": instance.name,
                "status": instance.status,
                "duration_ms": (time.time() - start_time) * 1000
            }
        )
        
        return instance
    
    @staticmethod
    def list_instances(project_id: str, zone: Optional[str] = None) -> List[Instance]:
        """
        List instances in a project, optionally filtered by zone
        
        Args:
            project_id: Project ID
            zone: Optional zone filter (None = all zones)
            
        Returns:
            List of Instance objects
        """
        start_time = time.time()
        
        log_service_stage(
            message="Listing instances",
            details={"project_id": project_id, "zone": zone or "all"}
        )
        
        instances = ComputeRepository.list_instances(project_id, zone)
        
        log_service_stage(
            message="Instances listed",
            details={
                "count": len(instances),
                "duration_ms": (time.time() - start_time) * 1000
            }
        )
        
        return instances
    
    @staticmethod
    def get_instance(project_id: str, zone: str, name: str) -> Instance:
        """
        Get a specific instance
        
        Args:
            project_id: Project ID
            zone: Zone name
            name: Instance name
            
        Returns:
            Instance object
            
        Raises:
            InstanceNotFoundError: If instance not found
        """
        log_service_stage(
            message="Getting instance",
            details={"project_id": project_id, "zone": zone, "name": name}
        )
        
        instance = ComputeRepository.get_instance(project_id, zone, name)
        
        if not instance:
            raise InstanceNotFoundError(
                f"Instance '{name}' not found in zone '{zone}'"
            )
        
        return instance
    
    @staticmethod
    def start_instance(project_id: str, zone: str, name: str) -> Instance:
        """
        Start a terminated instance
        Transition: TERMINATED → STAGING → RUNNING
        
        Args:
            project_id: Project ID
            zone: Zone name
            name: Instance name
            
        Returns:
            Instance in RUNNING state
            
        Raises:
            InstanceNotFoundError: If instance not found
            InvalidStateError: If instance is not in TERMINATED state
        """
        start_time = time.time()
        
        log_service_stage(
            message="Starting instance",
            details={"project_id": project_id, "zone": zone, "name": name}
        )
        
        instance = ComputeService.get_instance(project_id, zone, name)
        
        # Validate state
        if instance.status != InstanceStatus.TERMINATED:
            raise InvalidStateError(
                f"Cannot start instance in '{instance.status}' state. "
                f"Instance must be in TERMINATED state."
            )
        
        # Phase 5: Attach external IP if not already allocated
        NetworkingService.attach_external_ip_on_start(instance)
        
        # Phase 3: Docker integration
        docker_runner = ComputeService._get_docker_runner()
        
        if docker_runner and instance.container_id:
            try:
                log_service_stage(
                    message="Starting Docker container",
                    details={
                        "instance_id": instance.id,
                        "container_id": instance.container_id
                    }
                )
                
                # Start existing container
                docker_runner.start_container(instance.container_id)
                
            except DockerError as e:
                log_service_stage(
                    message="Failed to start Docker container",
                    details={
                        "instance_id": instance.id,
                        "container_id": instance.container_id,
                        "error": str(e)
                    },
                    level="ERROR"
                )
                raise DockerExecutionError(f"Failed to start Docker container: {str(e)}")
        
        # Transition: TERMINATED → STAGING
        instance = ComputeRepository.update_instance_status(
            instance,
            InstanceStatus.STAGING,
            "Instance is being staged for start"
        )
        
        # Transition: STAGING → RUNNING
        instance = ComputeRepository.update_instance_status(
            instance,
            InstanceStatus.RUNNING,
            "Instance is running"
        )
        
        # Update start timestamp
        instance = ComputeRepository.update_start_timestamp(instance)
        
        log_service_stage(
            message="Instance started successfully",
            details={
                "instance_id": instance.id,
                "status": instance.status,
                "duration_ms": (time.time() - start_time) * 1000
            }
        )
        
        return instance
    
    @staticmethod
    def stop_instance(project_id: str, zone: str, name: str) -> Instance:
        """
        Stop a running instance
        Transition: RUNNING → STOPPING → TERMINATED
        
        Args:
            project_id: Project ID
            zone: Zone name
            name: Instance name
            
        Returns:
            Instance in TERMINATED state
            
        Raises:
            InstanceNotFoundError: If instance not found
            InvalidStateError: If instance is not in RUNNING state
        """
        start_time = time.time()
        
        log_service_stage(
            message="Stopping instance",
            details={"project_id": project_id, "zone": zone, "name": name}
        )
        
        instance = ComputeService.get_instance(project_id, zone, name)
        
        # Validate state
        if instance.status != InstanceStatus.RUNNING:
            raise InvalidStateError(
                f"Cannot stop instance in '{instance.status}' state. "
                f"Instance must be in RUNNING state."
            )
        
        # Phase 3: Docker integration
        docker_runner = ComputeService._get_docker_runner()
        
        if docker_runner and instance.container_id:
            try:
                log_service_stage(
                    message="Stopping Docker container",
                    details={
                        "instance_id": instance.id,
                        "container_id": instance.container_id
                    }
                )
                
                # Stop container
                docker_runner.stop_container(instance.container_id)
                
            except DockerError as e:
                log_service_stage(
                    message="Failed to stop Docker container",
                    details={
                        "instance_id": instance.id,
                        "container_id": instance.container_id,
                        "error": str(e)
                    },
                    level="ERROR"
                )
                raise DockerExecutionError(f"Failed to stop Docker container: {str(e)}")
        
        # Transition: RUNNING → STOPPING
        instance = ComputeRepository.update_instance_status(
            instance,
            InstanceStatus.STOPPING,
            "Instance is stopping"
        )
        
        # Transition: STOPPING → TERMINATED
        instance = ComputeRepository.update_instance_status(
            instance,
            InstanceStatus.TERMINATED,
            "Instance has been terminated"
        )
        
        # Update stop timestamp
        instance = ComputeRepository.update_stop_timestamp(instance)
        
        log_service_stage(
            message="Instance stopped successfully",
            details={
                "instance_id": instance.id,
                "status": instance.status,
                "duration_ms": (time.time() - start_time) * 1000
            }
        )
        
        return instance
    
    @staticmethod
    def delete_instance(project_id: str, zone: str, name: str) -> Instance:
        """
        Delete an instance
        If RUNNING: Force transition RUNNING → STOPPING → TERMINATED, then remove
        If already TERMINATED: Just remove
        
        Args:
            project_id: Project ID
            zone: Zone name
            name: Instance name
            
        Returns:
            Instance object (before deletion)
            
        Raises:
            InstanceNotFoundError: If instance not found
        """
        start_time = time.time()
        
        log_service_stage(
            message="Deleting instance",
            details={"project_id": project_id, "zone": zone, "name": name}
        )
        
        instance = ComputeService.get_instance(project_id, zone, name)
        
        # Phase 3: Docker integration - stop and remove container
        docker_runner = ComputeService._get_docker_runner()
        
        if docker_runner and instance.container_id:
            try:
                log_service_stage(
                    message="Stopping and removing Docker container",
                    details={
                        "instance_id": instance.id,
                        "container_id": instance.container_id
                    }
                )
                
                # Stop container (if running)
                docker_runner.stop_container(instance.container_id)
                
                # Remove container
                docker_runner.remove_container(instance.container_id, force=True)
                
                log_service_stage(
                    message="Docker container stopped and removed",
                    details={
                        "instance_id": instance.id,
                        "container_id": instance.container_id
                    }
                )
                
            except DockerError as e:
                log_service_stage(
                    message="Docker operation failed during deletion (continuing anyway)",
                    details={
                        "instance_id": instance.id,
                        "container_id": instance.container_id,
                        "error": str(e)
                    },
                    level="WARNING"
                )
                # Continue with deletion even if Docker cleanup fails
        
        # If RUNNING, force stop first
        if instance.status == InstanceStatus.RUNNING:
            log_service_stage(
                message="Instance is RUNNING, forcing stop before delete",
                details={"instance_id": instance.id}
            )
            
            instance = ComputeRepository.update_instance_status(
                instance,
                InstanceStatus.STOPPING,
                "Stopping instance for deletion"
            )
            
            instance = ComputeRepository.update_instance_status(
                instance,
                InstanceStatus.TERMINATED,
                "Instance terminated for deletion"
            )
        
        # Store instance data for return (before deletion)
        instance_copy = instance
        
        # Delete from database
        ComputeRepository.delete_instance(instance)
        
        log_service_stage(
            message="Instance deleted successfully",
            details={
                "instance_id": instance_copy.id,
                "duration_ms": (time.time() - start_time) * 1000
            }
        )
        
        return instance_copy
    
    @staticmethod
    def get_instance_serial_port_output(
        project_id: str,
        zone: str,
        name: str,
        port: int = 1,
        start: int = 0
    ) -> str:
        """
        Get serial port output for an instance
        Phase 2: Returns placeholder (no Docker logs yet)
        
        Args:
            project_id: Project ID
            zone: Zone name
            name: Instance name
            port: Serial port number (default 1)
            start: Start byte position
            
        Returns:
            Serial port output string
            
        Raises:
            InstanceNotFoundError: If instance not found
        """
        instance = ComputeService.get_instance(project_id, zone, name)
        
        # Phase 2: Return placeholder
        return (
            f"Serial port {port} output for instance '{instance.name}'\n"
            f"Status: {instance.status}\n"
            f"Phase 2: No Docker container logs yet\n"
            f"Start position: {start}\n"
        )
