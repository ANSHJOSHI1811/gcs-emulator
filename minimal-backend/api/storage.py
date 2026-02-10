import base64
import hashlib
import json
import struct
import zlib
import uuid
import os
import re
import secrets
import tempfile
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from urllib.parse import unquote
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response, status, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db, Bucket as DBBucket, Object as DBObject, SignedUrlSession

router = APIRouter()

STORAGE_DIR = "/tmp/gcs-storage"


def sanitize_object_name(name: str) -> str:
    """
    Sanitize object name to prevent path traversal attacks.
    Removes dangerous sequences like ../, ~, and absolute paths.
    """
    if not name:
        raise HTTPException(status_code=400, detail="Object name cannot be empty")
    
    # Remove leading/trailing slashes
    name = name.strip('/')
    
    # Replace dangerous sequences
    name = name.replace('..', '')
    name = name.replace('~', '')
    
    # Remove null bytes
    name = name.replace('\x00', '')
    
    # Ensure name doesn't start with special characters
    if name.startswith(('.', '/')):
        raise HTTPException(status_code=400, detail="Invalid object name")
    
    return name


def validate_object_path(bucket: str, object_name: str) -> Path:
    """
    Validate that the resulting file path is within the bucket directory.
    Prevents path traversal attacks.
    """
    base_path = Path(STORAGE_DIR) / bucket
    file_path = base_path / object_name
    
    try:
        # Resolve to absolute path and check if it's within base_path
        resolved = file_path.resolve()
        base_resolved = base_path.resolve()
        
        if not str(resolved).startswith(str(base_resolved)):
            raise HTTPException(
                status_code=400,
                detail="Invalid object name: path traversal detected"
            )
        
        return file_path
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid path: {e}")


@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get aggregated storage statistics for dashboard"""
    total_objects = db.query(DBObject).filter(DBObject.deleted == False).count()
    total_bytes = db.query(func.coalesce(func.sum(DBObject.size), 0)).filter(
        DBObject.deleted == False
    ).scalar() or 0
    
    return {
        "totalObjects": total_objects,
        "totalStorageBytes": int(total_bytes)
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _calc_hashes(content: bytes):
    md5_b64 = base64.b64encode(hashlib.md5(content).digest()).decode("utf-8")
    crc = zlib.crc32(content) & 0xFFFFFFFF
    crc_b64 = base64.b64encode(struct.pack(">I", crc)).decode("utf-8")
    return md5_b64, crc_b64


def _validate_bucket_name(name: str) -> None:
    """Validate bucket name according to GCS rules"""
    if not name:
        raise HTTPException(status_code=400, detail="Bucket name cannot be empty")
    
    if len(name) < 3 or len(name) > 63:
        raise HTTPException(status_code=400, detail="Bucket name must be between 3 and 63 characters")
    
    # Must start and end with alphanumeric
    if not (name[0].isalnum() and name[-1].isalnum()):
        raise HTTPException(status_code=400, detail="Bucket name must start and end with alphanumeric character")
    
    # Only lowercase letters, numbers, hyphens, and underscores
    if not re.match(r'^[a-z0-9][a-z0-9_-]*[a-z0-9]$', name):
        raise HTTPException(status_code=400, detail="Bucket name must contain only lowercase letters, numbers, hyphens, and underscores")
    
    # Cannot contain 'google' or close variations
    if 'google' in name.lower():
        raise HTTPException(status_code=400, detail="Bucket name cannot contain 'google'")


def _get_bucket_or_404(bucket_name: str, db: Session) -> DBBucket:
    """Get bucket from database or raise 404"""
    db_bucket = db.query(DBBucket).filter(DBBucket.name == bucket_name).first()
    if not db_bucket:
        raise HTTPException(status_code=404, detail=f"Bucket '{bucket_name}' not found")
    return db_bucket


def _bucket_to_response(bucket: DBBucket) -> Dict[str, Any]:
    """Convert database bucket to API response format"""
    # Generate a numeric project number from project_id hash
    project_number = abs(hash(bucket.project_id)) % (10**12)
    
    return {
        "kind": "storage#bucket",
        "id": bucket.name,
        "selfLink": f"http://localhost:8080/storage/v1/b/{bucket.name}",
        "name": bucket.name,
        "projectNumber": str(project_number),  # Must be string per GCS API spec
        "project": bucket.project_id,
        "location": bucket.location,
        "storageClass": bucket.storage_class,
        "versioning": {"enabled": bucket.versioning_enabled} if bucket.versioning_enabled else None,
        "timeCreated": bucket.created_at.isoformat().replace("+00:00", "Z") if bucket.created_at else _now(),
        "updated": bucket.updated_at.isoformat().replace("+00:00", "Z") if bucket.updated_at else _now(),
        "metageneration": "1",
        "iamConfiguration": {
            "bucketPolicyOnly": {"enabled": False},
            "uniformBucketLevelAccess": {"enabled": False}
        },
        "locationType": "multi-region" if bucket.location in ["US", "EU", "ASIA"] else "region",
    }


class BucketCreate(BaseModel):
    name: str
    location: Optional[str] = "US"
    storageClass: Optional[str] = "STANDARD"


@router.get("/storage/v1/b")
def list_buckets(
    project: Optional[str] = Query(None),
    prefix: Optional[str] = Query(None),
    maxResults: Optional[int] = Query(None, ge=1, le=1000),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """List buckets with optional filtering and pagination"""
    query = db.query(DBBucket)
    
    if project:
        query = query.filter(DBBucket.project_id == project)
    
    if prefix:
        query = query.filter(DBBucket.name.startswith(prefix))
    
    # Order by name for consistent results
    query = query.order_by(DBBucket.name)
    
    if maxResults:
        query = query.limit(maxResults)
    
    buckets = query.all()
    
    items = [_bucket_to_response(b) for b in buckets]
    
    return {
        "kind": "storage#buckets",
        "items": items
    }


@router.post("/storage/v1/b")
def create_bucket(
    payload: BucketCreate, 
    project: Optional[str] = Query(None),
    ifNotExists: Optional[bool] = Query(False, description="Return existing bucket instead of error if already exists"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Create a new bucket with validation and proper error handling"""
    # Validate bucket name
    _validate_bucket_name(payload.name)
    
    # Validate project
    if not project:
        raise HTTPException(status_code=400, detail="Project parameter is required")
    
    # Check if bucket already exists
    existing = db.query(DBBucket).filter(DBBucket.name == payload.name).first()
    if existing:
        if ifNotExists:
            # Return existing bucket instead of error
            return _bucket_to_response(existing)
        else:
            raise HTTPException(
                status_code=409,
                detail=f"Bucket '{payload.name}' already exists"
            )
    
    # Validate storage class
    valid_storage_classes = ["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"]
    storage_class = payload.storageClass or "STANDARD"
    if storage_class not in valid_storage_classes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid storage class. Must be one of: {', '.join(valid_storage_classes)}"
        )
    
    # Validate location
    valid_locations = ["US", "EU", "ASIA", "us-central1", "us-east1", "europe-west1", "asia-east1"]
    location = payload.location or "US"
    if location not in valid_locations:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid location. Must be one of: {', '.join(valid_locations)}"
        )
    
    try:
        # Use transaction for atomic operation
        now = datetime.now(timezone.utc)
        bucket = DBBucket(
            id=payload.name,
            name=payload.name,
            project_id=project,
            location=location,
            storage_class=storage_class,
            versioning_enabled=False,
            created_at=now,
            updated_at=now
        )
        db.add(bucket)
        db.commit()
        db.refresh(bucket)
        
        # Create directory after successful database commit
        try:
            bucket_dir = f"{STORAGE_DIR}/{payload.name}"
            os.makedirs(bucket_dir, exist_ok=True)
        except Exception as e:
            # Rollback database if filesystem fails
            db.delete(bucket)
            db.commit()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create bucket directory: {str(e)}"
            )
        
        return _bucket_to_response(bucket)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create bucket: {str(e)}")


@router.get("/storage/v1/b/{bucket}")
def get_bucket(bucket: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get bucket details by name"""
    db_bucket = _get_bucket_or_404(bucket, db)
    return _bucket_to_response(db_bucket)


@router.delete("/storage/v1/b/{bucket}", status_code=204)
def delete_bucket(
    bucket: str, 
    force: bool = Query(False, description="Force delete even if bucket contains objects"),
    deleteObjects: bool = Query(False, description="Delete all objects before deleting bucket"),
    db: Session = Depends(get_db)
):
    """Delete a bucket (must be empty unless force=true or deleteObjects=true)"""
    db_bucket = _get_bucket_or_404(bucket, db)
    
    # Check if bucket has objects
    object_count = db.query(DBObject).filter(
        DBObject.bucket_id == bucket,
        DBObject.deleted == False
    ).count()
    
    if object_count > 0:
        if not (force or deleteObjects):
            raise HTTPException(
                status_code=409,
                detail=f"Bucket '{bucket}' is not empty. Contains {object_count} objects. Use force=true or deleteObjects=true to proceed."
            )
        elif deleteObjects:
            # User explicitly wants to delete objects
            pass  # Continue to deletion
        # else force=true, proceed with deletion
    
    try:
        # Delete ALL objects first (including deleted=True ones) to avoid foreign key constraint
        all_objects = db.query(DBObject).filter(DBObject.bucket_id == bucket).all()
        if all_objects:
            for obj in all_objects:
                # Delete file from filesystem (only if not already deleted)
                if not obj.deleted:
                    file_path = obj.file_path or f"{STORAGE_DIR}/{bucket}/{obj.name}"
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            print(f"Deleted file: {file_path}")
                        except Exception as e:
                            print(f"Warning: Failed to delete file {file_path}: {e}")
                # Delete from database
                db.delete(obj)
            
            # Commit object deletions first
            db.commit()
            print(f"Deleted {len(all_objects)} objects from bucket {bucket}")
        
        # Now delete bucket from database
        db.delete(db_bucket)
        db.commit()
        
        # Delete bucket directory from filesystem
        bucket_dir = f"{STORAGE_DIR}/{bucket}"
        if os.path.exists(bucket_dir):
            try:
                import shutil
                shutil.rmtree(bucket_dir)
            except Exception as e:
                print(f"Warning: Failed to delete bucket directory {bucket_dir}: {e}")
        
        return Response(status_code=204)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete bucket: {str(e)}")


@router.patch("/storage/v1/b/{bucket}")
def update_bucket(bucket: str, payload: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Update bucket properties (versioning, storage class, etc.)"""
    db_bucket = _get_bucket_or_404(bucket, db)
    
    # Update versioning if provided
    if "versioning" in payload:
        versioning_enabled = payload["versioning"].get("enabled", False)
        db_bucket.versioning_enabled = versioning_enabled
    
    # Update storage class if provided
    if "storageClass" in payload:
        valid_storage_classes = ["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"]
        new_class = payload["storageClass"]
        if new_class not in valid_storage_classes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid storage class. Must be one of: {', '.join(valid_storage_classes)}"
            )
        db_bucket.storage_class = new_class
    
    # Update lifecycle config if provided
    if "lifecycle" in payload:
        db_bucket.lifecycle_config = json.dumps(payload["lifecycle"])
    
    # Update CORS if provided
    if "cors" in payload:
        db_bucket.cors = json.dumps(payload["cors"])
    
    db_bucket.updated_at = datetime.now(timezone.utc)
    
    try:
        db.commit()
        db.refresh(db_bucket)
        return _bucket_to_response(db_bucket)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update bucket: {str(e)}")


@router.get("/storage/v1/b/{bucket}/storageLayout")
def get_storage_layout(bucket: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    # Validate bucket exists
    _get_bucket_or_404(bucket, db)
    return {"kind": "storage#storageLayout", "bucket": bucket, "hierarchicalNamespace": {"enabled": False}}


@router.get("/storage/v1/b/{bucket}/stats")
def get_bucket_stats(bucket: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get bucket statistics (object count, total size, etc.)"""
    db_bucket = _get_bucket_or_404(bucket, db)
    
    # Get object statistics
    stats = db.query(
        func.count(DBObject.id).label('count'),
        func.coalesce(func.sum(DBObject.size), 0).label('total_size')
    ).filter(
        DBObject.bucket_id == bucket,
        DBObject.deleted == False
    ).first()
    
    return {
        "kind": "storage#bucketStats",
        "bucket": bucket,
        "objectCount": stats.count,
        "totalBytes": int(stats.total_size),
        "location": db_bucket.location,
        "storageClass": db_bucket.storage_class,
        "versioning": db_bucket.versioning_enabled
    }


@router.get("/storage/v1/b/{bucket}/o")
def list_objects(bucket: str, prefix: Optional[str] = None, db: Session = Depends(get_db)) -> Dict[str, Any]:
    # Validate bucket exists
    _get_bucket_or_404(bucket, db)
    
    query = db.query(DBObject).filter(DBObject.bucket_id == bucket, DBObject.deleted == False)
    if prefix:
        query = query.filter(DBObject.name.startswith(prefix))
    objects = query.all()
    
    items = []
    for obj in objects:
        # Ensure all values are strings, not bytes
        content_type = obj.content_type or "application/octet-stream"
        if isinstance(content_type, bytes):
            content_type = content_type.decode("utf-8")
        
        md5_hash = obj.md5_hash or ""
        if isinstance(md5_hash, bytes):
            md5_hash = md5_hash.decode("utf-8")
        
        crc32c_hash = obj.crc32c_hash or ""
        if isinstance(crc32c_hash, bytes):
            crc32c_hash = crc32c_hash.decode("utf-8")
        
        items.append({
            "kind": "storage#object",
            "id": f"{obj.bucket_id}/{obj.name}",
            "selfLink": f"http://localhost:8080/storage/v1/b/{obj.bucket_id}/o/{obj.name}",
            "mediaLink": f"http://localhost:8080/download/storage/v1/b/{obj.bucket_id}/o/{obj.name}?alt=media",
            "bucket": str(obj.bucket_id),
            "name": str(obj.name),
            "size": str(obj.size),
            "contentType": str(content_type),
            "timeCreated": obj.time_created.isoformat().replace("+00:00", "Z") if obj.time_created else _now(),
            "updated": obj.updated_at.isoformat().replace("+00:00", "Z") if obj.updated_at else _now(),
            "generation": str(obj.generation),
            "md5Hash": str(md5_hash),
            "crc32c": str(crc32c_hash),
            "etag": f'"{str(md5_hash)}"',
        })
    return {"kind": "storage#objects", "items": items}


@router.get("/storage/v1/b/{bucket}/o/{object_name:path}/versions")
def list_object_versions(
    bucket: str,
    object_name: str,
    db: Session = Depends(get_db)
):
    """List all versions of an object"""
    # Query all versions of the object
    objects = db.query(DBObject).filter(
        DBObject.bucket_id == bucket,
        DBObject.name == object_name
    ).order_by(DBObject.generation.desc()).all()
    
    if not objects:
        raise HTTPException(status_code=404, detail="No versions found for object")
    
    # Build response items
    items = []
    for obj in objects:
        items.append({
            "kind": "storage#object",
            "id": obj.id,
            "name": obj.name,
            "bucket": obj.bucket_id,
            "generation": str(obj.generation),
            "metageneration": str(obj.metageneration),
            "contentType": obj.content_type,
            "size": str(obj.size),
            "md5Hash": obj.md5_hash,
            "crc32c": obj.crc32c_hash,
            "timeCreated": obj.created_at.isoformat() + "Z",
            "updated": obj.updated_at.isoformat() + "Z",
            "mediaLink": f"http://localhost:8080/storage/v1/b/{bucket}/o/{obj.name}?generation={obj.generation}&alt=media",
            "isLatest": obj.is_latest,
            "deleted": obj.deleted
        })
    
    return {
        "kind": "storage#objectVersions",
        "items": items
    }


@router.get("/storage/v1/b/{bucket}/o/{object:path}")
@router.get("/download/storage/v1/b/{bucket}/o/{object:path}")
def get_object(
    bucket: str, 
    object: str, 
    alt: Optional[str] = Query(None),
    generation: Optional[int] = Query(None, description="Specific version to retrieve"),
    db: Session = Depends(get_db)
):
    """Get object metadata or download file. Supports specific version via generation parameter."""
    # Validate bucket exists
    _get_bucket_or_404(bucket, db)
    
    raw_name = unquote(object)
    
    # Query with optional generation filter
    query = db.query(DBObject).filter(
        DBObject.bucket_id == bucket,
        ((DBObject.name == object) | (DBObject.name == raw_name)),
        DBObject.deleted == False
    )
    
    if generation is not None:
        # Get specific version
        query = query.filter(DBObject.generation == generation)
        db_obj = query.first()
    else:
        # Get latest version
        query = query.filter(DBObject.is_latest == True)
        db_obj = query.first()
    
    if not db_obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    if alt == "media":
        # Use the versioned file path from database
        file_path = db_obj.file_path
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # All values should already be strings from upload, but double-check
            content_type = str(db_obj.content_type or "application/octet-stream")
            md5_hash = str(db_obj.md5_hash or "")
            crc32c_hash = str(db_obj.crc32c_hash or "")
                
            headers = {
                "Content-Length": str(len(file_content)),
                "x-goog-hash": f"crc32c={crc32c_hash},md5={md5_hash}",
                "x-goog-generation": str(db_obj.generation),
                "x-goog-metageneration": str(db_obj.metageneration),
                "x-goog-stored-content-length": str(len(file_content)),
                "ETag": f'"{md5_hash}"',
                "Content-Disposition": f'attachment; filename="{db_obj.name}"'
            }
            
            return Response(
                content=file_content, 
                media_type=content_type,
                headers=headers
            )
            
        raise HTTPException(status_code=404, detail="Object file not found")
    
    # Return metadata (all values must be strings, no bytes!)
    # Ensure we decode any bytes to strings
    content_type = db_obj.content_type or "application/octet-stream"
    if isinstance(content_type, bytes):
        content_type = content_type.decode("utf-8")
    
    md5_hash = db_obj.md5_hash or ""
    if isinstance(md5_hash, bytes):
        md5_hash = md5_hash.decode("utf-8")
    
    crc32c_hash = db_obj.crc32c_hash or ""
    if isinstance(crc32c_hash, bytes):
        crc32c_hash = crc32c_hash.decode("utf-8")
    
    return {
        "kind": "storage#object",
        "id": f"{db_obj.bucket_id}/{db_obj.name}",
        "selfLink": f"http://localhost:8080/storage/v1/b/{db_obj.bucket_id}/o/{db_obj.name}",
        "mediaLink": f"http://localhost:8080/download/storage/v1/b/{db_obj.bucket_id}/o/{db_obj.name}?alt=media",
        "bucket": str(db_obj.bucket_id),
        "name": str(db_obj.name),
        "size": str(db_obj.size),
        "contentType": str(content_type),
        "timeCreated": db_obj.time_created.isoformat().replace("+00:00", "Z") if db_obj.time_created else _now(),
        "updated": db_obj.updated_at.isoformat().replace("+00:00", "Z") if db_obj.updated_at else _now(),
        "generation": str(db_obj.generation),
        "md5Hash": str(md5_hash),
        "crc32c": str(crc32c_hash),
        "etag": f'"{str(md5_hash)}"',
    }


@router.delete("/storage/v1/b/{bucket}/o/{object:path}", status_code=204)
def delete_object(bucket: str, object: str, db: Session = Depends(get_db)):
    # Validate bucket exists using helper function
    _get_bucket_or_404(bucket, db)
    
    raw_name = unquote(object)
    db_obj = db.query(DBObject).filter(
        DBObject.bucket_id == bucket,
        ((DBObject.name == object) | (DBObject.name == raw_name)),
        DBObject.deleted == False
    ).first()
    
    if not db_obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    file_path = f"{STORAGE_DIR}/{bucket}/{db_obj.name}"
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db_obj.deleted = True
    db.commit()
    return Response(status_code=204)


@router.post("/upload/storage/v1/b/{bucket}/o")
async def upload_object(bucket: str, request: Request, name: Optional[str] = Query(None), db: Session = Depends(get_db)) -> Dict[str, Any]:
    # Validate bucket exists using helper function
    _get_bucket_or_404(bucket, db)
    
    raw_body = await request.body()
    object_name = name
    
    if not object_name:
        match = re.search(rb'"name"\s*:\s*"([^"]+)"', raw_body)
        if match:
            object_name = match.group(1).decode('utf-8')
    
    if not object_name:
        raise HTTPException(status_code=400, detail="Object name required")
    
    # SECURITY: Sanitize object name to prevent path traversal
    object_name = sanitize_object_name(object_name)
    
    content = raw_body
    if b'"name"' in raw_body and raw_body.startswith(b'--'):
        try:
            boundary_line = raw_body.split(b'\n', 1)[0]
            parts = raw_body.split(boundary_line)
            if len(parts) >= 3:
                data_part = parts[2]
                if b'\n\n' in data_part:
                    content = data_part.split(b'\n\n', 1)[1]
                    if content.endswith(b'\n'):
                        content = content[:-1]
        except:
            pass
    
    # Determine generation number FIRST (before writing file)
    existing_obj = db.query(DBObject).filter(
        DBObject.bucket_id == bucket,
        DBObject.name == object_name,
        DBObject.is_latest == True,
        DBObject.deleted == False
    ).with_for_update().first()
    
    next_generation = existing_obj.generation + 1 if existing_obj else 1
    
    # SECURITY: Validate base file path is within bucket directory
    base_file_path = validate_object_path(bucket, object_name)
    
    # Create versioned file path: bucket/object.txt.v1, bucket/object.txt.v2, etc.
    file_path_parts = str(base_file_path).rsplit('.', 1)
    if len(file_path_parts) == 2:
        versioned_file_path = Path(f"{file_path_parts[0]}.v{next_generation}.{file_path_parts[1]}")
    else:
        versioned_file_path = Path(f"{base_file_path}.v{next_generation}")
    
    # Create directory if needed
    os.makedirs(versioned_file_path.parent, exist_ok=True)
    
    # SECURITY: Atomic write using temporary file
    temp_fd, temp_path = tempfile.mkstemp(dir=versioned_file_path.parent, prefix='.tmp_')
    try:
        with os.fdopen(temp_fd, 'wb') as f:
            f.write(content)
        
        # Atomically rename temp file to final destination
        os.replace(temp_path, versioned_file_path)
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Failed to write file: {e}")
    
    with open(versioned_file_path, "rb") as f:
        file_content = f.read()
    
    md5_hash, crc32c = _calc_hashes(file_content)
    
    # CRITICAL: Ensure all values are strings, not bytes (fixes gcloud download bug)
    md5_hash = str(md5_hash) if not isinstance(md5_hash, str) else md5_hash
    crc32c = str(crc32c) if not isinstance(crc32c, str) else crc32c
    content_type = "application/octet-stream"  # Always string
    
    # Validate that hashes are actually strings
    assert isinstance(md5_hash, str), f"md5_hash must be string, got {type(md5_hash)}"
    assert isinstance(crc32c, str), f"crc32c must be string, got {type(crc32c)}"
    assert isinstance(content_type, str), f"content_type must be string, got {type(content_type)}"
    
    now = datetime.now(timezone.utc)
    
    # Note: existing_obj was already queried above with locking
    if existing_obj:
        # Mark old version as not latest
        existing_obj.is_latest = False
        
        # Create new version (new row)
        db_obj = DBObject(
            id=f"{bucket}/{object_name}/generation/{existing_obj.generation + 1}",
            bucket_id=bucket,
            name=object_name,
            size=len(file_content),
            content_type=content_type,  # String
            md5_hash=md5_hash,  # String
            crc32c_hash=crc32c,  # String
            file_path=str(versioned_file_path),  # Versioned file path
            generation=existing_obj.generation + 1,
            metageneration=1,
            time_created=now,
            created_at=now,
            updated_at=now,
            is_latest=True,
            deleted=False
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
    else:
        # Create new object (first version)
        db_obj = DBObject(
            id=f"{bucket}/{object_name}/generation/1",
            bucket_id=bucket,
            name=object_name,
            size=len(file_content),
            content_type=content_type,  # String
            md5_hash=md5_hash,  # String
            crc32c_hash=crc32c,  # String
            file_path=str(versioned_file_path),  # Versioned file path
            generation=1,
            metageneration=1,
            time_created=now,
            created_at=now,
            updated_at=now,
            is_latest=True,
            deleted=False
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
    
    return {
        "kind": "storage#object",
        "id": f"{bucket}/{object_name}",
        "selfLink": f"http://localhost:8080/storage/v1/b/{bucket}/o/{object_name}",
        "bucket": bucket,
        "name": object_name,
        "size": str(len(file_content)),
        "contentType": "application/octet-stream",
        "timeCreated": db_obj.time_created.isoformat().replace("+00:00", "Z"),
        "updated": db_obj.updated_at.isoformat().replace("+00:00", "Z"),
        "generation": str(db_obj.generation),
        "md5Hash": md5_hash,
        "crc32c": crc32c,
        "etag": f'"{md5_hash}"',
    }


@router.post("/storage/v1/b/{src_bucket}/o/{src_obj}/rewriteTo/b/{dst_bucket}/o/{dst_obj}")
def rewrite_object(src_bucket: str, src_obj: str, dst_bucket: str, dst_obj: str, db: Session = Depends(get_db)):
    src_obj = unquote(src_obj)
    dst_obj = unquote(dst_obj)
    
    src_db_bucket = db.query(DBBucket).filter(DBBucket.name == src_bucket).first()
    dst_db_bucket = db.query(DBBucket).filter(DBBucket.name == dst_bucket).first()
    
    if not src_db_bucket or not dst_db_bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    
    src_db_obj = db.query(DBObject).filter(
        DBObject.bucket_id == src_bucket,
        DBObject.name == src_obj,
        DBObject.deleted == False
    ).first()
    
    if not src_db_obj:
        raise HTTPException(status_code=404, detail="Source object not found")
    
    src_file = f"{STORAGE_DIR}/{src_bucket}/{src_obj}"
    dst_file = f"{STORAGE_DIR}/{dst_bucket}/{dst_obj}"
    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
    
    with open(src_file, "rb") as sf:
        content = sf.read()
    with open(dst_file, "wb") as df:
        df.write(content)
    
    now = datetime.now(timezone.utc)
    dst_db_obj = DBObject(
        id=f"{dst_bucket}/{dst_obj}",
        bucket_id=dst_bucket,
        name=dst_obj,
        size=src_db_obj.size,
        content_type=src_db_obj.content_type,
        md5_hash=src_db_obj.md5_hash,
        crc32c_hash=src_db_obj.crc32c_hash,
        file_path=dst_file,
        generation=1,
        metageneration=1,
        time_created=now,
        created_at=now,
        updated_at=now,
        deleted=False
    )
    db.add(dst_db_obj)
    db.commit()
    db.refresh(dst_db_obj)
    
    return {
        "kind": "storage#rewriteResponse",
        "totalBytesRewritten": str(dst_db_obj.size),
        "objectSize": str(dst_db_obj.size),
        "done": True,
        "resource": {
            "kind": "storage#object",
            "id": f"{dst_bucket}/{dst_obj}",
            "selfLink": f"http://localhost:8080/storage/v1/b/{dst_bucket}/o/{dst_obj}",
            "bucket": dst_bucket,
            "name": dst_obj,
            "size": str(dst_db_obj.size),
            "contentType": dst_db_obj.content_type,
            "timeCreated": dst_db_obj.time_created.isoformat().replace("+00:00", "Z"),
            "updated": dst_db_obj.updated_at.isoformat().replace("+00:00", "Z"),
            "generation": str(dst_db_obj.generation),
            "md5Hash": dst_db_obj.md5_hash,
            "crc32c": dst_db_obj.crc32c_hash,
        },
    }


# ============================================================================
# SIGNED URL ENDPOINTS
# ============================================================================

@router.post("/storage/v1/b/{bucket}/o/{object:path}/signedUrl")
def generate_signed_url(
    bucket: str,
    object: str,
    payload: Dict[str, Any],
    project: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Generate a temporary signed URL for secure object access.
    
    Request body:
    {
        "method": "GET",      # HTTP method (GET or PUT)
        "expiresIn": 3600     # Expiration in seconds (default: 1 hour)
    }
    
    Returns:
    {
        "signedUrl": "http://localhost:8080/signed/{token}",
        "expiresAt": "2026-02-06T12:00:00Z"
    }
    """
    # Validate bucket exists
    _get_bucket_or_404(bucket, db)
    
    # Decode and validate object exists
    object_name = unquote(object)
    object_name = sanitize_object_name(object_name)
    
    db_obj = db.query(DBObject).filter(
        DBObject.bucket_id == bucket,
        ((DBObject.name == object) | (DBObject.name == object_name)),
        DBObject.deleted == False
    ).first()
    
    if not db_obj:
        raise HTTPException(status_code=404, detail=f"Object '{object_name}' not found in bucket '{bucket}'")
    
    # Generate cryptographically secure token
    token = secrets.token_urlsafe(32)  # 256 bits of entropy
    
    # Calculate expiration time
    expires_in = payload.get("expiresIn", 3600)
    if expires_in > 604800:  # 7 days max (GCS limit)
        raise HTTPException(status_code=400, detail="expiresIn cannot exceed 604800 seconds (7 days)")
    if expires_in < 1:
        raise HTTPException(status_code=400, detail="expiresIn must be at least 1 second")
    
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    
    # Create session record
    session = SignedUrlSession(
        id=token,
        bucket=bucket,
        object_name=db_obj.name,  # Use canonical name from database
        method=payload.get("method", "GET").upper(),
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(session)
    db.commit()
    
    # Build signed URL
    signed_url = f"http://localhost:8080/signed/{token}"
    
    return {
        "signedUrl": signed_url,
        "expiresAt": expires_at.isoformat().replace("+00:00", "Z")
    }


@router.get("/signed/{token}")
def access_signed_url(token: str, db: Session = Depends(get_db)):
    """
    Access object via signed URL token.
    
    URL format: http://localhost:8080/signed/{token}
    
    Validates:
    - Token exists
    - Token has not expired
    - Object still exists
    
    Returns object content with appropriate headers.
    """
    # Opportunistic cleanup of expired sessions (every ~100th request)
    import random
    if random.randint(1, 100) == 1:
        expired_count = db.query(SignedUrlSession).filter(
            SignedUrlSession.expires_at < datetime.now(timezone.utc)
        ).delete()
        if expired_count > 0:
            db.commit()
    
    # Look up session
    session = db.query(SignedUrlSession).filter(
        SignedUrlSession.id == token
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Signed URL not found. The URL may be invalid or has already expired."
        )
    
    # Check expiration (ensure both times are timezone-aware)
    now = datetime.now(timezone.utc)
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if now > expires_at:
        # Delete expired session
        db.delete(session)
        db.commit()
        raise HTTPException(
            status_code=403,
            detail=f"Signed URL has expired. Expired at: {expires_at.isoformat()}"
        )
    
    # Increment access count
    session.access_count += 1
    db.commit()
    
    # Fetch object from database
    db_obj = db.query(DBObject).filter(
        DBObject.bucket_id == session.bucket,
        DBObject.name == session.object_name,
        DBObject.deleted == False
    ).first()
    
    if not db_obj:
        raise HTTPException(
            status_code=404,
            detail=f"Object '{session.object_name}' no longer exists in bucket '{session.bucket}'"
        )
    
    # Read file from filesystem
    file_path = validate_object_path(session.bucket, db_obj.name)
    if not file_path.exists():
        raise HTTPException(
            status_code=500,
            detail="Object file not found on disk. Storage may be corrupted."
        )
    
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    # Ensure all values are strings (not bytes)
    content_type = str(db_obj.content_type or "application/octet-stream")
    md5_hash = str(db_obj.md5_hash or "")
    crc32c_hash = str(db_obj.crc32c_hash or "")
    
    # Calculate time remaining (use the timezone-aware expires_at from above)
    time_remaining = (expires_at - now).total_seconds()
    
    # Return object with GCS-compatible headers
    return Response(
        content=file_content,
        media_type=content_type,
        headers={
            "Content-Length": str(len(file_content)),
            "Content-Disposition": f'attachment; filename="{db_obj.name}"',
            "x-goog-hash": f"crc32c={crc32c_hash},md5={md5_hash}",
            "x-goog-generation": str(db_obj.generation),
            "x-goog-metageneration": str(db_obj.metageneration),
            "Cache-Control": f"private, max-age={int(time_remaining)}",
            "ETag": f'"{md5_hash}"'
        }
    )


# ============================================================================
# ACL (Access Control List) ENDPOINTS
# ============================================================================

@router.get("/storage/v1/b/{bucket}/o/{object:path}/acl")
def get_object_acl(bucket: str, object: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get object ACL"""
    _get_bucket_or_404(bucket, db)
    
    object_name = unquote(object)
    db_obj = db.query(DBObject).filter(
        DBObject.bucket_id == bucket,
        ((DBObject.name == object) | (DBObject.name == object_name)),
        DBObject.deleted == False
    ).first()
    
    if not db_obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    # Return current ACL or default
    acl_value = db_obj.acl or "private"
    
    return {
        "kind": "storage#objectAccessControl",
        "acl": acl_value
    }


@router.patch("/storage/v1/b/{bucket}/o/{object:path}/acl")
def update_object_acl(
    bucket: str,
    object: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update object ACL"""
    _get_bucket_or_404(bucket, db)
    
    object_name = unquote(object)
    db_obj = db.query(DBObject).filter(
        DBObject.bucket_id == bucket,
        ((DBObject.name == object) | (DBObject.name == object_name)),
        DBObject.deleted == False
    ).with_for_update().first()
    
    if not db_obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    # Update ACL
    new_acl = payload.get("acl")
    if new_acl:
        # Validate ACL value
        valid_acls = ["private", "public-read", "public-read-write", "authenticated-read"]
        if new_acl not in valid_acls:
            raise HTTPException(status_code=400, detail=f"Invalid ACL value. Must be one of: {valid_acls}")
        
        db_obj.acl = new_acl
        db.commit()
        db.refresh(db_obj)
    
    return {
        "kind": "storage#objectAccessControl",
        "acl": db_obj.acl
    }


@router.get("/storage/v1/b/{bucket}/defaultObjectAcl")
def get_bucket_default_acl(bucket: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get bucket default object ACL"""
    db_bucket = _get_bucket_or_404(bucket, db)
    
    acl_value = db_bucket.acl or "private"
    
    return {
        "kind": "storage#bucketAccessControl",
        "acl": acl_value
    }


@router.patch("/storage/v1/b/{bucket}/defaultObjectAcl")
def update_bucket_default_acl(
    bucket: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update bucket default object ACL"""
    db_bucket = _get_bucket_or_404(bucket, db)
    
    new_acl = payload.get("acl")
    if new_acl:
        valid_acls = ["private", "public-read", "public-read-write", "authenticated-read"]
        if new_acl not in valid_acls:
            raise HTTPException(status_code=400, detail=f"Invalid ACL value. Must be one of: {valid_acls}")
        
        db_bucket.acl = new_acl
        db.commit()
    
    return {
        "kind": "storage#bucketAccessControl",
        "acl": db_bucket.acl
    }

