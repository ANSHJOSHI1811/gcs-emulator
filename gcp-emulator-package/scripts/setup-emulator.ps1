param(
    [string]$Project = "test-project",
    [string]$Zone = "us-central1-a"
)

Write-Host "Setting up emulator environment for gcloud + gsutil" -ForegroundColor Cyan

# Point CLIs/SDKs to local emulator endpoints
$env:STORAGE_EMULATOR_HOST = "http://localhost:8080"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE = "http://localhost:8080/compute/v1"

# Use bundled gsutil emulator boto config
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$docsDir = Join-Path $scriptDir "..\docs"
$env:BOTO_CONFIG = Join-Path $docsDir "gsutil-emulator.boto"

# Configure gcloud
& gcloud config set core/project $Project | Out-Null
& gcloud config set compute/zone $Zone | Out-Null
& gcloud config set auth/disable_credentials true | Out-Null

Write-Host "Emulator setup complete" -ForegroundColor Green
Write-Host "- STORAGE_EMULATOR_HOST=$($env:STORAGE_EMULATOR_HOST)" -ForegroundColor White
Write-Host "- CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE=$($env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE)" -ForegroundColor White
Write-Host "- BOTO_CONFIG=$($env:BOTO_CONFIG)" -ForegroundColor White
Write-Host "Try: gsutil ls   |   gcloud compute instances list" -ForegroundColor Yellow
