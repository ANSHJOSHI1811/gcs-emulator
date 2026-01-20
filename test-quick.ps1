Write-Host '=== GCP Emulator - All Services Test ===' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Configuring environment...' -ForegroundColor Yellow
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = 'http://127.0.0.1:8080'
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = 'http://127.0.0.1:8080'
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE = 'http://127.0.0.1:8080'
$env:CLOUDSDK_CORE_PROJECT = 'test-project'
Write-Host 'Environment configured' -ForegroundColor Green
Write-Host ''
Write-Host 'Testing backend connectivity...' -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8080/' -UseBasicParsing -TimeoutSec 5
    Write-Host 'Backend is running on port 8080' -ForegroundColor Green
} catch {
    Write-Host 'Backend not reachable' -ForegroundColor Red
    exit 1
}
Write-Host ''
Write-Host 'Testing Storage API...' -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8080/storage/v1/b?project=test-project' -Headers @{Authorization='Bearer mock'} -UseBasicParsing
    Write-Host 'Storage API works' -ForegroundColor Green
} catch {
    Write-Host 'Storage API failed' -ForegroundColor Red
}
Write-Host ''
Write-Host 'Testing IAM API...' -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8080/v1/projects/test-project/serviceAccounts' -Headers @{Authorization='Bearer mock'} -UseBasicParsing
    Write-Host 'IAM API works' -ForegroundColor Green
} catch {
    Write-Host 'IAM API failed' -ForegroundColor Red
}
Write-Host ''
Write-Host 'Testing Compute API...' -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8080/compute/v1/projects/test-project/zones/us-central1-a/instances' -Headers @{Authorization='Bearer mock'} -UseBasicParsing
    Write-Host 'Compute API works' -ForegroundColor Green
} catch {
    Write-Host 'Compute API failed (Docker may not be running)' -ForegroundColor Red
}
Write-Host ''
Write-Host 'Configuration Summary:' -ForegroundColor Cyan
Write-Host '  Storage: '$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE -ForegroundColor Gray
Write-Host '  IAM: '$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM -ForegroundColor Gray
Write-Host '  Compute: '$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE -ForegroundColor Gray
Write-Host ''
