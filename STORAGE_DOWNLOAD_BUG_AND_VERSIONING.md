# Storage Download Bug & Versioning Implementation Guide

**Document Version:** 1.0  
**Date:** February 5, 2026  
**Status:** Bug Identified - Solution Proposed

---

## 📋 Table of Contents

1. [Problem Overview](#problem-overview)
2. [Failing Commands](#failing-commands)
3. [Root Cause Analysis](#root-cause-analysis)
4. [Immediate Fix Solution](#immediate-fix-solution)
5. [Object Versioning Feature](#object-versioning-feature)
6. [Implementation Challenges](#implementation-challenges)

---

## 🐛 Problem Overview

### What's Happening

When trying to download objects from Cloud Storage using `gcloud storage` commands, the operation fails with a Python `TypeError` instead of successfully retrieving the file.

### Error Message

```bash
ERROR: endswith first arg must be bytes or a tuple of bytes, not str
```

### Impact

- ❌ `gcloud storage cp` (download) fails
- ❌ `gcloud storage cat` (read) crashes
- ✅ Upload operations work fine
- ✅ REST API calls work fine
- ✅ Frontend UI works fine

### Why It's NOT Authentication

**If it were authentication, you'd see:**
- `401 Unauthorized`
- `403 Permission Denied`
- `Invalid credentials`

**Instead, you see:**
- `TypeError` - A Python programming error
- This happens AFTER the request succeeds
- It's a data type mismatch in the response

---

## 💻 Failing Commands

### Command 1: Download File (cp)

```bash
source /home/ubuntu/gcs-stimulator/.env-gcloud && \
rm -f /tmp/downloaded-file.txt && \
gcloud storage cp gs://test-bucket-final/test-dl.txt /tmp/downloaded-file.txt \
  --project=test-project 2>&1
```

**Output:**
```
Copying gs://test-bucket-final/test-dl.txt to file:///tmp/downloaded-file.txt
ERROR: endswith first arg must be bytes or a tuple of bytes, not str
  Completed files 0/1 | 0B/39.0B
```

**Expected Behavior:**
- Should download the file
- Should display: `Copying complete`
- Exit code: 0

**Actual Behavior:**
- Request reaches backend
- Backend returns response
- gcloud CLI crashes while processing response
- File not downloaded
- Exit code: 1

---

### Command 2: Display File Contents (cat)

```bash
source /home/ubuntu/gcs-stimulator/.env-gcloud && \
gcloud storage cat gs://test-bucket-final/test-dl.txt 2>&1
```

**Output:**
```
ERROR: gcloud crashed (TypeError): endswith first arg must be bytes or a tuple of bytes, not str

If you would like to report this issue, please run the following command:
  gcloud feedback

To check gcloud for common problems, please run the following command:
  gcloud info --run-diagnostics
```

**Expected Behavior:**
- Should print file contents to stdout
- Exit code: 0

**Actual Behavior:**
- gcloud CLI crashes immediately
- No output displayed
- Exit code: 1

---

## 🔍 Root Cause Analysis

### The Problem: Bytes vs Strings Mismatch

Python has two distinct data types:
- **`str`** (string) - Text data: `"hello.txt"`, `"text/plain"`
- **`bytes`** - Binary data: `b"hello"`, file contents

### What's Happening in Your Code

```python
# In storage.py - download endpoint
@router.get("/storage/v1/b/{bucket}/o/{object:path}")
def get_object(bucket: str, object: str, alt: str = Query(None)):
    db_obj = db.query(Object).filter_by(bucket_id=bucket, name=object).first()
    
    if alt == "media":
        with open(file_path, "rb") as f:
            file_content = f.read()  # Returns bytes ✅
        
        return Response(
            content=file_content,              # bytes ✅
            media_type=db_obj.content_type,    # Could be bytes ❌
            headers={
                "x-goog-hash": f"crc32c={db_obj.crc32c_hash},md5={db_obj.md5_hash}"
                # If hashes are bytes, this creates mixed types ❌
            }
        )
```

### Where the Bug Occurs

1. **Upload Phase:** When calculating hashes
   ```python
   # Step 4: Calculate hashes
   md5_hash = base64.b64encode(hashlib.md5(content).digest()).decode()  # ✅ String
   crc32c = calculate_crc32c(content)  # ❓ Might return bytes or string
   
   # Step 5: Save to database
   obj = Object(
       content_type="application/octet-stream",  # ✅ String
       md5_hash=md5_hash,     # Should be string
       crc32c_hash=crc32c     # Might be bytes! ❌
   )
   ```

2. **Download Phase:** When sending response
   ```python
   # gcloud receives response and tries:
   content_type = response.headers['content-type']
   
   # If content_type is bytes:
   if content_type.endswith('utf-8'):  # ❌ CRASH!
       # Can't call .endswith() on bytes with str argument
   ```

### The Likely Culprit: `crc32c_hash` Calculation

```python
def _calc_hashes(content: bytes):
    md5_b64 = base64.b64encode(hashlib.md5(content).digest()).decode("utf-8")  # ✅ String
    crc = zlib.crc32(content) & 0xFFFFFFFF
    crc_b64 = base64.b64encode(struct.pack(">I", crc)).decode("utf-8")  # ✅ Should be string
    return md5_b64, crc_b64

# But if .decode() is missing somewhere:
crc_b64_bytes = base64.b64encode(struct.pack(">I", crc))  # ❌ bytes without decode()
```

---

## 🔧 Immediate Fix Solution

### Step 1: Verify Hash Encoding

**File:** `minimal-backend/api/storage.py`

**Find the hash calculation function:**
```python
def _calc_hashes(content: bytes):
    md5_b64 = base64.b64encode(hashlib.md5(content).digest()).decode("utf-8")
    crc = zlib.crc32(content) & 0xFFFFFFFF
    crc_b64 = base64.b64encode(struct.pack(">I", crc)).decode("utf-8")
    return md5_b64, crc_b64
```

**Ensure `.decode("utf-8")` is present on all base64 encoding!**

### Step 2: Add Type Validation in Upload

```python
@router.post("/upload/storage/v1/b/{bucket}/o")
async def upload_object(bucket: str, request: Request, name: str = Query(None)):
    # ... existing code ...
    
    # Calculate hashes
    md5_hash, crc32c_hash = _calc_hashes(content)
    
    # CRITICAL: Ensure they are strings, not bytes
    assert isinstance(md5_hash, str), f"md5_hash is {type(md5_hash)}, expected str"
    assert isinstance(crc32c_hash, str), f"crc32c_hash is {type(crc32c_hash)}, expected str"
    
    # Save metadata to database
    obj = Object(
        id=f"{bucket}/{object_name}",
        bucket_id=bucket,
        name=object_name,
        size=len(content),
        content_type="application/octet-stream",  # Ensure this is str
        md5_hash=md5_hash,      # Now guaranteed to be str
        crc32c_hash=crc32c_hash # Now guaranteed to be str
    )
```

### Step 3: Add Type Validation in Download

```python
@router.get("/storage/v1/b/{bucket}/o/{object:path}")
def get_object(bucket: str, object: str, alt: str = Query(None)):
    db_obj = db.query(Object).filter_by(bucket_id=bucket, name=object).first()
    
    if not db_obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    if alt == "media":
        with open(db_obj.file_path, "rb") as f:
            file_content = f.read()
        
        # CRITICAL: Ensure all header values are strings
        content_type = db_obj.content_type or "application/octet-stream"
        if isinstance(content_type, bytes):
            content_type = content_type.decode("utf-8")
        
        md5_hash = db_obj.md5_hash
        if isinstance(md5_hash, bytes):
            md5_hash = md5_hash.decode("utf-8")
        
        crc32c_hash = db_obj.crc32c_hash
        if isinstance(crc32c_hash, bytes):
            crc32c_hash = crc32c_hash.decode("utf-8")
        
        return Response(
            content=file_content,
            media_type=content_type,  # Now guaranteed to be str
            headers={
                "Content-Length": str(len(file_content)),
                "x-goog-hash": f"crc32c={crc32c_hash},md5={md5_hash}"  # All strings
            }
        )
```

### Step 4: Fix Existing Data (Database Migration)

```python
# One-time script to fix existing data
from database import get_db, Object

def fix_bytes_in_database():
    db = next(get_db())
    
    objects = db.query(Object).all()
    
    for obj in objects:
        updated = False
        
        # Fix content_type
        if isinstance(obj.content_type, bytes):
            obj.content_type = obj.content_type.decode("utf-8")
            updated = True
        
        # Fix md5_hash
        if isinstance(obj.md5_hash, bytes):
            obj.md5_hash = obj.md5_hash.decode("utf-8")
            updated = True
        
        # Fix crc32c_hash
        if isinstance(obj.crc32c_hash, bytes):
            obj.crc32c_hash = obj.crc32c_hash.decode("utf-8")
            updated = True
        
        if updated:
            print(f"Fixed: {obj.name}")
    
    db.commit()
    print("Database migration complete!")

# Run once:
if __name__ == "__main__":
    fix_bytes_in_database()
```

### Step 5: Update Database Schema (Optional - Add Type Constraints)

```sql
-- Add check constraints to ensure strings only
ALTER TABLE objects 
ADD CONSTRAINT check_content_type_is_text 
CHECK (octet_length(content_type) = length(content_type));

ALTER TABLE objects 
ADD CONSTRAINT check_md5_hash_is_text 
CHECK (octet_length(md5_hash) = length(md5_hash));

ALTER TABLE objects 
ADD CONSTRAINT check_crc32c_hash_is_text 
CHECK (octet_length(crc32c_hash) = length(crc32c_hash));
```

---

## 🗂️ Object Versioning Feature

### Overview

Object versioning allows you to keep multiple versions of the same file. When enabled:
- Each upload creates a new version (doesn't overwrite)
- Old versions are preserved
- You can download any specific version
- Deleted files leave a "delete marker" but versions remain

### Database Schema Changes

```sql
-- Add versioning columns to objects table
ALTER TABLE objects ADD COLUMN generation BIGINT;
ALTER TABLE objects ADD COLUMN is_current_version BOOLEAN DEFAULT true;

-- Update primary key to include generation
ALTER TABLE objects DROP CONSTRAINT objects_pkey;
ALTER TABLE objects ADD PRIMARY KEY (id, generation);

-- Create indexes for performance
CREATE INDEX idx_current_version ON objects(bucket_id, name, is_current_version);
CREATE INDEX idx_generation ON objects(bucket_id, name, generation);
```

**New Schema:**
```sql
CREATE TABLE objects (
    id VARCHAR,                      -- bucket/object_name
    bucket_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    generation BIGINT NOT NULL,      -- Version number (timestamp in microseconds)
    size INTEGER,
    content_type VARCHAR,
    md5_hash VARCHAR,
    crc32c_hash VARCHAR,
    file_path VARCHAR,               -- /tmp/gcs-storage/{bucket}/{name}/{generation}
    is_current_version BOOLEAN DEFAULT true,
    deleted BOOLEAN DEFAULT false,
    time_created TIMESTAMP,
    PRIMARY KEY (id, generation),
    FOREIGN KEY (bucket_id) REFERENCES buckets(id)
);
```

### File System Structure

**Before (No Versioning):**
```
/tmp/gcs-storage/
└── test-bucket/
    ├── file.txt           ← Single file
    ├── document.pdf
    └── image.png
```

**After (With Versioning):**
```
/tmp/gcs-storage/
└── test-bucket/
    ├── file.txt/
    │   ├── 1738713600000000    ← Version 1: "Hello Sonnet"
    │   └── 1738713700000000    ← Version 2: "Hello Sonnet 4.5"
    ├── document.pdf/
    │   └── 1738713800000000
    └── image.png/
        └── 1738713900000000
```

### Upload Logic with Versioning

```python
@router.post("/upload/storage/v1/b/{bucket}/o")
async def upload_object(bucket: str, request: Request, name: str = Query(None)):
    raw_body = await request.body()
    content = parse_multipart_content(raw_body)
    object_name = name or extract_name_from_body(raw_body)
    
    # Generate version number (microseconds since epoch)
    generation = int(datetime.now(timezone.utc).timestamp() * 1000000)
    
    # Create versioned file path
    file_path = f"/tmp/gcs-storage/{bucket}/{object_name}/{generation}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Write file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Calculate hashes
    md5_hash, crc32c_hash = _calc_hashes(content)
    
    # Use database transaction for atomicity
    with db.begin():
        # Mark all previous versions as not current
        db.query(Object).filter_by(
            bucket_id=bucket,
            name=object_name
        ).update({"is_current_version": False})
        
        # Create new version
        obj = Object(
            id=f"{bucket}/{object_name}",
            bucket_id=bucket,
            name=object_name,
            generation=generation,           # NEW
            size=len(content),
            content_type="application/octet-stream",
            md5_hash=md5_hash,
            crc32c_hash=crc32c_hash,
            file_path=file_path,
            is_current_version=True,         # NEW
            deleted=False,
            time_created=datetime.now(timezone.utc)
        )
        db.add(obj)
    
    return {
        "kind": "storage#object",
        "name": object_name,
        "bucket": bucket,
        "generation": str(generation),       # NEW
        "size": str(len(content)),
        "md5Hash": md5_hash,
        "timeCreated": obj.time_created.isoformat()
    }
```

### Download Logic with Versioning

```python
@router.get("/storage/v1/b/{bucket}/o/{object:path}")
def get_object(
    bucket: str, 
    object: str, 
    alt: str = Query(None),
    generation: Optional[str] = Query(None)  # NEW: Version parameter
):
    # Build query
    query = db.query(Object).filter_by(
        bucket_id=bucket,
        name=object,
        deleted=False
    )
    
    # Get specific version or latest
    if generation:
        # Download specific version
        db_obj = query.filter_by(generation=int(generation)).first()
    else:
        # Download latest version
        db_obj = query.filter_by(is_current_version=True).first()
    
    if not db_obj:
        raise HTTPException(status_code=404, detail="Object not found")
    
    if alt == "media":
        # Read from versioned file path
        with open(db_obj.file_path, "rb") as f:
            file_content = f.read()
        
        return Response(
            content=file_content,
            media_type=db_obj.content_type or "application/octet-stream",
            headers={
                "Content-Length": str(len(file_content)),
                "x-goog-generation": str(db_obj.generation),  # NEW
                "x-goog-hash": f"crc32c={db_obj.crc32c_hash},md5={db_obj.md5_hash}"
            }
        )
    else:
        # Return JSON metadata
        return {
            "kind": "storage#object",
            "name": db_obj.name,
            "bucket": bucket,
            "generation": str(db_obj.generation),  # NEW
            "size": str(db_obj.size),
            "md5Hash": db_obj.md5_hash,
            "timeCreated": db_obj.time_created.isoformat()
        }
```

### List Versions Endpoint

```python
@router.get("/storage/v1/b/{bucket}/o")
def list_objects(
    bucket: str,
    versions: bool = Query(False),  # NEW: Include all versions
    db: Session = Depends(get_db)
):
    query = db.query(Object).filter_by(bucket_id=bucket)
    
    if not versions:
        # Only current versions (default behavior)
        query = query.filter_by(is_current_version=True, deleted=False)
    
    objects = query.order_by(Object.name, Object.generation.desc()).all()
    
    items = []
    for obj in objects:
        items.append({
            "kind": "storage#object",
            "name": obj.name,
            "bucket": bucket,
            "generation": str(obj.generation),
            "size": str(obj.size),
            "timeCreated": obj.time_created.isoformat(),
            "md5Hash": obj.md5_hash,
            "isLatest": obj.is_current_version  # NEW
        })
    
    return {
        "kind": "storage#objects",
        "items": items
    }
```

### Usage Examples

#### Upload and Create Versions

```bash
# Upload version 1
echo "Hello Sonnet" > file.txt
gcloud storage cp file.txt gs://bucket/
# Response: generation=1738713600000000

# Upload version 2 (doesn't overwrite v1)
echo "Hello Sonnet 4.5" > file.txt
gcloud storage cp file.txt gs://bucket/
# Response: generation=1738713700000000
```

#### Download Latest Version

```bash
# Download current version (v2)
gcloud storage cp gs://bucket/file.txt downloaded.txt
# Gets: "Hello Sonnet 4.5"
```

#### Download Specific Version

```bash
# Download version 1
gcloud storage cp gs://bucket/file.txt#1738713600000000 downloaded-v1.txt
# Gets: "Hello Sonnet"

# Download version 2
gcloud storage cp gs://bucket/file.txt#1738713700000000 downloaded-v2.txt
# Gets: "Hello Sonnet 4.5"
```

#### List All Versions

```bash
# List only current versions (default)
gcloud storage ls gs://bucket/

# List all versions
gcloud storage ls -a gs://bucket/file.txt
# Output:
# gs://bucket/file.txt#1738713600000000  (v1)
# gs://bucket/file.txt#1738713700000000  (v2 - current)
```

---

## ⚠️ Implementation Challenges

### 1. Database Migration Challenge

**Problem:** Existing data has no generation numbers

**Solution Options:**

**Option A: Clean Start (Destructive)**
```sql
-- Delete all existing objects
DELETE FROM objects;

-- Add required columns
ALTER TABLE objects ADD COLUMN generation BIGINT NOT NULL;
ALTER TABLE objects ADD COLUMN is_current_version BOOLEAN DEFAULT true;
```
- ✅ Simple and clean
- ❌ Loses all existing data

**Option B: Backfill (Preserves Data)**
```sql
-- Add columns as nullable first
ALTER TABLE objects ADD COLUMN generation BIGINT;
ALTER TABLE objects ADD COLUMN is_current_version BOOLEAN;

-- Generate fake generations from timestamps
UPDATE objects 
SET generation = EXTRACT(EPOCH FROM time_created) * 1000000,
    is_current_version = true
WHERE generation IS NULL;

-- Make required
ALTER TABLE objects ALTER COLUMN generation SET NOT NULL;
```
- ✅ Keeps existing data
- ⚠️ Requires careful testing

### 2. File System Reorganization

**Problem:** Files need to move into versioned directories

**Migration Script:**
```python
import os
import shutil
from database import get_db, Object

def migrate_filesystem():
    db = next(get_db())
    objects = db.query(Object).all()
    
    for obj in objects:
        old_path = f"/tmp/gcs-storage/{obj.bucket_id}/{obj.name}"
        
        if os.path.isfile(old_path):
            # Create versioned structure
            new_dir = f"/tmp/gcs-storage/{obj.bucket_id}/{obj.name}"
            new_path = f"{new_dir}/{obj.generation}"
            
            # Move file
            os.makedirs(new_dir, exist_ok=True)
            shutil.move(old_path, new_path)
            
            # Update database
            obj.file_path = new_path
            print(f"Migrated: {old_path} -> {new_path}")
    
    db.commit()
    print("Migration complete!")
```

### 3. Race Conditions

**Problem:** Two simultaneous uploads

**Solution:** Use database transactions with row locking
```python
from sqlalchemy import select

async def upload_with_locking(bucket, name, content, db):
    with db.begin():
        # Lock all rows for this object
        db.execute(
            select(Object)
            .where(Object.bucket_id == bucket, Object.name == name)
            .with_for_update()
        )
        
        # Now safe to update
        generation = int(datetime.now().timestamp() * 1000000)
        
        db.query(Object).filter_by(
            bucket_id=bucket, name=name
        ).update({"is_current_version": False})
        
        obj = Object(generation=generation, is_current_version=True, ...)
        db.add(obj)
```

### 4. Storage Management

**Problem:** Versions accumulate forever

**Solution:** Implement lifecycle policies
```python
def cleanup_old_versions(max_versions=3):
    """Keep only N latest versions"""
    db = next(get_db())
    
    # Get all unique objects
    unique_objects = db.query(Object.bucket_id, Object.name).distinct().all()
    
    for bucket_id, name in unique_objects:
        # Get all versions sorted by generation
        versions = db.query(Object).filter_by(
            bucket_id=bucket_id,
            name=name
        ).order_by(Object.generation.desc()).all()
        
        # Keep latest N, delete rest
        for old_version in versions[max_versions:]:
            if os.path.exists(old_version.file_path):
                os.remove(old_version.file_path)
            db.delete(old_version)
    
    db.commit()
```

### 5. Performance Impact

**Problem:** More database rows = slower queries

**Solution:** Add strategic indexes
```sql
-- Index for finding current version quickly
CREATE INDEX idx_current_version 
ON objects(bucket_id, name, is_current_version)
WHERE is_current_version = true;

-- Index for finding specific generation
CREATE INDEX idx_generation 
ON objects(bucket_id, name, generation);

-- Index for listing non-deleted objects
CREATE INDEX idx_active_objects 
ON objects(bucket_id, is_current_version, deleted)
WHERE deleted = false;
```

---

## 🎯 Summary

### Immediate Priority: Fix Download Bug

1. **Verify** all hash calculations use `.decode("utf-8")`
2. **Add** type validation in upload and download
3. **Fix** existing data with migration script
4. **Test** both gcloud commands work

### Future Enhancement: Add Versioning

1. **Phase 1:** Add columns (nullable for backward compatibility)
2. **Phase 2:** Migrate existing data
3. **Phase 3:** Make columns required
4. **Phase 4:** Implement lifecycle management

### Testing Checklist

- [ ] Upload file via gcloud
- [ ] Download file via gcloud cp
- [ ] Display file via gcloud cat
- [ ] Upload same file twice (versioning)
- [ ] Download latest version
- [ ] Download specific version
- [ ] List files (current only)
- [ ] List files (all versions)
- [ ] Delete file
- [ ] Attempt to download deleted file

---

**Next Steps:**

1. Apply immediate bug fix to `storage.py`
2. Run database migration script
3. Test with failing commands
4. Document results
5. Plan versioning implementation timeline

---

**Document Maintained By:** GCP Stimulator Team  
**Last Review:** February 5, 2026
