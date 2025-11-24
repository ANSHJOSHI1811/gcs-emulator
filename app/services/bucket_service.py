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
        BucketService._validate_project_id(project_id)
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
        # Validate inputs
        BucketService._validate_project_id(project_id)
        BucketService._validate_bucket_name(name)
        
        # Ensure bucket name is unique across all projects
        BucketService._check_bucket_uniqueness(name)
        
        # Create bucket instance with generated unique ID
        bucket = BucketService._build_bucket_instance(
            project_id, name, location, storage_class, versioning_enabled
        )
        
        # Persist to database
        BucketService._save_bucket(bucket)
        return bucket
    
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
        BucketService._validate_bucket_name(bucket_name)
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
        BucketService._validate_bucket_name(bucket_name)
        
        bucket = BucketService._find_bucket_or_raise(bucket_name)
        
        # GCS requires buckets to be empty before deletion
        BucketService._ensure_bucket_is_empty(bucket)
        
        db.session.delete(bucket)
        db.session.commit()
        return True
    
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
    def _check_bucket_uniqueness(bucket_name: str) -> None:
        """Ensure bucket name doesn't already exist in database"""
        existing_bucket = Bucket.query.filter_by(name=bucket_name).first()
        if existing_bucket:
            raise ValueError(f"Bucket name '{bucket_name}' already exists")
    
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
        try:
            db.session.add(bucket)
            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
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
        """Verify bucket has no objects before allowing deletion"""
        if bucket.objects:
            raise ValueError(f"Bucket '{bucket.name}' is not empty")
