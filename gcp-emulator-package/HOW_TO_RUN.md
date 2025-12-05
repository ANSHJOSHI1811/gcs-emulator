# 🚀 GCS Storage Emulator - Quick Start Guide

**LocalStack-style operations for GCS Emulator**

---

## 📋 Quick Setup

### 1. Prerequisites
- Python 3.12+
- PostgreSQL 17 (running)
- Virtual environment activated

### 2. Start PostgreSQL
```powershell
Start-Service postgresql-x64-17
```

### 3. Activate Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Start the Server
```powershell
python run.py
```

**You should see:**
```
Starting GCS Emulator on http://127.0.0.1:8080
 * Running on http://0.0.0.0:8080
```

---

## 🪣 Bucket Operations

### ⚡ Method 1: CLI Commands (LocalStack-Style - RECOMMENDED)

**Just like `awslocal s3`, we now have `gcslocal`!**

#### Create Bucket
```powershell
python gcslocal.py mb gs://my-bucket
```
**Output:**
```
✅ Bucket created: gs://my-bucket
  Location: US
  Storage Class: STANDARD
```

#### Create Bucket in Different Location
```powershell
python gcslocal.py mb gs://eu-bucket --location EU
python gcslocal.py mb gs://asia-bucket --location ASIA --storage-class COLDLINE
```

#### List All Buckets
```powershell
python gcslocal.py ls
```
**Output:**
```
Buckets in project 'test-project':
  gs://my-bucket/
    Location: US, Class: STANDARD, Created: 2025-11-28
  gs://eu-bucket/
    Location: EU, Class: STANDARD, Created: 2025-11-28
```

#### List Objects in Bucket
```powershell
python gcslocal.py ls gs://my-bucket/
```
**Output:**
```
Objects in gs://my-bucket/
  file1.txt (2.5 KB, updated: 2025-11-28)
  folder/file2.pdf (150.23 KB, updated: 2025-11-28)
```

#### Remove Bucket
```powershell
python gcslocal.py rb gs://my-bucket
```
**Output:**
```
✅ Bucket removed: gs://my-bucket
```

#### Upload File (Coming Soon)
```powershell
python gcslocal.py cp file.txt gs://my-bucket/file.txt
```

#### Download File (Coming Soon)
```powershell
python gcslocal.py cp gs://my-bucket/file.txt local-file.txt
```

#### Remove Object
```powershell
python gcslocal.py rm gs://my-bucket/file.txt
```

#### Custom Project
```powershell
python gcslocal.py mb gs://my-bucket --project my-other-project
```

---

### Method 2: Using Python SDK

**Create a file `bucket_operations.py`:**

```python
import os
from google.cloud import storage

# Point to local emulator
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'

# Create client (no credentials needed!)
client = storage.Client(project='my-project')

# ============================================
# 1. CREATE BUCKET
# ============================================
print("1. Creating bucket...")
bucket = client.create_bucket('my-test-bucket', location='US')
print(f"✅ Bucket '{bucket.name}' created successfully!\n")

# ============================================
# 2. LIST ALL BUCKETS
# ============================================
print("2. Listing all buckets...")
buckets = list(client.list_buckets())
for b in buckets:
    print(f"   - {b.name} (Location: {b.location}, Class: {b.storage_class})")
print()

# ============================================
# 3. GET BUCKET DETAILS
# ============================================
print("3. Getting bucket details...")
bucket = client.get_bucket('my-test-bucket')
print(f"   Name: {bucket.name}")
print(f"   Location: {bucket.location}")
print(f"   Storage Class: {bucket.storage_class}")
print(f"   Created: {bucket.time_created}")
print()

# ============================================
# 4. CHECK IF BUCKET EXISTS
# ============================================
print("4. Checking if bucket exists...")
try:
    bucket = client.get_bucket('my-test-bucket')
    print(f"✅ Bucket exists: {bucket.name}\n")
except:
    print("❌ Bucket does not exist\n")

# ============================================
# 5. CREATE BUCKET WITH CUSTOM SETTINGS
# ============================================
print("5. Creating bucket with custom settings...")
bucket = client.create_bucket(
    'premium-bucket',
    location='EUROPE',
)
bucket.storage_class = 'COLDLINE'
bucket.patch()
print(f"✅ Bucket '{bucket.name}' created with:")
print(f"   Location: {bucket.location}")
print(f"   Storage Class: {bucket.storage_class}\n")

# ============================================
# 6. DELETE BUCKET
# ============================================
print("6. Deleting bucket...")
bucket = client.get_bucket('my-test-bucket')
bucket.delete()
print(f"✅ Bucket 'my-test-bucket' deleted successfully!\n")

# ============================================
# 7. LIST REMAINING BUCKETS
# ============================================
print("7. Listing remaining buckets...")
buckets = list(client.list_buckets())
print(f"   Total buckets: {len(buckets)}")
for b in buckets:
    print(f"   - {b.name}")
```

**Run it:**
```powershell
# Make sure server is running in another terminal
python bucket_operations.py
```

**Expected Output:**
```
1. Creating bucket...
✅ Bucket 'my-test-bucket' created successfully!

2. Listing all buckets...
   - my-test-bucket (Location: US, Class: STANDARD)

3. Getting bucket details...
   Name: my-test-bucket
   Location: US
   Storage Class: STANDARD
   Created: 2025-11-28 10:30:15

4. Checking if bucket exists...
✅ Bucket exists: my-test-bucket

5. Creating bucket with custom settings...
✅ Bucket 'premium-bucket' created with:
   Location: EUROPE
   Storage Class: COLDLINE

6. Deleting bucket...
✅ Bucket 'my-test-bucket' deleted successfully!

7. Listing remaining buckets...
   Total buckets: 1
   - premium-bucket
```

---

### Method 3: Using REST API (curl)

**Open a new PowerShell terminal:**

#### Create Bucket
```powershell
curl -X POST "http://localhost:8080/storage/v1/b?project=my-project" `
  -H "Content-Type: application/json" `
  -d '{"name": "rest-bucket", "location": "US", "storageClass": "STANDARD"}'
```

**Response:**
```json
{
  "id": "rest-bucket-abc123",
  "name": "rest-bucket",
  "projectNumber": "my-project",
  "location": "US",
  "storageClass": "STANDARD",
  "timeCreated": "2025-11-28T10:30:15Z",
  "updated": "2025-11-28T10:30:15Z"
}
```

#### List Buckets
```powershell
curl "http://localhost:8080/storage/v1/b?project=my-project"
```

**Response:**
```json
{
  "kind": "storage#buckets",
  "items": [
    {
      "name": "rest-bucket",
      "location": "US",
      "storageClass": "STANDARD"
    }
  ]
}
```

#### Get Bucket
```powershell
curl "http://localhost:8080/storage/v1/b/rest-bucket"
```

#### Delete Bucket
```powershell
curl -X DELETE "http://localhost:8080/storage/v1/b/rest-bucket"
```

**Response:** `204 No Content` (success)

---

### Method 4: Using Python Requests Library

**Create a file `rest_operations.py`:**

```python
import requests
import json

BASE_URL = "http://localhost:8080/storage/v1"
PROJECT = "my-project"

print("=" * 60)
print("REST API BUCKET OPERATIONS")
print("=" * 60)

# 1. CREATE BUCKET
print("\n1. Creating bucket...")
response = requests.post(
    f"{BASE_URL}/b?project={PROJECT}",
    json={
        "name": "api-bucket",
        "location": "ASIA",
        "storageClass": "STANDARD"
    }
)
if response.status_code == 201:
    print(f"✅ Bucket created: {response.json()['name']}")
    print(f"   Status: {response.status_code}")
else:
    print(f"❌ Error: {response.status_code}")
    print(f"   {response.json()}")

# 2. LIST BUCKETS
print("\n2. Listing buckets...")
response = requests.get(f"{BASE_URL}/b?project={PROJECT}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Found {len(data.get('items', []))} buckets:")
    for bucket in data.get('items', []):
        print(f"   - {bucket['name']} ({bucket['location']})")
else:
    print(f"❌ Error: {response.status_code}")

# 3. GET BUCKET DETAILS
print("\n3. Getting bucket details...")
response = requests.get(f"{BASE_URL}/b/api-bucket")
if response.status_code == 200:
    bucket = response.json()
    print(f"✅ Bucket details:")
    print(f"   Name: {bucket['name']}")
    print(f"   Location: {bucket['location']}")
    print(f"   Storage Class: {bucket['storageClass']}")
    print(f"   Created: {bucket['timeCreated']}")
else:
    print(f"❌ Error: {response.status_code}")

# 4. TRY TO GET NON-EXISTENT BUCKET
print("\n4. Trying to get non-existent bucket...")
response = requests.get(f"{BASE_URL}/b/does-not-exist")
if response.status_code == 404:
    print(f"✅ Correctly returned 404")
    print(f"   Error: {response.json()['error']['message']}")
else:
    print(f"❌ Unexpected status: {response.status_code}")

# 5. TRY TO CREATE DUPLICATE BUCKET
print("\n5. Trying to create duplicate bucket...")
response = requests.post(
    f"{BASE_URL}/b?project={PROJECT}",
    json={"name": "api-bucket", "location": "US"}
)
if response.status_code == 409:
    print(f"✅ Correctly returned 409 Conflict")
    print(f"   Error: {response.json()['error']['message']}")
else:
    print(f"❌ Unexpected status: {response.status_code}")

# 6. DELETE BUCKET
print("\n6. Deleting bucket...")
response = requests.delete(f"{BASE_URL}/b/api-bucket")
if response.status_code == 204:
    print(f"✅ Bucket deleted successfully")
else:
    print(f"❌ Error: {response.status_code}")

# 7. VERIFY DELETION
print("\n7. Verifying deletion...")
response = requests.get(f"{BASE_URL}/b?project={PROJECT}")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Remaining buckets: {len(data.get('items', []))}")
else:
    print(f"❌ Error: {response.status_code}")

print("\n" + "=" * 60)
print("OPERATIONS COMPLETE")
print("=" * 60)
```

**Run it:**
```powershell
python rest_operations.py
```

---

## 🧪 Test All Operations

**Run the test suite to verify all operations work:**

```powershell
# Test all bucket operations
python -m pytest tests/test_bucket_flow_e2e.py -v

# Expected output:
# test_create_bucket_success PASSED
# test_create_bucket_duplicate_conflict PASSED
# test_list_buckets_scoped_by_project PASSED
# test_get_bucket_metadata PASSED
# test_get_bucket_not_found PASSED
# test_delete_bucket_success PASSED
# test_delete_bucket_not_empty PASSED
# test_full_bucket_lifecycle PASSED
```

---

## 📋 Quick Reference

### Common Commands

```powershell
# ============================================
# LOCALSTACK-STYLE CLI (RECOMMENDED)
# ============================================

# Create bucket
python gcslocal.py mb gs://my-bucket

# List buckets
python gcslocal.py ls

# List objects in bucket
python gcslocal.py ls gs://my-bucket/

# Delete bucket
python gcslocal.py rb gs://my-bucket

# Remove object
python gcslocal.py rm gs://my-bucket/file.txt

# Custom location
python gcslocal.py mb gs://bucket --location EU

# Custom project
python gcslocal.py mb gs://bucket --project my-project

# ============================================
# OTHER METHODS
# ============================================

# Start server
python run.py

# Run Python SDK examples
python bucket_operations.py

# Run REST API examples
python rest_operations.py

# Test all operations
python -m pytest tests/test_bucket_flow_e2e.py -v

# Check server health
curl http://localhost:8080/health

# View logs
Get-Content logs/emulator.log -Tail 20

# Check database
psql -U gcs_user -d gcs_emulator -c "SELECT name, location FROM buckets;"
```

### Bucket Operation Summary

| Operation | CLI Command | SDK Method | REST Endpoint |
|-----------|------------|-----------|---------------|
| Create Bucket | `python gcslocal.py mb gs://bucket` | `client.create_bucket()` | `POST /storage/v1/b` |
| List Buckets | `python gcslocal.py ls` | `client.list_buckets()` | `GET /storage/v1/b` |
| List Objects | `python gcslocal.py ls gs://bucket/` | `bucket.list_blobs()` | `GET /storage/v1/b/{bucket}/o` |
| Get Bucket | N/A | `client.get_bucket(name)` | `GET /storage/v1/b/{bucket}` |
| Delete Bucket | `python gcslocal.py rb gs://bucket` | `bucket.delete()` | `DELETE /storage/v1/b/{bucket}` |
| Remove Object | `python gcslocal.py rm gs://bucket/file` | `blob.delete()` | `DELETE /storage/v1/b/{bucket}/o/{object}` |
| Upload | `python gcslocal.py cp file gs://bucket/` | `bucket.blob().upload_from_filename()` | `POST /upload/storage/v1/b/{bucket}/o` |
| Download | `python gcslocal.py cp gs://bucket/file .` | `blob.download_to_filename()` | `GET /storage/v1/b/{bucket}/o/{object}?alt=media` |

---

**🎉 That's it! You now know how to start the server and perform all bucket operations.**
