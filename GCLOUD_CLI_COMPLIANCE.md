# GCP CLI Compatibility Implementation Plan

## Current Status Assessment

### ✅ What We Have
1. **REST APIs** matching GCP patterns for Storage, IAM, and Compute
2. **OAuth2 Mock Endpoints** (`/token`, `/o/oauth2/v2/auth`, `/oauth2/v1/tokeninfo`)
3. **IAM Enforcement** via `@require_permission` decorators
4. **Environment Variable Support** (STORAGE_EMULATOR_HOST, CLOUDSDK_API_ENDPOINT_OVERRIDES_*)
5. **Database-backed state** with proper resource hierarchy

### ❌ Gaps Identified

1. **gcloud CLI Not Tested** - No validation that real gcloud commands work
2. **Authentication Flow** - OAuth2 mock may not fully satisfy gcloud auth expectations
3. **API Endpoint Registration** - Need to verify all endpoints match GCP exactly
4. **Error Response Format** - Must match GCP error patterns precisely
5. **Service Account Key Format** - Keys must match GCP's JSON key format

---

## Implementation Requirements (From Directive)

### 1. Real gcloud CLI Must Work

**Commands that MUST work:**
```bash
gcloud auth login                          # Mock login flow
gcloud auth activate-service-account       # Mock service account auth
gcloud config set project demo-project     # Set project context
gcloud iam service-accounts list           # List service accounts
gcloud storage buckets list                # List storage buckets
gcloud storage ls                          # List bucket contents
gcloud compute zones list                  # List compute zones
gcloud compute instances list              # List instances
```

**Current Implementation:**
- ✅ REST endpoints exist
- ❌ Not tested with real gcloud CLI
- ⚠️  OAuth2 flow may need adjustments

### 2. SDK Compatibility

**Python SDK Example:**
```python
from google.cloud import storage, compute_v1, iam_admin_v1

# Must work with environment variables:
# export STORAGE_EMULATOR_HOST="http://127.0.0.1:8080"
# export CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE="http://127.0.0.1:8080/compute/v1/"
# export CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM="http://127.0.0.1:8080/"

client = storage.Client(project="demo-project")
buckets = list(client.list_buckets())
```

**Current Implementation:**
- ✅ REST APIs compatible
- ⚠️  Need to test with official SDKs
- ⚠️  Authentication token handling needs verification

### 3. Authentication Model

**Requirements:**
- Emulate OAuth2 flows (no real Google credentials)
- Generate valid-looking service account keys
- Token validation that satisfies SDK expectations
- Support for `gcloud auth application-default login`

**Current Implementation:**
- ✅ OAuth2 mock endpoints exist
- ❌ Service account key generation not GCP-compatible format
- ⚠️  Token validation needs enhancement
- ❌ Application Default Credentials (ADC) not implemented

### 4. IAM Enforcement

**Requirements:**
- Evaluate IAM policies on every request
- Return GCP-style errors (PERMISSION_DENIED, UNAUTHENTICATED)
- Can be bypassed with MOCK_AUTH_ENABLED=true
- Must work with service account impersonation

**Current Implementation:**
- ✅ `@require_permission` decorators on Storage APIs
- ✅ IAM policy evaluation logic exists
- ✅ Can be disabled via environment variable
- ⚠️  Error responses need to match GCP format exactly

---

## Action Items to Achieve Full Compliance

### Priority 1: Critical (Blocking gcloud CLI usage)

1. **Install and Test gcloud CLI**
   ```bash
   # Install gcloud on the emulator host
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   gcloud init
   ```

2. **Fix Service Account Key Format**
   - Keys must be valid GCP JSON format with all required fields:
     ```json
     {
       "type": "service_account",
       "project_id": "demo-project",
       "private_key_id": "...",
       "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
       "client_email": "test-sa@demo-project.iam.gserviceaccount.com",
       "client_id": "...",
       "auth_uri": "http://127.0.0.1:8080/o/oauth2/v2/auth",
       "token_uri": "http://127.0.0.1:8080/token",
       "auth_provider_x509_cert_url": "http://127.0.0.1:8080/oauth2/v1/certs",
       "client_x509_cert_url": "http://127.0.0.1:8080/robot/v1/metadata/x509/..."
     }
     ```

3. **Implement Application Default Credentials (ADC)**
   - Support `gcloud auth application-default login`
   - Store credentials in `~/.config/gcloud/application_default_credentials.json`
   - Mock OAuth2 consent flow

4. **Verify API Endpoint Compatibility**
   - Test each endpoint with real gcloud commands
   - Ensure response formats match GCP exactly
   - Add missing endpoints if any

### Priority 2: Important (Full SDK compatibility)

5. **Test with Official Python SDK**
   ```python
   # Test script to validate
   from google.cloud import storage, compute_v1, iam_admin_v1
   
   # Test Storage
   storage_client = storage.Client(project="demo-project")
   buckets = list(storage_client.list_buckets())
   
   # Test Compute
   compute_client = compute_v1.InstancesClient()
   instances = compute_client.list(project="demo-project", zone="us-central1-a")
   
   # Test IAM
   iam_client = iam_admin_v1.IAMClient()
   service_accounts = iam_client.list_service_accounts(name="projects/demo-project")
   ```

6. **Enhance Error Response Format**
   ```python
   # Must return GCP-style errors
   {
     "error": {
       "code": 403,
       "message": "Permission denied on resource project 'demo-project'",
       "status": "PERMISSION_DENIED",
       "details": [{
         "@type": "type.googleapis.com/google.rpc.ErrorInfo",
         "reason": "IAM_PERMISSION_DENIED",
         "domain": "googleapis.com",
         "metadata": {
           "permission": "storage.buckets.list",
           "resource": "projects/demo-project"
         }
       }]
     }
   }
   ```

7. **Add Missing OAuth2 Endpoints**
   - `/oauth2/v1/certs` - X.509 certificates (mock)
   - `/robot/v1/metadata/x509/{email}` - Service account certs
   - `/oauth2/v2/tokeninfo` - Enhanced token info

### Priority 3: Enhanced (Complete feature parity)

8. **Support gRPC APIs**
   - Add gRPC server alongside REST
   - Implement protobuf message definitions
   - Support both HTTP/1.1 and HTTP/2

9. **Implement Discovery API**
   - `/discovery/v1/apis/{api}/{version}/rest`
   - Allows dynamic API endpoint discovery

10. **Add Quota and Rate Limiting**
    - Emulate GCP quota behavior
    - Return 429 errors with proper headers

---

## Testing Strategy

### Phase 1: Basic gcloud Commands
```bash
# Set up environment
export STORAGE_EMULATOR_HOST="http://127.0.0.1:8080"
export CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE="http://127.0.0.1:8080/compute/v1/"
export CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM="http://127.0.0.1:8080/"

# Test each service
gcloud storage buckets list --project=demo-project
gcloud iam service-accounts list --project=demo-project
gcloud compute zones list --project=demo-project
gcloud compute instances list --project=demo-project --zone=us-central1-a
```

### Phase 2: SDK Integration
```python
# test_sdk_compatibility.py
import os
os.environ["STORAGE_EMULATOR_HOST"] = "http://127.0.0.1:8080"

from google.cloud import storage

client = storage.Client(project="demo-project")
for bucket in client.list_buckets():
    print(f"Bucket: {bucket.name}")
```

### Phase 3: Full Workflow
```bash
# Follow a real GCP tutorial end-to-end
# Example: Create bucket, upload object, set IAM policy
gcloud storage buckets create gs://test-bucket --project=demo-project
echo "test content" | gcloud storage cp - gs://test-bucket/test.txt
gcloud storage buckets add-iam-policy-binding gs://test-bucket \
  --member=serviceAccount:test-sa@demo-project.iam.gserviceaccount.com \
  --role=roles/storage.objectViewer
```

---

## Success Criteria

✅ **Implementation is correct if:**

1. A developer can follow any GCP tutorial
2. Use the real `gcloud` CLI
3. Point it at the emulator via environment variables
4. Complete the workflow **without changing commands**

❌ **Implementation is incomplete if:**

1. Commands require modification
2. Custom wrappers or tools are needed
3. SDK code requires changes to work
4. Authentication doesn't work like GCP

---

## Next Steps

1. **Install gcloud CLI** on the emulator host
2. **Test current implementation** with real gcloud commands
3. **Identify gaps** between expected and actual behavior
4. **Fix service account key format** to match GCP
5. **Add missing OAuth2 endpoints** for full auth flow
6. **Test with Python SDK** to verify compatibility
7. **Document any limitations** (e.g., gRPC not supported yet)

---

## Recommendation

**Immediate action:** Install gcloud CLI and run the Phase 1 test commands to see what works and what doesn't. This will give us concrete evidence of compliance and a clear list of remaining work.

Would you like me to proceed with installing gcloud and running these tests?
