"""
Object Versioning Service - Handles generation, metageneration, and preconditions
"""
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from app.factory import db
from app.models.object import Object, ObjectVersion
from app.models.bucket import Bucket
from app.utils.hashing import calculate_md5, calculate_crc32c
from app.services.object_event_service import ObjectEventService, EventType
from app.logging import log_service_stage


class PreconditionFailedError(Exception):
    """Raised when precondition check fails (HTTP 412)"""
    pass


class ObjectVersioningService:
    """Service for object versioning operations"""
    
    STORAGE_PATH = os.getenv("STORAGE_PATH", "./storage")
    
    @staticmethod
    def upload_object_with_versioning(
        bucket_name: str,
        object_name: str,
        content: bytes,
        content_type: str = "application/octet-stream",
        if_generation_match: Optional[int] = None,
        if_generation_not_match: Optional[int] = None,
        if_metageneration_match: Optional[int] = None,
        if_metageneration_not_match: Optional[int] = None
    ) -> Object:
        """
        Upload object with versioning support and precondition validation
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            content: Binary content
            content_type: MIME type
            if_generation_match: Proceed only if generation matches
            if_generation_not_match: Proceed only if generation doesn't match
            if_metageneration_match: Proceed only if metageneration matches
            if_metageneration_not_match: Proceed only if metageneration doesn't match
            
        Returns:
            Updated/created Object with new generation
            
        Raises:
            ValueError: If bucket doesn't exist or inputs invalid
            PreconditionFailedError: If precondition check fails
        """
        # Validate bucket exists
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        # Get existing object (if any)
        existing_obj = Object.query.filter_by(
            bucket_id=bucket.id,
            name=object_name,
            is_latest=True,
            deleted=False
        ).first()
        
        # Validate preconditions (early inline enforcement for robustness)
        if existing_obj is None:
            if if_generation_match is not None and if_generation_match != 0:
                raise PreconditionFailedError(
                    f"Precondition failed: object does not exist (ifGenerationMatch={if_generation_match})"
                )
            if if_metageneration_match is not None:
                raise PreconditionFailedError(
                    f"Precondition failed: object does not exist (ifMetagenerationMatch={if_metageneration_match})"
                )
        else:
            if if_generation_match is not None and existing_obj.generation != if_generation_match:
                raise PreconditionFailedError(
                    f"Precondition failed: generation {existing_obj.generation} != {if_generation_match}"
                )
            if if_generation_not_match is not None and existing_obj.generation == if_generation_not_match:
                raise PreconditionFailedError(
                    f"Precondition failed: generation {existing_obj.generation} == {if_generation_not_match}"
                )
            if if_metageneration_match is not None and existing_obj.metageneration != if_metageneration_match:
                raise PreconditionFailedError(
                    f"Precondition failed: metageneration {existing_obj.metageneration} != {if_metageneration_match}"
                )
            if if_metageneration_not_match is not None and existing_obj.metageneration == if_metageneration_not_match:
                raise PreconditionFailedError(
                    f"Precondition failed: metageneration {existing_obj.metageneration} == {if_metageneration_not_match}"
                )

        # Secondary validation via helper for future extensions
        ObjectVersioningService._validate_preconditions(
            existing_obj,
            if_generation_match,
            if_generation_not_match,
            if_metageneration_match,
            if_metageneration_not_match
        )
        
        # Calculate hashes
        md5_hash = calculate_md5(content)
        crc32c_hash = calculate_crc32c(content)
        
        # Determine next generation
        if existing_obj:
            next_generation = existing_obj.generation + 1
        else:
            next_generation = 1
        
        # Save file to versioned storage
        file_path = ObjectVersioningService._save_versioned_file(
            bucket.id, object_name, next_generation, content
        )
        
        # Create new object version record
        version = ObjectVersion(
            id=f"{bucket.id}/{object_name}/{next_generation}/{uuid.uuid4().hex[:8]}",
            object_id=existing_obj.id if existing_obj else f"{bucket.id}/{object_name}/{uuid.uuid4().hex[:8]}",
            bucket_id=bucket.id,
            name=object_name,
            generation=next_generation,
            metageneration=1,
            size=len(content),
            content_type=content_type,
            md5_hash=md5_hash,
            crc32c_hash=crc32c_hash,
            file_path=file_path,
            deleted=False,
            meta={}
        )
        
        # Create or update main object record
        if existing_obj:
            # Update existing object to latest version
            existing_obj.generation = next_generation
            existing_obj.metageneration = 1
            existing_obj.size = len(content)
            existing_obj.content_type = content_type
            existing_obj.md5_hash = md5_hash
            existing_obj.crc32c_hash = crc32c_hash
            existing_obj.file_path = file_path
            existing_obj.is_latest = True  # Ensure it stays latest
            existing_obj.updated_at = datetime.utcnow()
            obj = existing_obj
        else:
            # Create new object
            obj = Object(
                id=version.object_id,
                bucket_id=bucket.id,
                name=object_name,
                generation=next_generation,
                metageneration=1,
                size=len(content),
                content_type=content_type,
                md5_hash=md5_hash,
                crc32c_hash=crc32c_hash,
                file_path=file_path,
                is_latest=True,
                deleted=False,
                time_created=datetime.utcnow(),
                meta={}
            )
            db.session.add(obj)
        
        # Save version
        db.session.add(version)
        db.session.commit()
        
        # Phase 4: Log OBJECT_FINALIZE event
        ObjectEventService.log_event(
            bucket_name=bucket_name,
            object_name=object_name,
            event_type=EventType.OBJECT_FINALIZE,
            generation=next_generation
        )
        
        return obj
    
    @staticmethod
    def get_object_version(
        bucket_name: str,
        object_name: str,
        generation: Optional[int] = None
    ) -> Tuple[Object, ObjectVersion]:
        """
        Get object metadata for specific generation or latest
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            generation: Specific generation number (None = latest)
            
        Returns:
            Tuple of (Object, ObjectVersion)
            
        Raises:
            ValueError: If object or version not found
        """
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        # Get main object
        obj = Object.query.filter_by(
            bucket_id=bucket.id,
            name=object_name,
            deleted=False
        ).first()
        
        if not obj:
            raise ValueError(f"Object '{object_name}' not found in bucket '{bucket_name}'")
        
        # Get specific version
        if generation is not None:
            version = ObjectVersion.query.filter_by(
                bucket_id=bucket.id,
                name=object_name,
                generation=generation,
                deleted=False
            ).first()
            
            if not version:
                raise ValueError(f"Object '{object_name}' generation {generation} not found")
        else:
            # Get latest version
            version = ObjectVersion.query.filter_by(
                bucket_id=bucket.id,
                name=object_name,
                generation=obj.generation,
                deleted=False
            ).first()
            
            if not version:
                raise ValueError(f"No version found for object '{object_name}'")
        
        return obj, version
    
    @staticmethod
    def download_object_version(
        bucket_name: str,
        object_name: str,
        generation: Optional[int] = None
    ) -> Tuple[bytes, ObjectVersion]:
        """
        Download object content for specific generation or latest
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            generation: Specific generation number (None = latest)
            
        Returns:
            Tuple of (content bytes, ObjectVersion)
            
        Raises:
            ValueError: If object, version, or file not found
        """
        obj, version = ObjectVersioningService.get_object_version(
            bucket_name, object_name, generation
        )
        
        # Read file from filesystem
        file_path = Path(version.file_path)
        if not file_path.exists():
            raise ValueError(f"Object file not found on disk: {version.file_path}")
        
        content = file_path.read_bytes()
        return content, version
    
    @staticmethod
    def delete_object_version(
        bucket_name: str,
        object_name: str,
        generation: Optional[int] = None
    ) -> bool:
        """
        Delete specific object version or all versions
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            generation: Specific generation to delete (None = delete all)
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If object or version not found
        """
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        obj = Object.query.filter_by(
            bucket_id=bucket.id,
            name=object_name,
            deleted=False
        ).first()
        
        if not obj:
            raise ValueError(f"Object '{object_name}' not found in bucket '{bucket_name}'")
        
        if generation is not None:
            # Delete specific version
            return ObjectVersioningService._delete_specific_version(
                bucket.id, object_name, generation, obj
            )
        else:
            # Delete all versions (object deletion)
            return ObjectVersioningService._delete_all_versions(obj)
    
    @staticmethod
    def list_object_versions(
        bucket_name: str,
        object_name: str
    ) -> list:
        """
        List all versions of an object
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            
        Returns:
            List of ObjectVersion models
            
        Raises:
            ValueError: If bucket not found
        """
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        versions = ObjectVersion.query.filter_by(
            bucket_id=bucket.id,
            name=object_name,
            deleted=False
        ).order_by(ObjectVersion.generation.desc()).all()
        
        return versions
    
    @staticmethod
    def update_object_metadata(
        bucket_name: str,
        object_name: str,
        metadata: dict,
        if_metageneration_match: Optional[int] = None
    ) -> Object:
        """
        Update object metadata (increments metageneration, same generation)
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            metadata: Metadata dictionary to update
            if_metageneration_match: Precondition on metageneration
            
        Returns:
            Updated Object
            
        Raises:
            ValueError: If object not found
            PreconditionFailedError: If metageneration doesn't match
        """
        bucket = Bucket.query.filter_by(name=bucket_name).first()
        if not bucket:
            raise ValueError(f"Bucket '{bucket_name}' not found")
        
        obj = Object.query.filter_by(
            bucket_id=bucket.id,
            name=object_name,
            is_latest=True,
            deleted=False
        ).first()
        
        if not obj:
            raise ValueError(f"Object '{object_name}' not found in bucket '{bucket_name}'")
        
        # Validate metageneration precondition
        if if_metageneration_match is not None:
            if obj.metageneration != if_metageneration_match:
                raise PreconditionFailedError(
                    f"Precondition failed: metageneration {obj.metageneration} != {if_metageneration_match}"
                )
        
        # Update metadata and increment metageneration
        obj.meta.update(metadata)
        obj.metageneration += 1
        obj.updated_at = datetime.utcnow()
        
        # Update corresponding version record
        version = ObjectVersion.query.filter_by(
            bucket_id=bucket.id,
            name=object_name,
            generation=obj.generation
        ).first()
        
        if version:
            version.meta.update(metadata)
            version.metageneration = obj.metageneration
            version.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Phase 4: Log OBJECT_METADATA_UPDATE event
        ObjectEventService.log_event(
            bucket_name=bucket_name,
            object_name=object_name,
            event_type=EventType.OBJECT_METADATA_UPDATE,
            generation=obj.generation,
            metadata=metadata
        )
        
        return obj
    
    # ========== Private Helper Methods ==========
    
    @staticmethod
    def _validate_preconditions(
        existing_obj: Optional[Object],
        if_generation_match: Optional[int],
        if_generation_not_match: Optional[int],
        if_metageneration_match: Optional[int],
        if_metageneration_not_match: Optional[int]
    ) -> None:
        """
        Validate all precondition headers
        
        Raises:
            PreconditionFailedError: If any precondition fails
        """
        # Log inputs for visibility
        try:
            log_service_stage(
                message="Validate preconditions",
                details={
                    "existing": bool(existing_obj),
                    "current_generation": (existing_obj.generation if existing_obj else None),
                    "current_metageneration": (existing_obj.metageneration if existing_obj else None),
                    "if_generation_match": if_generation_match,
                    "if_generation_not_match": if_generation_not_match,
                    "if_metageneration_match": if_metageneration_match,
                    "if_metageneration_not_match": if_metageneration_not_match,
                }
            )
        except Exception:
            pass

        if existing_obj is None:
            # Object doesn't exist
            if if_generation_match is not None and if_generation_match != 0:
                raise PreconditionFailedError(
                    f"Precondition failed: object does not exist (ifGenerationMatch={if_generation_match})"
                )
            if if_metageneration_match is not None:
                raise PreconditionFailedError(
                    f"Precondition failed: object does not exist (ifMetagenerationMatch={if_metageneration_match})"
                )
        else:
            # Object exists - check preconditions
            if if_generation_match is not None:
                if existing_obj.generation != if_generation_match:
                    raise PreconditionFailedError(
                        f"Precondition failed: generation {existing_obj.generation} != {if_generation_match}"
                    )
            
            if if_generation_not_match is not None:
                if existing_obj.generation == if_generation_not_match:
                    raise PreconditionFailedError(
                        f"Precondition failed: generation {existing_obj.generation} == {if_generation_not_match}"
                    )
            
            if if_metageneration_match is not None:
                if existing_obj.metageneration != if_metageneration_match:
                    raise PreconditionFailedError(
                        f"Precondition failed: metageneration {existing_obj.metageneration} != {if_metageneration_match}"
                    )
            
            if if_metageneration_not_match is not None:
                if existing_obj.metageneration == if_metageneration_not_match:
                    raise PreconditionFailedError(
                        f"Precondition failed: metageneration {existing_obj.metageneration} == {if_metageneration_not_match}"
                    )
    
    @staticmethod
    def _save_versioned_file(bucket_id: str, object_name: str, generation: int, content: bytes) -> str:
        """
        Save file to versioned storage path
        
        Format: ./storage/<bucket>/<object>/v<generation>
        
        Returns:
            File path string
            
        Raises:
            ValueError: If object_name contains path traversal attempts
        """
        # Validate object name to prevent path traversal
        ObjectVersioningService._validate_object_name_for_path_traversal(object_name)
        
        # Create directory structure: storage/bucket/object/
        storage_root = Path(ObjectVersioningService.STORAGE_PATH).resolve()
        object_dir = storage_root / bucket_id / object_name
        
        # Ensure the resolved path is still within storage root
        try:
            resolved_object_dir = object_dir.resolve()
            if not str(resolved_object_dir).startswith(str(storage_root)):
                raise ValueError(f"Invalid object name: path traversal detected")
        except (ValueError, OSError) as e:
            raise ValueError(f"Invalid object name: {str(e)}")
        
        object_dir.mkdir(parents=True, exist_ok=True)
        
        # Save with generation in filename
        file_path = object_dir / f"v{generation}"
        file_path.write_bytes(content)
        
        return str(file_path)
    
    @staticmethod
    def _validate_object_name_for_path_traversal(object_name: str) -> None:
        """
        Validate object name to prevent path traversal attacks
        
        Raises:
            ValueError: If object name contains dangerous patterns
        """
        if not object_name:
            raise ValueError("Object name cannot be empty")
        
        # Reject if contains ".." anywhere
        if ".." in object_name:
            raise ValueError("Invalid object name: '..' not allowed")
        
        # Reject backslashes (Windows path separator)
        if "\\" in object_name:
            raise ValueError("Invalid object name: backslashes not allowed")
        
        # Reject absolute paths (Unix-style)
        if object_name.startswith("/"):
            raise ValueError("Invalid object name: absolute paths not allowed")
        
        # Reject Windows drive letters (C:, D:, etc.)
        if len(object_name) >= 2 and object_name[1] == ":":
            raise ValueError("Invalid object name: drive letters not allowed")
    
    @staticmethod
    def _delete_specific_version(bucket_id: str, object_name: str, generation: int, obj: Object) -> bool:
        """Delete specific version and promote previous if needed"""
        version = ObjectVersion.query.filter_by(
            bucket_id=bucket_id,
            name=object_name,
            generation=generation,
            deleted=False
        ).first()
        
        if not version:
            raise ValueError(f"Version {generation} not found for object '{object_name}'")
        
        # Mark version as deleted
        version.deleted = True
        
        # Delete physical file
        file_path = Path(version.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # If deleting latest version, promote previous
        if obj.generation == generation and obj.is_latest:
            previous_version = ObjectVersion.query.filter_by(
                bucket_id=bucket_id,
                name=object_name,
                deleted=False
            ).filter(
                ObjectVersion.generation < generation
            ).order_by(ObjectVersion.generation.desc()).first()
            
            if previous_version:
                # Promote previous version to latest
                obj.generation = previous_version.generation
                obj.metageneration = previous_version.metageneration
                obj.size = previous_version.size
                obj.content_type = previous_version.content_type
                obj.md5_hash = previous_version.md5_hash
                obj.crc32c_hash = previous_version.crc32c_hash
                obj.file_path = previous_version.file_path
                obj.updated_at = datetime.utcnow()
            else:
                # No more versions - mark object as deleted
                obj.deleted = True
                obj.is_latest = False
        
        db.session.commit()
        
        # Phase 4: Log OBJECT_DELETE event
        ObjectEventService.log_event(
            bucket_name=bucket.name,
            object_name=object_name,
            event_type=EventType.OBJECT_DELETE,
            generation=generation
        )
        
        return True
    
    @staticmethod
    def _delete_all_versions(obj: Object) -> bool:
        """Delete all versions of an object"""
        # Get all versions
        versions = ObjectVersion.query.filter_by(
            bucket_id=obj.bucket_id,
            name=obj.name,
            deleted=False
        ).all()
        
        # Delete all physical files and mark versions as deleted
        for version in versions:
            version.deleted = True
            file_path = Path(version.file_path)
            if file_path.exists():
                file_path.unlink()
        
        # Mark object as deleted
        obj.deleted = True
        obj.is_latest = False
        
        db.session.commit()
        return True
