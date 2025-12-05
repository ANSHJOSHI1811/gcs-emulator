# `gcslocal cp` - Upload & Download Command

## Overview

The `gcslocal cp` command enables file uploads and downloads between your local filesystem and the GCS emulator, matching the behavior of `gsutil cp` and `awslocal s3 cp`.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    gcslocal cp Command                           │
│              (CLI argument parsing)                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
             ┌───────────────┴───────────────┐
             │                               │
      LOCAL → GCS                     GCS → LOCAL
      (Upload)                        (Download)
             │                               │
             ↓                               ↓
┌────────────────────────┐      ┌──────────────────────────┐
│   1. Read local file   │      │  1. GET with alt=media   │
│   2. Detect MIME type  │      │  2. Receive binary data  │
│   3. POST to /upload   │      │  3. Write to local file  │
└────────────┬───────────┘      └───────────┬──────────────┘
             │                               │
             ↓                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Flask Application                             │
│                                                                   │
│  Upload Route: /upload/storage/v1/b/{bucket}/o                  │
│                ?uploadType=media&name={object}                   │
│                                                                   │
│  Download Route: /storage/v1/b/{bucket}/o/{object}              │
│                  ?alt=media                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                 8-Stage Pipeline                                 │
│                                                                   │
│  Handler → Service → Repository                                  │
│  • Validate input                                                │
│  • Store metadata in PostgreSQL                                  │
│  • Store bytes in ./storage/{bucket}/                           │
│  • Calculate MD5 + CRC32C checksums                             │
└─────────────────────────────────────────────────────────────────┘
```

## Usage

### Upload (Local → GCS)

```bash
# Upload a single file
gcslocal cp ./file.txt gs://mybucket/file.txt

# Upload to a folder path
gcslocal cp ./document.pdf gs://mybucket/documents/doc.pdf

# Upload with automatic MIME type detection
gcslocal cp ./image.png gs://mybucket/images/logo.png
```

### Download (GCS → Local)

```bash
# Download a single file
gcslocal cp gs://mybucket/file.txt ./file.txt

# Download to specific directory
gcslocal cp gs://mybucket/data.json ./downloads/data.json

# Download binary file
gcslocal cp gs://mybucket/archive.zip ./archive.zip
```

## Upload Flow

### 1. Client-Side (gcslocal.py)

```python
def upload_file(local_path: str, gs_url: str):
    # 1. Parse GCS URL
    bucket_name, object_name = parse_gs_url(gs_url)  # gs://bucket/object
    
    # 2. Read file content
    with open(local_path, 'rb') as f:
        content = f.read()
    
    # 3. Detect MIME type
    import mimetypes
    content_type, _ = mimetypes.guess_type(local_path)
    
    # 4. POST to upload endpoint
    url = f"{EMULATOR_HOST}/upload/storage/v1/b/{bucket_name}/o"
    params = {
        'uploadType': 'media',
        'name': object_name
    }
    headers = {
        'Content-Type': content_type,
        'Content-Length': str(len(content))
    }
    
    response = requests.post(url, data=content, headers=headers, params=params)
```

### 2. Server-Side (Flask Handler)

```python
@upload_bp.route("/storage/v1/b/<bucket>/o", methods=["POST"])
def upload_object_media(bucket):
    # 1. Validate uploadType parameter
    upload_type = request.args.get("uploadType")
    if upload_type != "media":
        return error(400, "Only 'media' uploadType supported")
    
    # 2. Get object name
    object_name = request.args.get("name")
    
    # 3. Read request body
    content = request.get_data()
    content_type = request.headers.get("Content-Type")
    
    # 4. Delegate to service layer
    obj = ObjectService.upload_object(
        bucket_name=bucket,
        object_name=object_name,
        content=content,
        content_type=content_type
    )
    
    # 5. Return GCS-compliant JSON
    return jsonify(obj.to_dict()), 200
```

### 3. Service Layer

```python
@staticmethod
def upload_object(bucket_name, object_name, content, content_type):
    # 1. Validate bucket exists
    bucket = Bucket.query.filter_by(name=bucket_name).first()
    if not bucket:
        raise ValueError(f"Bucket '{bucket_name}' not found")
    
    # 2. Calculate checksums
    md5_hash = calculate_md5(content)
    crc32c_hash = calculate_crc32c(content)
    
    # 3. Save file to filesystem
    file_path = f"./storage/{bucket.id}/{uuid4().hex}"
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    Path(file_path).write_bytes(content)
    
    # 4. Create/update database record
    obj = Object(
        id=f"{bucket.id}/{object_name}",
        bucket_id=bucket.id,
        name=object_name,
        size=len(content),
        content_type=content_type,
        md5_hash=md5_hash,
        crc32c_hash=crc32c_hash,
        file_path=file_path
    )
    
    db.session.merge(obj)  # Use merge for upsert behavior
    db.session.commit()
    
    return obj
```

## Download Flow

### 1. Client-Side (gcslocal.py)

```python
def download_file(gs_url: str, local_path: str):
    # 1. Parse GCS URL
    bucket_name, object_name = parse_gs_url(gs_url)
    
    # 2. GET with alt=media parameter
    url = f"{EMULATOR_HOST}/storage/v1/b/{bucket_name}/o/{object_name}"
    params = {'alt': 'media'}
    
    response = requests.get(url, params=params)
    
    # 3. Create parent directories
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 4. Write file content
    with open(local_path, 'wb') as f:
        f.write(response.content)
```

### 2. Server-Side (Flask Handler)

```python
@objects_bp.route("/<bucket>/o/<path:object_name>", methods=["GET"])
def get_object(bucket, object_name):
    alt = request.args.get("alt", "json").lower()
    
    if alt == "media":
        # Download mode
        content, obj = ObjectService.download_object(bucket, object_name)
        
        return send_file(
            BytesIO(content),
            mimetype=obj.content_type,
            as_attachment=True,
            download_name=object_name
        ), 200
    else:
        # Metadata mode
        obj = ObjectService.get_object(bucket, object_name)
        return jsonify(obj.to_dict()), 200
```

### 3. Service Layer

```python
@staticmethod
def download_object(bucket_name, object_name):
    # 1. Find object in database
    bucket = Bucket.query.filter_by(name=bucket_name).first()
    obj = Object.query.filter_by(
        bucket_id=bucket.id,
        name=object_name
    ).first()
    
    if not obj:
        raise ValueError(f"Object '{object_name}' not found")
    
    # 2. Read file from filesystem
    file_path = Path(obj.file_path)
    if not file_path.exists():
        raise ValueError(f"Object file not found on disk")
    
    content = file_path.read_bytes()
    
    return content, obj
```

## Response Format

### Upload Success Response (GCS-compliant)

```json
{
  "kind": "storage#object",
  "id": "bucket/object/1234567890",
  "name": "file.txt",
  "bucket": "mybucket",
  "size": "1024",
  "contentType": "text/plain",
  "md5Hash": "5d41402abc4b2a76b9719d911017c592",
  "crc32c": "yZRlqg==",
  "generation": "1",
  "metageneration": "1",
  "timeCreated": "2025-12-02T10:30:00.000Z",
  "updated": "2025-12-02T10:30:00.000Z"
}
```

### Download Response

- **HTTP 200**
- **Headers:**
  - `Content-Type`: Original MIME type (e.g., `text/plain`, `image/png`)
  - `Content-Length`: Size in bytes
  - `Content-Disposition`: `attachment; filename="object_name"`
- **Body:** Raw file bytes

## Error Handling

### Upload Errors

| Error | Status | Message |
|-------|--------|---------|
| Bucket not found | 404 | `Bucket 'name' not found` |
| Missing name parameter | 400 | `Missing required query parameter 'name'` |
| Invalid uploadType | 400 | `Unsupported uploadType: {type}` |
| Empty content | 400 | `Empty request body` |
| Invalid object name | 400 | `Invalid object name` |

### Download Errors

| Error | Status | Message |
|-------|--------|---------|
| Object not found | 404 | `Object 'name' not found in bucket 'bucket'` |
| Bucket not found | 404 | `Bucket 'name' not found` |
| File missing on disk | 500 | `Object file not found on disk` |

## CLI Examples

### Basic Upload

```bash
$ gcslocal cp hello.txt gs://mybucket/hello.txt
✅ Uploaded: hello.txt -> gs://mybucket/hello.txt
  Size: 13 bytes
  Content-Type: text/plain
  MD5: 5d41402abc4b2a76b9719d911017c592
```

### Basic Download

```bash
$ gcslocal cp gs://mybucket/hello.txt ./downloaded.txt
✅ Downloaded: gs://mybucket/hello.txt -> ./downloaded.txt
  Size: 13 bytes
  Content-Type: text/plain
```

### Upload Error (Bucket Not Found)

```bash
$ gcslocal cp file.txt gs://nonexistent/file.txt
❌ Bucket gs://nonexistent not found
```

### Download Error (Object Not Found)

```bash
$ gcslocal cp gs://mybucket/missing.txt ./file.txt
❌ Object gs://mybucket/missing.txt not found
```

## Comparison with gsutil and awslocal

| Feature | gsutil cp | awslocal s3 cp | gcslocal cp | Status |
|---------|-----------|----------------|-------------|--------|
| **Upload file** | `gsutil cp file gs://bucket/` | `awslocal s3 cp file s3://bucket/` | `gcslocal cp file gs://bucket/` | ✅ |
| **Download file** | `gsutil cp gs://bucket/file .` | `awslocal s3 cp s3://bucket/file .` | `gcslocal cp gs://bucket/file .` | ✅ |
| **Binary files** | ✅ | ✅ | ✅ | ✅ |
| **MIME detection** | ✅ | ✅ | ✅ | ✅ |
| **Nested paths** | ✅ | ✅ | ✅ | ✅ |
| **Overwrite** | ✅ | ✅ | ✅ | ✅ |
| **Recursive** | ✅ `-r` | ✅ `--recursive` | ⏳ TODO | ⏳ |
| **Wildcards** | ✅ | ✅ | ⏳ TODO | ⏳ |
| **Multipart** | ✅ | ✅ | ⏳ TODO | ⏳ |
| **Resumable** | ✅ | ✅ | ⏳ TODO | ⏳ |

## Testing

### Run Tests

```bash
# Run all cp tests
pytest tests/e2e/test_gcslocal_cp.py -v

# Run specific test
pytest tests/e2e/test_gcslocal_cp.py::test_upload_text_file -v

# Run with output
pytest tests/e2e/test_gcslocal_cp.py -v -s
```

### Test Coverage

- ✅ Upload text files
- ✅ Upload binary files
- ✅ Download text files
- ✅ Download binary files
- ✅ Overwrite existing objects
- ✅ Nested path handling
- ✅ Error handling (404, 400)
- ✅ Round-trip integrity
- ✅ Large file handling
- ✅ MIME type detection

## Implementation Constraints

### Current Limitations

1. **No Resumable Uploads**: Large files (>5MB) should use resumable upload protocol (not yet implemented)
2. **No Multipart Upload**: Single HTTP request only
3. **No Recursive Copy**: Cannot do `gcslocal cp -r ./folder/ gs://bucket/`
4. **No Wildcards**: Cannot do `gcslocal cp *.txt gs://bucket/`
5. **No Versioning**: Overwrites previous version (no generation tracking)

### Future Enhancements

- [ ] Resumable upload support (`uploadType=resumable`)
- [ ] Multipart upload for large files
- [ ] Recursive directory upload (`-r` flag)
- [ ] Wildcard support (`*.txt`, `*.jpg`)
- [ ] Progress bars for large files
- [ ] Parallel transfers
- [ ] Object versioning
- [ ] Signed URL upload

## Integration with SDK

The upload/download endpoints are also compatible with the Google Cloud Storage Python SDK:

```python
from google.cloud import storage

client = storage.Client()
bucket = client.bucket('mybucket')

# Upload via SDK
blob = bucket.blob('file.txt')
blob.upload_from_filename('./local_file.txt')

# Download via SDK
blob.download_to_filename('./downloaded_file.txt')
```

The SDK internally uses the same `/upload/storage/v1/b/{bucket}/o` and `/storage/v1/b/{bucket}/o/{object}?alt=media` endpoints.

## Summary

The `gcslocal cp` command provides:
- ✅ Simple media uploads (uploadType=media)
- ✅ Binary-safe downloads
- ✅ GCS-compliant JSON responses
- ✅ MD5 + CRC32C checksum validation
- ✅ MIME type detection
- ✅ Nested path support
- ✅ Error handling matching GCS behavior

This enables LocalStack-style local development with full upload/download capabilities for object storage testing.
