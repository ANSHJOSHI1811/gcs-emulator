# Quick Setup Script for gcloud CLI with GCP Emulator
# Save this as: setup-gcloud-emulator.ps1

Write-Host "🚀 Setting up gcloud CLI to point to GCP Emulator..." -ForegroundColor Cyan
Write-Host ""

# Set environment variables
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE = "http://127.0.0.1:8080"
$env:CLOUDSDK_AUTH_ACCESS_TOKEN = "mock-token-12345"
$env:CLOUDSDK_CORE_PROJECT = "test-project"
$env:CLOUDSDK_AUTH_DISABLE_CREDENTIALS = "True"
$env:CLOUDSDK_CORE_DISABLE_PROMPTS = "True"

Write-Host "✅ Environment variables set:" -ForegroundColor Green
Write-Host "   CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = http://127.0.0.1:8080"
Write-Host "   CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = http://127.0.0.1:8080"
Write-Host "   CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE = http://127.0.0.1:8080"
Write-Host "   CLOUDSDK_AUTH_ACCESS_TOKEN = mock-token-12345"
Write-Host "   CLOUDSDK_CORE_PROJECT = test-project"
Write-Host ""

# Test backend connectivity
Write-Host "🔍 Testing emulator connectivity..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8080/storage/v1" -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ Backend is reachable!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ Cannot reach backend at http://127.0.0.1:8080" -ForegroundColor Red
    Write-Host "   Make sure the backend server is running:" -ForegroundColor Yellow
    Write-Host "   cd gcp-emulator-package; `$env:COMPUTE_ENABLED = 'false'; python run.py" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Check if gcloud is installed
Write-Host "🔍 Checking gcloud CLI installation..." -ForegroundColor Cyan
try {
    $gcloudVersion = gcloud version 2>&1 | Select-String "Google Cloud SDK"
    Write-Host "✅ gcloud CLI is installed: $gcloudVersion" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ gcloud CLI not found!" -ForegroundColor Red
    Write-Host "   Install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "🎉 Setup complete! You can now use gcloud commands:" -ForegroundColor Green
Write-Host ""
Write-Host "📦 Try these commands:" -ForegroundColor Cyan
Write-Host "   gcloud storage buckets create gs://test-bucket --project=test-project" -ForegroundColor White
Write-Host "   gcloud storage buckets list --project=test-project" -ForegroundColor White
Write-Host "   gcloud iam service-accounts list --project=test-project" -ForegroundColor White
Write-Host ""
Write-Host "📚 Full guide: .\GCLOUD_CLI_SETUP.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 To disable emulator mode, run: .\disable-gcloud-emulator.ps1" -ForegroundColor Yellow
