"""
Compute Engine repository - Database operations for instances
Phase 2: Query helpers and state management
"""
import time
from typing import List, Optional
from datetime import datetime, timezone
from app.factory import db
from app.models.compute import Instance, InstanceStatus
from app.logging import log_repository_stage


class ComputeRepository:
    """Repository for Compute Engine instance database operations"""
    
    @staticmethod
    def create_instance(instance: Instance) -> Instance:
        """
        Save new instance to database
        
        Args:
            instance: Instance object to save
            
        Returns:
            Saved instance with generated ID
        """
        start_time = time.time()
        
        log_repository_stage(
            message="Creating instance in database",
            details={
                "instance_name": instance.name,
                "project_id": instance.project_id,
                "zone": instance.zone
            }
        )
        
        try:
            db.session.add(instance)
            db.session.commit()
            
            log_repository_stage(
                message="Instance created successfully",
                details={
                    "instance_id": instance.id,
                    "duration_ms": (time.time() - start_time) * 1000
                }
            )
            
            return instance
            
        except Exception as e:
            db.session.rollback()
            log_repository_stage(
                message="Failed to create instance",
                details={"error": str(e)},
                level="ERROR"
            )
            raise
    
    @staticmethod
    def get_instance(project_id: str, zone: str, name: str) -> Optional[Instance]:
        """
        Get instance by project, zone, and name
        
        Args:
            project_id: Project ID
            zone: Zone name
            name: Instance name
            
        Returns:
            Instance if found, None otherwise
        """
        log_repository_stage(
            message="Querying instance",
            details={"project_id": project_id, "zone": zone, "name": name}
        )
        
        return Instance.query.filter_by(
            project_id=project_id,
            zone=zone,
            name=name
        ).first()
    
    @staticmethod
    def get_instance_by_id(instance_id: str) -> Optional[Instance]:
        """
        Get instance by ID
        
        Args:
            instance_id: Instance UUID
            
        Returns:
            Instance if found, None otherwise
        """
        return Instance.query.filter_by(id=instance_id).first()
    
    @staticmethod
    def list_instances(project_id: str, zone: Optional[str] = None) -> List[Instance]:
        """
        List instances in a project, optionally filtered by zone
        
        Args:
            project_id: Project ID
            zone: Optional zone filter
            
        Returns:
            List of instances
        """
        log_repository_stage(
            message="Listing instances",
            details={"project_id": project_id, "zone": zone or "all"}
        )
        
        query = Instance.query.filter_by(project_id=project_id)
        
        if zone:
            query = query.filter_by(zone=zone)
        
        instances = query.order_by(Instance.creation_timestamp.desc()).all()
        
        log_repository_stage(
            message="Instances retrieved",
            details={"count": len(instances)}
        )
        
        return instances
    
    @staticmethod
    def update_instance_status(
        instance: Instance,
        status: str,
        status_message: str = ""
    ) -> Instance:
        """
        Update instance status and optionally status message
        
        Args:
            instance: Instance to update
            status: New status
            status_message: Optional status message
            
        Returns:
            Updated instance
        """
        start_time = time.time()
        
        log_repository_stage(
            message="Updating instance status",
            details={
                "instance_id": instance.id,
                "old_status": instance.status,
                "new_status": status
            }
        )
        
        try:
            instance.status = status
            if status_message:
                instance.status_message = status_message
            
            db.session.commit()
            
            log_repository_stage(
                message="Status updated successfully",
                details={
                    "instance_id": instance.id,
                    "status": status,
                    "duration_ms": (time.time() - start_time) * 1000
                }
            )
            
            return instance
            
        except Exception as e:
            db.session.rollback()
            log_repository_stage(
                message="Failed to update status",
                details={"error": str(e)},
                level="ERROR"
            )
            raise
    
    @staticmethod
    def update_start_timestamp(instance: Instance) -> Instance:
        """
        Update instance last start timestamp
        
        Args:
            instance: Instance to update
            
        Returns:
            Updated instance
        """
        instance.last_start_timestamp = datetime.now(timezone.utc)
        db.session.commit()
        return instance
    
    @staticmethod
    def update_stop_timestamp(instance: Instance) -> Instance:
        """
        Update instance last stop timestamp
        
        Args:
            instance: Instance to update
            
        Returns:
            Updated instance
        """
        instance.last_stop_timestamp = datetime.now(timezone.utc)
        db.session.commit()
        return instance
    
    @staticmethod
    def delete_instance(instance: Instance) -> None:
        """
        Delete instance from database
        
        Args:
            instance: Instance to delete
        """
        start_time = time.time()
        
        log_repository_stage(
            message="Deleting instance",
            details={
                "instance_id": instance.id,
                "instance_name": instance.name
            }
        )
        
        try:
            db.session.delete(instance)
            db.session.commit()
            
            log_repository_stage(
                message="Instance deleted successfully",
                details={
                    "instance_id": instance.id,
                    "duration_ms": (time.time() - start_time) * 1000
                }
            )
            
        except Exception as e:
            db.session.rollback()
            log_repository_stage(
                message="Failed to delete instance",
                details={"error": str(e)},
                level="ERROR"
            )
            raise
    
    @staticmethod
    def instance_exists(project_id: str, zone: str, name: str) -> bool:
        """
        Check if instance exists
        
        Args:
            project_id: Project ID
            zone: Zone name
            name: Instance name
            
        Returns:
            True if exists, False otherwise
        """
        return ComputeRepository.get_instance(project_id, zone, name) is not None
