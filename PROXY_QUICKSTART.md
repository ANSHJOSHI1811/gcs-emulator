# GCP Proxy Mode - Quick Start

## ✅ Implementation Complete!

Your emulator now supports **3 operating modes**:

### 1. LOCAL_ONLY (Default)
```powershell
# No setup needed - works immediately
python run.py
# All requests handled locally, free, offline
```

### 2. PROXY MODE (Hybrid)
```powershell
# Setup once:
$env:GCP_PROXY_MODE = "proxy"
$env:GCP_PROJECT_ID = "your-project-id"
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\credentials.json"
$env:GCP_LOCAL_APIS = "storage,iam"  # These stay local

# Run:
python run.py

# Result: Storage/IAM local, everything else to GCP
```

### 3. PASSTHROUGH MODE (Full Proxy)
```powershell
# Setup:
$env:GCP_PROXY_MODE = "passthrough"
$env:GCP_PROJECT_ID = "your-project-id"
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\credentials.json"

# Run:
python run.py

# Result: All requests forwarded to GCP (with logging)
```

## 🚀 Try It Now

### Option A: Run Setup Script (Interactive)
```powershell
cd gcp-emulator-package
.\setup-proxy-mode.ps1
```

### Option B: Manual Setup for Proxy Mode

**Step 1:** Get GCP Service Account Key
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Create service account (or use existing)
3. Add roles: Storage Admin, IAM Admin
4. Create key (JSON format)
5. Download to secure location

**Step 2:** Configure Environment
```powershell
# Set credentials
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\key.json"
$env:GCP_PROJECT_ID = "your-project-id"

# Choose mode
$env:GCP_PROXY_MODE = "proxy"  # or "local" or "passthrough"

# Configure which APIs stay local (proxy mode only)
$env:GCP_LOCAL_APIS = "storage,iam"

# Configure gcloud CLI
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080/"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080/"
```

**Step 3:** Start Emulator
```powershell
cd gcp-emulator-package
python run.py
```

Look for:
```
✓ Running in local-only mode (no proxy)
# OR
✓ Proxy mode enabled: proxy
✓ Upstream GCP connection verified
```

**Step 4:** Test It
```powershell
# Local request (handled by emulator)
gcloud storage buckets create gs://test-bucket

# Check if it went to GCP or local
# Look for [LOCAL] or [UPSTREAM] in emulator logs
```

## 📊 Feature Comparison

| Feature | LOCAL_ONLY | PROXY | PASSTHROUGH |
|---------|------------|-------|-------------|
| **GCP Credentials** | Not needed | Required | Required |
| **Internet** | Offline | Required | Required |
| **Costs** | Free | Partial | Full GCP costs |
| **Speed** | Fastest | Mixed | GCP speed |
| **Use Case** | Development | Testing | Debugging |

## 🎯 Common Scenarios

### Scenario 1: Developer Without GCP Access
```powershell
# Use local-only (default)
python run.py
# Everything free, fast, offline
```

### Scenario 2: Test Storage Locally, Use Real IAM
```powershell
$env:GCP_PROXY_MODE = "proxy"
$env:GCP_LOCAL_APIS = "storage"
# Storage fast/free, IAM uses real GCP permissions
```

### Scenario 3: Debug Production API Calls
```powershell
$env:GCP_PROXY_MODE = "passthrough"
$env:GCP_PROXY_LOG_REQUESTS = "true"
# All requests logged before forwarding to GCP
```

## 🔍 Troubleshooting

### Problem: "Credentials file not found"
```powershell
# Check file exists
Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS
# Should return True
```

### Problem: Not sure which mode is active
```powershell
# Check API endpoint
Invoke-WebRequest -Uri "http://127.0.0.1:8080/storage/v1" | ConvertFrom-Json
# Shows current mode and settings
```

### Problem: Want to see routing decisions
```powershell
# Enable request logging
$env:GCP_PROXY_LOG_REQUESTS = "true"
python run.py
# Logs show [LOCAL] or [UPSTREAM] for each request
```

## 📚 Full Documentation

- **Complete Guide**: `docs/PROXY_MODE.md`
- **Overview**: `PROXY_IMPLEMENTATION_OVERVIEW.md`
- **Setup Script**: `setup-proxy-mode.ps1`

## 🎉 What's New?

**New Files:**
- `app/proxy/config.py` - Configuration & routing logic
- `app/proxy/upstream.py` - GCP API client (real auth)
- `app/proxy/middleware.py` - Request interceptor
- `docs/PROXY_MODE.md` - Complete documentation
- `setup-proxy-mode.ps1` - Interactive setup

**Updated:**
- `app/factory.py` - Integrated proxy middleware
- `requirements.txt` - Added google-auth dependencies

**Total:** ~800 lines of new code

## ⚡ Next Steps

1. ✅ Try local-only mode (works immediately, no setup)
2. ⚠️ Get GCP service account key (when you need proxy features)
3. 📝 Run `.\setup-proxy-mode.ps1` (interactive setup)
4. 🧪 Test hybrid proxy mode (mix local + real GCP)
5. 📊 Monitor logs to see routing decisions

---

**You now have 3 emulators in 1!**
- 🏠 **Standalone** - Original local simulator
- 🔀 **Hybrid** - Smart routing between local & GCP
- 📡 **Proxy** - Full GCP with logging/debugging

Choose the mode that fits your workflow! 🚀
