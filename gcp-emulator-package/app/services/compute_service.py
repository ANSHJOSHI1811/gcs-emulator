"""
PHASE 1: Compute Service
Manages VM instances using Docker containers (basic lifecycle only)
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.exc import IntegrityError

from app.factory import db
from app.models.instance import Instance
from app.services.docker_driver import DockerDriver

logger = logging.getLogger(__name__)


class ComputeService:
    """
    PHASE 1: Basic compute service for instance lifecycle
    
    State machine enforced:
    - pending → running
    - running → stopping → stopped
    - any → terminated
    """
    
    def __init__(self):
        """Initialize Compute Service with Docker driver"""
        self.docker_driver = DockerDriver()
        logger.info("ComputeService initialized (PHASE 1)")
    
    def run_instance(
        self,
        name: str,
        image: str,
        cpu: int = 1,
        memory: int = 512
    ) -> Optional[Instance]:
        """
        Create and launch a new instance
        
        Args:
            name: Instance name
            image: Docker image (e.g., 'alpine:latest')
            cpu: Number of CPU cores
            memory: Memory in MB
        
        Returns:
            Instance object or None if failed
        """
        try:
            # Generate unique instance ID
            instance_id = str(uuid.uuid4())
            container_name = f"gcs-compute-{instance_id[:8]}"
            
            logger.info(f"Creating instance: {name} (image={image}, cpu={cpu}, memory={memory})")
            
            # Create instance record in DB (state: pending)
            instance = Instance(
                id=instance_id,
                name=name,
                image=image,
                cpu=cpu,
                memory_mb=memory,
                state='pending'
            )
            
            db.session.add(instance)
            db.session.commit()
            
            # Create Docker container
            container_id = self.docker_driver.create_container(
                image=image,
                name=container_name,
                cpu=cpu,
                memory=memory
            )
            
            if not container_id:
                logger.error(f"Failed to create Docker container for instance {instance_id}")
                instance.state = 'terminated'
                db.session.commit()
                return None
            
            # Update instance with container info and state
            instance.container_id = container_id
            instance.state = 'running'  # Container starts immediately
            db.session.commit()
            
            logger.info(f"Instance {instance_id} created successfully (container: {container_id[:12]})")
            return instance
        
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Database integrity error: {e}")
            return None
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create instance: {e}", exc_info=True)
            return None
    
    def stop_instance(self, instance_id: str) -> bool:
        """
        Stop a running instance
        
        Args:
            instance_id: Instance ID
        
        Returns:
            True if successful, False otherwise
        """
        instance = Instance.query.filter_by(id=instance_id).first()
        if not instance:
            logger.warning(f"Instance not found: {instance_id}")
            return False
        
        if instance.state == 'stopped':
            logger.info(f"Instance {instance_id} already stopped")
            return True
        
        if instance.state != 'running':
            logger.warning(f"Cannot stop instance {instance_id} in state: {instance.state}")
            return False
        
        if not instance.container_id:
            logger.error(f"Instance {instance_id} has no container ID")
            return False
        
        # Update state to stopping
        instance.state = 'stopping'
        db.session.commit()
        
        # Stop Docker container
        if self.docker_driver.stop_container(instance.container_id):
            instance.state = 'stopped'
            db.session.commit()
            logger.info(f"Stopped instance {instance_id}")
            return True
        else:
            # Rollback state if Docker operation failed
            instance.state = 'running'
            db.session.commit()
            return False
    
    def terminate_instance(self, instance_id: str) -> bool:
        """
        Terminate an instance (stop and remove container)
        
        Args:
            instance_id: Instance ID
        
        Returns:
            True if successful, False otherwise
        """
        instance = Instance.query.filter_by(id=instance_id).first()
        if not instance:
            logger.warning(f"Instance not found: {instance_id}")
            return False
        
        if instance.state == 'terminated':
            logger.info(f"Instance {instance_id} already terminated")
            return True
        
        # Stop container if running
        if instance.state == 'running' and instance.container_id:
            self.docker_driver.stop_container(instance.container_id)
        
        # Remove Docker container
        if instance.container_id:
            self.docker_driver.remove_container(instance.container_id, force=True)
        
        # Update instance state
        instance.state = 'terminated'
        db.session.commit()
        
        logger.info(f"Terminated instance {instance_id}")
        return True
    
    def describe_instances(
        self,
        project_id: Optional[str] = None,
        instance_ids: Optional[List[str]] = None,
        states: Optional[List[str]] = None
    ) -> List[Instance]:
        """
        List instances with optional filters
        
        Args:
            project_id: Filter by project (not used in PHASE 1)
            instance_ids: Filter by specific instance IDs
            states: Filter by states (e.g., ['running', 'stopped'])
        
        Returns:
            List of Instance objects
        """
        query = Instance.query
        
        if instance_ids:
            query = query.filter(Instance.id.in_(instance_ids))
        
        if states:
            query = query.filter(Instance.state.in_(states))
        
        return query.order_by(Instance.created_at.desc()).all()
    
    def get_instance(self, instance_id: str) -> Optional[Instance]:
        """
        Get single instance by ID
        
        Args:
            instance_id: Instance ID
        
        Returns:
            Instance object or None
        """
        return Instance.query.filter_by(id=instance_id).first()
    
    def sync_instance_state(self, instance: Instance) -> bool:
        """
        Synchronize instance state with Docker container state
        
        Args:
            instance: Instance object
        
        Returns:
            True if state was updated, False otherwise
        """
        if not instance.container_id:
            return False
        
        # Get Docker container state
        docker_state = self.docker_driver.get_container_state(instance.container_id)
        
        if not docker_state:
            # Container not found - mark as terminated
            if instance.state != 'terminated':
                logger.warning(f"Container not found for instance {instance.id}, marking as terminated")
                instance.state = 'terminated'
                db.session.commit()
                return True
            return False
        
        # Map Docker state to instance state
        current_state = instance.state
        new_state = None
        
        if docker_state == 'running':
            if current_state not in ['running', 'pending']:
                new_state = 'running'
        elif docker_state in ['exited', 'dead']:
            if current_state not in ['stopped', 'terminated']:
                new_state = 'stopped'
        elif docker_state == 'paused':
            if current_state != 'stopped':
                new_state = 'stopped'
        
        if new_state and new_state != current_state:
            logger.info(f"Syncing instance {instance.id} state: {current_state} -> {new_state}")
            instance.state = new_state
            db.session.commit()
            return True
        
        return False
