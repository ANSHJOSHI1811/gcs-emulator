# Object Versioning & Preconditions

## Overview

This document describes the implementation of **Object Versioning** and **Preconditions** in the GCS Storage Emulator. These features enable generation-based versioning, conditional operations, and fine-grained control over object uploads and updates — exactly matching Google Cloud Storage behavior.

---

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Generation vs Metageneration](#generation-vs-metageneration)
3. [Precondition Headers](#precondition-headers)
4. [API Reference](#api-reference)
5. [Database Schema](#database-schema)
6. [Filesystem Layout](#filesystem-layout)
7. [Workflows](#workflows)
8. [Error Codes](#error-codes)
9. [Examples](#examples)
10. [Comparison with GCS](#comparison-with-gcs)

---

## Core Concepts

### What is Object Versioning?

Object versioning allows multiple revisions of the same object to coexist. Each time an object is overwritten, a new **generation** is created. This enables:

- **Historical access**: Retrieve old versions of an object
- **Rollback**: Restore previous versions
- **Audit trails**: Track object changes over time
- **Concurrent updates**: Use preconditions to prevent race conditions

### Key Terms

| Term | Definition |
|------|------------|
| **Generation** | Unique version identifier (integer) that increments on each object overwrite |
| **Metageneration** | Metadata version counter that increments when object metadata changes (but content stays the same) |
| **Precondition** | Query parameter or header that enforces a condition before allowing an operation |
| **Latest Version** | The most recent generation of an object (default for operations) |

---

## Generation vs Metageneration

### Generation

- **Increments when**: Object content is overwritten (new upload)
- **Starts at**: 1 for new objects
- **Behavior**: Generation 1 → 2 → 3 → ...
- **Resets**: Never (always increments)

**Example:**
```
Upload file.txt (first time)  → generation=1
Upload file.txt (overwrite)   → generation=2
Upload file.txt (overwrite)   → generation=3
```

### Metageneration

- **Increments when**: Object metadata changes (without content change)
- **Starts at**: 1 for each new generation
- **Behavior**: Resets to 1 when generation increments
- **Resets**: On every new generation

**Example:**
```
Upload file.txt                   → generation=1, metageneration=1
Update metadata (content type)    → generation=1, metageneration=2
Update metadata (custom metadata) → generation=1, metageneration=3
Overwrite file.txt (new content)  → generation=2, metageneration=1
```

---

## Precondition Headers

Preconditions allow you to enforce conditions before operations execute. If preconditions fail, the operation returns **HTTP 412 Precondition Failed**.

### Supported Preconditions

| Query Parameter | Behavior | Use Case |
|-----------------|----------|----------|
| `ifGenerationMatch=N` | Proceed only if current generation equals N | Prevent overwrites if object changed |
| `ifGenerationNotMatch=N` | Proceed only if current generation ≠ N | Ensure object has changed since last read |
| `ifMetagenerationMatch=N` | Proceed only if current metageneration equals N | Prevent metadata conflicts |
| `ifMetagenerationNotMatch=N` | Proceed only if current metageneration ≠ N | Ensure metadata changed |

### Special Cases

#### `ifGenerationMatch=0`
- **Behavior**: Operation succeeds only if object **does not exist**
- **Use Case**: Create object only if it's new (prevent overwrites)

#### For Non-Existent Objects
- `ifGenerationMatch > 0` → Fails with 412
- `ifMetagenerationMatch` → Fails with 412
- `ifGenerationNotMatch` → Succeeds (any generation ≠ specified)

---

## API Reference

### Upload Object (with Versioning)

**Endpoint:**
```
POST /upload/storage/v1/b/{bucket}/o?uploadType=media&name={object}
```

**Query Parameters:**
```
uploadType=media                      # Required: Must be 'media'
name={object_name}                    # Required: Object name
ifGenerationMatch={N}                 # Optional: Precondition
ifGenerationNotMatch={N}              # Optional: Precondition
ifMetagenerationMatch={N}             # Optional: Precondition
ifMetagenerationNotMatch={N}          # Optional: Precondition
```

**Request Body:**
```
Binary file content
```

**Response (200 OK):**
```json
{
  "kind": "storage#object",
  "id": "bucket/object/123",
  "selfLink": "/storage/v1/b/bucket/o/object",
  "name": "object.txt",
  "bucket": "my-bucket",
  "generation": "2",
  "metageneration": "1",
  "contentType": "text/plain",
  "timeCreated": "2025-12-02T10:00:00.000Z",
  "updated": "2025-12-02T10:05:00.000Z",
  "size": "1024",
  "md5Hash": "rL0Y20zC+Fzt72VPzMSk2A==",
  "crc32c": "AAAAAA=="
}
```

**Errors:**
- `400` - Invalid uploadType or missing name parameter
- `404` - Bucket not found
- `412` - Precondition failed

---

### Download Object (Versioned)

**Endpoint:**
```
GET /storage/v1/b/{bucket}/o/{object}?alt=media&generation={N}
```

**Query Parameters:**
```
alt=media                  # Required for download (binary response)
generation={N}             # Optional: Specific version (default: latest)
```

**Response (200 OK):**
```
Binary file content
Content-Type: {object's content type}
```

**Errors:**
- `404` - Object or version not found

**Examples:**
```bash
# Download latest version
GET /storage/v1/b/my-bucket/o/file.txt?alt=media

# Download generation 5
GET /storage/v1/b/my-bucket/o/file.txt?alt=media&generation=5
```

---

### Get Object Metadata (Versioned)

**Endpoint:**
```
GET /storage/v1/b/{bucket}/o/{object}?generation={N}
```

**Query Parameters:**
```
generation={N}  # Optional: Specific version (default: latest)
```

**Response (200 OK):**
```json
{
  "kind": "storage#object",
  "name": "file.txt",
  "bucket": "my-bucket",
  "generation": "3",
  "metageneration": "1",
  "size": "2048",
  "contentType": "application/json",
  "timeCreated": "2025-12-02T12:00:00Z",
  "updated": "2025-12-02T12:30:00Z",
  "md5Hash": "abc123...",
  "crc32c": "xyz789=="
}
```

---

### Delete Object Version

**Endpoint:**
```
DELETE /storage/v1/b/{bucket}/o/{object}?generation={N}
```

**Query Parameters:**
```
generation={N}  # Optional: Delete specific version (omit = delete all)
```

**Behavior:**

| Scenario | Action |
|----------|--------|
| `generation` specified | Delete only that version |
| `generation` omitted | Delete all versions (object removed) |
| Deleting latest version | Previous version becomes latest |
| Deleting last remaining version | Object marked as deleted |

**Response:**
- `204 No Content` - Success
- `404 Not Found` - Object or version doesn't exist

---

## Database Schema

### Objects Table (Latest Version Tracking)

```sql
CREATE TABLE objects (
    id VARCHAR(255) PRIMARY KEY,
    bucket_id VARCHAR(63) NOT NULL,
    name VARCHAR(1024) NOT NULL,
    generation BIGINT DEFAULT 1 NOT NULL,
    metageneration BIGINT DEFAULT 1,
    size BIGINT DEFAULT 0,
    content_type VARCHAR(255),
    md5_hash VARCHAR(32),
    crc32c_hash VARCHAR(44),
    file_path VARCHAR(1024),
    is_latest BOOLEAN DEFAULT TRUE NOT NULL,
    deleted BOOLEAN DEFAULT FALSE NOT NULL,
    time_created TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    meta JSON,
    FOREIGN KEY (bucket_id) REFERENCES buckets(id)
);

CREATE INDEX idx_objects_bucket_name ON objects(bucket_id, name);
```

### Object_Versions Table (All Versions)

```sql
CREATE TABLE object_versions (
    id VARCHAR(255) PRIMARY KEY,
    object_id VARCHAR(255) NOT NULL,
    bucket_id VARCHAR(63) NOT NULL,
    name VARCHAR(1024) NOT NULL,
    generation BIGINT NOT NULL,
    metageneration BIGINT DEFAULT 1,
    size BIGINT DEFAULT 0,
    content_type VARCHAR(255),
    md5_hash VARCHAR(32),
    crc32c_hash VARCHAR(44),
    file_path VARCHAR(1024),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    deleted BOOLEAN DEFAULT FALSE NOT NULL,
    meta JSON,
    FOREIGN KEY (object_id) REFERENCES objects(id) ON DELETE CASCADE,
    FOREIGN KEY (bucket_id) REFERENCES buckets(id) ON DELETE CASCADE,
    UNIQUE (bucket_id, name, generation)
);

CREATE INDEX idx_object_versions_generation ON object_versions(bucket_id, name, generation);
```

### Relationships

```
buckets (1) ─────> (N) objects
objects (1) ─────> (N) object_versions
```

---

## Filesystem Layout

### Versioned Storage Structure

Objects are stored with generation-specific filenames:

```
storage/
├── bucket-id-1/
│   ├── file.txt/
│   │   ├── v1          # Generation 1
│   │   ├── v2          # Generation 2
│   │   └── v3          # Generation 3
│   └── image.png/
│       ├── v1
│       └── v2
└── bucket-id-2/
    └── data.json/
        └── v1
```

### Path Format

```
./storage/{bucket_id}/{object_name}/v{generation}
```

**Examples:**
```
./storage/my-bucket-abc123/report.pdf/v1
./storage/my-bucket-abc123/report.pdf/v2
./storage/my-bucket-abc123/data/file.txt/v1
```

---

## Workflows

### 1. Upload New Object

```
┌─────────────────┐
│ Client uploads  │
│ new object      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ No existing object      │
│ found                   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Create generation=1     │
│ metageneration=1        │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Save to:                │
│ storage/bucket/obj/v1   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Insert into:            │
│ - objects (latest)      │
│ - object_versions (v1)  │
└─────────────────────────┘
```

### 2. Overwrite Existing Object

```
┌─────────────────┐
│ Client uploads  │
│ existing object │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Find existing object    │
│ (generation=N)          │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Validate preconditions  │
│ (if any)                │
└────────┬────────────────┘
         │ ✓ Pass
         ▼
┌─────────────────────────┐
│ Mark old version        │
│ is_latest=FALSE         │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Create generation=N+1   │
│ metageneration=1        │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Save to:                │
│ storage/bucket/obj/vN+1 │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Update objects table    │
│ Insert object_versions  │
└─────────────────────────┘
```

### 3. Download Specific Version

```
┌─────────────────────────┐
│ GET ?generation=2       │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Query object_versions   │
│ WHERE generation=2      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Read file from:         │
│ storage/bucket/obj/v2   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Return binary content   │
│ with Content-Type       │
└─────────────────────────┘
```

### 4. Delete Specific Version

```
┌─────────────────────────┐
│ DELETE ?generation=3    │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Mark version deleted    │
│ in object_versions      │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Delete physical file:   │
│ storage/bucket/obj/v3   │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Is this latest version? │
└────┬───────────┬────────┘
     │ Yes       │ No
     ▼           ▼
┌────────────┐ ┌───────────┐
│ Promote    │ │ Done      │
│ previous   │ └───────────┘
│ version to │
│ latest     │
└────────────┘
```

---

## Error Codes

| HTTP Status | Error | Scenario |
|-------------|-------|----------|
| **200** | Success | Operation completed successfully |
| **204** | No Content | Deletion successful |
| **400** | Bad Request | Invalid parameters (missing name, wrong uploadType) |
| **404** | Not Found | Bucket, object, or version doesn't exist |
| **412** | Precondition Failed | ifGenerationMatch/ifMetagenerationMatch conditions not met |
| **500** | Internal Server Error | Unexpected server-side failure |

### Precondition Failure Examples

```json
{
  "error": {
    "code": 412,
    "message": "Precondition failed: generation 2 != 5"
  }
}
```

```json
{
  "error": {
    "code": 412,
    "message": "Precondition failed: object does not exist (ifGenerationMatch=5)"
  }
}
```

---

## Examples

### Example 1: Upload with Precondition

```bash
# Create bucket
curl -X POST http://localhost:8080/storage/v1/b?project=test \
  -H "Content-Type: application/json" \
  -d '{"name": "my-bucket"}'

# Upload initial version
curl -X POST "http://localhost:8080/upload/storage/v1/b/my-bucket/o?uploadType=media&name=file.txt" \
  -H "Content-Type: text/plain" \
  --data-binary "Version 1"

# Response:
# {
#   "generation": "1",
#   "metageneration": "1",
#   ...
# }

# Safely overwrite only if generation is still 1
curl -X POST "http://localhost:8080/upload/storage/v1/b/my-bucket/o?uploadType=media&name=file.txt&ifGenerationMatch=1" \
  -H "Content-Type: text/plain" \
  --data-binary "Version 2"

# Response:
# {
#   "generation": "2",
#   "metageneration": "1",
#   ...
# }

# Try to overwrite with wrong generation (fails)
curl -X POST "http://localhost:8080/upload/storage/v1/b/my-bucket/o?uploadType=media&name=file.txt&ifGenerationMatch=1" \
  -H "Content-Type: text/plain" \
  --data-binary "Version 3"

# Response: 412
# {
#   "error": {
#     "code": 412,
#     "message": "Precondition failed: generation 2 != 1"
#   }
# }
```

### Example 2: Download Specific Version

```bash
# Upload multiple versions
curl -X POST "http://localhost:8080/upload/storage/v1/b/my-bucket/o?uploadType=media&name=doc.txt" \
  --data-binary "Content A"

curl -X POST "http://localhost:8080/upload/storage/v1/b/my-bucket/o?uploadType=media&name=doc.txt" \
  --data-binary "Content B"

curl -X POST "http://localhost:8080/upload/storage/v1/b/my-bucket/o?uploadType=media&name=doc.txt" \
  --data-binary "Content C"

# Download latest (generation 3)
curl "http://localhost:8080/storage/v1/b/my-bucket/o/doc.txt?alt=media"
# Output: Content C

# Download generation 1
curl "http://localhost:8080/storage/v1/b/my-bucket/o/doc.txt?alt=media&generation=1"
# Output: Content A

# Download generation 2
curl "http://localhost:8080/storage/v1/b/my-bucket/o/doc.txt?alt=media&generation=2"
# Output: Content B
```

### Example 3: Delete Specific Version

```bash
# Upload three versions
for i in 1 2 3; do
  curl -X POST "http://localhost:8080/upload/storage/v1/b/my-bucket/o?uploadType=media&name=file.txt" \
    --data-binary "Version $i"
done

# Delete generation 2
curl -X DELETE "http://localhost:8080/storage/v1/b/my-bucket/o/file.txt?generation=2"

# Generation 1 still exists
curl "http://localhost:8080/storage/v1/b/my-bucket/o/file.txt?generation=1"
# 200 OK

# Generation 2 is gone
curl "http://localhost:8080/storage/v1/b/my-bucket/o/file.txt?generation=2"
# 404 Not Found

# Latest version is still generation 3
curl "http://localhost:8080/storage/v1/b/my-bucket/o/file.txt?alt=media"
# Output: Version 3
```

### Example 4: Prevent Accidental Overwrites

```bash
# Create object only if it doesn't exist (generation=0)
curl -X POST "http://localhost:8080/upload/storage/v1/b/my-bucket/o?uploadType=media&name=new.txt&ifGenerationMatch=0" \
  --data-binary "Initial content"
# 200 OK (created)

# Try again with same precondition (fails because object exists)
curl -X POST "http://localhost:8080/upload/storage/v1/b/my-bucket/o?uploadType=media&name=new.txt&ifGenerationMatch=0" \
  --data-binary "Second attempt"
# 412 Precondition Failed
```

---

## Comparison with GCS

| Feature | Google Cloud Storage | GCS Emulator (Step 3) |
|---------|---------------------|----------------------|
| Generation tracking | ✅ | ✅ |
| Metageneration | ✅ | ✅ |
| `ifGenerationMatch` | ✅ | ✅ |
| `ifGenerationNotMatch` | ✅ | ✅ |
| `ifMetagenerationMatch` | ✅ | ✅ |
| `ifMetagenerationNotMatch` | ✅ | ✅ |
| Download specific version | ✅ `?generation=N` | ✅ |
| Delete specific version | ✅ | ✅ |
| List all versions | ✅ `?versions=true` | ⚠️ (Not yet implemented) |
| Version promotion on delete | ✅ | ✅ |
| Versioned filesystem storage | ✅ | ✅ |
| HTTP 412 on precondition fail | ✅ | ✅ |

### Differences

1. **List Versions**: GCS supports `?versions=true` to list all versions. This emulator does not yet implement this endpoint (future enhancement).

2. **Soft Delete**: GCS supports "soft delete" with a retention period. This emulator marks versions as deleted immediately.

3. **Storage Class Transitions**: GCS can archive old versions to cheaper storage classes. This emulator stores all versions in the same filesystem location.

---

## CLI Usage with gcslocal

### Upload with Versioning

```bash
# Upload file (creates generation 1)
python gcslocal.py cp local-file.txt gs://my-bucket/file.txt

# Upload again (creates generation 2)
python gcslocal.py cp updated-file.txt gs://my-bucket/file.txt
```

### Download Specific Version

```bash
# Download latest version
python gcslocal.py cp gs://my-bucket/file.txt ./downloaded.txt

# Download specific version (generation 5)
# Note: CLI support for ?generation= parameter would need to be added
curl "http://localhost:8080/storage/v1/b/my-bucket/o/file.txt?alt=media&generation=5" -o v5.txt
```

---

## Testing

### Run Versioning Tests

```bash
# Run all versioning tests
pytest tests/e2e/test_object_versioning.py -v

# Run specific test class
pytest tests/e2e/test_object_versioning.py::TestPreconditions -v

# Run with coverage
pytest tests/e2e/test_object_versioning.py --cov=app.services.object_versioning_service
```

### Test Coverage

The test suite includes **20+ tests** covering:

- ✅ Generation incrementing (1 → 2 → 3)
- ✅ Metageneration reset on new generation
- ✅ All precondition combinations
- ✅ Download latest and specific versions
- ✅ Delete specific versions
- ✅ Version promotion on delete
- ✅ Round-trip workflows
- ✅ Error handling (404, 412)

---

## Migration

### Apply Migration

```bash
# Run migration script
python migrations/001_add_object_versioning.py
```

### Migration Steps

1. Adds `generation`, `is_latest`, `deleted`, `time_created` columns to `objects` table
2. Creates `object_versions` table with indexes
3. Migrates existing objects to `object_versions` (generation=1)
4. Creates unique constraint on `(bucket_id, name, generation)`

### Rollback

```python
from migrations.001_add_object_versioning import downgrade
from app.factory import create_app, db

app = create_app()
downgrade(db, app)
```

---

## Future Enhancements

### Planned Features

1. **List Versions API**: `GET /storage/v1/b/{bucket}/o/{object}?versions=true`
2. **Version Expiration**: Auto-delete old versions after N days
3. **Soft Delete with Retention**: Keep deleted versions for recovery period
4. **Resumable Uploads**: Support `uploadType=resumable` with versioning
5. **Lifecycle Policies**: Auto-archive old generations to cheaper storage

### Architecture Extensions

- **Async Version Cleanup**: Background job to prune old versions
- **Version Compression**: Compress historical versions to save disk space
- **Delta Storage**: Store only diffs between versions for large files

---

## Summary

✅ **Implemented:**
- Generation tracking (1 → 2 → 3...)
- Metageneration for metadata changes
- All precondition headers (`ifGenerationMatch`, `ifGenerationNotMatch`, etc.)
- Versioned filesystem storage (`storage/{bucket}/{object}/v{N}`)
- Download specific versions
- Delete specific versions with promotion
- GCS-compliant error codes (412 for precondition failures)
- 20+ comprehensive tests

🎯 **Use Cases:**
- Prevent race conditions in concurrent uploads
- Maintain audit trails of object changes
- Rollback to previous versions
- Implement optimistic locking patterns

📚 **References:**
- [Google Cloud Storage Versioning Docs](https://cloud.google.com/storage/docs/object-versioning)
- [GCS JSON API v1 Spec](https://cloud.google.com/storage/docs/json_api/v1)
