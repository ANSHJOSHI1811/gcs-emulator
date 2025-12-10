# GCP API Proxy Mode - Complete Guide

## Overview

The emulator now supports **three operating modes**:

1. **LOCAL_ONLY** (default) - All requests handled locally (original behavior)
2. **PROXY** - Intelligently route requests between local and real GCP
3. **PASSTHROUGH** - Forward all requests to real GCP (pure proxy)

## Architecture

```
┌─────────────┐
│  gcloud CLI │ 
│  or SDK     │
└──────┬──────┘
       │
       ↓
┌──────────────────────────────────────┐
│  Local Emulator (Port 8080)          │
│  ┌────────────────────────────────┐  │
│  │  Proxy Middleware              │  │
│  │  - Intercepts all requests     │  │
│  │  - Routes based on config      │  │
│  └────────┬───────────────┬───────┘  │
│           │               │           │
│           ↓               ↓           │
│  ┌────────────┐  ┌─────────────────┐ │
│  │   Local    │  │   Upstream      │ │
│  │  Handlers  │  │  GCP Client     │ │
│  │            │  │  (Real Auth)    │ │
│  └─────┬──────┘  └────────┬────────┘ │
└────────┼──────────────────┼──────────┘
         │                  │
         ↓                  ↓
   ┌──────────┐      ┌──────────────┐
   │PostgreSQL│      │ Google Cloud │
   │  Local   │      │  (Real APIs) │
   └──────────┘      └──────────────┘
```

## Quick Start

### 1. Setup GCP Credentials

```powershell
# Download service account key from GCP Console
# Save as: gcp-credentials.json

# Set environment variable
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\gcp-credentials.json"
$env:GCP_PROJECT_ID = "your-gcp-project-id"
```

### 2. Configure Proxy Mode

```powershell
# Option A: Proxy mode (local for some, GCP for others)
$env:GCP_PROXY_MODE = "proxy"
$env:GCP_LOCAL_APIS = "storage,iam"  # Handle these locally
# Anything else (compute, etc.) goes to GCP

# Option B: Passthrough mode (everything to GCP)
$env:GCP_PROXY_MODE = "passthrough"

# Option C: Local only (default - no GCP)
$env:GCP_PROXY_MODE = "local"
```

### 3. Start Emulator

```powershell
cd gcp-emulator-package
python run.py
```

You should see:
```
✓ Upstream GCP connection verified
Proxy mode enabled: proxy
```

## Configuration Reference

### Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `GCP_PROXY_MODE` | Operating mode | `local`, `proxy`, `passthrough` | No (default: `local`) |
| `GCP_PROJECT_ID` | Your GCP project ID | `my-project-123` | Yes for proxy/passthrough |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | `C:\creds\key.json` | Yes for proxy/passthrough |
| `GCP_LOCAL_APIS` | APIs to handle locally | `storage,iam,compute` | No (default: `storage,iam`) |
| `GCP_LOCAL_PATTERNS` | Regex patterns for local routing | `.*test.*,.*dev.*` | No |
| `GCP_UPSTREAM_TIMEOUT` | Timeout for GCP calls (seconds) | `30` | No (default: `30`) |
| `GCP_PROXY_LOG_REQUESTS` | Log all requests | `true`, `false` | No (default: `true`) |
| `GCP_PROXY_CACHE` | Cache upstream responses | `true`, `false` | No (default: `false`) |

### Routing Logic (PROXY Mode)

The proxy decides where to route each request:

```python
# Local if:
- API in GCP_LOCAL_APIS (e.g., "storage", "iam")
- OR resource path matches GCP_LOCAL_PATTERNS

# Otherwise → forward to real GCP
```

## Usage Examples

### Example 1: Local Storage + Real IAM

Test storage locally but use real GCP IAM:

```powershell
# Configuration
$env:GCP_PROXY_MODE = "proxy"
$env:GCP_LOCAL_APIS = "storage"  # Only storage local
$env:GCP_PROJECT_ID = "my-project"
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\creds\key.json"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080/"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080/"

# Start emulator
cd gcp-emulator-package
python run.py

# In another terminal:
# Storage goes to local
gcloud storage buckets create gs://test-bucket  # → Local PostgreSQL

# IAM goes to real GCP
gcloud iam service-accounts list  # → Real Google Cloud
```

### Example 2: Pattern-Based Routing

Route based on resource names:

```powershell
# Keep dev/test resources local, production goes to GCP
$env:GCP_PROXY_MODE = "proxy"
$env:GCP_LOCAL_PATTERNS = ".*-dev,.*-test,.*-local"

# This bucket is handled locally (matches pattern)
gcloud storage buckets create gs://my-app-dev

# This bucket goes to GCP (no pattern match)
gcloud storage buckets create gs://my-app-prod
```

### Example 3: Full Passthrough

Use emulator as pure proxy to GCP (for debugging):

```powershell
$env:GCP_PROXY_MODE = "passthrough"
$env:GCP_PROJECT_ID = "my-project"
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\creds\key.json"

# All requests logged then forwarded to GCP
gcloud storage buckets list  # → Real GCP (logged)
gcloud iam service-accounts list  # → Real GCP (logged)
```

## PowerShell Helper Functions

Add to your `$PROFILE`:

```powershell
# Switch to local-only mode
function Enable-LocalGCP {
    $env:GCP_PROXY_MODE = "local"
    Write-Host "✓ Local-only mode enabled" -ForegroundColor Green
}

# Switch to proxy mode
function Enable-ProxyGCP {
    param(
        [string]$ProjectId,
        [string]$CredentialsPath,
        [string]$LocalAPIs = "storage,iam"
    )
    
    $env:GCP_PROXY_MODE = "proxy"
    $env:GCP_PROJECT_ID = $ProjectId
    $env:GOOGLE_APPLICATION_CREDENTIALS = $CredentialsPath
    $env:GCP_LOCAL_APIS = $LocalAPIs
    
    Write-Host "✓ Proxy mode enabled for project: $ProjectId" -ForegroundColor Green
    Write-Host "  Local APIs: $LocalAPIs" -ForegroundColor Cyan
}

# Switch to passthrough mode
function Enable-PassthroughGCP {
    param(
        [string]$ProjectId,
        [string]$CredentialsPath
    )
    
    $env:GCP_PROXY_MODE = "passthrough"
    $env:GCP_PROJECT_ID = $ProjectId
    $env:GOOGLE_APPLICATION_CREDENTIALS = $CredentialsPath
    
    Write-Host "✓ Passthrough mode enabled for project: $ProjectId" -ForegroundColor Green
}

# Usage:
# Enable-LocalGCP
# Enable-ProxyGCP -ProjectId "my-project" -CredentialsPath "C:\creds\key.json"
# Enable-ProxyGCP -ProjectId "my-project" -CredentialsPath "C:\creds\key.json" -LocalAPIs "storage"
# Enable-PassthroughGCP -ProjectId "my-project" -CredentialsPath "C:\creds\key.json"
```

## Testing

### Verify Configuration

```powershell
# Check what mode is active
Invoke-WebRequest -Uri "http://127.0.0.1:8080/storage/v1" | ConvertFrom-Json | Format-List
```

Response shows:
```json
{
  "emulator": true,
  "features": {
    "mockAuth": false,  // false in proxy mode
    "proxyMode": "proxy",
    "localAPIs": ["storage", "iam"]
  }
}
```

### Test Routing

```powershell
# Enable request logging
$env:GCP_PROXY_LOG_REQUESTS = "true"

# Watch logs to see routing decisions
# Logs show: [LOCAL] or [UPSTREAM] prefix
```

## Troubleshooting

### Error: "Credentials file not found"

```powershell
# Check file exists
Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS

# Should return: True
```

### Error: "Invalid proxy configuration"

```powershell
# Ensure required variables are set
echo $env:GCP_PROJECT_ID
echo $env:GOOGLE_APPLICATION_CREDENTIALS
echo $env:GCP_PROXY_MODE
```

### Error: "Could not verify upstream GCP connection"

```powershell
# Test credentials manually
gcloud auth activate-service-account --key-file=$env:GOOGLE_APPLICATION_CREDENTIALS
gcloud projects describe $env:GCP_PROJECT_ID
```

### Check if request went to GCP or local

Look at emulator logs:
```
[LOCAL] GET /storage/v1/b/test-bucket      # Handled locally
[UPSTREAM] GET /compute/v1/projects/...    # Forwarded to GCP
```

## Benefits

### 1. **Hybrid Development**
- Keep test data local (fast, free)
- Use real GCP for production-like testing
- No data duplication

### 2. **Cost Control**
- Only pay for GCP calls you choose
- Storage API calls free locally
- IAM/Compute billed normally

### 3. **Debugging**
- Log all requests to GCP
- Inspect/modify requests
- Test error scenarios locally

### 4. **Team Workflows**
- Devs use local mode (no GCP account needed)
- CI/CD uses proxy mode (mix local + real)
- Staging uses passthrough (full GCP with logging)

## Security Notes

⚠️ **Important:**
- Service account key grants full GCP access
- Keep credentials secure (never commit)
- Use least-privilege service accounts
- Rotate keys regularly

```powershell
# Good: Least privilege
# Create service account with only needed roles
gcloud iam service-accounts create emulator-proxy --display-name="Emulator Proxy"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:emulator-proxy@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"
```

## Performance Tuning

```powershell
# Reduce timeout for faster failures
$env:GCP_UPSTREAM_TIMEOUT = "5"

# Enable caching (experimental)
$env:GCP_PROXY_CACHE = "true"

# Reduce logging overhead
$env:GCP_PROXY_LOG_REQUESTS = "false"
```

## Next Steps

1. ✅ Start in **local-only mode** (no changes needed)
2. ✅ Add GCP credentials when ready for proxy
3. ✅ Test with **proxy mode** for hybrid workflows
4. ✅ Use **passthrough mode** for debugging production

---

**Note:** Proxy mode requires:
- Active internet connection
- Valid GCP credentials
- Appropriate IAM permissions
- GCP project with billing enabled (for real API calls)
