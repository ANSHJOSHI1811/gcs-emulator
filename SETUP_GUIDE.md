# GCP Stimulator - Quick Setup Guide

## 🚀 One-Command Setup for gcloud CLI

This directory contains environment setup files that automatically configure your gcloud CLI to use the local GCP Stimulator.

---

## 📁 Setup Files

### 1. `setup-gcloud-env.sh` (Recommended)
Interactive setup script with colored output and helpful information.

**Usage:**
```bash
source setup-gcloud-env.sh
```

### 2. `.env-gcloud` (Simple)
Minimal environment file for quick sourcing.

**Usage:**
```bash
source .env-gcloud
```

---

## 🎯 Quick Start

### Step 1: Start GCP Stimulator Server
```bash
cd gcp-stimulator-package
python3 run.py
```

### Step 2: Setup Environment (in another terminal)
```bash
cd /home/ubuntu/gcs-stimulator
source setup-gcloud-env.sh
```

### Step 3: Use gcloud Commands Directly!
```bash
# Storage
gcloud storage buckets list
gcloud storage buckets create gs://my-test-bucket

# Compute
gcloud compute zones list
gcloud compute networks list
gcloud compute instances list

# IAM
gcloud iam service-accounts list
gcloud iam service-accounts create my-sa
```

**That's it! No manual exports needed!** ✨

---

## 🔧 What Gets Configured

The setup files configure these environment variables:

| Variable | Value | Purpose |
|----------|-------|---------|
| `CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE` | `http://localhost:8080/storage/v1/` | Storage API endpoint |
| `CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE` | `http://localhost:8080/compute/v1/` | Compute API endpoint |
| `CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM` | `http://localhost:8080/iam/` | IAM API endpoint |
| `CLOUDSDK_CORE_PROJECT` | `test-project` | Default project |
| `STORAGE_EMULATOR_HOST` | `http://localhost:8080` | Python SDK storage |

---

## 💡 Usage Options

### Option 1: Per-Session Setup (Recommended for Testing)
Source the file in each terminal session:
```bash
source setup-gcloud-env.sh
```

### Option 2: Auto-Setup for All Sessions
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
# Auto-setup GCP Stimulator for gcloud (optional)
if [ -f /home/ubuntu/gcs-stimulator/setup-gcloud-env.sh ]; then
    source /home/ubuntu/gcs-stimulator/setup-gcloud-env.sh
fi
```

### Option 3: Create an Alias
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
alias gcp-local='source /home/ubuntu/gcs-stimulator/setup-gcloud-env.sh'
```

Then just run:
```bash
gcp-local
```

---

## 🔄 Switching Between Local and Real GCP

### Use Local GCP Stimulator:
```bash
source setup-gcloud-env.sh
gcloud storage buckets list  # Uses localhost:8080
```

### Use Real GCP:
```bash
unset CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE
unset CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE
unset CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM
unset STORAGE_EMULATOR_HOST
gcloud storage buckets list  # Uses real GCP
```

Or simply **open a new terminal** (without sourcing the setup file).

---

## 📝 Example Workflow

```bash
# Terminal 1: Start server
cd gcp-stimulator-package
python3 run.py

# Terminal 2: Use gcloud
cd /home/ubuntu/gcs-stimulator
source setup-gcloud-env.sh

# Now all gcloud commands use local simulator
gcloud storage buckets create gs://test-bucket
gcloud compute networks create my-vpc --subnet-mode=custom
gcloud iam service-accounts create my-service-account

# Verify
gcloud storage buckets list
gcloud compute networks list
gcloud iam service-accounts list
```

---

## ✅ Verify Setup

After sourcing the setup file, verify it's working:

```bash
# Check environment variables
echo $CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE
# Should output: http://localhost:8080/storage/v1/

# Test a command
gcloud storage buckets list
# Should list buckets from local server

# Check which endpoint is being used
gcloud config list
```

---

## 🐍 Python SDK Setup

The environment files also configure the Python SDK:

```python
import os
from google.cloud import storage

# No additional setup needed! Environment is already configured
client = storage.Client(project='test-project')
buckets = client.list_buckets()
for bucket in buckets:
    print(bucket.name)
```

---

## 🆘 Troubleshooting

### Commands still hitting real GCP?
- Make sure you **sourced** the file (not just executed it):
  ```bash
  source setup-gcloud-env.sh  # ✓ Correct
  ./setup-gcloud-env.sh       # ✗ Wrong
  ```

### Environment not persisting?
- Source the file in **each new terminal session**, OR
- Add it to your `~/.bashrc` for automatic setup

### Server not responding?
- Check if GCP Stimulator is running:
  ```bash
  curl http://localhost:8080/health
  # Should return: {"status":"ok"}
  ```

### Need to use real GCP?
- Open a new terminal without sourcing the setup file, OR
- Unset the environment variables (see "Switching Between Local and Real GCP")

---

## 📚 Additional Resources

- **Examples:** See `examples/gcloud-cli.md` for command examples
- **Python SDK:** See `examples/python-sdk.md` for Python examples
- **REST API:** See `examples/rest-api.md` for REST API examples
- **Full Documentation:** See main `README.md`

---

## 🎉 Benefits

✅ **No Manual Exports:** Just source one file  
✅ **Easy Switching:** Between local and real GCP  
✅ **Consistent Setup:** Same environment every time  
✅ **Zero Cost:** Test without cloud bills  
✅ **Fast Iteration:** Instant feedback on changes  

Happy local GCP development! 🚀
