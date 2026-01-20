# 🎯 **QUICK START: Real `gcloud` CLI with Your Local Emulator**

## ✅ **Setup (One-Time - Run This Once)**

Open PowerShell and run:

```powershell
cd c:\Users\ansh.joshi\gcp_emulator\gcp-emulator-package

# Set environment variables to redirect gcloud commands
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080"
$env:CLOUDSDK_AUTH_ACCESS_TOKEN = "mock-token-12345"
$env:CLOUDSDK_CORE_PROJECT = "test-project"
$env:CLOUDSDK_AUTH_DISABLE_CREDENTIALS = "True"
```

✅ **Done!** Now ALL `gcloud` commands point to your local emulator!

---

## 🚀 **Start Your Emulator**

```powershell
# Terminal 1 - Backend
cd c:\Users\ansh.joshi\gcp_emulator\gcp-emulator-package
$env:COMPUTE_ENABLED = "false"
python run.py

# Terminal 2 - Frontend (optional - for UI)
cd c:\Users\ansh.joshi\gcp_emulator\gcp-emulator-ui
npm run dev
```

---

## 📦 **Test GCS Commands**

```powershell
# Create a bucket
gcloud storage buckets create gs://my-local-bucket --project=test-project

# List buckets
gcloud storage buckets list --project=test-project

# Upload a file
echo "Hello gcloud!" > test.txt
gcloud storage cp test.txt gs://my-local-bucket/

# List objects
gcloud storage ls gs://my-local-bucket/

# Download file
gcloud storage cp gs://my-local-bucket/test.txt downloaded.txt

# Delete object
gcloud storage rm gs://my-local-bucket/test.txt

# Delete bucket
gcloud storage buckets delete gs://my-local-bucket
```

---

## 🔐 **Test IAM Commands**

```powershell
# Create service account
gcloud iam service-accounts create my-sa `
  --display-name="My Service Account" `
  --project=test-project

# List service accounts
gcloud iam service-accounts list --project=test-project

# Describe a service account
gcloud iam service-accounts describe my-sa@test-project.iam.gserviceaccount.com

# Create a key
gcloud iam service-accounts keys create key.json `
  --iam-account=my-sa@test-project.iam.gserviceaccount.com

# List keys
gcloud iam service-accounts keys list `
  --iam-account=my-sa@test-project.iam.gserviceaccount.com

# Delete service account
gcloud iam service-accounts delete my-sa@test-project.iam.gserviceaccount.com
```

---

## 🎯 **What's Happening?**

1. **Environment variables** redirect gcloud requests
2. **`CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE`** → Points to your emulator (port 8080)
3. **`CLOUDSDK_AUTH_ACCESS_TOKEN`** → Mock token (no real GCP auth needed!)
4. **All commands** hit your local PostgreSQL database
5. **Zero cloud costs!** 🎉

---

## 🔄 **Switch Back to Real GCP**

To use real Google Cloud again:

```powershell
Remove-Item Env:\CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE
Remove-Item Env:\CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM
Remove-Item Env:\CLOUDSDK_AUTH_ACCESS_TOKEN
Remove-Item Env:\CLOUDSDK_CORE_PROJECT
Remove-Item Env:\CLOUDSDK_AUTH_DISABLE_CREDENTIALS
```

Now `gcloud` points back to real GCP!

---

## 💡 **Pro Tips**

### Make It Permanent (PowerShell Profile)

Add to `$PROFILE`:

```powershell
function Enable-GCPEmulator {
    $env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080"
    $env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080"
    $env:CLOUDSDK_AUTH_ACCESS_TOKEN = "mock-token-12345"
    $env:CLOUDSDK_CORE_PROJECT = "test-project"
    $env:CLOUDSDK_AUTH_DISABLE_CREDENTIALS = "True"
    Write-Host "✅ gcloud now points to LOCAL EMULATOR" -ForegroundColor Green
}

function Disable-GCPEmulator {
    Remove-Item Env:\CLOUDSDK_API_ENDPOINT_OVERRIDES_* -ErrorAction SilentlyContinue
    Remove-Item Env:\CLOUDSDK_AUTH_ACCESS_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:\CLOUDSDK_CORE_PROJECT -ErrorAction SilentlyContinue
    Remove-Item Env:\CLOUDSDK_AUTH_DISABLE_CREDENTIALS -ErrorAction SilentlyContinue
    Write-Host "✅ gcloud now points to REAL GCP" -ForegroundColor Yellow
}
```

Then just run:
- `Enable-GCPEmulator` → Use local
- `Disable-GCPEmulator` → Use real GCP

---

## 🐛 **Troubleshooting**

### "Unable to connect"
- Check backend is running: `http://127.0.0.1:8080/storage/v1`
- Restart backend: `cd gcp-emulator-package; python run.py`

### "Authentication error"
- Ensure: `$env:CLOUDSDK_AUTH_ACCESS_TOKEN = "mock-token-12345"`
- Verify mock auth enabled in `app/config.py`: `MOCK_AUTH_ENABLED = True`

### Commands still go to real GCP
- Check environment variables: `Get-ChildItem Env: | Where-Object { $_.Name -like "*CLOUDSDK*" }`
- Re-run setup commands above

---

## 📚 **More Documentation**

- **Full Guide**: `GCLOUD_CLI_SETUP.md`
- **IAM Module**: `docs/IAM_MODULE.md`
- **API Reference**: `README.md`
- **Test Script**: Run `.\test-gcloud.ps1` for automated testing

---

## 🎉 **YOU'RE ALL SET!**

**The real `gcloud` CLI now works with your local emulator!**

- ✅ No cloud costs
- ✅ No internet required  
- ✅ Fast local testing
- ✅ Perfect for CI/CD
- ✅ Full GCS + IAM simulation

**Everything runs on your machine at http://127.0.0.1:8080** 🚀
