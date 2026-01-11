Write-Host "Reverting environment to Real GCP" -ForegroundColor Cyan

# Unset emulator overrides
Remove-Item Env:STORAGE_EMULATOR_HOST -ErrorAction SilentlyContinue
Remove-Item Env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE -ErrorAction SilentlyContinue
Remove-Item Env:BOTO_CONFIG -ErrorAction SilentlyContinue

# Re-enable gcloud credentials
& gcloud config unset auth/disable_credentials | Out-Null

Write-Host "Environment reverted" -ForegroundColor Green
Write-Host "Run 'gcloud auth login' to use real GCP credentials" -ForegroundColor Yellow
