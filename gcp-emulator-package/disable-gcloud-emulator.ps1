# Disable gcloud CLI emulator mode
# Save this as: disable-gcloud-emulator.ps1

Write-Host "🔄 Disabling GCP Emulator mode..." -ForegroundColor Cyan
Write-Host ""

# Remove environment variables
Remove-Item Env:\CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE -ErrorAction SilentlyContinue
Remove-Item Env:\CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM -ErrorAction SilentlyContinue
Remove-Item Env:\CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE -ErrorAction SilentlyContinue
Remove-Item Env:\CLOUDSDK_AUTH_ACCESS_TOKEN -ErrorAction SilentlyContinue
Remove-Item Env:\CLOUDSDK_CORE_PROJECT -ErrorAction SilentlyContinue
Remove-Item Env:\CLOUDSDK_AUTH_DISABLE_CREDENTIALS -ErrorAction SilentlyContinue
Remove-Item Env:\CLOUDSDK_CORE_DISABLE_PROMPTS -ErrorAction SilentlyContinue

Write-Host "✅ Environment variables cleared!" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  gcloud CLI now points to real GCP" -ForegroundColor Yellow
Write-Host ""
Write-Host "💡 To re-enable emulator mode, run: .\setup-gcloud-emulator.ps1" -ForegroundColor Cyan
