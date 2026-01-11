# Compute Service Architecture Analysis & Solution

## Problem Statement

**Current Setup:**
- ✅ **IAM & Storage**: Running via Python Flask server (port 8080), accessible via terminal and real GCP SDK
- ✅ **Compute Engine**: Running in WSL2 Docker with separate architecture
- ❌ **Integration Issue**: GCP SDK commands for Compute will fail because of architectural mismatch

**The Challenge:**
When you run GCP SDK commands from Windows PowerShell:
1. IAM and Storage commands work → they hit Flask server on `localhost:8080`
2. Compute commands fail → Compute service runs inside WSL2 Docker environment

## Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Windows PowerShell                            │
│                                                                   │
│   GCP SDK / gcloud CLI                                          │
│   ├── Storage: CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE=:8080   │
│   └── IAM: CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM=:8080           │
│                                                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓ (Works - direct connection)
┌─────────────────────────────────────────────────────────────────┐
│              Flask Server (Port 8080) - Windows/WSL2            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  App Routes                                               │  │
│  │  ├── /storage/v1/*  → Storage Service → PostgreSQL      │  │
│  │  └── /v1/projects/* → IAM Service → PostgreSQL           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        WSL2 Ubuntu                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Docker Engine (/var/run/docker.sock)                    │  │
│  │  ├── PostgreSQL Container (gcp-postgres:5432)            │  │
│  │  ├── Compute Network (gcs-compute-net)                   │  │
│  │  └── VM Containers (simulated compute instances)         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                     ↑
                     │ (Issue: No SDK endpoint configured)
```

## Why It's a Problem

### 1. **Missing Compute Endpoint Override**
- IAM has: `CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM=http://127.0.0.1:8080/`
- Storage has: `CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE=http://127.0.0.1:8080/`
- Compute has: ❌ **NOT CONFIGURED** → defaults to real GCP API

### 2. **Compute Routes Exist But Unreachable**
The Flask app already has Compute routes:
- `GET /compute/v1/projects/{project}/zones/{zone}/instances`
- `POST /compute/v1/projects/{project}/zones/{zone}/instances`
- `DELETE /compute/v1/projects/{project}/zones/{zone}/instances/{instance}`

But GCP SDK doesn't know to use them!

### 3. **Docker Backend Confusion**
Compute service uses Docker containers in WSL2 to simulate VMs, but the API endpoints are still exposed through the same Flask server as IAM/Storage.

## Solution Options

### ✅ **Option 1: Add Compute Endpoint Override (RECOMMENDED)**

**What to do:**
Add one more environment variable to redirect Compute API calls to your local emulator.

**Implementation:**

```powershell
# Add to your PowerShell profile or setup script
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE = "http://127.0.0.1:8080/"
```

**Why it works:**
- Flask server already handles all three services on port 8080
- Compute routes are already implemented
- Docker backend is already configured in WSL2
- No code changes needed!

**Full setup:**

```powershell
# Complete environment configuration
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080/"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080/"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE = "http://127.0.0.1:8080/"
$env:CLOUDSDK_CORE_PROJECT = "test-project"
```

### ✅ **Option 2: Use Proxy Mode for Compute**

**What to do:**
Configure proxy mode to route Compute to real GCP while keeping Storage/IAM local.

**Implementation:**

```powershell
# Setup proxy mode
$env:GCP_PROXY_MODE = "proxy"
$env:GCP_LOCAL_APIS = "storage,iam"  # Only these are local
$env:GCP_PROJECT_ID = "your-real-gcp-project"
$env:GOOGLE_APPLICATION_CREDENTIALS = "path\to\credentials.json"

# All Compute calls go to real GCP automatically
```

**Why this works:**
- Proxy middleware already exists in your codebase
- Routes Compute to real GCP seamlessly
- Storage and IAM stay local (free)
- Compute uses real GCP resources (costs apply)

**When to use:**
- You want to test against real GCP Compute Engine
- You need actual VM features not in emulator
- You're willing to pay for real GCP usage

### ❌ **Option 3: Separate Compute Server** (NOT RECOMMENDED)

Run Compute on a different port and configure separately.

**Why not recommended:**
- Unnecessary complexity
- Requires code refactoring
- Breaks existing architecture
- No real benefit over Option 1

## Detailed Solution: Option 1 (Step-by-Step)

### Step 1: Update Setup Scripts

**File: `setup-gcloud-emulator.ps1`** (create if doesn't exist)

```powershell
# Complete GCP Emulator Setup Script

Write-Host "=== GCP Emulator Configuration ===" -ForegroundColor Cyan
Write-Host ""

# Set endpoint overrides for all services
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080/"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080/"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE = "http://127.0.0.1:8080/"

# Set project
$env:CLOUDSDK_CORE_PROJECT = "test-project"

# Disable auth for local emulator
$env:CLOUDSDK_AUTH_DISABLE = "true"

Write-Host "✓ Storage API → http://127.0.0.1:8080/" -ForegroundColor Green
Write-Host "✓ IAM API → http://127.0.0.1:8080/" -ForegroundColor Green
Write-Host "✓ Compute API → http://127.0.0.1:8080/" -ForegroundColor Green
Write-Host "✓ Project: test-project" -ForegroundColor Green
Write-Host ""

Write-Host "To persist these settings, add to PowerShell profile:" -ForegroundColor Yellow
Write-Host "  notepad `$PROFILE" -ForegroundColor White
Write-Host ""
```

### Step 2: Verify Flask Routes

**Check that Compute routes are registered:**

```powershell
# Start the server
cd gcp-emulator-package
python run.py
```

You should see logs indicating Compute routes are registered:
```
INFO: Registered route: /compute/v1/projects/<project>/zones/<zone>/instances
INFO: Compute Engine service enabled
```

### Step 3: Test with GCP SDK

```powershell
# Setup environment
.\setup-gcloud-emulator.ps1

# Test Compute API
gcloud compute instances list --project=test-project

# Expected: Lists instances from your local emulator (may be empty initially)
# NOT Expected: Error about authentication or connectivity to real GCP
```

### Step 4: Create Test Instance

```powershell
# Using gcloud (if supported by your emulator)
gcloud compute instances create test-vm `
    --project=test-project `
    --zone=us-central1-a `
    --machine-type=e2-micro `
    --image-family=debian-11 `
    --image-project=debian-cloud

# OR using Python SDK
python -c "
from google.cloud import compute_v1

client = compute_v1.InstancesClient()
request = compute_v1.InsertInstanceRequest(
    project='test-project',
    zone='us-central1-a',
    instance_resource={
        'name': 'test-vm',
        'machine_type': 'zones/us-central1-a/machineTypes/e2-micro'
    }
)
operation = client.insert(request)
print(f'Instance created: {operation}')
"
```

## Architecture After Solution

```
┌─────────────────────────────────────────────────────────────────┐
│                    Windows PowerShell                            │
│                                                                   │
│   GCP SDK / gcloud CLI                                          │
│   ├── Storage: → :8080/storage/*                               │
│   ├── IAM: → :8080/v1/*                                        │
│   └── Compute: → :8080/compute/* ✅ NOW CONFIGURED             │
│                                                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓ (All work through same endpoint)
┌─────────────────────────────────────────────────────────────────┐
│          Flask Server (Port 8080) - Windows/WSL2                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  App Routes (All Services Unified)                        │  │
│  │  ├── /storage/v1/* → Storage Service → PostgreSQL       │  │
│  │  ├── /v1/projects/* → IAM Service → PostgreSQL          │  │
│  │  └── /compute/v1/* → Compute Service → Docker (WSL2) ✅ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Compute Service (Backend)                                │  │
│  │  └── Docker Driver → WSL2 Docker Socket                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│                        WSL2 Ubuntu                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Docker Engine (/var/run/docker.sock)                    │  │
│  │  ├── PostgreSQL Container (gcp-postgres:5432)            │  │
│  │  ├── Compute Network (gcs-compute-net)                   │  │
│  │  └── VM Containers (simulated compute instances)         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Testing Checklist

- [ ] Environment variables set
- [ ] Flask server running on port 8080
- [ ] Docker running in WSL2
- [ ] PostgreSQL container running
- [ ] Storage API works: `gcloud storage ls`
- [ ] IAM API works: `gcloud iam service-accounts list`
- [ ] Compute API works: `gcloud compute instances list`

## Troubleshooting

### Issue: "Compute API calls still go to real GCP"

**Check:**
```powershell
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE
# Should output: http://127.0.0.1:8080/
```

**Fix:**
```powershell
# Re-run setup
.\setup-gcloud-emulator.ps1

# Or set manually
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE = "http://127.0.0.1:8080/"
```

### Issue: "Connection refused on port 8080"

**Check:**
```powershell
# Is server running?
curl http://127.0.0.1:8080/

# Should return: 404 or emulator response (not connection error)
```

**Fix:**
```powershell
cd gcp-emulator-package
python run.py
```

### Issue: "Compute routes not found (404)"

**Check Flask logs:**
```
INFO: Registered route: /compute/v1/projects/<project>/zones/<zone>/instances
```

**If missing:**
1. Check `app/routes/__init__.py` registers compute blueprint
2. Check `COMPUTE_ENABLED` in config
3. Restart Flask server

### Issue: "Docker connection error"

**Check Docker in WSL2:**
```powershell
wsl docker ps
# Should show running containers including gcp-postgres
```

**Fix:**
```bash
# Inside WSL2
sudo service docker start
```

## Summary

### What You Have
✅ Unified Flask server handling Storage, IAM, and Compute
✅ Compute backend using Docker in WSL2
✅ All services on same port (8080)
✅ Existing proxy mode infrastructure

### What You Need
🎯 Add `CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE` environment variable
🎯 This routes Compute SDK calls to your local emulator
🎯 No code changes required!

### Why It Will Work
1. **Same server**: All three services run in the same Flask app
2. **Same port**: All accessible on 8080
3. **Existing routes**: Compute endpoints already implemented
4. **Just routing**: SDK needs to know where to send Compute requests

### Alternative: Hybrid Mode
If you want:
- Local Storage & IAM (free, fast)
- Real GCP Compute (full features, costs money)

Use proxy mode:
```powershell
$env:GCP_PROXY_MODE = "proxy"
$env:GCP_LOCAL_APIS = "storage,iam"
# Compute automatically goes to real GCP
```

## Next Steps

1. **Immediate**: Add Compute endpoint override
2. **Test**: Verify all three services work via SDK
3. **Document**: Update your setup scripts
4. **Optional**: Configure proxy mode if needed

The solution is simpler than you might think - it's just a configuration issue, not an architecture problem! 🎉
