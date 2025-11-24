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
        ObjectService._validate_bucket_name(bucket_name)
        
        bucket = ObjectService._find_bucket_or_raise(bucket_name)
        
        # Query objects with optional prefix filter
        all_objects = ObjectService._query_objects_by_bucket(bucket.id, prefix)
        
        # Group by delimiter if specified (simulates folder structure)
        if delimiter:
            return ObjectService._group_objects_by_delimiter(all_objects, prefix, delimiter)
        
        return {
            "items": all_objects,
            "prefixes": []
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
        # Validate inputs
        ObjectService._validate_upload_inputs(bucket_name, object_name, content)
        
        bucket = ObjectService._find_bucket_or_raise(bucket_name)
        
        # Calculate content hashes for integrity verification
        content_hashes = ObjectService._calculate_content_hashes(content)
        
        # Save file to filesystem and get storage path
        file_storage_path = ObjectService._save_file_to_storage(bucket.id, content)
        
        # Create database record
        obj = ObjectService._create_object_record(
            bucket.id, object_name, content, content_type,
            content_hashes, file_storage_path
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
        ObjectService._validate_object_identifiers(bucket_name, object_name)
        
        bucket = ObjectService._find_bucket_or_raise(bucket_name)
        obj = ObjectService._find_object_or_raise(bucket.id, bucket_name, object_name)
        
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
            ValueError: If object not found or file missing on disk
        """
        obj = ObjectService.get_object(bucket_name, object_name)
        
        # Read file content from filesystem
        content = ObjectService._read_file_from_storage(obj.file_path)
        
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
        ObjectService._validate_object_identifiers(bucket_name, object_name)
        
        bucket = ObjectService._find_bucket_or_raise(bucket_name)
        obj = ObjectService._find_object_or_raise(bucket.id, bucket_name, object_name)
        
        # Remove physical file from storage
        ObjectService._delete_file_from_storage(obj.file_path)
        
        # Remove database record
        db.session.delete(obj)
        db.session.commit()
        return True
    
    # ========== Private Helper Methods ==========
    
    @staticmethod
    def _validate_bucket_name(bucket_name: str) -> None:
        """Validate that bucket_name is not empty"""
        if not bucket_name:
            raise ValueError("bucket_name is required")
    
    @staticmethod
    def _validate_object_identifiers(bucket_name: str, object_name: str) -> None:
        """Validate both bucket and object names are provided"""
        if not bucket_name:
            raise ValueError("bucket_name is required")
        if not object_name:
            raise ValueError("object_name is required")
    
    @staticmethod
    def _validate_upload_inputs(bucket_name: str, object_name: str, content: bytes) -> None:
        """Validate all required inputs for object upload"""
        ObjectService._validate_object_identifiers(bucket_name, object_name)
        if not isinstance(content, bytes):
            raise ValueError("content must be bytes")
    
    @staticmethod
    def _find_bucket_or_raise(bucket_name: str) -> Bucket:
        """Find bucket by name or raise ValueError if not found"""
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        return bucket
    
    @staticmethod
    def _find_object_or_raise(bucket_id: str, bucket_name: str, object_name: str) -> Object:
        """Find object by bucket_id and name or raise ValueError if not found"""
        obj = Object.query.filter_by(
            bucket_id=bucket_id,
            name=object_name
        ).first()
        
        if not obj:
            raise ValueError(f"Object '{object_name}' not found in bucket '{bucket_name}'")
        return obj
    
    @staticmethod
    def _query_objects_by_bucket(bucket_id: str, prefix: str = None) -> list:
        """Query all objects in bucket, optionally filtered by prefix"""
        query = Object.query.filter_by(bucket_id=bucket_id)
        
        if prefix:
            query = query.filter(Object.name.startswith(prefix))
        
        return query.all()
    
    @staticmethod
    def _group_objects_by_delimiter(objects: list, prefix: str, delimiter: str) -> dict:
        """
        Group objects by delimiter to simulate folder hierarchy
        Objects with delimiter in name become prefixes, others remain as items
        """
        prefix_length = len(prefix or "")
        unique_prefixes = set()
        ungrouped_items = []
        
        for obj in objects:
            remaining_name = obj.name[prefix_length:]
            
            # If delimiter found in remaining name, extract as prefix
            if delimiter in remaining_name:
                delimiter_index = obj.name.find(delimiter, prefix_length)
                folder_prefix = obj.name[:delimiter_index + len(delimiter)]
                unique_prefixes.add(folder_prefix)
            else:
                ungrouped_items.append(obj)
        
        return {
            "items": ungrouped_items,
            "prefixes": sorted(list(unique_prefixes))
        }
    
    @staticmethod
    def _calculate_content_hashes(content: bytes) -> dict:
        """Calculate MD5 and CRC32C hashes for content integrity"""
        return {
            "md5": calculate_md5(content),
            "crc32c": calculate_crc32c(content)
        }
    
    @staticmethod
    def _save_file_to_storage(bucket_id: str, content: bytes) -> str:
        """Save file content to filesystem and return storage path"""
        # Create bucket-specific storage directory
        storage_directory = Path(ObjectService.STORAGE_PATH) / bucket_id
        storage_directory.mkdir(parents=True, exist_ok=True)
        
        # Generate unique file ID and save content
        unique_file_id = uuid.uuid4().hex
        file_path = storage_directory / unique_file_id
        file_path.write_bytes(content)
        
        return str(file_path)
    
    @staticmethod
    def _create_object_record(
        bucket_id: str,
        object_name: str,
        content: bytes,
        content_type: str,
        content_hashes: dict,
        file_path: str
    ) -> Object:
        """Create Object model instance with all metadata"""
        object_id = f"{bucket_id}/{object_name}/{uuid.uuid4().hex[:8]}"
        
        return Object(
            id=object_id,
            bucket_id=bucket_id,
            name=object_name,
            size=len(content),
            content_type=content_type,
            md5_hash=content_hashes["md5"],
            crc32c_hash=content_hashes["crc32c"],
            file_path=file_path,
            metageneration=1,
            meta={}
        )
    
    @staticmethod
    def _read_file_from_storage(file_path: str) -> bytes:
        """Read file content from filesystem, raise error if missing"""
        file_location = Path(file_path)
        if not file_location.exists():
            raise ValueError(f"Object file not found on disk: {file_path}")
        return file_location.read_bytes()
    
    @staticmethod
    def _delete_file_from_storage(file_path: str) -> None:
        """Delete physical file from filesystem if it exists"""
        file_location = Path(file_path)
        if file_location.exists():
            file_location.unlink()
