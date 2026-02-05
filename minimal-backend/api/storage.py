import base64
import hashlib
import json
import struct
import zlib
import uuid
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Request, Response, status, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db, Bucket as DBBucket, Object as DBObject

router = APIRouter()

STORAGE_DIR = "/tmp/gcs-storage"


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


@router.get("/storage/v1/b/{bucket}/o/{object:path}")
@router.get("/download/storage/v1/b/{bucket}/o/{object:path}")
def get_object(bucket: str, object: str, alt: Optional[str] = Query(None), db: Session = Depends(get_db)):
    # Validate bucket exists
    _get_bucket_or_404(bucket, db)
    
    raw_name = unquote(object)
    db_obj = db.query(DBObject).filter(
        DBObject.bucket_id == bucket,
        ((DBObject.name == object) | (DBObject.name == raw_name)),
        DBObject.deleted == False
    ).first()
    
    if not db_obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    if alt == "media":
        file_path = f"{STORAGE_DIR}/{bucket}/{db_obj.name}"
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
    
    file_path = f"{STORAGE_DIR}/{bucket}/{object_name}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)
    
    with open(file_path, "rb") as f:
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
    
    # Check if object exists
    existing_obj = db.query(DBObject).filter(
        DBObject.bucket_id == bucket,
        DBObject.name == object_name,
        DBObject.deleted == False
    ).first()
    
    if existing_obj:
        # Update existing object
        existing_obj.size = len(file_content)
        existing_obj.content_type = content_type  # String
        existing_obj.md5_hash = md5_hash  # String
        existing_obj.crc32c_hash = crc32c  # String
        existing_obj.file_path = file_path
        existing_obj.updated_at = now
        existing_obj.generation += 1
        db.commit()
        db.refresh(existing_obj)
        db_obj = existing_obj
    else:
        # Create new object
        db_obj = DBObject(
            id=f"{bucket}/{object_name}",
            bucket_id=bucket,
            name=object_name,
            size=len(file_content),
            content_type=content_type,  # String
            md5_hash=md5_hash,  # String
            crc32c_hash=crc32c,  # String
            file_path=file_path,
            generation=1,
            metageneration=1,
            time_created=now,
            created_at=now,
            updated_at=now,
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
