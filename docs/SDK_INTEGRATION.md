# SDK Integration Guide

## Overview

Your GCS emulator is **fully compatible** with the official Google Cloud Storage Python SDK. This means you can use the real `google-cloud-storage` library for development and testing without connecting to actual GCP services.

## Quick Start

### 1. Install SDK

```bash
pip install google-cloud-storage
```

### 2. Point SDK to Emulator

**Method A: Environment Variable (Recommended)**

```python
import os
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'
```

**Method B: Client Options**

```python
from google.cloud import storage
from google.auth.credentials import AnonymousCredentials

client = storage.Client(
    project='my-project',
    credentials=AnonymousCredentials(),
    client_options={"api_endpoint": "http://localhost:8080"}
)
```

### 3. Use SDK Normally

```python
from google.cloud import storage

# SDK automatically detects STORAGE_EMULATOR_HOST
client = storage.Client(project='test-project')

# All operations work exactly like real GCP
bucket = client.create_bucket('my-bucket')
blob = bucket.blob('file.txt')
blob.upload_from_string('Hello World!')
```

## How It Works

### Request Flow

```
Your Code
    ↓
google-cloud-storage SDK
    ↓
Detects STORAGE_EMULATOR_HOST env var
    ↓
Sends HTTP requests to localhost:8080 instead of googleapis.com
    ↓
Your Flask Emulator (app/handlers/*)
    ↓
PostgreSQL Database + Local File Storage
```

### Authentication

The emulator accepts requests **without valid OAuth2 tokens**:

```python
from google.auth.credentials import AnonymousCredentials

# This works locally (no real Google account needed)
client = storage.Client(
    project='test-project',
    credentials=AnonymousCredentials()
)
```

The emulator's middleware (`app/factory.py:handle_sdk_auth`) logs but doesn't validate the `Authorization` header in `MOCK_AUTH_ENABLED` mode.

### URL Path Mapping

The SDK sends requests to these paths (already implemented in your emulator):

| SDK Method | HTTP Request | Emulator Route |
|------------|-------------|----------------|
| `client.list_buckets()` | `GET /storage/v1/b?project=X` | `buckets_bp.list_buckets()` |
| `client.create_bucket('name')` | `POST /storage/v1/b?project=X` | `buckets_bp.create_bucket()` |
| `client.get_bucket('name')` | `GET /storage/v1/b/name` | `buckets_bp.get_bucket()` |
| `bucket.delete()` | `DELETE /storage/v1/b/name` | `buckets_bp.delete_bucket()` |
| `bucket.list_blobs()` | `GET /storage/v1/b/name/o` | `objects_bp.list_objects()` |
| `blob.upload_from_string()` | `POST /storage/v1/b/name/o?name=X` | `objects_bp.upload_object()` |
| `blob.download_as_bytes()` | `GET /storage/v1/b/name/o/X?alt=media` | `objects_bp.get_object()` |
| `blob.delete()` | `DELETE /storage/v1/b/name/o/X` | `objects_bp.delete_object()` |

## Configuration Options

### Environment Variables

```bash
# Required: Points SDK to your emulator
export STORAGE_EMULATOR_HOST=http://localhost:8080

# Optional: Emulator configuration
export SDK_COMPATIBLE_MODE=true        # Enable SDK compatibility features
export MOCK_AUTH_ENABLED=true          # Accept any auth token
export STRICT_GCS_MODE=false           # Enforce strict GCS field validation
```

### Flask Config (app/config.py)

```python
class Config:
    SDK_COMPATIBLE_MODE = True   # SDK features enabled
    MOCK_AUTH_ENABLED = True     # Accept mock credentials
    STRICT_GCS_MODE = False      # Lenient validation
```

## Testing Your Integration

### Run Quick Example

```bash
# Terminal 1: Start emulator
python run.py

# Terminal 2: Run example
python example_sdk_usage.py
```

### Run Full Test Suite

```bash
python test_sdk_integration.py
```

This runs 6 test categories:
1. ✅ SDK Connection
2. ✅ Bucket Operations (list, create, get, delete)
3. ✅ Object Operations (upload, download, list, get)
4. ✅ Prefix & Delimiter Listing (folder simulation)
5. ✅ Delete Operations
6. ✅ Error Handling (404, 409, 400)

## Advanced Usage

### Multiple Projects

```python
client1 = storage.Client(project='project-a')
client2 = storage.Client(project='project-b')

# Each client has isolated buckets
client1.create_bucket('bucket-a')
client2.create_bucket('bucket-b')
```

### Folder Simulation with Prefixes

```python
bucket = client.get_bucket('my-bucket')

# Upload files with "/" in names (simulates folders)
bucket.blob('docs/readme.txt').upload_from_string('...')
bucket.blob('docs/guide.txt').upload_from_string('...')
bucket.blob('images/logo.png').upload_from_file('logo.png')

# List "root level" files and folders
for blob in bucket.list_blobs(delimiter='/'):
    print(f"File: {blob.name}")

for prefix in bucket.list_blobs(delimiter='/').prefixes:
    print(f"Folder: {prefix}")

# List files inside "docs/" folder
for blob in bucket.list_blobs(prefix='docs/'):
    print(f"Doc: {blob.name}")
```

### Streaming Large Files

```python
# Upload large file in chunks
blob = bucket.blob('large-file.bin')
with open('large-file.bin', 'rb') as f:
    blob.upload_from_file(f, content_type='application/octet-stream')

# Download large file in chunks
with open('downloaded.bin', 'wb') as f:
    blob.download_to_file(f)
```

### Metadata and Content Types

```python
blob = bucket.blob('document.pdf')
blob.content_type = 'application/pdf'
blob.metadata = {'author': 'John Doe', 'version': '1.0'}
blob.upload_from_filename('doc.pdf')

# Retrieve metadata
blob.reload()
print(f"Content-Type: {blob.content_type}")
print(f"Metadata: {blob.metadata}")
print(f"MD5: {blob.md5_hash}")
print(f"Size: {blob.size} bytes")
```

## Troubleshooting

### Issue: SDK still connects to real GCP

**Solution:** Ensure environment variable is set **before** importing SDK:

```python
# ❌ Wrong order
from google.cloud import storage
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'

# ✅ Correct order
import os
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'
from google.cloud import storage
```

### Issue: Authentication errors

**Solution:** Use `AnonymousCredentials()`:

```python
from google.auth.credentials import AnonymousCredentials

client = storage.Client(
    project='test-project',
    credentials=AnonymousCredentials()
)
```

### Issue: 404 errors on valid endpoints

**Solution:** Check Flask routes are registered with `/storage/v1` prefix:

```bash
# Should see these routes
GET    /storage/v1/b
POST   /storage/v1/b
GET    /storage/v1/b/<bucket>
DELETE /storage/v1/b/<bucket>
GET    /storage/v1/b/<bucket>/o
POST   /storage/v1/b/<bucket>/o
...
```

### Issue: Bucket names rejected

**Solution:** Follow GCS naming rules:
- 3-63 characters
- Lowercase letters, numbers, hyphens, periods, underscores
- Must start and end with alphanumeric

```python
# ✅ Valid names
'my-bucket', 'test-bucket-123', 'bucket.name'

# ❌ Invalid names
'My-Bucket' (uppercase), 'ab' (too short), '-bucket' (starts with hyphen)
```

## Switching to Real GCP

When ready to deploy, just remove the emulator configuration:

```python
# Local development
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'
client = storage.Client(project='test-project', credentials=AnonymousCredentials())

# Production (remove emulator config)
# Remove: os.environ['STORAGE_EMULATOR_HOST']
client = storage.Client(project='production-project')  # Uses real GCP credentials
```

**No code changes needed!** The SDK automatically uses real GCP when `STORAGE_EMULATOR_HOST` is not set.

## Comparison: Direct HTTP vs SDK

### Direct HTTP (Your Current Postman Tests)

```python
import requests

response = requests.post(
    'http://localhost:8080/storage/v1/b',
    params={'project': 'test-project'},
    json={'name': 'my-bucket', 'location': 'US'}
)
```

### Using SDK (Recommended)

```python
from google.cloud import storage

client = storage.Client(project='test-project')
bucket = client.create_bucket('my-bucket', location='US')
```

**Advantages of SDK:**
- ✅ Automatic retry logic
- ✅ Built-in error handling
- ✅ Type safety (Python objects, not raw JSON)
- ✅ Streaming support for large files
- ✅ Same code works in production (just remove emulator config)
- ✅ Better documentation and IDE support

## Next Steps

1. ✅ **Test basic operations**: `python example_sdk_usage.py`
2. ✅ **Run full test suite**: `python test_sdk_integration.py`
3. ✅ **Integrate into your app**: Replace direct HTTP calls with SDK
4. ⏭️ **Add more features**: IAM, signed URLs, lifecycle policies
5. ⏭️ **Performance testing**: Benchmark SDK operations
6. ⏭️ **Docker deployment**: Package emulator with SDK tests

## Resources

- [Official SDK Docs](https://googleapis.dev/python/storage/latest/)
- [GCS API Reference](https://cloud.google.com/storage/docs/json_api/v1)
- Your emulator endpoints: `http://localhost:8080/storage/v1`
