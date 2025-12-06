# Quick Reference: New Features Usage Guide

## 1. Object Copy API

### Same-Bucket Copy
```bash
# Copy file.txt to copy.txt in the same bucket
curl -X POST "http://localhost:8080/storage/v1/b/my-bucket/o/file.txt/copyTo/b/my-bucket/o/copy.txt"
```

### Cross-Bucket Copy
```bash
# Copy from bucket-a to bucket-b
curl -X POST "http://localhost:8080/storage/v1/b/bucket-a/o/source.txt/copyTo/b/bucket-b/o/dest.txt"
```

### Python SDK
```python
from google.cloud import storage

client = storage.Client()
source_bucket = client.bucket("source-bucket")
source_blob = source_bucket.blob("file.txt")
destination_bucket = client.bucket("dest-bucket")

# Copy
source_bucket.copy_blob(source_blob, destination_bucket, "copy.txt")
```

---

## 2. CORS Configuration

### Get CORS Configuration
```bash
curl http://localhost:8080/storage/v1/b/my-bucket/cors
```

### Set CORS Rules
```bash
curl -X PUT http://localhost:8080/storage/v1/b/my-bucket/cors \
  -H "Content-Type: application/json" \
  -d '{
    "cors": [
      {
        "origin": ["https://example.com", "https://app.example.com"],
        "method": ["GET", "POST", "PUT", "DELETE"],
        "responseHeader": ["Content-Type", "Authorization"],
        "maxAgeSeconds": 3600
      }
    ]
  }'
```

### Allow All Origins (Development)
```bash
curl -X PUT http://localhost:8080/storage/v1/b/my-bucket/cors \
  -H "Content-Type: application/json" \
  -d '{
    "cors": [
      {
        "origin": ["*"],
        "method": ["GET", "POST", "PUT", "DELETE", "HEAD"],
        "responseHeader": ["*"],
        "maxAgeSeconds": 3600
      }
    ]
  }'
```

### Delete CORS Configuration
```bash
curl -X DELETE http://localhost:8080/storage/v1/b/my-bucket/cors
```

---

## 3. Event Delivery (Webhooks)

### Create Notification Configuration
```bash
curl -X POST http://localhost:8080/storage/v1/b/my-bucket/notificationConfigs \
  -H "Content-Type: application/json" \
  -d '{
    "webhookUrl": "https://my-app.com/webhook",
    "eventTypes": ["OBJECT_FINALIZE", "OBJECT_DELETE"],
    "objectNamePrefix": "logs/",
    "payloadFormat": "JSON_API_V1"
  }'
```

### List All Notifications
```bash
curl http://localhost:8080/storage/v1/b/my-bucket/notificationConfigs
```

### Get Specific Notification
```bash
curl http://localhost:8080/storage/v1/b/my-bucket/notificationConfigs/{config-id}
```

### Delete Notification
```bash
curl -X DELETE http://localhost:8080/storage/v1/b/my-bucket/notificationConfigs/{config-id}
```

### Webhook Payload Format
Your webhook will receive:
```json
{
  "kind": "storage#objectChangeNotification",
  "bucket": "my-bucket",
  "object": "logs/app.log",
  "eventType": "OBJECT_FINALIZE",
  "generation": 1701234567890,
  "metadata": {}
}
```

### Test Webhook Locally (using webhook.site)
1. Go to https://webhook.site
2. Copy your unique URL
3. Create notification:
```bash
curl -X POST http://localhost:8080/storage/v1/b/test-bucket/notificationConfigs \
  -H "Content-Type: application/json" \
  -d '{
    "webhookUrl": "https://webhook.site/your-unique-id",
    "eventTypes": ["OBJECT_FINALIZE"]
  }'
```
4. Upload a file - check webhook.site for the event

---

## 4. Lifecycle Rules

### Set Lifecycle Rules
```bash
curl -X PUT http://localhost:8080/storage/v1/b/my-bucket/lifecycle \
  -H "Content-Type: application/json" \
  -d '{
    "rule": [
      {
        "action": "Delete",
        "ageDays": 30
      },
      {
        "action": "Archive",
        "ageDays": 90
      }
    ]
  }'
```

### Example: Delete Logs After 7 Days
```bash
curl -X PUT http://localhost:8080/storage/v1/b/logs-bucket/lifecycle \
  -H "Content-Type: application/json" \
  -d '{
    "rule": [
      {
        "action": "Delete",
        "ageDays": 7
      }
    ]
  }'
```

### Get Lifecycle Rules
```bash
curl http://localhost:8080/storage/v1/b/my-bucket/lifecycle
```

### Delete Lifecycle Rules
```bash
curl -X DELETE http://localhost:8080/storage/v1/b/my-bucket/lifecycle
```

### Configure Lifecycle Interval
```bash
# Set lifecycle check interval (default: 5 minutes)
export LIFECYCLE_INTERVAL_MINUTES=10

# Start server
python run.py
```

---

## 5. Bucket Name Uniqueness (Fixed)

### Before Fix
```bash
# This would fail
curl -X POST "http://localhost:8080/storage/v1/b?project=project1" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-bucket"}'

curl -X POST "http://localhost:8080/storage/v1/b?project=project2" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-bucket"}'  # ERROR: already exists
```

### After Fix
```bash
# Now both succeed - same bucket name in different projects
curl -X POST "http://localhost:8080/storage/v1/b?project=project1" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-bucket", "location": "US"}'

curl -X POST "http://localhost:8080/storage/v1/b?project=project2" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-bucket", "location": "EU"}'  # ✅ Works!
```

---

## Common Workflows

### Workflow 1: Backup Files to Archive Bucket
```bash
# 1. Create backup bucket
curl -X POST "http://localhost:8080/storage/v1/b?project=my-project" \
  -H "Content-Type: application/json" \
  -d '{"name": "backups", "storageClass": "ARCHIVE"}'

# 2. Copy files from production to backup
curl -X POST "http://localhost:8080/storage/v1/b/production/o/data.db/copyTo/b/backups/o/backup-2025-12-06.db"

# 3. Set lifecycle to delete old backups after 90 days
curl -X PUT http://localhost:8080/storage/v1/b/backups/lifecycle \
  -H "Content-Type: application/json" \
  -d '{"rule": [{"action": "Delete", "ageDays": 90}]}'
```

### Workflow 2: Auto-Archive + Webhook Notification
```bash
# 1. Create bucket with CORS for web uploads
curl -X POST "http://localhost:8080/storage/v1/b?project=my-project" \
  -H "Content-Type: application/json" \
  -d '{"name": "uploads"}'

# 2. Set CORS
curl -X PUT http://localhost:8080/storage/v1/b/uploads/cors \
  -H "Content-Type: application/json" \
  -d '{"cors": [{"origin": ["*"], "method": ["POST"]}]}'

# 3. Set webhook for upload notifications
curl -X POST http://localhost:8080/storage/v1/b/uploads/notificationConfigs \
  -H "Content-Type: application/json" \
  -d '{"webhookUrl": "https://my-app.com/on-upload", "eventTypes": ["OBJECT_FINALIZE"]}'

# 4. Set lifecycle to archive after 30 days
curl -X PUT http://localhost:8080/storage/v1/b/uploads/lifecycle \
  -H "Content-Type: application/json" \
  -d '{"rule": [{"action": "Archive", "ageDays": 30}]}'
```

### Workflow 3: Multi-Region Bucket Setup
```bash
# Now possible with fixed uniqueness constraint!
curl -X POST "http://localhost:8080/storage/v1/b?project=my-app" \
  -H "Content-Type: application/json" \
  -d '{"name": "assets", "location": "US"}'

curl -X POST "http://localhost:8080/storage/v1/b?project=my-app" \
  -H "Content-Type: application/json" \
  -d '{"name": "assets", "location": "EU"}'

curl -X POST "http://localhost:8080/storage/v1/b?project=my-app" \
  -H "Content-Type: application/json" \
  -d '{"name": "assets", "location": "ASIA"}'
```

---

## Troubleshooting

### Webhook Not Receiving Events
```bash
# Check notification configs
curl http://localhost:8080/storage/v1/b/my-bucket/notificationConfigs

# Verify webhook URL is reachable
curl -X POST YOUR_WEBHOOK_URL -d '{"test": "data"}'

# Check server logs for delivery errors
tail -f logs/gcs-emulator.log | grep "notification"
```

### Lifecycle Rules Not Executing
```bash
# Check if rules are set
curl http://localhost:8080/storage/v1/b/my-bucket/lifecycle

# Verify lifecycle interval (default: 5 minutes)
# Wait at least LIFECYCLE_INTERVAL_MINUTES before expecting execution

# Check logs
tail -f logs/gcs-emulator.log | grep "lifecycle"
```

### Copy Failing
```bash
# Verify source exists
curl http://localhost:8080/storage/v1/b/source-bucket/o/file.txt

# Verify destination bucket exists
curl http://localhost:8080/storage/v1/b/dest-bucket

# Check error response
curl -v -X POST "http://localhost:8080/storage/v1/b/src/o/file.txt/copyTo/b/dst/o/copy.txt"
```

---

## Environment Variables

```bash
# Lifecycle execution interval (minutes)
export LIFECYCLE_INTERVAL_MINUTES=10

# Database connection
export DATABASE_URL="postgresql://user:pass@localhost/gcs_emulator"

# Storage path
export STORAGE_PATH="./storage"

# Log level
export LOG_LEVEL="INFO"
```

---

## Python SDK Examples

### Object Copy
```python
from google.cloud import storage
import os

os.environ["STORAGE_EMULATOR_HOST"] = "http://localhost:8080"
client = storage.Client(project="test-project")

# Copy within bucket
source_bucket = client.bucket("my-bucket")
source_blob = source_bucket.blob("original.txt")
destination_blob = source_bucket.copy_blob(source_blob, source_bucket, "copy.txt")

# Copy across buckets
dest_bucket = client.bucket("other-bucket")
cross_copy = source_bucket.copy_blob(source_blob, dest_bucket, "copied.txt")
```

### Set Bucket CORS
```python
from google.cloud import storage

client = storage.Client()
bucket = client.bucket("my-bucket")

bucket.cors = [
    {
        "origin": ["https://example.com"],
        "method": ["GET", "POST"],
        "responseHeader": ["Content-Type"],
        "maxAgeSeconds": 3600
    }
]
bucket.patch()
```

---

## API Compatibility

All new endpoints follow GCS JSON API v1 format:
- ✅ Compatible with `google-cloud-storage` Python SDK
- ✅ Compatible with `gcloud` CLI (where applicable)
- ✅ REST API compatible with standard HTTP clients

**GCS API Documentation:**
- Object Copy: https://cloud.google.com/storage/docs/json_api/v1/objects/copy
- CORS: https://cloud.google.com/storage/docs/cross-origin
- Notifications: https://cloud.google.com/storage/docs/object-change-notification
- Lifecycle: https://cloud.google.com/storage/docs/lifecycle
