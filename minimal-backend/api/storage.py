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


class BucketCreate(BaseModel):
    name: str
    location: Optional[str] = "US"
    storageClass: Optional[str] = "STANDARD"


@router.get("/storage/v1/b")
def list_buckets(project: Optional[str] = Query(None), db: Session = Depends(get_db)) -> Dict[str, Any]:
    query = db.query(DBBucket)
    if project:
        query = query.filter(DBBucket.project_id == project)
    buckets = query.all()
    
    items = []
    for b in buckets:
        items.append({
            "kind": "storage#bucket",
            "id": b.name,
            "name": b.name,
            "project": b.project_id,
            "location": b.location,
            "storageClass": b.storage_class,
            "timeCreated": b.created_at.isoformat().replace("+00:00", "Z") if b.created_at else _now(),
            "updated": b.updated_at.isoformat().replace("+00:00", "Z") if b.updated_at else _now(),
        })
    return {"kind": "storage#buckets", "items": items}


@router.post("/storage/v1/b")
def create_bucket(payload: BucketCreate, project: Optional[str] = Query(None), db: Session = Depends(get_db)) -> Dict[str, Any]:
    # Check if bucket already exists
    existing = db.query(DBBucket).filter(DBBucket.name == payload.name).first()
    if existing:
        return {
            "kind": "storage#bucket",
            "id": existing.name,
            "name": existing.name,
            "project": existing.project_id,
            "location": existing.location,
            "storageClass": existing.storage_class,
            "timeCreated": existing.created_at.isoformat().replace("+00:00", "Z") if existing.created_at else _now(),
            "updated": existing.updated_at.isoformat().replace("+00:00", "Z") if existing.updated_at else _now(),
        }
    
    now = datetime.now(timezone.utc)
    bucket = DBBucket(
        id=payload.name,
        name=payload.name,
        project_id=project,
        location=payload.location or "US",
        storage_class=payload.storageClass or "STANDARD",
        created_at=now,
        updated_at=now
    )
    db.add(bucket)
    db.commit()
    db.refresh(bucket)
    
    os.makedirs(f"{STORAGE_DIR}/{payload.name}", exist_ok=True)
    
    return {
        "kind": "storage#bucket",
        "id": bucket.name,
        "name": bucket.name,
        "project": bucket.project_id,
        "location": bucket.location,
        "storageClass": bucket.storage_class,
        "timeCreated": bucket.created_at.isoformat().replace("+00:00", "Z"),
        "updated": bucket.updated_at.isoformat().replace("+00:00", "Z"),
    }


@router.get("/storage/v1/b/{bucket}")
def get_bucket(bucket: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    db_bucket = db.query(DBBucket).filter(DBBucket.name == bucket).first()
    if not db_bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    return {
        "kind": "storage#bucket",
        "id": db_bucket.name,
        "name": db_bucket.name,
        "project": db_bucket.project_id,
        "location": db_bucket.location,
        "storageClass": db_bucket.storage_class,
        "timeCreated": db_bucket.created_at.isoformat().replace("+00:00", "Z") if db_bucket.created_at else _now(),
        "updated": db_bucket.updated_at.isoformat().replace("+00:00", "Z") if db_bucket.updated_at else _now(),
    }


@router.delete("/storage/v1/b/{bucket}", status_code=204)
def delete_bucket(bucket: str, db: Session = Depends(get_db)):
    db_bucket = db.query(DBBucket).filter(DBBucket.name == bucket).first()
    if not db_bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    
    # Delete all objects in bucket
    db.query(DBObject).filter(DBObject.bucket_id == bucket).delete()
    db.delete(db_bucket)
    db.commit()
    return Response(status_code=204)


@router.get("/storage/v1/b/{bucket}/storageLayout")
def get_storage_layout(bucket: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    db_bucket = db.query(DBBucket).filter(DBBucket.name == bucket).first()
    if not db_bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    return {"kind": "storage#storageLayout", "bucket": bucket, "hierarchicalNamespace": {"enabled": False}}


@router.get("/storage/v1/b/{bucket}/o")
def list_objects(bucket: str, prefix: Optional[str] = None, db: Session = Depends(get_db)) -> Dict[str, Any]:
    db_bucket = db.query(DBBucket).filter(DBBucket.name == bucket).first()
    if not db_bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    
    query = db.query(DBObject).filter(DBObject.bucket_id == bucket, DBObject.deleted == False)
    if prefix:
        query = query.filter(DBObject.name.startswith(prefix))
    objects = query.all()
    
    items = []
    for obj in objects:
        items.append({
            "kind": "storage#object",
            "id": f"{obj.bucket_id}/{obj.name}",
            "selfLink": f"http://localhost:8080/storage/v1/b/{obj.bucket_id}/o/{obj.name}",
            "bucket": obj.bucket_id,
            "name": obj.name,
            "size": str(obj.size),
            "contentType": obj.content_type,
            "timeCreated": obj.time_created.isoformat().replace("+00:00", "Z") if obj.time_created else _now(),
            "updated": obj.updated_at.isoformat().replace("+00:00", "Z") if obj.updated_at else _now(),
            "generation": str(obj.generation),
            "md5Hash": obj.md5_hash,
            "crc32c": obj.crc32c_hash,
            "etag": f'"{obj.md5_hash}"',
        })
    return {"kind": "storage#objects", "items": items}


@router.get("/storage/v1/b/{bucket}/o/{object:path}")
@router.get("/download/storage/v1/b/{bucket}/o/{object:path}")
def get_object(bucket: str, object: str, alt: Optional[str] = Query(None), db: Session = Depends(get_db)):
    db_bucket = db.query(DBBucket).filter(DBBucket.name == bucket).first()
    if not db_bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    
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
                
            headers = {
                "Content-Length": str(len(file_content)),
                "x-goog-hash": f"crc32c={db_obj.crc32c_hash},md5={db_obj.md5_hash}",
                "x-goog-generation": str(db_obj.generation),
                "x-goog-metageneration": str(db_obj.metageneration),
                "x-goog-stored-content-length": str(len(file_content)),
                "ETag": f'"{db_obj.md5_hash}"',
                "Content-Disposition": f'attachment; filename="{db_obj.name}"'
            }
            
            return Response(
                content=file_content, 
                media_type=db_obj.content_type or "application/octet-stream",
                headers=headers
            )
            
        raise HTTPException(status_code=404, detail="Object file not found")
    
    return {
        "kind": "storage#object",
        "id": f"{db_obj.bucket_id}/{db_obj.name}",
        "selfLink": f"http://localhost:8080/storage/v1/b/{db_obj.bucket_id}/o/{db_obj.name}",
        "bucket": db_obj.bucket_id,
        "name": db_obj.name,
        "size": str(db_obj.size),
        "contentType": db_obj.content_type,
        "timeCreated": db_obj.time_created.isoformat().replace("+00:00", "Z") if db_obj.time_created else _now(),
        "updated": db_obj.updated_at.isoformat().replace("+00:00", "Z") if db_obj.updated_at else _now(),
        "generation": str(db_obj.generation),
        "md5Hash": db_obj.md5_hash,
        "crc32c": db_obj.crc32c_hash,
        "etag": f'"{db_obj.md5_hash}"',
    }


@router.delete("/storage/v1/b/{bucket}/o/{object:path}", status_code=204)
def delete_object(bucket: str, object: str, db: Session = Depends(get_db)):
    db_bucket = db.query(DBBucket).filter(DBBucket.name == bucket).first()
    if not db_bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    
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
    db_bucket = db.query(DBBucket).filter(DBBucket.name == bucket).first()
    if not db_bucket:
        raise HTTPException(status_code=404, detail="Bucket not found")
    
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
        existing_obj.md5_hash = md5_hash
        existing_obj.crc32c_hash = crc32c
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
            content_type="application/octet-stream",
            md5_hash=md5_hash,
            crc32c_hash=crc32c,
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
