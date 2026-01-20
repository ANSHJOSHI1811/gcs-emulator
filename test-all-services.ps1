# Test All GCP Emulator Services (Storage, IAM, Compute)
# This script verifies that all three services are properly configured and working

param(
    [switch]$SkipSetup
)

$ErrorActionPreference = "Stop"

Write-Host "=== GCP Emulator - All Services Test ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Setup environment (unless skipped)
if (-not $SkipSetup) {
    Write-Host "Step 1: Configuring environment..." -ForegroundColor Yellow
    $env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080"
    $env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080"
    $env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE = "http://127.0.0.1:8080"
    $env:CLOUDSDK_CORE_PROJECT = "test-project"
    $env:CLOUDSDK_AUTH_DISABLE_CREDENTIALS = "True"
    Write-Host "✓ Environment configured" -ForegroundColor Green
    Write-Host ""
}

# Step 2: Check backend
Write-Host "Step 2: Checking backend connectivity..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8080/" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ Backend is running on port 8080" -ForegroundColor Green
}
catch {
    Write-Host "✗ Backend not reachable at http://127.0.0.1:8080" -ForegroundColor Red
    Write-Host "  Please start the backend first:" -ForegroundColor Yellow
    Write-Host "  cd gcp-emulator-package && python run.py" -ForegroundColor White
    Write-Host ""
    exit 1
}
Write-Host ""

# Step 3: Test Storage API
Write-Host "Step 3: Testing Storage API..." -ForegroundColor Yellow
try {
    $storageResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8080/storage/v1/b?project=test-project" -Method GET -Headers @{"Authorization" = "Bearer mock-token-12345"} -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ Storage API responding (Status: $($storageResponse.StatusCode))" -ForegroundColor Green
    $storageData = $storageResponse.Content | ConvertFrom-Json
    if ($storageData.items) {
        Write-Host "  Found $($storageData.items.Count) bucket(s)" -ForegroundColor Gray
    }
    else {
        Write-Host "  No buckets found (expected for fresh install)" -ForegroundColor Gray
    }
}
catch {
    Write-Host "✗ Storage API failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Step 4: Test IAM API
Write-Host "Step 4: Testing IAM API..." -ForegroundColor Yellow
try {
    $iamResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8080/v1/projects/test-project/serviceAccounts" -Method GET -Headers @{"Authorization" = "Bearer mock-token-12345"} -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ IAM API responding (Status: $($iamResponse.StatusCode))" -ForegroundColor Green
    $iamData = $iamResponse.Content | ConvertFrom-Json
    if ($iamData.accounts) {
        Write-Host "  Found $($iamData.accounts.Count) service account(s)" -ForegroundColor Gray
    }
    else {
        Write-Host "  No service accounts found" -ForegroundColor Gray
    }
}
catch {
    Write-Host "✗ IAM API failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Step 5: Test Compute API
Write-Host "Step 5: Testing Compute API..." -ForegroundColor Yellow
try {
    $computeResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8080/compute/v1/projects/test-project/zones/us-central1-a/instances" -Method GET -Headers @{"Authorization" = "Bearer mock-token-12345"} -UseBasicParsing -ErrorAction Stop
    Write-Host "✓ Compute API responding (Status: $($computeResponse.StatusCode))" -ForegroundColor Green
    $computeData = $computeResponse.Content | ConvertFrom-Json
    if ($computeData.items) {
        Write-Host "  Found $($computeData.items.Count) instance(s)" -ForegroundColor Gray
    }
    else {
        Write-Host "  No instances found" -ForegroundColor Gray
    }
}
catch {
    Write-Host "✗ Compute API failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Note: Compute requires Docker running in WSL2" -ForegroundColor Yellow
}
Write-Host ""

# Step 6: Test with gcloud CLI (if available)
Write-Host "Step 6: Testing with gcloud CLI..." -ForegroundColor Yellow
$gcloudAvailable = Get-Command gcloud -ErrorAction SilentlyContinue
if ($gcloudAvailable) {
    Write-Host "  Testing Storage..." -ForegroundColor Gray
    try {
        $buckets = gcloud storage ls 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ gcloud storage works" -ForegroundColor Green
        }
        else {
            Write-Host "  ✗ gcloud storage failed" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "  ✗ gcloud storage error" -ForegroundColor Red
    }
    
    Write-Host "  Testing IAM..." -ForegroundColor Gray
    try {
        $accounts = gcloud iam service-accounts list --project=test-project 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ gcloud iam works" -ForegroundColor Green
        }
        else {
            Write-Host "  ✗ gcloud iam failed" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "  ✗ gcloud iam error" -ForegroundColor Red
    }
    
    Write-Host "  Testing Compute..." -ForegroundColor Gray
    try {
        $instances = gcloud compute instances list --project=test-project --zones=us-central1-a 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ gcloud compute works" -ForegroundColor Green
        }
        else {
            Write-Host "  ✗ gcloud compute failed" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "  ✗ gcloud compute error" -ForegroundColor Red
    }
}
else {
    Write-Host "  ⊘ gcloud CLI not installed (skipping)" -ForegroundColor Gray
}
Write-Host ""

# Summary
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor White
Write-Host "  Storage endpoint: $env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE" -ForegroundColor Gray
Write-Host "  IAM endpoint: $env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM" -ForegroundColor Gray
Write-Host "  Compute endpoint: $env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE" -ForegroundColor Gray
Write-Host "  Project: $env:CLOUDSDK_CORE_PROJECT" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. All services working? Start using the emulator!" -ForegroundColor White
Write-Host "  2. Compute failed? Ensure Docker is running in WSL2" -ForegroundColor White
Write-Host "  3. Want to persist settings? Run: .\setup-gcloud-emulator.ps1" -ForegroundColor White
Write-Host ""
