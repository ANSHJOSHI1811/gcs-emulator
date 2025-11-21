"""
Object service - Object business logic
"""
import os
import uuid
from pathlib import Path
from app.factory import db
from app.models.object import Object
from app.models.bucket import Bucket
from app.utils.hashing import calculate_md5, calculate_crc32c


class ObjectService:
    """Service for object operations"""
    
    STORAGE_PATH = os.getenv("STORAGE_PATH", "./storage")
    
    @staticmethod
    def list_objects(bucket_name: str, prefix: str = None, delimiter: str = None):
        """
        List objects in a bucket
        
        Args:
            bucket_name: The bucket name
            prefix: Filter objects by prefix
            delimiter: Path delimiter for grouping
            
        Returns:
            Dictionary with items list and prefixes
            
        Raises:
            ValueError: If bucket doesn't exist
        """
        if not bucket_name:
            raise ValueError("bucket_name is required")
        
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        query = Object.query.filter_by(bucket_id=bucket.id)
        
        if prefix:
            query = query.filter(Object.name.startswith(prefix))
        
        objects = query.all()
        
        prefixes = []
        items = []
        
        if delimiter:
            # Group by prefix
            prefixes_set = set()
            for obj in objects:
                if delimiter in obj.name[len(prefix or ""):]:
                    next_delimiter = obj.name.find(delimiter, len(prefix or ""))
                    prefix_part = obj.name[:next_delimiter + len(delimiter)]
                    prefixes_set.add(prefix_part)
                else:
                    items.append(obj)
            prefixes = sorted(list(prefixes_set))
        else:
            items = objects
        
        return {
            "items": items,
            "prefixes": prefixes
        }
    
    @staticmethod
    def upload_object(bucket_name: str, object_name: str, content: bytes, 
                     content_type: str = "application/octet-stream"):
        """
        Upload an object
        
        Args:
            bucket_name: The bucket name
            object_name: The object name
            content: Binary file content
            content_type: Content type (default: application/octet-stream)
            
        Returns:
            Created Object object
            
        Raises:
            ValueError: If bucket or input is invalid
        """
        if not bucket_name:
            raise ValueError("bucket_name is required")
        if not object_name:
            raise ValueError("object_name is required")
        if not isinstance(content, bytes):
            raise ValueError("content must be bytes")
        
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        # Calculate hashes
        md5_hash = calculate_md5(content)
        crc32c_hash = calculate_crc32c(content)
        
        # Store file on disk
        storage_dir = Path(ObjectService.STORAGE_PATH) / bucket.id
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        file_id = uuid.uuid4().hex
        file_path = storage_dir / file_id
        file_path.write_bytes(content)
        
        # Create object record
        object_id = f"{bucket.id}/{object_name}/{uuid.uuid4().hex[:8]}"
        obj = Object(
            id=object_id,
            bucket_id=bucket.id,
            name=object_name,
            size=len(content),
            content_type=content_type,
            md5_hash=md5_hash,
            crc32c_hash=crc32c_hash,
            file_path=str(file_path),
            metageneration=1,
            meta={}
        )
        
        db.session.add(obj)
        db.session.commit()
        return obj
    
    @staticmethod
    def get_object(bucket_name: str, object_name: str):
        """
        Get object metadata
        
        Args:
            bucket_name: The bucket name
            object_name: The object name
            
        Returns:
            Object object
            
        Raises:
            ValueError: If object not found
        """
        if not bucket_name:
            raise ValueError("bucket_name is required")
        if not object_name:
            raise ValueError("object_name is required")
        
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        obj = Object.query.filter_by(
            bucket_id=bucket.id,
            name=object_name
        ).first()
        
        if not obj:
            raise ValueError(f"Object '{object_name}' not found in bucket '{bucket_name}'")
        
        return obj
    
    @staticmethod
    def download_object(bucket_name: str, object_name: str):
        """
        Download an object (get file content)
        
        Args:
            bucket_name: The bucket name
            object_name: The object name
            
        Returns:
            Tuple of (content bytes, Object)
            
        Raises:
            ValueError: If object not found
        """
        obj = ObjectService.get_object(bucket_name, object_name)
        
        file_path = Path(obj.file_path)
        if not file_path.exists():
            raise ValueError(f"Object file not found on disk: {obj.file_path}")
        
        content = file_path.read_bytes()
        return content, obj
    
    @staticmethod
    def delete_object(bucket_name: str, object_name: str):
        """
        Delete an object
        
        Args:
            bucket_name: The bucket name
            object_name: The object name
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If object not found
        """
        if not bucket_name:
            raise ValueError("bucket_name is required")
        if not object_name:
            raise ValueError("object_name is required")
        
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        obj = Object.query.filter_by(
            bucket_id=bucket.id,
            name=object_name
        ).first()
        
        if not obj:
            raise ValueError(f"Object '{object_name}' not found")
        
        # Delete file from disk
        file_path = Path(obj.file_path)
        if file_path.exists():
            file_path.unlink()
        
        db.session.delete(obj)
        db.session.commit()
        return True
