# IAM Module Testing Guide 🎯

## ✅ SYSTEM STATUS

**Backend:** ✅ Running on `http://127.0.0.1:8080`
**Frontend:** ✅ Running on `http://localhost:3002`  
**Database:** ✅ IAM tables created with 7 predefined roles
**Compute Engine:** ⏸️  Disabled (not priority - IAM CODERED focus)

---

## 🔥 CODERED: Test IAM Now!

### 1. **Test via REST API (PowerShell)**

```powershell
# Create a service account
$body = @{
    accountId = "my-service-account"
    serviceAccount = @{
        displayName = "My SA"
        description = "Test service account"
    }
} | ConvertTo-Json

Invoke-RestMethod -Method POST `
    -Uri "http://127.0.0.1:8080/v1/projects/test-project/serviceAccounts" `
    -ContentType "application/json" `
    -Body $body

# List service accounts
Invoke-RestMethod -Uri "http://127.0.0.1:8080/v1/projects/test-project/serviceAccounts"

# Create a service account key
$keyBody = @{
    keyAlgorithm = "KEY_ALG_RSA_2048"
} | ConvertTo-Json

Invoke-RestMethod -Method POST `
    -Uri "http://127.0.0.1:8080/v1/projects/test-project/serviceAccounts/my-service-account@test-project.iam.gserviceaccount.com/keys" `
    -ContentType "application/json" `
    -Body $keyBody

# List all IAM roles
Invoke-RestMethod -Uri "http://127.0.0.1:8080/v1/roles"

# Get specific role
Invoke-RestMethod -Uri "http://127.0.0.1:8080/v1/roles/roles%2Fstorage.admin"
```

### 2. **Test via Python Script**

Save this as `test_iam_api.py`:

```python
import requests
import json

BASE_URL = "http://127.0.0.1:8080"
PROJECT_ID = "test-project"

# Create service account
sa_data = {
    "accountId": "python-test-sa",
    "serviceAccount": {
        "displayName": "Python Test SA",
        "description": "Created via Python"
    }
}

response = requests.post(
    f"{BASE_URL}/v1/projects/{PROJECT_ID}/serviceAccounts",
    json=sa_data
)
print("Create SA:", response.status_code)
print(json.dumps(response.json(), indent=2))

# List service accounts
response = requests.get(f"{BASE_URL}/v1/projects/{PROJECT_ID}/serviceAccounts")
print("\nList SAs:", response.status_code)
print(json.dumps(response.json(), indent=2))

# Create key
response = requests.post(
    f"{BASE_URL}/v1/projects/{PROJECT_ID}/serviceAccounts/python-test-sa@{PROJECT_ID}.iam.gserviceaccount.com/keys",
    json={"keyAlgorithm": "KEY_ALG_RSA_2048"}
)
print("\nCreate Key:", response.status_code)
print(json.dumps(response.json(), indent=2))

# List roles
response = requests.get(f"{BASE_URL}/v1/roles")
print("\nList Roles:", response.status_code)
print(f"Found {len(response.json().get('roles', []))} roles")
```

Run it:
```powershell
cd c:\Users\ansh.joshi\gcp_emulator\gcp-emulator-package
python test_iam_api.py
```

### 3. **Test via Frontend UI**

Open your browser to:
```
http://localhost:3002/services/iam
```

You'll see:
- **Service Accounts Page** - Create, list, enable/disable, delete service accounts
- **Roles Page** - Browse predefined roles and create custom roles
- **Beautiful UI** with React + TypeScript

### 4. **Configure gcloud CLI**

Make gcloud CLI point to your local emulator:

```powershell
# Set environment variables
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080"
$env:CLOUDSDK_AUTH_ACCESS_TOKEN = "mock-token-12345"

# Now use gcloud commands (they'll hit your local server!)
gcloud iam service-accounts create local-test-sa `
    --project=test-project `
    --display-name="Local Test SA"

gcloud iam service-accounts list --project=test-project

gcloud iam service-accounts keys create key.json `
    --iam-account=local-test-sa@test-project.iam.gserviceaccount.com
```

---

## 📋 Available IAM Endpoints

### Service Accounts
- `POST /v1/projects/{project}/serviceAccounts` - Create
- `GET /v1/projects/{project}/serviceAccounts` - List
- `GET /v1/projects/{project}/serviceAccounts/{email}` - Get
- `PATCH /v1/projects/{project}/serviceAccounts/{email}` - Update
- `DELETE /v1/projects/{project}/serviceAccounts/{email}` - Delete
- `POST /v1/projects/{project}/serviceAccounts/{email}:enable` - Enable
- `POST /v1/projects/{project}/serviceAccounts/{email}:disable` - Disable

### Service Account Keys
- `POST /v1/projects/{project}/serviceAccounts/{email}/keys` - Create key
- `GET /v1/projects/{project}/serviceAccounts/{email}/keys` - List keys
- `GET /v1/projects/{project}/serviceAccounts/{email}/keys/{key}` - Get key
- `DELETE /v1/projects/{project}/serviceAccounts/{email}/keys/{key}` - Delete key
- `POST /v1/projects/{project}/serviceAccounts/{email}/keys/{key}:disable` - Disable key

### IAM Policies
- `POST /v1/{resource}:getIamPolicy` - Get policy
- `POST /v1/{resource}:setIamPolicy` - Set policy
- `POST /v1/{resource}:testIamPermissions` - Test permissions

### Roles
- `GET /v1/roles` - List all roles
- `GET /v1/roles/{role}` - Get role
- `POST /v1/projects/{project}/roles` - Create custom role
- `GET /v1/projects/{project}/roles` - List project roles
- `GET /v1/projects/{project}/roles/{role}` - Get project role
- `PATCH /v1/projects/{project}/roles/{role}` - Update role
- `DELETE /v1/projects/{project}/roles/{role}` - Delete role
- `POST /v1/projects/{project}/roles/{role}:undelete` - Undelete role

---

## 🎭 Predefined Roles

Your emulator comes with 7 GCP-compatible roles:

1. **roles/storage.objectViewer** - View objects
2. **roles/storage.objectCreator** - Create objects  
3. **roles/storage.objectAdmin** - Full object control
4. **roles/storage.admin** - Full storage control
5. **roles/owner** - Full access (*)
6. **roles/editor** - Edit access (*)
7. **roles/viewer** - Read access (*.get, *.list)

---

## 🚀 Quick Test Sequence

```powershell
# 1. Create service account
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8080/v1/projects/test-project/serviceAccounts" -ContentType "application/json" -Body '{"accountId":"quick-test","serviceAccount":{"displayName":"Quick Test"}}'

# 2. List service accounts (should see 1)
Invoke-RestMethod -Uri "http://127.0.0.1:8080/v1/projects/test-project/serviceAccounts"

# 3. Create a key
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8080/v1/projects/test-project/serviceAccounts/quick-test@test-project.iam.gserviceaccount.com/keys" -ContentType "application/json" -Body '{}'

# 4. List roles (should see 7 predefined)
Invoke-RestMethod -Uri "http://127.0.0.1:8080/v1/roles"

# 5. Set IAM policy on bucket
$policy = @{
    policy = @{
        bindings = @(
            @{
                role = "roles/storage.objectViewer"
                members = @("serviceAccount:quick-test@test-project.iam.gserviceaccount.com")
            }
        )
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8080/v1/projects/test-project/buckets/my-bucket:setIamPolicy" -ContentType "application/json" -Body $policy
```

---

## 📖 Full Documentation

See these files for complete details:
- `docs/IAM_MODULE.md` - Complete API reference
- `docs/IAM_QUICKSTART.md` - Quick start guide
- `IAM_COMPLETE_IMPLEMENTATION.md` - Implementation overview

---

## ✨ What's Working

✅ Service account CRUD operations  
✅ Service account key generation (RSA 2048)  
✅ IAM policy get/set/test  
✅ Predefined role seeding  
✅ Custom role creation  
✅ Role management (create, update, delete, undelete)  
✅ Frontend UI (React + TypeScript)  
✅ REST API (GCP IAM API v1 compatible)  
✅ Mock authentication  
✅ Database persistence (PostgreSQL)  

---

## 🎉 SUCCESS!

Your GCP IAM emulator is **FULLY OPERATIONAL** and ready for `gcloud` CLI integration!

**Backend:** http://127.0.0.1:8080  
**Frontend:** http://localhost:3002  
**Status:** 🟢 ALL SYSTEMS GO - CODERED COMPLETE!
