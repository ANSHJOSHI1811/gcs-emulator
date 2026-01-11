# Compute Engine Quick Test Script
# Tests if compute service is working properly

Write-Host "=== GCP Emulator Compute Engine Test ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check WSL
Write-Host "[1/6] Checking WSL..." -ForegroundColor Yellow
$wslOutput = wsl --list --verbose 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "CHECK WSL is available" -ForegroundColor Green
    Write-Host $wslOutput
} else {
    Write-Host "X WSL not found" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Check Docker
Write-Host "[2/6] Checking Docker in WSL..." -ForegroundColor Yellow
$dockerStatus = wsl -d Ubuntu-24.04 docker ps 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "CHECK Docker is running" -ForegroundColor Green
    Write-Host $dockerStatus
} else {
    Write-Host "X Docker is not running" -ForegroundColor Red
    Write-Host "Start Docker with: wsl -d Ubuntu-24.04 sudo service docker start" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# 3. Check Backend
Write-Host "[3/6] Checking Backend API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -Method GET -TimeoutSec 5 2>&1
    if ($response.StatusCode -eq 200) {
        Write-Host "CHECK Backend is running on port 8080" -ForegroundColor Green
    } else {
        Write-Host "X Backend returned status: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "X Backend is not responding" -ForegroundColor Red
    Write-Host "Start backend first!" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# 4. Check Compute Endpoint
Write-Host "[4/6] Checking Compute API endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/compute/instances" -Method GET -TimeoutSec 5 2>&1
    Write-Host "CHECK Compute API is accessible" -ForegroundColor Green
    $content = $response.Content | ConvertFrom-Json
    Write-Host "Current instances: $($content.count)" -ForegroundColor Cyan
} catch {
    Write-Host "X Compute API is not accessible" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}
Write-Host ""

# 5. Test Instance Creation
Write-Host "[5/6] Testing instance creation..." -ForegroundColor Yellow
$instanceData = @{
    name = "test-vm-$(Get-Random -Maximum 9999)"
    image = "alpine:latest"
    cpu = 1
    memory = 256
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/compute/instances" -Method POST -Body $instanceData -ContentType "application/json"
    Write-Host "CHECK Instance created successfully" -ForegroundColor Green
    Write-Host "  ID: $($response.id)"
    Write-Host "  Name: $($response.name)"
    Write-Host "  State: $($response.state)"
    Write-Host "  Container ID: $($response.container_id)"
    $testInstanceId = $response.id
} catch {
    Write-Host "X Failed to create instance" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}
Write-Host ""

# Wait a bit for container to start
Write-Host "Waiting 3 seconds for container to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 6. Verify Instance
Write-Host "[6/6] Verifying instance..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/compute/instances/$testInstanceId" -Method GET
    Write-Host "CHECK Instance is $($response.state)" -ForegroundColor Green
    
    # Check Docker container
    $containerId = $response.container_id
    if ($containerId) {
        $containerStatus = wsl -d Ubuntu-24.04 docker ps --filter "id=$containerId" --format "{{.Status}}"
        Write-Host "  Docker status: $containerStatus" -ForegroundColor Cyan
    }
} catch {
    Write-Host "X Failed to verify instance" -ForegroundColor Red
}
Write-Host ""

# Cleanup
Write-Host "Cleaning up test instance..." -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "http://localhost:8080/compute/instances/$testInstanceId/terminate" -Method POST | Out-Null
    Write-Host "CHECK Test instance terminated" -ForegroundColor Green
} catch {
    Write-Host "X Failed to cleanup test instance" -ForegroundColor Red
}
Write-Host ""

Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  CHECK WSL: Running"
Write-Host "  CHECK Docker: Running"
Write-Host "  CHECK Backend: Running on http://localhost:8080"
Write-Host "  CHECK Compute API: Working"
Write-Host "  CHECK Instance Creation: Success"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Start the UI: cd gcp-emulator-ui && npm run dev"
Write-Host "  2. Open browser: http://localhost:3000"
Write-Host "  3. Navigate to Services -> Compute Engine"
Write-Host "  4. Create and manage instances!"
Write-Host ""
