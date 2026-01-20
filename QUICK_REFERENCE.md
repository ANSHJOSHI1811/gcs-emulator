# Quick Reference: Unified GCP Emulator Configuration

## TL;DR - The Solution

**Problem**: GCP SDK Compute commands fail because no endpoint override is configured.

**Solution**: Add one environment variable:
```powershell
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE = "http://127.0.0.1:8080"
```

That's it! All three services (Storage, IAM, Compute) now work through the same Flask server on port 8080.

---

## Complete Setup (One-Time)

```powershell
# Navigate to emulator directory
cd C:\Users\ansh.joshi\gcp_emulator\gcp-emulator-package

# Run setup script (adds all endpoint overrides)
.\setup-gcloud-emulator.ps1
```

## Manual Setup (For Understanding)

```powershell
# Point all GCP SDK commands to local emulator
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE = "http://127.0.0.1:8080"

# Set project
$env:CLOUDSDK_CORE_PROJECT = "test-project"

# Disable auth (not needed for local emulator)
$env:CLOUDSDK_AUTH_DISABLE_CREDENTIALS = "True"
```

## Test Everything

```powershell
# Run comprehensive test
.\test-all-services.ps1

# Or test manually
gcloud storage ls
gcloud iam service-accounts list --project=test-project
gcloud compute instances list --project=test-project --zones=us-central1-a
```

## How It Works

```
Your PowerShell → GCP SDK → Checks endpoint overrides → Routes to emulator

Before (broken):
  Storage → localhost:8080 ✅
  IAM → localhost:8080 ✅
  Compute → real GCP ❌ (fails)

After (working):
  Storage → localhost:8080 ✅
  IAM → localhost:8080 ✅
  Compute → localhost:8080 ✅
```

## Architecture

```
┌─────────────────────────────────────┐
│   Windows PowerShell                │
│   GCP SDK / gcloud CLI              │
└──────────────┬──────────────────────┘
               │ All API calls
               ↓
┌─────────────────────────────────────┐
│   Flask Server (Port 8080)          │
│   ├── /storage/v1/*                 │
│   ├── /v1/projects/* (IAM)          │
│   └── /compute/v1/*                 │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Backend Services                  │
│   ├── Storage → PostgreSQL          │
│   ├── IAM → PostgreSQL              │
│   └── Compute → Docker (WSL2)       │
└─────────────────────────────────────┘
```

## Why Compute Uses Docker

- **Not a separate server**: Compute backend runs in the same Flask app
- **Docker for VMs**: Uses Docker containers to simulate compute instances
- **Same endpoint**: Accessible through http://127.0.0.1:8080/compute/*
- **WSL2 location**: Docker engine runs in WSL2, but API is exposed through Flask

## Alternative: Hybrid Mode (Real GCP Compute)

Want to use real GCP Compute while keeping Storage/IAM local?

```powershell
# Configure proxy mode
$env:GCP_PROXY_MODE = "proxy"
$env:GCP_LOCAL_APIS = "storage,iam"  # Only these stay local
$env:GCP_PROJECT_ID = "your-real-project"
$env:GOOGLE_APPLICATION_CREDENTIALS = "path\to\credentials.json"

# Compute automatically routes to real GCP
# (costs will apply)
```

## Troubleshooting

### "Cannot connect to port 8080"
```powershell
# Start the backend
cd gcp-emulator-package
python run.py
```

### "Compute API returns 404"
```powershell
# Check if Compute is enabled
$env:COMPUTE_ENABLED = "true"

# Restart backend
python run.py
```

### "Docker connection error"
```powershell
# Check Docker in WSL2
wsl docker ps

# If not running
wsl sudo service docker start
```

### "Still hitting real GCP"
```powershell
# Verify environment variables
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE
# Should output: http://127.0.0.1:8080

# If empty, re-run setup
.\setup-gcloud-emulator.ps1
```

## Disable Emulator Mode

```powershell
# Return to real GCP
.\disable-gcloud-emulator.ps1

# Or manually
Remove-Item Env:\CLOUDSDK_API_ENDPOINT_OVERRIDES_*
```

## Key Files

- `setup-gcloud-emulator.ps1` - Configure all services
- `disable-gcloud-emulator.ps1` - Return to real GCP
- `test-all-services.ps1` - Verify everything works
- `COMPUTE_ARCHITECTURE_ANALYSIS.md` - Detailed explanation

## Important Notes

1. **No code changes needed**: This is purely a configuration change
2. **All services unified**: Storage, IAM, and Compute all use the same Flask server
3. **Docker is backend only**: Docker runs in WSL2 to simulate VMs, but the API is exposed through Flask
4. **Works with SDK and CLI**: Both `gcloud` CLI and Python SDK respect endpoint overrides

## Summary

✅ **What changed**: Added `CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE`  
✅ **Why it works**: Compute API was already implemented, just not configured  
✅ **How to use**: Run `.\setup-gcloud-emulator.ps1` and start coding!

The "problem" was just a missing configuration variable - everything else was already in place! 🎉
