# GCLOUD CLI Compatibility Test Results

**Test Date:** January 11, 2026  
**gcloud Version:** Google Cloud SDK 551.0.0  
**Emulator Backend:** http://127.0.0.1:8080  

## Test Environment Setup

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir=$HOME

# Configure gcloud to use emulator
export PATH=$HOME/google-cloud-sdk/bin:$PATH
export STORAGE_EMULATOR_HOST="http://127.0.0.1:8080"
gcloud config set api_endpoint_overrides/storage "http://127.0.0.1:8080/storage/v1/"
gcloud config set api_endpoint_overrides/compute "http://127.0.0.1:8080/compute/v1/"
gcloud config set api_endpoint_overrides/iam "http://127.0.0.1:8080/"
gcloud config set auth/disable_credentials true
```

## Phase 1: gcloud CLI Compatibility Tests

### ✅ Storage Service (Cloud Storage)

#### Test 1: List Buckets
**Command:**
```bash
gcloud storage buckets list --project=demo-project
```

**Result:** ✅ **SUCCESS**
```yaml
---
creation_time: 2026-01-10T13:33:22+0000
default_storage_class: STANDARD
location: US
name: demo-images
storage_url: gs://demo-images/
update_time: 2026-01-10T13:33:22+0000
versioning_enabled: true
---
creation_time: 2026-01-10T13:33:22+0000
default_storage_class: STANDARD
location: US
name: demo-documents
storage_url: gs://demo-documents/
update_time: 2026-01-10T13:33:22+0000
versioning_enabled: false
---
creation_time: 2026-01-10T13:33:22+0000
default_storage_class: NEARLINE
location: US
name: demo-logs
storage_url: gs://demo-logs/
update_time: 2026-01-10T13:33:22+0000
versioning_enabled: false
```

**Analysis:** gcloud CLI successfully parsed the bucket list response after fixing `projectNumber` to return a string representation of a numeric value.

---

### ✅ Compute Engine Service

#### Test 2: List Zones
**Command:**
```bash
gcloud compute zones list --project=demo-project
```

**Result:** ✅ **SUCCESS**
```
NAME            REGION        STATUS  NEXT_MAINTENANCE  TURNDOWN_DATE
us-central1-a   us-central1   UP
us-central1-b   us-central1   UP
us-east1-a      us-east1      UP
us-west1-a      us-west1      UP
europe-west1-a  europe-west1  UP
asia-east1-a    asia-east1    UP
```

**Analysis:** gcloud CLI successfully parsed zones after adding `selfLink` field to Zone model.

---

#### Test 3: List Instances
**Command:**
```bash
gcloud compute instances list --project=demo-project --zones=us-central1-a
```

**Result:** ✅ **SUCCESS**
```
NAME           ZONE           MACHINE_TYPE   PREEMPTIBLE  INTERNAL_IP   EXTERNAL_IP    STATUS
web-server-01  us-central1-a  n1-standard-1               10.128.0.254  35.100.175.40  RUNNING
```

**Analysis:** gcloud CLI successfully listed VM instances with Docker container backing.

---

### ✅ IAM Service

#### Test 4: List Service Accounts
**Command:**
```bash
gcloud iam service-accounts list --project=demo-project
```

**Result:** ✅ **SUCCESS**
```
DISPLAY NAME          EMAIL                                         DISABLED
Test Service Account  test-sa@demo-project.iam.gserviceaccount.com  False
```

**Analysis:** gcloud CLI successfully parsed service accounts without requiring changes (already GCP-compliant).

---

## Issues Found and Fixed

### Issue 1: projectNumber Type Mismatch
**Error:**
```
ERROR: gcloud crashed (InvalidDataFromServerError): Expected type (<class 'int'>,) 
for field projectNumber, found demo-project (type <class 'str'>)
```

**Root Cause:** Bucket model was returning `project_id` (string) for `projectNumber` field, but GCP expects a numeric string.

**Fix Applied:**
1. Added `project_number` field to Project model (BIGINT)
2. Generate numeric project number from hash of project_id
3. Return as string in bucket serialization

**Files Modified:**
- `app/models/project.py` - Added project_number field
- `app/models/bucket.py` - Generate numeric project number from project_id hash
- `migrations/006_add_project_number.py` - Database migration

---

### Issue 2: Missing selfLink Fields
**Error:**
```
ERROR: gcloud crashed (KeyError): 'selfLink'
```

**Root Cause:** Compute Engine zone and instance responses missing required `selfLink` field.

**Fix Applied:**
1. Added `selfLink` to Zone.to_dict() method
2. Added `selfLink` to ComputeInstance.to_dict() method
3. Added `selfLink` to MachineType.to_dict() method
4. Formatted zone and machineType as full URLs (GCP-compliant)

**Files Modified:**
- `app/models/compute.py` - Updated Zone, MachineType, ComputeInstance models
- `app/handlers/compute_handler.py` - Pass project_id to to_dict() calls

---

## GCP API Compliance Improvements

### 1. Bucket Response Format
```json
{
  "id": "demo-images",
  "name": "demo-images",
  "projectNumber": "871934685274",  // ✅ Now numeric string
  "location": "US",
  "storageClass": "STANDARD",
  "versioning": {"enabled": true},
  "timeCreated": "2026-01-10T13:33:22.092Z",
  "updated": "2026-01-10T13:33:22.092Z"
}
```

### 2. Zone Response Format
```json
{
  "id": "8716392745018293746",
  "name": "us-central1-a",
  "region": "https://www.googleapis.com/compute/v1/projects/demo-project/regions/us-central1",
  "status": "UP",
  "description": "Zone us-central1-a",
  "selfLink": "https://www.googleapis.com/compute/v1/projects/demo-project/zones/us-central1-a"
}
```

### 3. Instance Response Format
```json
{
  "id": "2847562938475629384",
  "name": "web-server-01",
  "zone": "https://www.googleapis.com/compute/v1/projects/demo-project/zones/us-central1-a",
  "machineType": "https://www.googleapis.com/compute/v1/projects/demo-project/zones/us-central1-a/machineTypes/n1-standard-1",
  "status": "RUNNING",
  "creationTimestamp": "2026-01-10T13:33:22.125Z",
  "selfLink": "https://www.googleapis.com/compute/v1/projects/demo-project/zones/us-central1-a/instances/web-server-01",
  "networkInterfaces": [
    {
      "network": "https://www.googleapis.com/compute/v1/projects/demo-project/global/networks/default",
      "networkIP": "10.128.0.254",
      "accessConfigs": [
        {
          "natIP": "35.100.175.40",
          "type": "ONE_TO_ONE_NAT",
          "name": "External NAT"
        }
      ]
    }
  ],
  "_emulator": {
    "containerId": "49c0c313d089...",
    "containerName": "gce-demo-project-us-central1-a-web-server-01"
  }
}
```

---

## Test Summary

| Service | Command | Status | Notes |
|---------|---------|--------|-------|
| Storage | `gcloud storage buckets list` | ✅ | All 3 buckets listed correctly |
| Compute | `gcloud compute zones list` | ✅ | All 6 zones listed correctly |
| Compute | `gcloud compute instances list` | ✅ | Instance with Docker backing works |
| IAM | `gcloud iam service-accounts list` | ✅ | Service account listed correctly |

---

## Remaining Work

### Priority 1: Storage Operations
- [ ] Test object upload (`gcloud storage cp`)
- [ ] Test object download
- [ ] Test object deletion
- [ ] Implement missing storage APIs for object CRUD

### Priority 2: Service Account Keys
- [ ] Fix service account key JSON format
- [ ] Test `gcloud iam service-accounts keys create`
- [ ] Verify key format matches GCP exactly

### Priority 3: Python SDK Testing
- [ ] Install `google-cloud-storage`
- [ ] Test Storage client
- [ ] Install `google-cloud-compute`
- [ ] Test Compute client
- [ ] Test IAM client

### Priority 4: Advanced Features
- [ ] Application Default Credentials (ADC) support
- [ ] OAuth2 token validation
- [ ] gRPC API support
- [ ] Discovery API implementation

---

## Success Criteria Status

✅ **ACHIEVED:**
- Real `gcloud` CLI works WITHOUT modification
- Developer can list buckets, zones, instances, and service accounts
- API responses match GCP format expectations
- No custom wrappers or command modifications required

🟡 **PARTIAL:**
- Storage object operations need more API endpoints
- Service account key format needs verification

⏸️ **NOT TESTED:**
- Official Google Cloud SDKs
- Application Default Credentials
- Complete GCP tutorial workflows

---

## Conclusion

The emulator now achieves **real gcloud CLI compatibility** for listing operations across Storage, Compute, and IAM services. The key insight from testing is that gcloud CLI is very strict about response format:

1. **Field types matter** - `projectNumber` must be numeric (even if returned as string)
2. **selfLink is required** - Compute resources must include full self-referential URLs
3. **Field names matter** - camelCase vs snake_case must match GCP exactly

The next critical step is testing with official Google Cloud Python SDKs to ensure they can authenticate and perform operations against the emulator.
