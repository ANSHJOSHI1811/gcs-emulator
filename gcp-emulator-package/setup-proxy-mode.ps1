# Setup script for GCP Proxy Mode

Write-Host "=== GCP Emulator Proxy Mode Setup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check for credentials
Write-Host "Step 1: Checking GCP Credentials..." -ForegroundColor Yellow

if (-not $env:GOOGLE_APPLICATION_CREDENTIALS) {
    Write-Host "❌ GOOGLE_APPLICATION_CREDENTIALS not set" -ForegroundColor Red
    Write-Host ""
    Write-Host "To use proxy mode, you need a GCP service account key:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts" -ForegroundColor White
    Write-Host "2. Create a service account (or use existing)" -ForegroundColor White
    Write-Host "3. Add roles: Storage Admin, IAM Admin (or as needed)" -ForegroundColor White
    Write-Host "4. Create key (JSON format)" -ForegroundColor White
    Write-Host "5. Download and save to a secure location" -ForegroundColor White
    Write-Host ""
    
    $credPath = Read-Host "Enter path to your credentials JSON file (or press Enter to skip)"
    if ($credPath) {
        if (Test-Path $credPath) {
            $env:GOOGLE_APPLICATION_CREDENTIALS = $credPath
            Write-Host "✓ Credentials path set" -ForegroundColor Green
        } else {
            Write-Host "❌ File not found: $credPath" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "⚠ Skipping proxy setup (will run in local-only mode)" -ForegroundColor Yellow
        $env:GCP_PROXY_MODE = "local"
        exit 0
    }
} else {
    if (Test-Path $env:GOOGLE_APPLICATION_CREDENTIALS) {
        Write-Host "✓ Credentials found: $env:GOOGLE_APPLICATION_CREDENTIALS" -ForegroundColor Green
    } else {
        Write-Host "❌ Credentials file not found: $env:GOOGLE_APPLICATION_CREDENTIALS" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Check for project ID
Write-Host ""
Write-Host "Step 2: Checking GCP Project ID..." -ForegroundColor Yellow

if (-not $env:GCP_PROJECT_ID) {
    Write-Host "❌ GCP_PROJECT_ID not set" -ForegroundColor Red
    $projectId = Read-Host "Enter your GCP project ID"
    if ($projectId) {
        $env:GCP_PROJECT_ID = $projectId
        Write-Host "✓ Project ID set: $projectId" -ForegroundColor Green
    } else {
        Write-Host "❌ Project ID required for proxy mode" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ Project ID: $env:GCP_PROJECT_ID" -ForegroundColor Green
}

# Step 3: Choose proxy mode
Write-Host ""
Write-Host "Step 3: Select Proxy Mode..." -ForegroundColor Yellow
Write-Host "1. local     - All requests handled locally (no GCP, free)" -ForegroundColor White
Write-Host "2. proxy     - Mix local + GCP (recommended)" -ForegroundColor White
Write-Host "3. passthrough - All to GCP (debugging)" -ForegroundColor White
Write-Host ""

$modeChoice = Read-Host "Select mode (1-3) [default: 2]"
switch ($modeChoice) {
    "1" {
        $env:GCP_PROXY_MODE = "local"
        Write-Host "✓ Local-only mode selected" -ForegroundColor Green
    }
    "3" {
        $env:GCP_PROXY_MODE = "passthrough"
        Write-Host "✓ Passthrough mode selected" -ForegroundColor Green
    }
    default {
        $env:GCP_PROXY_MODE = "proxy"
        Write-Host "✓ Proxy mode selected" -ForegroundColor Green
        
        # Step 4: Configure local APIs
        Write-Host ""
        Write-Host "Step 4: Configure Local APIs..." -ForegroundColor Yellow
        Write-Host "Which APIs should be handled locally?" -ForegroundColor White
        Write-Host "Examples: storage,iam or just storage" -ForegroundColor White
        Write-Host ""
        
        $localApis = Read-Host "Local APIs (comma-separated) [default: storage,iam]"
        if (-not $localApis) {
            $localApis = "storage,iam"
        }
        $env:GCP_LOCAL_APIS = $localApis
        Write-Host "✓ Local APIs: $localApis" -ForegroundColor Green
    }
}

# Step 5: Configure endpoint overrides
Write-Host ""
Write-Host "Step 5: Configuring gcloud CLI..." -ForegroundColor Yellow

$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080/"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080/"
$env:CLOUDSDK_CORE_PROJECT = $env:GCP_PROJECT_ID

Write-Host "✓ gcloud CLI configured to use emulator" -ForegroundColor Green

# Step 6: Install dependencies
Write-Host ""
Write-Host "Step 6: Installing dependencies..." -ForegroundColor Yellow

try {
    python -m pip install -q google-auth google-auth-httplib2 google-auth-oauthlib
    Write-Host "✓ Proxy dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "⚠ Could not install dependencies (continuing anyway)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Mode: $env:GCP_PROXY_MODE" -ForegroundColor White
Write-Host "  Project: $env:GCP_PROJECT_ID" -ForegroundColor White
Write-Host "  Credentials: $env:GOOGLE_APPLICATION_CREDENTIALS" -ForegroundColor White
if ($env:GCP_LOCAL_APIS) {
    Write-Host "  Local APIs: $env:GCP_LOCAL_APIS" -ForegroundColor White
}
Write-Host ""

Write-Host "To start the emulator:" -ForegroundColor Yellow
Write-Host "  cd gcp-emulator-package" -ForegroundColor White
Write-Host "  python run.py" -ForegroundColor White
Write-Host ""

Write-Host "To persist settings, add to your PowerShell profile:" -ForegroundColor Yellow
Write-Host "  notepad `$PROFILE" -ForegroundColor White
Write-Host ""
Write-Host "Then add these lines:" -ForegroundColor White
Write-Host "  `$env:GCP_PROXY_MODE = `"$env:GCP_PROXY_MODE`"" -ForegroundColor Cyan
Write-Host "  `$env:GCP_PROJECT_ID = `"$env:GCP_PROJECT_ID`"" -ForegroundColor Cyan
Write-Host "  `$env:GOOGLE_APPLICATION_CREDENTIALS = `"$env:GOOGLE_APPLICATION_CREDENTIALS`"" -ForegroundColor Cyan
if ($env:GCP_LOCAL_APIS) {
    Write-Host "  `$env:GCP_LOCAL_APIS = `"$env:GCP_LOCAL_APIS`"" -ForegroundColor Cyan
}
Write-Host "  `$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = `"http://127.0.0.1:8080/`"" -ForegroundColor Cyan
Write-Host "  `$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = `"http://127.0.0.1:8080/`"" -ForegroundColor Cyan
Write-Host ""
