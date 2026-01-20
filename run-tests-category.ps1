# Run specific test categories

param(
    [ValidateSet("storage", "compute", "database", "all")]
    [string]$Category = "all",
    
    [switch]$Coverage,
    [switch]$Verbose
)

$env:EMULATOR_ENDPOINT = "http://localhost:8080"
$env:TEST_DATABASE_URL = "postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator"

Push-Location "gcp-emulator-package"

$pytest_args = @()

# Select test file
switch ($Category) {
    "storage" { 
        $pytest_args += "tests/sdk/test_storage.py"
        Write-Host "Running Storage SDK Tests..." -ForegroundColor Cyan
    }
    "compute" { 
        $pytest_args += "tests/sdk/test_compute.py"
        Write-Host "Running Compute SDK Tests..." -ForegroundColor Cyan
    }
    "database" { 
        $pytest_args += "tests/sdk/test_database_integrity.py"
        Write-Host "Running Database Integrity Tests..." -ForegroundColor Cyan
    }
    "all" { 
        $pytest_args += "tests/sdk/"
        Write-Host "Running All SDK Tests..." -ForegroundColor Cyan
    }
}

# Add flags
if ($Verbose) {
    $pytest_args += "-vv"
} else {
    $pytest_args += "-v"
}

$pytest_args += "--tb=short"
$pytest_args += "--color=yes"

if ($Coverage) {
    $pytest_args += "--cov=app"
    $pytest_args += "--cov-report=html"
    $pytest_args += "--cov-report=term"
}

Write-Host ""
Write-Host "Command: pytest $($pytest_args -join ' ')" -ForegroundColor Gray
Write-Host ""

# Run tests
pytest @pytest_args

$result = $LASTEXITCODE

Pop-Location

if ($Coverage -and $result -eq 0) {
    Write-Host ""
    Write-Host "Coverage report: gcp-emulator-package/htmlcov/index.html" -ForegroundColor Cyan
}

exit $result
