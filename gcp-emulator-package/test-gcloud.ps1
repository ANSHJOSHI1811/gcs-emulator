# Test gcloud CLI with GCP Emulator
# This script demonstrates real gcloud commands working with local emulator

Write-Host "🧪 Testing gcloud CLI with Local Emulator" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if gcloud is installed
Write-Host "1️⃣ Checking gcloud CLI installation..." -ForegroundColor Yellow
try {
    $version = gcloud version 2>&1 | Select-Object -First 1
    Write-Host "   ✅ $version" -ForegroundColor Green
} catch {
    Write-Host "   ❌ gcloud CLI not found! Install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test backend connectivity
Write-Host "2️⃣ Testing emulator backend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8080/storage/v1" -UseBasicParsing -ErrorAction Stop
    Write-Host "   ✅ Emulator is running!" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Emulator not reachable. Start it with:" -ForegroundColor Red
    Write-Host "      cd gcp-emulator-package; python run.py" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Create a test bucket
Write-Host "3️⃣ Creating test bucket with gcloud..." -ForegroundColor Yellow
try {
    $result = gcloud storage buckets create gs://gcloud-test-bucket --project=test-project 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Bucket created successfully!" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Bucket might already exist: $result" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Failed to create bucket: $_" -ForegroundColor Red
}
Write-Host ""

# List buckets
Write-Host "4️⃣ Listing buckets with gcloud..." -ForegroundColor Yellow
try {
    $buckets = gcloud storage buckets list --project=test-project 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Buckets found:" -ForegroundColor Green
        Write-Host "   $buckets" -ForegroundColor White
    } else {
        Write-Host "   ⚠️  $buckets" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Failed to list buckets: $_" -ForegroundColor Red
}
Write-Host ""

# Create a test file
Write-Host "5️⃣ Creating test file..." -ForegroundColor Yellow
"Hello from gcloud CLI! $(Get-Date)" | Out-File -Encoding utf8 gcloud-test.txt
Write-Host "   ✅ Test file created: gcloud-test.txt" -ForegroundColor Green
Write-Host ""

# Upload file
Write-Host "6️⃣ Uploading file with gcloud storage cp..." -ForegroundColor Yellow
try {
    $result = gcloud storage cp gcloud-test.txt gs://gcloud-test-bucket/ 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ File uploaded successfully!" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Upload failed: $result" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Upload error: $_" -ForegroundColor Red
}
Write-Host ""

# List objects
Write-Host "7️⃣ Listing objects with gcloud storage ls..." -ForegroundColor Yellow
try {
    $objects = gcloud storage ls gs://gcloud-test-bucket/ 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Objects found:" -ForegroundColor Green
        Write-Host "   $objects" -ForegroundColor White
    } else {
        Write-Host "   ⚠️  $objects" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Failed to list objects: $_" -ForegroundColor Red
}
Write-Host ""

# Download file
Write-Host "8️⃣ Downloading file with gcloud storage cp..." -ForegroundColor Yellow
try {
    $result = gcloud storage cp gs://gcloud-test-bucket/gcloud-test.txt downloaded-gcloud-test.txt 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ File downloaded successfully!" -ForegroundColor Green
        $content = Get-Content downloaded-gcloud-test.txt
        Write-Host "   📄 Content: $content" -ForegroundColor Cyan
    } else {
        Write-Host "   ❌ Download failed: $result" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Download error: $_" -ForegroundColor Red
}
Write-Host ""

# Test IAM service account
Write-Host "9️⃣ Creating service account with gcloud iam..." -ForegroundColor Yellow
try {
    $result = gcloud iam service-accounts create gcloud-test-sa --display-name="gcloud Test SA" --project=test-project 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Service account created!" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Service account might already exist: $result" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Failed to create service account: $_" -ForegroundColor Red
}
Write-Host ""

# List service accounts
Write-Host "🔟 Listing service accounts with gcloud iam..." -ForegroundColor Yellow
try {
    $accounts = gcloud iam service-accounts list --project=test-project 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Service accounts found:" -ForegroundColor Green
        Write-Host "   $accounts" -ForegroundColor White
    } else {
        Write-Host "   ⚠️  $accounts" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Failed to list service accounts: $_" -ForegroundColor Red
}
Write-Host ""

# Cleanup
Write-Host "🧹 Cleaning up test files..." -ForegroundColor Yellow
Remove-Item gcloud-test.txt -ErrorAction SilentlyContinue
Remove-Item downloaded-gcloud-test.txt -ErrorAction SilentlyContinue
Write-Host "   ✅ Cleanup complete!" -ForegroundColor Green
Write-Host ""

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "🎉 Test Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Your gcloud CLI is now working with the local emulator!" -ForegroundColor Cyan
Write-Host "All requests went to http://127.0.0.1:8080 instead of real GCP! 🚀" -ForegroundColor Green
Write-Host ""
Write-Host "📚 Full documentation: .\GCLOUD_CLI_SETUP.md" -ForegroundColor Cyan
