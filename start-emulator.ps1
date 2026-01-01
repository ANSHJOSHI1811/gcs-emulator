# Start GCP Emulator - Complete Stack
# This script starts both backend and frontend

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$ErrorActionPreference = "Stop"

Write-Host "=== GCP Emulator Startup ===" -ForegroundColor Cyan
Write-Host ""

# Check WSL
Write-Host "Checking WSL Ubuntu-24.04..." -ForegroundColor Yellow
$wslCheck = wsl -d Ubuntu-24.04 echo "OK" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ WSL Ubuntu-24.04 not found or not started" -ForegroundColor Red
    Write-Host "  Starting WSL..." -ForegroundColor Yellow
    wsl -d Ubuntu-24.04 echo "Starting..."
}
Write-Host "✓ WSL is ready" -ForegroundColor Green
Write-Host ""

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Yellow
$dockerCheck = wsl -d Ubuntu-24.04 docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker is not running" -ForegroundColor Red
    Write-Host "  Starting Docker service..." -ForegroundColor Yellow
    wsl -d Ubuntu-24.04 sudo service docker start
    Start-Sleep -Seconds 3
}
Write-Host "✓ Docker is running" -ForegroundColor Green
Write-Host ""

# Start Backend
if (-not $FrontendOnly) {
    Write-Host "Starting Backend API..." -ForegroundColor Yellow
    Write-Host "  Location: gcp-emulator-package" -ForegroundColor Cyan
    Write-Host "  Port: 8080" -ForegroundColor Cyan
    Write-Host ""
    
    $backendPath = "/mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package"
    
    # Start in new window
    $backendCommand = "wsl -d Ubuntu-24.04 bash -c 'cd $backendPath && source .venv/bin/activate && python run.py'"
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand
    
    Write-Host "✓ Backend starting in new window..." -ForegroundColor Green
    Write-Host "  Waiting for backend to be ready..." -ForegroundColor Yellow
    
    # Wait for backend to start
    $maxWait = 30
    $waited = 0
    $backendReady = $false
    
    while ($waited -lt $maxWait -and -not $backendReady) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -Method GET -TimeoutSec 1 2>&1
            if ($response.StatusCode -eq 200) {
                $backendReady = $true
            }
        } catch {
            # Not ready yet
        }
        
        if (-not $backendReady) {
            Start-Sleep -Seconds 1
            $waited++
            Write-Host "." -NoNewline
        }
    }
    
    Write-Host ""
    
    if ($backendReady) {
        Write-Host "✓ Backend is ready at http://localhost:8080" -ForegroundColor Green
    } else {
        Write-Host "⚠ Backend is starting but not responding yet" -ForegroundColor Yellow
        Write-Host "  Check the backend window for errors" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Start Frontend
if (-not $BackendOnly) {
    Write-Host "Starting Frontend UI..." -ForegroundColor Yellow
    Write-Host "  Location: gcp-emulator-ui" -ForegroundColor Cyan
    Write-Host "  Port: 3000" -ForegroundColor Cyan
    Write-Host ""
    
    Set-Location "gcp-emulator-ui"
    
    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Host "  Installing dependencies (first run)..." -ForegroundColor Yellow
        npm install
    }
    
    # Start in new window
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev"
    
    Write-Host "✓ Frontend starting in new window..." -ForegroundColor Green
    Write-Host "  UI will be available at http://localhost:3000" -ForegroundColor Cyan
    Write-Host ""
    
    Set-Location ..
}

Write-Host ""
Write-Host "=== Startup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services:" -ForegroundColor Yellow
if (-not $FrontendOnly) {
    Write-Host "  • Backend API: http://localhost:8080" -ForegroundColor Green
    Write-Host "    Health check: http://localhost:8080/health" -ForegroundColor Cyan
}
if (-not $BackendOnly) {
    Write-Host "  • Frontend UI: http://localhost:3000" -ForegroundColor Green
}
Write-Host ""
Write-Host "Available Features:" -ForegroundColor Yellow
Write-Host "  • Cloud Storage (Buckets & Objects)"
Write-Host "  • IAM (Service Accounts, Roles, Policies)"
Write-Host "  • Compute Engine (Docker-backed VMs)"
Write-Host ""
Write-Host "Quick Links:" -ForegroundColor Yellow
Write-Host "  • Storage: http://localhost:3000/services/storage"
Write-Host "  • IAM: http://localhost:3000/services/iam"
Write-Host "  • Compute: http://localhost:3000/services/compute"
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop services" -ForegroundColor Gray
Write-Host ""
