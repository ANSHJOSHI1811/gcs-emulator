"""
Bucket service - Bucket business logic
"""
import uuid
import time
from app.factory import db
from app.models.bucket import Bucket
from app.models.project import Project
from app.logging import log_service_stage, log_repository_stage


class BucketService:
    """Service for bucket operations"""
    
    @staticmethod
    def update_bucket(bucket_name: str, versioning_enabled: bool = None):
        """
        Update bucket metadata
        
        Args:
            bucket_name: The bucket name
            versioning_enabled: Whether to enable versioning (None = no change)
            
        Returns:
            Updated Bucket object
            
        Raises:
            ValueError: If bucket not found
        """
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        # Update versioning if specified
        if versioning_enabled is not None:
            bucket.versioning_enabled = versioning_enabled
            log_service_stage(
                message="Updating bucket versioning",
                details={
                    "bucket_name": bucket_name,
                    "versioning_enabled": versioning_enabled
                }
            )
        
        db.session.commit()
        
        log_service_stage(
            message="Bucket updated successfully",
            details={
                "bucket_id": bucket.id,
                "bucket_name": bucket_name
            }
        )
        
        return bucket
    
    @staticmethod
    def list_buckets(project_id: str):
        """
        List buckets for a project
        
        Args:
            project_id: The project ID
            
        Returns:
            List of Bucket objects
            
        Raises:
            ValueError: If project_id is invalid
        """
        BucketService._validate_project_id(project_id)
        
        log_repository_stage(
            message="Database query executing",
            details={
                "operation": "SELECT",
                "table": "buckets",
                "filter": f"project_id={project_id}"
            }
        )
        
        buckets = Bucket.query.filter_by(project_id=project_id).all()
        
        log_repository_stage(
            message="Database query completed",
            details={
                "operation": "SELECT",
                "table": "buckets",
                "records_returned": len(buckets)
            }
        )
        
        return buckets
    
    @staticmethod
    def create_bucket(project_id: str, name: str, location: str = "US", 
                     storage_class: str = "STANDARD", versioning_enabled: bool = False):
        """
        Create a new bucket
        
        Args:
            project_id: The project ID
            name: Bucket name (must be globally unique)
            location: Bucket location (default: US)
            storage_class: Storage class (default: STANDARD)
            versioning_enabled: Enable versioning (default: False)
            
        Returns:
            Created Bucket object
            
        Raises:
            ValueError: If input is invalid or bucket already exists
        """
        start_time = time.time()
        
        log_service_stage(
            message="Service create_bucket executing business logic",
            details={
                "service": "BucketService",
                "method": "create_bucket",
                "project_id": project_id,
                "bucket_name": name,
                "location": location,
                "storage_class": storage_class
            }
        )
        
        # Validate inputs
        BucketService._validate_project_id(project_id)
        BucketService._ensure_project_exists(project_id)
        BucketService._validate_bucket_name(name)
        
        # Ensure bucket name is unique within the project
        BucketService._check_bucket_uniqueness(project_id, name)
        
        log_service_stage(
            message="Business validations passed - creating bucket",
            details={
                "business_rules": ["project_validation", "name_validation", "uniqueness_check"]
            }
        )
        
        # Create bucket instance with generated unique ID
        bucket = BucketService._build_bucket_instance(
            project_id, name, location, storage_class, versioning_enabled
        )
        
        # Persist to database
        BucketService._save_bucket(bucket)
        
        duration_ms = (time.time() - start_time) * 1000
        log_service_stage(
            message="Service create_bucket completed successfully",
            duration_ms=duration_ms,
            details={
                "generated_id": bucket.id,
                "bucket_name": bucket.name,
                "project_id": bucket.project_id
            }
        )
        
        return bucket
    
    @staticmethod
    def get_bucket(bucket_name: str, project_id: str = None):
        """
        Get bucket details by name
        
        Args:
            bucket_name: The bucket name
            project_id: Optional project ID for scoped lookup
            
        Returns:
            Bucket object or None if not found
            
        Raises:
            ValueError: If bucket_name is invalid
        """
        BucketService._validate_bucket_name(bucket_name)
        
        log_repository_stage(
            message="Database query executing",
            details={
                "operation": "SELECT",
                "table": "buckets",
                "filter": f"name={bucket_name}, project_id={project_id}" if project_id else f"name={bucket_name}"
            }
        )
        
        if project_id:
            bucket = Bucket.query.filter_by(project_id=project_id, name=bucket_name).first()
        else:
            # Backwards compatibility: find any bucket with this name
            bucket = Bucket.query.filter_by(name=bucket_name).first()
        
        log_repository_stage(
            message="Database query completed",
            details={
                "operation": "SELECT",
                "table": "buckets",
                "records_found": 1 if bucket else 0,
                "bucket_exists": bucket is not None
            }
        )
        
        return bucket
    
    @staticmethod
    def delete_bucket(bucket_name: str):
        """
        Delete a bucket (hard delete - removes all objects and versions)
        Uses ObjectVersioningService for consistent deletion logic.
        
        Args:
            bucket_name: The bucket name
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If bucket doesn't exist or not empty
        """
        import os
        import shutil
        from pathlib import Path
        from app.models.object import Object, ObjectVersion
        from app.services.object_versioning_service import ObjectVersioningService
        
        BucketService._validate_bucket_name(bucket_name)
        
        bucket = BucketService._find_bucket_or_raise(bucket_name)
        
        # GCS requires buckets to be empty before deletion
        BucketService._ensure_bucket_is_empty(bucket)
        
        log_repository_stage(
            message="Database delete operation executing",
            details={
                "operation": "DELETE",
                "table": "buckets",
                "bucket_id": bucket.id,
                "bucket_name": bucket.name
            }
        )
        
        try:
            # Get all objects in bucket
            objects = Object.query.filter_by(bucket_id=bucket.id).all()
            
            # Use ObjectVersioningService for consistent deletion
            # This ensures physical files are deleted in proper order
            for obj in objects:
                ObjectVersioningService._delete_all_versions(obj)
            
            # Delete the bucket row from DB
            db.session.delete(bucket)
            db.session.commit()
            
            # Delete physical storage directory AFTER successful DB commit
            storage_path = os.getenv("STORAGE_PATH", "./storage")
            bucket_dir = Path(storage_path) / bucket.id
            if bucket_dir.exists():
                shutil.rmtree(bucket_dir)
            
            log_repository_stage(
                message="Database delete operation completed",
                details={
                    "operation": "DELETE",
                    "table": "buckets",
                    "records_affected": 1,
                    "bucket_id": bucket.id
                }
            )
            
            return True
        except Exception as db_error:
            db.session.rollback()
            
            log_repository_stage(
                message="Database delete operation failed",
                details={
                    "operation": "DELETE",
                    "table": "buckets",
                    "error": str(db_error),
                    "rollback_performed": True
                }
            )
            
            raise ValueError(f"Failed to delete bucket: {str(db_error)}")
    
    # ========== Private Helper Methods ==========
    
    @staticmethod
    def _validate_project_id(project_id: str) -> None:
        """Validate that project_id is not empty"""
        if not project_id:
            raise ValueError("project_id is required")
    
    @staticmethod
    def _validate_bucket_name(bucket_name: str) -> None:
        """Validate that bucket_name is not empty"""
        if not bucket_name:
            raise ValueError("Bucket name is required")
    
    @staticmethod
    def _check_bucket_uniqueness(project_id: str, bucket_name: str) -> None:
        """Ensure bucket name is globally unique (GCS specification)"""
        existing_bucket = Bucket.query.filter_by(
            name=bucket_name
        ).first()
        if existing_bucket:
            raise ValueError(f"Bucket name '{bucket_name}' already exists")

    @staticmethod
    def _ensure_project_exists(project_id: str) -> None:
        """Create project row on demand to satisfy FK constraints"""
        project = Project.query.filter_by(id=project_id).first()
        if project:
            return

        project = Project(
            id=project_id,
            name=project_id,
            meta={}
        )

        db.session.add(project)
        # Flush so FK-dependent inserts in the same transaction succeed
        db.session.flush()
    
    @staticmethod
    def _generate_bucket_id(bucket_name: str) -> str:
        """Generate unique bucket ID by appending random suffix to name"""
        random_suffix = uuid.uuid4().hex[:8]
        return f"{bucket_name}-{random_suffix}"
    
    @staticmethod
    def _build_bucket_instance(
        project_id: str, 
        bucket_name: str, 
        location: str, 
        storage_class: str, 
        versioning_enabled: bool
    ) -> Bucket:
        """Create Bucket model instance with all required attributes"""
        bucket_id = BucketService._generate_bucket_id(bucket_name)
        
        return Bucket(
            id=bucket_id,
            project_id=project_id,
            name=bucket_name,
            location=location,
            storage_class=storage_class,
            versioning_enabled=versioning_enabled,
            meta={}
        )
    
    @staticmethod
    def _save_bucket(bucket: Bucket) -> None:
        """Persist bucket to database with error handling"""
        log_repository_stage(
            message="Database operation starting",
            details={
                "operation": "INSERT",
                "table": "buckets",
                "bucket_id": bucket.id,
                "bucket_name": bucket.name
            }
        )
        
        try:
            db.session.add(bucket)
            db.session.commit()
            
            log_repository_stage(
                message="Database operation completed successfully",
                details={
                    "operation": "INSERT",
                    "table": "buckets",
                    "records_affected": 1,
                    "bucket_id": bucket.id
                }
            )
        except Exception as db_error:
            db.session.rollback()
            
            log_repository_stage(
                message="Database operation failed",
                details={
                    "operation": "INSERT",
                    "table": "buckets",
                    "error": str(db_error),
                    "rollback_performed": True
                }
            )
            
            raise ValueError(f"Failed to create bucket: {str(db_error)}")
    
    @staticmethod
    def _find_bucket_or_raise(bucket_name: str) -> Bucket:
        """Find bucket by name or raise ValueError if not found"""
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        return bucket
    
    @staticmethod
    def _ensure_bucket_is_empty(bucket: Bucket) -> None:
        """Verify bucket has no non-deleted objects before allowing deletion"""
        from app.models.object import Object
        # Only check for non-deleted objects
        active_objects = Object.query.filter_by(
            bucket_id=bucket.id,
            deleted=False
        ).first()
        
        if active_objects:
            raise ValueError(f"Bucket '{bucket.name}' is not empty")
