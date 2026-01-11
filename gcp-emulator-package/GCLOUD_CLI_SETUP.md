# 🚀 Using Real `gcloud` CLI with GCP Emulator

This guide shows you how to configure the **official Google Cloud SDK (`gcloud` CLI)** to interact with your local emulator instead of real GCP.

## 📋 Prerequisites

1. **Install Google Cloud SDK**: Download from https://cloud.google.com/sdk/docs/install
2. **Emulator Running**: Ensure backend is running on `http://127.0.0.1:8080`

## ⚙️ Configuration

### Quick Setup Scripts (Windows)

Prefer using the ready-made scripts to toggle emulator mode:

- Enable: [gcp-emulator-package/setup-gcloud-emulator.ps1](gcp-emulator-package/setup-gcloud-emulator.ps1)
- Disable: [gcp-emulator-package/disable-gcloud-emulator.ps1](gcp-emulator-package/disable-gcloud-emulator.ps1)

Run in PowerShell:

```powershell
./setup-gcloud-emulator.ps1
# ... use gcloud commands against the emulator ...
./disable-gcloud-emulator.ps1
```

### Windows PowerShell Setup

Set these environment variables to redirect `gcloud` commands to your local emulator:

```powershell
# Core GCS Storage endpoint override
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080"

# IAM endpoint override
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080"

# Mock authentication token (no real OAuth needed)
$env:CLOUDSDK_AUTH_ACCESS_TOKEN = "mock-token-12345"

# Disable SSL verification for local development
$env:CLOUDSDK_CORE_DISABLE_PROMPTS = "True"
$env:CLOUDSDK_AUTH_DISABLE_CREDENTIALS = "True"

# Set a test project
$env:CLOUDSDK_CORE_PROJECT = "test-project"
```

### Linux/macOS/WSL Setup

```bash
# Core GCS Storage endpoint override
export CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE="http://127.0.0.1:8080"

# IAM endpoint override
export CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM="http://127.0.0.1:8080"

# Mock authentication token
export CLOUDSDK_AUTH_ACCESS_TOKEN="mock-token-12345"

# Disable SSL verification
export CLOUDSDK_CORE_DISABLE_PROMPTS=True
export CLOUDSDK_AUTH_DISABLE_CREDENTIALS=True

# Set test project
export CLOUDSDK_CORE_PROJECT="test-project"
```

### gsutil Setup (optional)

Point `gsutil` to the emulator using the provided boto config and environment variable:

```powershell
$env:BOTO_CONFIG = "$PWD/gcp-emulator-package/docs/gsutil-emulator.boto"
gsutil ls
```

Or on bash/WSL:

```bash
export BOTO_CONFIG="$(pwd)/gcp-emulator-package/docs/gsutil-emulator.boto"
gsutil ls
```

## 🧪 Testing GCS Commands

Once configured, try these `gcloud storage` commands:

### Create a Bucket

```powershell
gcloud storage buckets create gs://my-test-bucket --project=test-project
```

### List Buckets

```powershell
gcloud storage buckets list --project=test-project
```

### Upload a File

```powershell
# Create a test file
"Hello from gcloud!" | Out-File -Encoding utf8 test.txt

# Upload to GCS
gcloud storage cp test.txt gs://my-test-bucket/
```

### List Objects

```powershell
gcloud storage ls gs://my-test-bucket/
```

### Download a File

```powershell
gcloud storage cp gs://my-test-bucket/test.txt downloaded.txt
```

### Delete an Object

```powershell
gcloud storage rm gs://my-test-bucket/test.txt
```

### Delete a Bucket

```powershell
gcloud storage buckets delete gs://my-test-bucket
```

## 🔐 Testing IAM Commands

### Service Account Operations

```powershell
# Create a service account
gcloud iam service-accounts create test-sa `
  --display-name="Test Service Account" `
  --project=test-project

# List service accounts
gcloud iam service-accounts list --project=test-project

# Get service account details
gcloud iam service-accounts describe test-sa@test-project.iam.gserviceaccount.com

# Create a key
gcloud iam service-accounts keys create key.json `
  --iam-account=test-sa@test-project.iam.gserviceaccount.com

# List keys
gcloud iam service-accounts keys list `
  --iam-account=test-sa@test-project.iam.gserviceaccount.com

# Delete a key
gcloud iam service-accounts keys delete KEY_ID `
  --iam-account=test-sa@test-project.iam.gserviceaccount.com

# Delete service account
gcloud iam service-accounts delete test-sa@test-project.iam.gserviceaccount.com
```

### Role Operations

```powershell
# List predefined roles
gcloud iam roles list

# Describe a role
gcloud iam roles describe roles/storage.objectViewer

# Create a custom role (if supported)
gcloud iam roles create customRole `
  --project=test-project `
  --title="Custom Role" `
  --description="My custom role" `
  --permissions=storage.buckets.list,storage.objects.get
```

### IAM Policy Management

```powershell
# Get IAM policy for a bucket
gcloud storage buckets get-iam-policy gs://my-test-bucket

# Add IAM policy binding
gcloud storage buckets add-iam-policy-binding gs://my-test-bucket `
  --member="serviceAccount:test-sa@test-project.iam.gserviceaccount.com" `
  --role="roles/storage.objectViewer"

# Remove IAM policy binding
gcloud storage buckets remove-iam-policy-binding gs://my-test-bucket `
  --member="serviceAccount:test-sa@test-project.iam.gserviceaccount.com" `
  --role="roles/storage.objectViewer"
```

## 🔧 Advanced Configuration

### Create a Configuration Profile

Instead of setting environment variables each time, create a dedicated gcloud configuration:

```powershell
# Create new configuration
gcloud config configurations create local-emulator

# Set properties
gcloud config set api_endpoint_overrides/storage http://127.0.0.1:8080
gcloud config set api_endpoint_overrides/iam http://127.0.0.1:8080
gcloud config set project test-project
gcloud config set auth/disable_credentials true
gcloud config set core/disable_prompts true

# Activate this configuration
gcloud config configurations activate local-emulator
```

Switch back to default GCP:

```powershell
gcloud config configurations activate default
```

### Persistent PowerShell Profile

To make these settings permanent in PowerShell, add to your profile:

```powershell
# Open profile
notepad $PROFILE

# Add these lines:
function Enable-GCPEmulator {
    $env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080"
    $env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080"
    $env:CLOUDSDK_AUTH_ACCESS_TOKEN = "mock-token-12345"
    $env:CLOUDSDK_CORE_PROJECT = "test-project"
    $env:CLOUDSDK_AUTH_DISABLE_CREDENTIALS = "True"
    Write-Host "✅ GCP Emulator mode enabled! All gcloud commands point to http://127.0.0.1:8080" -ForegroundColor Green
}

function Disable-GCPEmulator {
    Remove-Item Env:\CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE -ErrorAction SilentlyContinue
    Remove-Item Env:\CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM -ErrorAction SilentlyContinue
    Remove-Item Env:\CLOUDSDK_AUTH_ACCESS_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:\CLOUDSDK_CORE_PROJECT -ErrorAction SilentlyContinue
    Remove-Item Env:\CLOUDSDK_AUTH_DISABLE_CREDENTIALS -ErrorAction SilentlyContinue
    Write-Host "✅ GCP Emulator mode disabled! gcloud points to real GCP" -ForegroundColor Yellow
}
```

Then use:

```powershell
Enable-GCPEmulator   # Switch to local emulator
Disable-GCPEmulator  # Switch back to real GCP
```

## 🎯 Verification

Check if `gcloud` is pointing to your emulator:

```powershell
# This should show your emulator's endpoint
gcloud config list

# Try creating a bucket - watch your emulator logs!
gcloud storage buckets create gs://verification-bucket --project=test-project

# List buckets (should show in emulator)
gcloud storage buckets list
```

Check your backend terminal - you should see API requests logged!

## 🐛 Troubleshooting

### Issue: `gcloud` still connects to real GCP

**Solution**: Verify environment variables are set:

```powershell
Get-ChildItem Env: | Where-Object { $_.Name -like "*CLOUDSDK*" }
```

### Issue: Authentication errors

**Solution**: Ensure mock auth is enabled in `app/config.py`:

```python
MOCK_AUTH_ENABLED = True  # Should be true
```

And set the mock token:

```powershell
$env:CLOUDSDK_AUTH_ACCESS_TOKEN = "mock-token-12345"
```

### Issue: Commands fail with SSL errors

**Solution**: Use HTTP (not HTTPS) in endpoint overrides:

```powershell
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080"  # HTTP not HTTPS
```

### Issue: Bucket not found

**Solution**: Ensure backend is running and accessible:

```powershell
# Test backend connectivity
Invoke-WebRequest -Uri "http://127.0.0.1:8080/storage/v1" -UseBasicParsing
```

## 📊 Supported Commands

### ✅ Fully Supported

- `gcloud storage buckets create/list/delete/describe`
- `gcloud storage cp` (upload/download)
- `gcloud storage ls` (list objects)
- `gcloud storage rm` (delete objects)
- `gcloud iam service-accounts create/list/delete/describe`
- `gcloud iam service-accounts keys create/list/delete`
- `gcloud iam roles list/describe`
- `gcloud storage buckets get-iam-policy`
- `gcloud storage buckets add-iam-policy-binding`

### ⚠️ Partially Supported

Some advanced features may have limited functionality:
- `gcloud storage buckets update` (basic metadata only)
- `gcloud iam roles create` (custom roles via REST API)
- `gcloud storage buckets set-iam-policy` (use add/remove-iam-policy-binding)

### ❌ Not Supported

- `gcloud compute` instances (use Docker-based compute simulator)
- `gcloud functions` (Cloud Functions)
- `gcloud run` (Cloud Run)

## 🎉 Success!

You're now using the **real `gcloud` CLI** with your local emulator! 

- No cloud costs
- No internet required
- Fast iteration cycles
- Perfect for CI/CD testing

**The SDK thinks it's talking to real GCS, but everything runs locally!** 🎉

## 📚 Additional Resources

- [GCP Storage API Reference](https://cloud.google.com/storage/docs/json_api)
- [GCP IAM API Reference](https://cloud.google.com/iam/docs/reference/rest)
- [gcloud CLI Documentation](https://cloud.google.com/sdk/gcloud/reference)
- [Emulator REST API](./README.md)
- [IAM Module Documentation](./docs/IAM_MODULE.md)
