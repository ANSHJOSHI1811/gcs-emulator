# GCP Emulator Backend Startup Script
# This script starts the backend server with proper configuration

Write-Host "Starting GCP IAM Emulator Backend..." -ForegroundColor Cyan
Write-Host "Working Directory: $PWD" -ForegroundColor Yellow
Write-Host "Python Version:" -ForegroundColor Yellow
python --version

# Set environment variables
$env:COMPUTE_ENABLED = "false"
$env:FLASK_APP = "app.factory"
$env:FLASK_ENV = "development"

# Start the server
Write-Host "`nStarting server on http://127.0.0.1:8080..." -ForegroundColor Green
Write-Host "Press CTRL+C to stop" -ForegroundColor Yellow
Write-Host ""

python run.py
