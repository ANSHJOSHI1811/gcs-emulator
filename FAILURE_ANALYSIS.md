# 🚨 GCP Stimulator - Failure Point Analysis

**Document Version:** 1.0  
**Date:** February 5, 2026  
**Status:** Critical Review

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Cloud Storage Failures](#cloud-storage-failures)
3. [Compute Engine Failures](#compute-engine-failures)
4. [VPC Network Failures](#vpc-network-failures)
5. [Database Failures](#database-failures)
6. [Docker Integration Failures](#docker-integration-failures)
7. [File System Failures](#file-system-failures)
8. [API Compatibility Failures](#api-compatibility-failures)
9. [Race Conditions](#race-conditions)
10. [Resource Exhaustion](#resource-exhaustion)
11. [Priority Fix Recommendations](#priority-fix-recommendations)

---

## 📊 Executive Summary

### Critical Failures (Must Fix Now)
- ✅ **KNOWN:** Storage download bytes vs strings bug (documented in STORAGE_DOWNLOAD_BUG_AND_VERSIONING.md)
- 🔴 **NEW:** No error handling for Docker daemon failures
- 🔴 **NEW:** Race conditions in concurrent uploads
- 🔴 **NEW:** No disk space checks before file writes
- 🔴 **NEW:** Missing database transactions for atomic operations

### High Priority Failures (Fix Soon)
- 🟠 No cleanup of orphaned Docker containers
- 🟠 No file path validation (directory traversal vulnerability)
- 🟠 No limits on file uploads (can fill disk)
- 🟠 Missing database constraints and indexes
- 🟠 Container name collisions not handled

### Medium Priority Issues
- 🟡 No versioning support (planned feature)
- 🟡 No lifecycle policies for old objects
- 🟡 No metrics or monitoring
- 🟡 Hardcoded credentials in code

---

## 💾 Cloud Storage Failures

### 1. ✅ Download Bug (Already Documented)

**Location:** `minimal-backend/api/storage.py` - Download endpoint

**Issue:** bytes vs strings mismatch in response headers

**Status:** Documented in STORAGE_DOWNLOAD_BUG_AND_VERSIONING.md

**Impact:** gcloud storage cp/cat commands fail

---

### 2. 🔴 Race Condition in Concurrent Uploads

**Location:** `minimal-backend/api/storage.py` - Upload endpoint

**Code:**
```python
@router.post("/upload/storage/v1/b/{bucket}/o")
async def upload_object(bucket: str, request: Request, name: str = Query(None)):
    # ... parse content ...
    
    # ❌ NO LOCKING - Multiple uploads can overwrite each other
    file_path = f"/tmp/gcs-storage/{bucket}/{object_name}"
    with open(file_path, "wb") as f:
        f.write(content)
    
    # ❌ If two requests write simultaneously:
    # 1. Both open same file
    # 2. Both write content
    # 3. Database gets two records with same ID
    # 4. File content is corrupted or incomplete
    
    obj = DBObject(
        id=f"{bucket}/{object_name}",  # ❌ Duplicate key error!
        ...
    )
    db.add(obj)
    db.commit()  # ❌ Will fail or create inconsistent state
```

**Failure Scenario:**
```bash
# Terminal 1 and 2 run simultaneously:
gcloud storage cp file1.txt gs://bucket/object.txt &
gcloud storage cp file2.txt gs://bucket/object.txt &

# Result:
# - File contains mixed content from both uploads
# - Database may have duplicate key error
# - One upload succeeds, other fails silently
```

**Fix:**
```python
from sqlalchemy import select
from fastapi import BackgroundTasks

@router.post("/upload/storage/v1/b/{bucket}/o")
async def upload_object(bucket: str, request: Request, name: str = Query(None), db: Session = Depends(get_db)):
    content = await request.body()
    object_name = name or extract_name_from_body(content)
    
    # Use database row locking to prevent concurrent updates
    with db.begin():
        # Lock the row if it exists
        existing = db.execute(
            select(DBObject)
            .where(DBObject.id == f"{bucket}/{object_name}")
            .with_for_update()
        ).first()
        
        # Now safe to write file
        file_path = f"/tmp/gcs-storage/{bucket}/{object_name}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Use atomic write with temp file
        temp_path = f"{file_path}.tmp.{uuid.uuid4()}"
        with open(temp_path, "wb") as f:
            f.write(content)
        os.rename(temp_path, file_path)  # Atomic on Unix
        
        # Update or create database record
        if existing:
            existing.size = len(content)
            existing.updated_at = datetime.utcnow()
        else:
            obj = DBObject(id=f"{bucket}/{object_name}", ...)
            db.add(obj)
```

---

### 3. 🔴 No Disk Space Checks

**Location:** `minimal-backend/api/storage.py` - Upload endpoint

**Issue:** No validation before writing large files

**Code:**
```python
@router.post("/upload/storage/v1/b/{bucket}/o")
async def upload_object(bucket: str, request: Request):
    content = await request.body()  # ❌ Can be gigabytes!
    
    # ❌ No check if disk has space
    with open(file_path, "wb") as f:
        f.write(content)  # ❌ Will crash if disk full
```

**Failure Scenario:**
```bash
# Upload 50GB file when only 10GB disk space available
dd if=/dev/zero of=huge.bin bs=1G count=50
gcloud storage cp huge.bin gs://bucket/

# Result:
# - Disk fills up completely
# - OS becomes unstable
# - All services fail
# - Database can't write logs
```

**Fix:**
```python
import shutil

@router.post("/upload/storage/v1/b/{bucket}/o")
async def upload_object(bucket: str, request: Request):
    content = await request.body()
    
    # Check available disk space
    stat = shutil.disk_usage("/tmp")
    available_gb = stat.free / (1024**3)
    content_gb = len(content) / (1024**3)
    
    MIN_FREE_SPACE_GB = 5  # Keep 5GB buffer
    
    if content_gb + MIN_FREE_SPACE_GB > available_gb:
        raise HTTPException(
            status_code=507,  # Insufficient Storage
            detail=f"Not enough disk space. Need {content_gb:.2f}GB, have {available_gb:.2f}GB"
        )
    
    # Now safe to write
    file_path = f"/tmp/gcs-storage/{bucket}/{object_name}"
    with open(file_path, "wb") as f:
        f.write(content)
```

---

### 4. 🔴 Directory Traversal Vulnerability

**Location:** `minimal-backend/api/storage.py` - Upload/Download endpoints

**Issue:** No validation of object names allows path traversal

**Code:**
```python
@router.post("/upload/storage/v1/b/{bucket}/o")
async def upload_object(bucket: str, name: str = Query(None)):
    object_name = name  # ❌ Not validated!
    
    file_path = f"/tmp/gcs-storage/{bucket}/{object_name}"
    # ❌ If object_name = "../../etc/passwd", this writes to /etc/passwd!
```

**Failure Scenario:**
```bash
# Attacker uploads malicious object name
gcloud storage cp malware.sh gs://bucket/../../../usr/bin/evil.sh

# Result:
# - Writes file outside storage directory
# - Can overwrite system files
# - Can read sensitive files on download
```

**Fix:**
```python
import os.path

def validate_object_name(name: str) -> str:
    """Validate and sanitize object name"""
    if not name or name.strip() == "":
        raise HTTPException(status_code=400, detail="Object name cannot be empty")
    
    # Reject path traversal attempts
    if ".." in name or name.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid object name")
    
    # Normalize path to prevent tricks
    normalized = os.path.normpath(name)
    if normalized != name or normalized.startswith(".."):
        raise HTTPException(status_code=400, detail="Invalid object name")
    
    return name

@router.post("/upload/storage/v1/b/{bucket}/o")
async def upload_object(bucket: str, name: str = Query(None)):
    object_name = validate_object_name(name)  # ✅ Validated
    
    # Build path safely
    base_dir = os.path.abspath("/tmp/gcs-storage")
    file_path = os.path.abspath(os.path.join(base_dir, bucket, object_name))
    
    # Ensure path is still within base directory
    if not file_path.startswith(base_dir):
        raise HTTPException(status_code=400, detail="Invalid object name")
    
    # Now safe to write
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)
```

---

### 5. 🟠 No Cleanup of Deleted Objects

**Location:** `minimal-backend/api/storage.py` - Delete endpoint

**Issue:** Files remain on disk after deletion

**Code:**
```python
@router.delete("/storage/v1/b/{bucket}/o/{object:path}")
def delete_object(bucket: str, object: str, db: Session = Depends(get_db)):
    obj = db.query(DBObject).filter_by(bucket_id=bucket, name=object).first()
    
    # ❌ Only marks as deleted in database
    obj.deleted = True
    db.commit()
    
    # ❌ File still exists on disk at /tmp/gcs-storage/{bucket}/{object}
    # Disk space never freed!
```

**Impact:**
- Disk fills up over time
- No way to reclaim space
- Deleted objects still readable if you know the path

**Fix:**
```python
import os

@router.delete("/storage/v1/b/{bucket}/o/{object:path}")
def delete_object(bucket: str, object: str, db: Session = Depends(get_db)):
    obj = db.query(DBObject).filter_by(bucket_id=bucket, name=object).first()
    
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    # Delete from file system
    if obj.file_path and os.path.exists(obj.file_path):
        try:
            os.remove(obj.file_path)
        except Exception as e:
            print(f"Warning: Failed to delete file {obj.file_path}: {e}")
    
    # Delete from database
    db.delete(obj)
    db.commit()
    
    return Response(status_code=204)  # No Content
```

---

### 6. 🟠 No Upload Size Limits

**Location:** `minimal-backend/api/storage.py` - Upload endpoint

**Issue:** Can upload unlimited size files

**Code:**
```python
@router.post("/upload/storage/v1/b/{bucket}/o")
async def upload_object(bucket: str, request: Request):
    content = await request.body()  # ❌ No size limit!
```

**Failure Scenario:**
```bash
# Upload 100GB file
dd if=/dev/zero of=huge.bin bs=1G count=100
gcloud storage cp huge.bin gs://bucket/

# Result:
# - API server runs out of memory trying to read entire body
# - Server crashes
# - All other requests fail
```

**Fix:**
```python
from fastapi import Request, HTTPException

MAX_UPLOAD_SIZE = 5 * 1024 * 1024 * 1024  # 5GB limit

@router.post("/upload/storage/v1/b/{bucket}/o")
async def upload_object(bucket: str, request: Request):
    # Check Content-Length header
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,  # Payload Too Large
            detail=f"File too large. Max size: {MAX_UPLOAD_SIZE / (1024**3):.1f}GB"
        )
    
    # Stream upload instead of loading entire body
    file_path = f"/tmp/gcs-storage/{bucket}/{object_name}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    size = 0
    with open(file_path, "wb") as f:
        async for chunk in request.stream():
            size += len(chunk)
            if size > MAX_UPLOAD_SIZE:
                f.close()
                os.remove(file_path)  # Clean up partial file
                raise HTTPException(status_code=413, detail="File too large")
            f.write(chunk)
```

---

## 💻 Compute Engine Failures

### 7. 🔴 No Docker Daemon Error Handling

**Location:** `minimal-backend/docker_manager.py` - All functions

**Issue:** No handling if Docker daemon is down

**Code:**
```python
import docker

client = docker.from_env()  # ❌ Crashes if Docker not running

def create_container(name: str, network: str = "gcp-default"):
    container = client.containers.run(...)  # ❌ No error handling
    return {"container_id": container.id}
```

**Failure Scenario:**
```bash
# Docker daemon crashes or is stopped
sudo systemctl stop docker

# Try to create VM
gcloud compute instances create my-vm --zone=us-central1-a

# Result:
# - FastAPI crashes with DockerException
# - HTTP 500 returned to client
# - No meaningful error message
# - API becomes unusable
```

**Fix:**
```python
import docker
from docker.errors import DockerException
from typing import Optional, Dict

class DockerManager:
    def __init__(self):
        self._client: Optional[docker.DockerClient] = None
        self._connect()
    
    def _connect(self):
        """Connect to Docker daemon with retry logic"""
        try:
            self._client = docker.from_env()
            self._client.ping()  # Test connection
            print("✅ Connected to Docker daemon")
        except DockerException as e:
            print(f"❌ Failed to connect to Docker: {e}")
            self._client = None
    
    def is_available(self) -> bool:
        """Check if Docker is available"""
        if not self._client:
            self._connect()
        try:
            if self._client:
                self._client.ping()
                return True
        except:
            self._client = None
        return False
    
    def create_container(self, name: str, network: str = "gcp-default") -> Dict:
        """Create container with error handling"""
        if not self.is_available():
            raise HTTPException(
                status_code=503,  # Service Unavailable
                detail="Docker daemon is not available. Cannot create VM instances."
            )
        
        try:
            container = self._client.containers.run(
                image="ubuntu:22.04",
                name=f"gcp-vm-{name}",
                network=network,
                detach=True
            )
            return {"container_id": container.id, "status": "created"}
        
        except docker.errors.ImageNotFound:
            raise HTTPException(
                status_code=400,
                detail="Container image not found. Please pull ubuntu:22.04 first."
            )
        
        except docker.errors.APIError as e:
            if "Conflict" in str(e):
                raise HTTPException(
                    status_code=409,
                    detail=f"Container with name '{name}' already exists"
                )
            raise HTTPException(status_code=500, detail=f"Docker error: {str(e)}")
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create container: {str(e)}")

docker_manager = DockerManager()
```

---

### 8. 🔴 Container Name Collisions

**Location:** `minimal-backend/docker_manager.py` - create_container()

**Issue:** No handling of duplicate container names

**Code:**
```python
def create_container(name: str, network: str = "gcp-default"):
    container_name = f"gcp-vm-{name}"
    
    # ❌ If container already exists, Docker raises error
    container = client.containers.run(
        image="ubuntu:22.04",
        name=container_name,  # ❌ Fails if name already used
        ...
    )
```

**Failure Scenario:**
```bash
# Create instance
gcloud compute instances create my-vm

# Delete from database but container still exists
DELETE FROM instances WHERE name='my-vm';

# Try to create again
gcloud compute instances create my-vm

# Result:
# - Docker error: "Conflict. The container name '/gcp-vm-my-vm' is already in use"
# - API returns 500 error
# - Instance not created
```

**Fix:**
```python
def create_container(name: str, network: str = "gcp-default"):
    container_name = f"gcp-vm-{name}"
    
    # Check if container already exists
    try:
        existing = client.containers.get(container_name)
        
        # If exists, decide what to do:
        if existing.status == "exited":
            # Reuse stopped container
            existing.start()
            existing.reload()
            return {
                "container_id": existing.id,
                "container_name": container_name,
                "internal_ip": get_container_ip(existing, network),
                "reused": True
            }
        else:
            # Container running but not in database (orphaned)
            raise HTTPException(
                status_code=409,
                detail=f"Container '{container_name}' already exists. Delete it first."
            )
    
    except docker.errors.NotFound:
        # Container doesn't exist, create new one
        pass
    
    # Create new container
    container = client.containers.run(...)
    return {"container_id": container.id, "reused": False}
```

---

### 9. 🟠 Orphaned Containers Never Cleaned Up

**Location:** `minimal-backend/api/compute.py` - Delete instance endpoint

**Issue:** Database deletion doesn't clean up Docker container

**Code:**
```python
@router.delete("/compute/v1/projects/{project}/zones/{zone}/instances/{instance}")
def delete_instance(project: str, zone: str, instance: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter_by(name=instance).first()
    
    # ❌ Only deletes from database
    db.delete(inst)
    db.commit()
    
    # ❌ Docker container still running!
    # Result: Orphaned containers accumulate forever
```

**Impact:**
- Containers run forever consuming resources
- `docker ps` shows hundreds of orphaned containers
- Eventually exhaust system resources

**Fix:**
```python
from docker_manager import delete_container

@router.delete("/compute/v1/projects/{project}/zones/{zone}/instances/{instance}")
def delete_instance(project: str, zone: str, instance: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter_by(name=instance).first()
    
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Delete Docker container first
    if inst.container_id:
        try:
            delete_container(inst.container_id)
        except Exception as e:
            print(f"Warning: Failed to delete container {inst.container_id}: {e}")
    
    # Then delete from database
    db.delete(inst)
    db.commit()
    
    return Response(status_code=204)
```

---

### 10. 🟠 No Container Status Sync

**Location:** `minimal-backend/api/compute.py` - Get/List instances

**Issue:** Database status doesn't reflect actual container state

**Code:**
```python
@router.get("/compute/v1/projects/{project}/zones/{zone}/instances/{instance}")
def get_instance(project: str, zone: str, instance: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter_by(name=instance).first()
    
    # ❌ Returns database status, not real container status
    return {
        "name": inst.name,
        "status": inst.status  # ❌ May be "RUNNING" even if container crashed
    }
```

**Failure Scenario:**
```bash
# Container crashes outside of API control
docker stop gcp-vm-my-vm

# Check status via gcloud
gcloud compute instances describe my-vm

# Result:
# - API says "status: RUNNING"
# - Actually stopped
# - Misleading information
```

**Fix:**
```python
from docker_manager import get_container_status

@router.get("/compute/v1/projects/{project}/zones/{zone}/instances/{instance}")
def get_instance(project: str, zone: str, instance: str, db: Session = Depends(get_db)):
    inst = db.query(Instance).filter_by(name=instance).first()
    
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    # Get real-time status from Docker
    real_status = "UNKNOWN"
    if inst.container_id:
        docker_status = get_container_status(inst.container_id)
        if docker_status == "running":
            real_status = "RUNNING"
        elif docker_status == "exited":
            real_status = "TERMINATED"
        elif docker_status is None:
            real_status = "DELETED"  # Container doesn't exist
    
    # Update database if status changed
    if real_status != inst.status:
        inst.status = real_status
        db.commit()
    
    return {
        "name": inst.name,
        "status": real_status,
        "machineType": inst.machine_type,
        "zone": inst.zone
    }
```

---

## 🌐 VPC Network Failures

### 11. 🔴 Network Deletion Doesn't Check for Attached Instances

**Location:** `minimal-backend/api/vpc.py` - Delete network endpoint

**Issue:** Can delete network while instances still attached

**Failure Scenario:**
```bash
# Create network and instances
gcloud compute networks create my-net
gcloud compute instances create vm1 --network=my-net
gcloud compute instances create vm2 --network=my-net

# Delete network
gcloud compute networks delete my-net

# Result:
# - Docker network deleted
# - Containers lose network connectivity
# - Database still references deleted network
# - Instances show "network not found"
```

**Fix:**
```python
@router.delete("/compute/v1/projects/{project}/global/networks/{network}")
def delete_network(project: str, network: str, db: Session = Depends(get_db)):
    net = db.query(Network).filter_by(project_id=project, name=network).first()
    
    if not net:
        raise HTTPException(status_code=404, detail="Network not found")
    
    # Check for attached instances
    instances_count = db.query(Instance).filter(
        Instance.network_url.like(f"%/{network}")
    ).count()
    
    if instances_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete network '{network}'. {instances_count} instances are still attached."
        )
    
    # Safe to delete
    if net.docker_network_name:
        try:
            docker_net = client.networks.get(net.docker_network_name)
            docker_net.remove()
        except Exception as e:
            print(f"Warning: Failed to delete Docker network: {e}")
    
    db.delete(net)
    db.commit()
    
    return Response(status_code=204)
```

---

## 🗄️ Database Failures

### 12. 🔴 Missing Database Transactions

**Location:** Multiple endpoints across all APIs

**Issue:** Operations not atomic, leading to inconsistent state

**Example:**
```python
@router.post("/compute/v1/projects/{project}/zones/{zone}/instances")
def create_instance(project: str, zone: str, payload: dict, db: Session = Depends(get_db)):
    # Step 1: Create Docker container
    result = create_container(name, network)  # ✅ Succeeds
    
    # Step 2: Save to database
    inst = Instance(
        name=name,
        container_id=result["container_id"],
        ...
    )
    db.add(inst)
    db.commit()  # ❌ Fails (e.g., database connection lost)
    
    # PROBLEM:
    # - Container created and running
    # - Database record not created
    # - Orphaned container
    # - No way to track it
```

**Fix:**
```python
@router.post("/compute/v1/projects/{project}/zones/{zone}/instances")
def create_instance(project: str, zone: str, payload: dict, db: Session = Depends(get_db)):
    container_id = None
    
    try:
        # Use database transaction
        with db.begin():
            # Create Docker container
            result = create_container(name, network)
            container_id = result["container_id"]
            
            # Save to database (in same transaction context)
            inst = Instance(
                name=name,
                container_id=container_id,
                ...
            )
            db.add(inst)
            # commit happens automatically if no exception
        
        return {"status": "success", "name": name}
    
    except Exception as e:
        # Rollback: cleanup container if database failed
        if container_id:
            try:
                delete_container(container_id)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))
```

---

### 13. 🟠 Missing Database Indexes

**Location:** `minimal-backend/database.py` - All models

**Issue:** Slow queries as data grows

**Current Schema:**
```python
class Instance(Base):
    __tablename__ = "instances"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # ❌ No index
    project_id = Column(String, nullable=False)  # ❌ No index
    zone = Column(String, nullable=False)  # ❌ No index
```

**Impact:**
- List instances query becomes slow with 1000+ instances
- Finding by name requires full table scan
- Frontend becomes sluggish

**Fix:**
```python
class Instance(Base):
    __tablename__ = "instances"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)  # ✅ Index
    project_id = Column(String, nullable=False, index=True)  # ✅ Index
    zone = Column(String, nullable=False, index=True)  # ✅ Index
    status = Column(String, default="RUNNING", index=True)  # ✅ Index
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_project_zone', 'project_id', 'zone'),
        Index('idx_project_name', 'project_id', 'name'),
    )
```

---

### 14. 🟠 No Foreign Key Constraints

**Location:** `minimal-backend/database.py` - Object model

**Issue:** Can create objects in non-existent buckets

**Current:**
```python
class Object(Base):
    __tablename__ = "objects"
    
    id = Column(String, primary_key=True)
    bucket_id = Column(String, nullable=False)  # ❌ No foreign key constraint
```

**Failure:**
```python
# Create object in non-existent bucket
obj = Object(
    id="fake-bucket/file.txt",
    bucket_id="fake-bucket",  # ❌ Bucket doesn't exist!
    ...
)
db.add(obj)
db.commit()  # ✅ Succeeds! But bucket doesn't exist.
```

**Fix:**
```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Object(Base):
    __tablename__ = "objects"
    
    id = Column(String, primary_key=True)
    bucket_id = Column(String, ForeignKey('buckets.id', ondelete='CASCADE'), nullable=False)
    
    # Relationship for easy access
    bucket = relationship("Bucket", back_populates="objects")

class Bucket(Base):
    __tablename__ = "buckets"
    
    id = Column(String, primary_key=True)
    # ...
    
    # Relationship
    objects = relationship("Object", back_populates="bucket", cascade="all, delete-orphan")
```

---

## 📁 File System Failures

### 15. 🔴 No Atomic File Writes

**Location:** `minimal-backend/api/storage.py` - Upload endpoint

**Issue:** File corruption if write interrupted

**Code:**
```python
file_path = f"/tmp/gcs-storage/{bucket}/{object_name}"
with open(file_path, "wb") as f:
    f.write(content)  # ❌ If process killed mid-write, file corrupted
```

**Failure Scenario:**
```bash
# Upload large file
gcloud storage cp large.bin gs://bucket/ &

# Kill process mid-upload
kill -9 $PID

# Result:
# - File partially written
# - Database says upload complete
# - File is corrupted (incomplete)
# - Download gives wrong content
```

**Fix:**
```python
import os
import tempfile

file_path = f"/tmp/gcs-storage/{bucket}/{object_name}"
os.makedirs(os.path.dirname(file_path), exist_ok=True)

# Write to temporary file first
temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(file_path))
try:
    with os.fdopen(temp_fd, 'wb') as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())  # Force write to disk
    
    # Atomic rename (on Unix systems)
    os.rename(temp_path, file_path)
except:
    # Cleanup on error
    if os.path.exists(temp_path):
        os.remove(temp_path)
    raise
```

---

### 16. 🟠 No Cleanup of Failed Uploads

**Location:** `minimal-backend/api/storage.py` - Upload endpoint

**Issue:** Partial files left on disk

**Failure Scenario:**
```python
# Upload fails after file written but before database commit
file_path = f"/tmp/gcs-storage/{bucket}/{object_name}"
with open(file_path, "wb") as f:
    f.write(content)  # ✅ File written

obj = DBObject(...)
db.add(obj)
db.commit()  # ❌ Fails due to database error

# Result:
# - File exists on disk
# - No database record
# - Orphaned file never deleted
# - Disk space wasted
```

**Fix:**
```python
@router.post("/upload/storage/v1/b/{bucket}/o")
async def upload_object(bucket: str, request: Request, db: Session = Depends(get_db)):
    file_path = None
    
    try:
        content = await request.body()
        object_name = extract_name(...)
        
        file_path = f"/tmp/gcs-storage/{bucket}/{object_name}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Save to database
        obj = DBObject(...)
        db.add(obj)
        db.commit()
        
        return {"status": "success"}
    
    except Exception as e:
        # Cleanup file on any error
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))
```

---

## ⚡ Race Conditions

### 17. 🔴 Concurrent Bucket Creation

**Location:** `minimal-backend/api/storage.py` - Create bucket

**Issue:** Multiple creates can succeed simultaneously

**Code:**
```python
@router.post("/storage/v1/b")
def create_bucket(payload: dict, db: Session = Depends(get_db)):
    bucket_name = payload["name"]
    
    # ❌ Race condition window here
    existing = db.query(Bucket).filter_by(name=bucket_name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Bucket exists")
    
    # ❌ Two requests can both pass the check above
    bucket = Bucket(id=bucket_name, name=bucket_name)
    db.add(bucket)
    db.commit()  # ❌ One succeeds, one gets duplicate key error
```

**Fix:**
```python
from sqlalchemy.exc import IntegrityError

@router.post("/storage/v1/b")
def create_bucket(payload: dict, db: Session = Depends(get_db)):
    bucket_name = payload["name"]
    
    try:
        # Let database enforce uniqueness
        bucket = Bucket(
            id=bucket_name,
            name=bucket_name,
            project_id=payload.get("project")
        )
        db.add(bucket)
        db.commit()
        
        # Create directory after successful DB insert
        bucket_dir = f"/tmp/gcs-storage/{bucket_name}"
        os.makedirs(bucket_dir, exist_ok=True)
        
        return {"kind": "storage#bucket", "name": bucket_name}
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Bucket already exists")
```

---

## 📊 Resource Exhaustion

### 18. 🔴 No Limits on Container Count

**Location:** `minimal-backend/api/compute.py` - Create instance

**Issue:** Can create unlimited containers

**Failure Scenario:**
```bash
# Create 1000 containers
for i in {1..1000}; do
    gcloud compute instances create vm-$i --zone=us-central1-a &
done

# Result:
# - System runs out of memory
# - Docker daemon crashes
# - All containers become unstable
```

**Fix:**
```python
MAX_INSTANCES_PER_PROJECT = 100

@router.post("/compute/v1/projects/{project}/zones/{zone}/instances")
def create_instance(project: str, zone: str, payload: dict, db: Session = Depends(get_db)):
    # Count existing instances
    count = db.query(Instance).filter_by(
        project_id=project,
        status="RUNNING"
    ).count()
    
    if count >= MAX_INSTANCES_PER_PROJECT:
        raise HTTPException(
            status_code=429,  # Too Many Requests
            detail=f"Project quota exceeded. Max {MAX_INSTANCES_PER_PROJECT} instances per project."
        )
    
    # Proceed with creation
    ...
```

---

## 🎯 Priority Fix Recommendations

### 🔴 Critical - Fix Immediately

1. **Storage Download Bug** ✅ Already documented - Implement type validation
2. **Docker Daemon Error Handling** - Add connection retry and meaningful errors
3. **Race Condition in Uploads** - Add database row locking
4. **Directory Traversal** - Validate and sanitize all file paths
5. **Disk Space Checks** - Validate before writes
6. **Database Transactions** - Wrap multi-step operations

### 🟠 High Priority - Fix This Week

7. **Orphaned Containers** - Add cleanup on delete
8. **Container Name Collisions** - Check before create
9. **Network Deletion** - Validate no attached instances
10. **Upload Size Limits** - Enforce max file size
11. **Atomic File Writes** - Use temp file + rename pattern

### 🟡 Medium Priority - Fix This Month

12. **Database Indexes** - Add indexes for performance
13. **Foreign Key Constraints** - Enforce referential integrity
14. **Container Status Sync** - Real-time status from Docker
15. **Resource Limits** - Add quotas per project
16. **Cleanup Failed Uploads** - Remove orphaned files

---

## 📝 Implementation Checklist

- [ ] Fix bytes vs strings in storage download
- [ ] Add Docker daemon connection handling
- [ ] Implement row locking for concurrent uploads
- [ ] Add path traversal validation
- [ ] Check disk space before uploads
- [ ] Wrap operations in database transactions
- [ ] Clean up Docker containers on instance delete
- [ ] Handle container name collisions
- [ ] Validate network deletion constraints
- [ ] Add upload size limits
- [ ] Implement atomic file writes
- [ ] Add database indexes
- [ ] Add foreign key constraints
- [ ] Sync container status with database
- [ ] Add resource quotas
- [ ] Clean up failed uploads

---

**Document Maintained By:** GCP Stimulator Team  
**Last Review:** February 5, 2026  
**Next Review:** February 12, 2026
