"""
Bucket service - Bucket business logic
"""
import uuid
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from app.factory import db
from app.models.bucket import Bucket


class BucketService:
    """Service for bucket operations"""
    
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
        if not project_id:
            raise ValueError("project_id is required")
        
        return Bucket.query.filter_by(project_id=project_id).all()
    
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
        if not project_id:
            raise ValueError("project_id is required")
        if not name:
            raise ValueError("Bucket name is required")
        
        # Check if bucket already exists
        existing = Bucket.query.filter_by(name=name).first()
        if existing:
            raise ValueError(f"Bucket name '{name}' already exists")
        
        # Generate unique ID
        bucket_id = f"{name}-{uuid.uuid4().hex[:8]}"
        
        bucket = Bucket(
            id=bucket_id,
            project_id=project_id,
            name=name,
            location=location,
            storage_class=storage_class,
            versioning_enabled=versioning_enabled,
            meta={}
        )
        
        try:
            db.session.add(bucket)
            db.session.commit()
            return bucket
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to create bucket: {str(e)}")
    
    @staticmethod
    def get_bucket(bucket_name: str):
        """
        Get bucket details by name
        
        Args:
            bucket_name: The bucket name
            
        Returns:
            Bucket object or None if not found
            
        Raises:
            ValueError: If bucket_name is invalid
        """
        if not bucket_name:
            raise ValueError("bucket_name is required")
        
        return Bucket.query.filter_by(name=bucket_name).first()
    
    @staticmethod
    def delete_bucket(bucket_name: str):
        """
        Delete a bucket
        
        Args:
            bucket_name: The bucket name
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If bucket doesn't exist or not empty
        """
        if not bucket_name:
            raise ValueError("bucket_name is required")
        
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        # Check if bucket has objects
        if bucket.objects:
            raise ValueError(f"Bucket '{bucket_name}' is not empty")
        
        db.session.delete(bucket)
        db.session.commit()
        return True
