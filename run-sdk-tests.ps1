# Quick Test Runner for GCP SDK Tests
# Run all SDK integration tests with proper setup

Write-Host "=== GCP Emulator SDK Test Suite ===" -ForegroundColor Cyan
Write-Host ""

# Check Python environment
Write-Host "[1/5] Checking Python environment..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check if in virtual environment
Write-Host "[2/5] Checking virtual environment..." -ForegroundColor Yellow
$inVenv = $env:VIRTUAL_ENV
if ($inVenv) {
    Write-Host "✓ Virtual environment active: $inVenv" -ForegroundColor Green
} else {
    Write-Host "⚠ Not in virtual environment" -ForegroundColor Yellow
    Write-Host "  Activate with: .venv\Scripts\activate" -ForegroundColor Gray
}
Write-Host ""

# Install test dependencies
Write-Host "[3/5] Installing test dependencies..." -ForegroundColor Yellow
Push-Location "gcp-emulator-package"
pip install -q -r tests/sdk/requirements-test.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host ""

# Check backend
Write-Host "[4/5] Checking backend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -Method GET -TimeoutSec 2 2>&1
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Backend is running on port 8080" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Backend not responding on port 8080" -ForegroundColor Red
    Write-Host "  Start with: .\start-emulator.ps1 -BackendOnly" -ForegroundColor Yellow
    Pop-Location
    exit 1
}
Write-Host ""

# Run tests
Write-Host "[5/5] Running SDK tests..." -ForegroundColor Yellow
Write-Host ""

# Set environment variables
$env:EMULATOR_ENDPOINT = "http://localhost:8080"
$env:TEST_DATABASE_URL = "postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator"

# Run pytest with nice output
pytest tests/sdk/ -v --tb=short --color=yes

$testResult = $LASTEXITCODE

Pop-Location

Write-Host ""
if ($testResult -eq 0) {
    Write-Host "=== All Tests Passed! ===" -ForegroundColor Green
} else {
    Write-Host "=== Some Tests Failed ===" -ForegroundColor Red
    Write-Host "Review output above for details" -ForegroundColor Yellow
}
Write-Host ""

exit $testResult
