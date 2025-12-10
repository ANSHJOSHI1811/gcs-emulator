# GCP API Proxy Implementation - Complete Overview

## What Changed?

Your emulator has been **transformed from a standalone simulator to a hybrid proxy** that can:

1. ✅ **Handle requests locally** (original behavior - free, fast, offline)
2. ✅ **Forward to real GCP APIs** (authenticated, billed, online)
3. ✅ **Mix both** (intelligent routing based on configuration)

## Architecture Comparison

### Before (Standalone Emulator)
```
┌─────────────┐
│  gcloud CLI │
└──────┬──────┘
       │ (Environment variables redirect)
       ↓
┌─────────────────┐
│ Local Emulator  │ ← Generates IDs locally
│   Flask App     │ ← Stores in PostgreSQL
└─────────────────┘
       ↓
┌─────────────────┐
│   PostgreSQL    │ (All data local)
└─────────────────┘
```

### After (Hybrid Proxy)
```
┌─────────────┐
│  gcloud CLI │
└──────┬──────┘
       │ (Environment variables redirect)
       ↓
┌──────────────────────────────────┐
│  Proxy Emulator (Port 8080)      │
│  ┌────────────────────────────┐  │
│  │  Proxy Middleware          │  │
│  │  Decision: Local or GCP?   │  │
│  └───────┬──────────┬─────────┘  │
│          │          │             │
│          ↓          ↓             │
│    ┌─────────┐  ┌──────────────┐ │
│    │  Local  │  │  Upstream    │ │
│    │ Handler │  │  GCP Client  │ │
│    └────┬────┘  └──────┬───────┘ │
└─────────┼───────────────┼────────┘
          │               │
          ↓               ↓
   ┌──────────┐    ┌─────────────┐
   │PostgreSQL│    │ Google Cloud│
   │  (Local) │    │   (Real)    │
   └──────────┘    └─────────────┘
```

## New Components

### 1. **Proxy Configuration** (`app/proxy/config.py`)
- **3 operating modes**: LOCAL_ONLY, PROXY, PASSTHROUGH
- **Routing rules**: Which APIs/resources go where
- **Environment-based**: Configure via env vars (no code changes)

```python
class ProxyMode(Enum):
    LOCAL_ONLY = "local"      # All local (default)
    PROXY = "proxy"           # Mixed (intelligent routing)
    PASSTHROUGH = "passthrough"  # All to GCP (pure proxy)
```

### 2. **Upstream GCP Client** (`app/proxy/upstream.py`)
- **Real authentication**: Uses google-auth library
- **Service account support**: Loads credentials from JSON
- **Application default**: Falls back to default credentials
- **Authenticated requests**: Adds OAuth2 tokens automatically

```python
class UpstreamGCPClient:
    def forward_request(self, method, api, path, headers, body):
        # Authenticates with real GCP
        # Makes actual API calls to googleapis.com
        # Returns real GCP responses
```

### 3. **Proxy Middleware** (`app/proxy/middleware.py`)
- **Intercepts all requests**: Sits between Flask and your handlers
- **Routing decision**: Checks config to decide local vs upstream
- **Request forwarding**: Passes to GCP when configured
- **Response proxying**: Returns GCP responses transparently

```python
class ProxyMiddleware:
    def __call__(self, environ, start_response):
        # Check: should we handle this locally?
        if should_handle_locally(api, path):
            return local_handler(...)  # PostgreSQL
        else:
            return forward_to_gcp(...)  # Real GCP API
```

### 4. **Integration** (`app/factory.py`)
- **Setup function**: `setup_proxy_middleware(app)`
- **Mode detection**: Checks GCP_PROXY_MODE env var
- **Credential validation**: Ensures required vars set
- **Health check**: Verifies GCP connection on startup

## Configuration Options

### Environment Variables

```powershell
# === Mode Selection ===
$env:GCP_PROXY_MODE = "local"        # Default: local-only
$env:GCP_PROXY_MODE = "proxy"        # Mixed: local + GCP
$env:GCP_PROXY_MODE = "passthrough"  # All to GCP

# === GCP Credentials (required for proxy/passthrough) ===
$env:GCP_PROJECT_ID = "your-project-id"
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\credentials.json"

# === Routing Configuration (for PROXY mode) ===
$env:GCP_LOCAL_APIS = "storage,iam"     # Handle these locally
$env:GCP_LOCAL_PATTERNS = ".*-dev,.*-test"  # Patterns for local

# === Advanced Options ===
$env:GCP_UPSTREAM_TIMEOUT = "30"        # Timeout for GCP calls
$env:GCP_PROXY_LOG_REQUESTS = "true"    # Log all requests
$env:GCP_PROXY_CACHE = "false"          # Cache responses
```

## Usage Examples

### Example 1: Local-Only (Default - No Changes)

```powershell
# No GCP credentials needed
$env:GCP_PROXY_MODE = "local"

cd gcp-emulator-package
python run.py

# All requests handled locally
gcloud storage buckets create gs://test  # → PostgreSQL
gcloud iam service-accounts list         # → PostgreSQL
```

**Use Case**: Development without GCP account, free testing, offline work

---

### Example 2: Hybrid Proxy (Recommended)

```powershell
# Setup
$env:GCP_PROXY_MODE = "proxy"
$env:GCP_PROJECT_ID = "my-project-123"
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\creds\key.json"
$env:GCP_LOCAL_APIS = "storage"  # Only storage local

cd gcp-emulator-package
python run.py

# Storage goes to local (free, fast)
gcloud storage buckets create gs://test-data  # → PostgreSQL

# IAM goes to real GCP (costs apply)
gcloud iam service-accounts create prod-sa    # → Real Google Cloud
gcloud iam service-accounts list              # → Real Google Cloud
```

**Use Case**: Test storage locally, use real IAM for production-like testing

---

### Example 3: Pattern-Based Routing

```powershell
# Route by resource name
$env:GCP_PROXY_MODE = "proxy"
$env:GCP_LOCAL_APIS = ""  # No APIs always local
$env:GCP_LOCAL_PATTERNS = ".*-dev,.*-test,.*-staging"

# Dev buckets → local
gcloud storage buckets create gs://my-app-dev      # → PostgreSQL
gcloud storage buckets create gs://my-app-test     # → PostgreSQL

# Prod buckets → GCP
gcloud storage buckets create gs://my-app-prod     # → Real GCP
```

**Use Case**: Keep dev/test resources local, production in cloud

---

### Example 4: Full Passthrough (Debugging)

```powershell
# All requests to GCP (with logging)
$env:GCP_PROXY_MODE = "passthrough"
$env:GCP_PROXY_LOG_REQUESTS = "true"

cd gcp-emulator-package
python run.py

# All requests logged then forwarded
gcloud storage buckets list  # Logged → Real GCP
gcloud iam roles list        # Logged → Real GCP
```

**Use Case**: Debug/inspect GCP API calls, intercept for testing

---

## Quick Setup

### Option A: Automated Setup Script

```powershell
# Run interactive setup
.\setup-proxy-mode.ps1

# Follow prompts:
# 1. Enter credentials path
# 2. Enter project ID
# 3. Select mode (local/proxy/passthrough)
# 4. Configure local APIs

# Then start:
cd gcp-emulator-package
python run.py
```

### Option B: Manual Setup

```powershell
# 1. Get GCP credentials
# Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
# Create service account → Create key (JSON)

# 2. Set environment
$env:GCP_PROXY_MODE = "proxy"
$env:GCP_PROJECT_ID = "your-project"
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\key.json"
$env:GCP_LOCAL_APIS = "storage,iam"

# 3. Configure gcloud
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080/"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080/"

# 4. Install dependencies
pip install google-auth google-auth-httplib2

# 5. Start emulator
cd gcp-emulator-package
python run.py
```

## Verification

### Check Startup Logs

```
✓ Upstream GCP connection verified
Proxy mode enabled: proxy
Local APIs: ['storage', 'iam']
 * Running on http://127.0.0.1:8080
```

### Test Routing

```powershell
# Enable request logging
$env:GCP_PROXY_LOG_REQUESTS = "true"

# Watch logs for routing decisions:
# [LOCAL] GET /storage/v1/b/test-bucket      ← Handled locally
# [UPSTREAM] GET /iam/v1/projects/...        ← Forwarded to GCP
```

### API Endpoint Check

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8080/storage/v1" | ConvertFrom-Json
```

Response shows proxy status:
```json
{
  "emulator": true,
  "features": {
    "mockAuth": false,      // false in proxy mode (real auth)
    "proxyMode": "proxy",
    "localAPIs": ["storage", "iam"]
  }
}
```

## Benefits & Trade-offs

### Local-Only Mode (Default)
✅ **Free** - No GCP costs  
✅ **Fast** - No network latency  
✅ **Offline** - Works without internet  
✅ **Isolated** - No cloud dependencies  
❌ **Limited** - Some features not implemented  
❌ **Mock data** - Not production-like  

### Proxy Mode (Hybrid)
✅ **Best of both** - Fast local + real GCP features  
✅ **Cost control** - Only pay for what you route to GCP  
✅ **Flexible** - Change routing without code changes  
✅ **Production-like** - Use real GCP when needed  
⚠️ **Costs apply** - GCP charges for upstream calls  
⚠️ **Internet required** - For GCP calls  

### Passthrough Mode (Full Proxy)
✅ **Debugging** - Log/inspect all GCP calls  
✅ **Testing** - Validate requests before they hit GCP  
✅ **Development** - Modify requests/responses  
❌ **All costs** - Every call billed by GCP  
❌ **Internet required** - For all operations  

## Common Use Cases

### 1. **Local Development** → `LOCAL_ONLY`
```
Developers without GCP accounts
Fast iteration without network calls
Testing without costs
```

### 2. **CI/CD Testing** → `PROXY` mode
```
Storage tests → Local (fast)
IAM integration → Real GCP (accurate)
Cost-effective testing
```

### 3. **Staging Environment** → `PROXY` mode
```
Test data → Local (isolated)
Production services → Real GCP (integration)
Gradual rollout
```

### 4. **Production Debugging** → `PASSTHROUGH` mode
```
Log all API calls
Inspect request/response
Debug without code changes
```

## Security Considerations

⚠️ **Service Account Key Security:**
- Never commit credentials to git
- Use least-privilege service accounts
- Rotate keys regularly
- Store securely (encrypted, access-controlled)

```powershell
# Create least-privilege service account
gcloud iam service-accounts create emulator-proxy
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:emulator-proxy@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"  # Only what's needed
```

## Troubleshooting

### Problem: "Credentials file not found"
```powershell
# Check file exists
Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS
# Should return: True
```

### Problem: "Could not verify upstream GCP connection"
```powershell
# Test credentials
gcloud auth activate-service-account \
    --key-file=$env:GOOGLE_APPLICATION_CREDENTIALS
gcloud projects describe $env:GCP_PROJECT_ID
```

### Problem: Not sure if using local or GCP
```powershell
# Check logs for [LOCAL] or [UPSTREAM] prefix
$env:GCP_PROXY_LOG_REQUESTS = "true"
```

## Files Added/Modified

### New Files
- `app/proxy/__init__.py` - Proxy module
- `app/proxy/config.py` - Configuration and routing logic (220 lines)
- `app/proxy/upstream.py` - GCP API client (150 lines)
- `app/proxy/middleware.py` - Flask middleware (170 lines)
- `docs/PROXY_MODE.md` - Complete documentation
- `setup-proxy-mode.ps1` - Interactive setup script

### Modified Files
- `app/factory.py` - Added `setup_proxy_middleware()` call
- `requirements.txt` - Added google-auth dependencies

### Total New Code
~800 lines of production code + comprehensive documentation

## Next Steps

1. ✅ **Try local-only mode** (default, no setup needed)
2. ✅ **Get GCP service account** (when ready for proxy)
3. ✅ **Run setup script**: `.\setup-proxy-mode.ps1`
4. ✅ **Test with gcloud CLI**: Mix local + real GCP calls
5. ✅ **Configure routing**: Adjust which APIs go where

## Summary

You now have **3 emulators in 1**:

1. **Standalone Simulator** (LOCAL_ONLY) - Original behavior, no changes
2. **Intelligent Proxy** (PROXY) - Mix local + GCP based on rules
3. **Full Proxy** (PASSTHROUGH) - All to GCP with logging

Choose the mode that fits your workflow, change anytime with environment variables!

---

**Documentation:**
- **Full guide**: `docs/PROXY_MODE.md`
- **Setup script**: `setup-proxy-mode.ps1`
- **Code**: `app/proxy/` directory
