# gcloud CLI Configuration Guide for GCS Emulator

This guide explains how to configure `gcloud` CLI to work with the GCS Emulator.

## Prerequisites

- Google Cloud SDK installed (`gcloud`)
- GCS Emulator running on `http://localhost:8080`
- Docker installed (for Compute Engine instances)

## Configuration Steps

### 1. Set API Endpoint Overrides

Configure `gcloud` to point to your emulator instead of real GCP:

```bash
# Set emulator host for Storage
export STORAGE_EMULATOR_HOST="http://localhost:8080"

# Set emulator host for Compute (if using)
export COMPUTE_EMULATOR_HOST="http://localhost:8080"

# Set API endpoint overrides
gcloud config set api_endpoint_overrides/storage http://localhost:8080/storage/v1/
gcloud config set api_endpoint_overrides/compute http://localhost:8080/compute/v1/
gcloud config set api_endpoint_overrides/iam http://localhost:8080/
```

### 2. Configure Authentication

The emulator uses mock authentication. You can use any service account or user credentials:

```bash
# Create a mock service account key (emulator will accept any key)
curl -X POST "http://localhost:8080/v1/projects/demo-project/serviceAccounts" \
  -H "Content-Type: application/json" \
  -d '{
    "accountId": "emulator-sa",
    "displayName": "Emulator Service Account"
  }'

# Create a key for the service account
curl -X POST "http://localhost:8080/v1/projects/demo-project/serviceAccounts/emulator-sa@demo-project.iam.gserviceaccount.com/keys" \
  -H "Content-Type: application/json" \
  > emulator-key.json

# Activate the service account (emulator accepts any credentials)
gcloud auth activate-service-account --key-file=emulator-key.json
```

Or use mock user authentication:

```bash
# The emulator's OAuth endpoint will auto-approve
gcloud auth login --no-launch-browser

# When prompted, visit: http://localhost:8080/o/oauth2/v2/auth?...
# The emulator will automatically redirect with a valid code
```

### 3. Set Default Project

```bash
gcloud config set project demo-project
```

### 4. Verify Configuration

```bash
# Check configuration
gcloud config list

# Test Storage API
gcloud storage buckets list --project=demo-project

# Test Compute API
gcloud compute zones list --project=demo-project
```

## Using gcloud with the Emulator

### Storage Operations

```bash
# Create a bucket
gcloud storage buckets create gs://my-test-bucket \
  --project=demo-project \
  --location=US

# List buckets
gcloud storage buckets list --project=demo-project

# Upload a file
echo "test content" > test.txt
gcloud storage cp test.txt gs://my-test-bucket/

# List objects
gcloud storage ls gs://my-test-bucket/

# Download a file
gcloud storage cp gs://my-test-bucket/test.txt downloaded.txt

# Delete a bucket
gcloud storage rm -r gs://my-test-bucket/
```

### IAM Operations

```bash
# Create a service account
gcloud iam service-accounts create my-sa \
  --display-name="My Service Account" \
  --project=demo-project

# List service accounts
gcloud iam service-accounts list --project=demo-project

# Create a key
gcloud iam service-accounts keys create key.json \
  --iam-account=my-sa@demo-project.iam.gserviceaccount.com

# Get IAM policy for a bucket
gcloud storage buckets get-iam-policy gs://my-test-bucket

# Set IAM policy
gcloud storage buckets add-iam-policy-binding gs://my-test-bucket \
  --member="serviceAccount:my-sa@demo-project.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

### Compute Engine Operations

```bash
# List zones
gcloud compute zones list --project=demo-project

# List machine types in a zone
gcloud compute machine-types list \
  --zones=us-central1-a \
  --project=demo-project

# Create an instance (spawns a Docker container!)
gcloud compute instances create test-vm \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --project=demo-project

# List instances
gcloud compute instances list \
  --zones=us-central1-a \
  --project=demo-project

# Get instance details
gcloud compute instances describe test-vm \
  --zone=us-central1-a \
  --project=demo-project

# Stop an instance
gcloud compute instances stop test-vm \
  --zone=us-central1-a \
  --project=demo-project

# Start an instance
gcloud compute instances start test-vm \
  --zone=us-central1-a \
  --project=demo-project

# Delete an instance
gcloud compute instances delete test-vm \
  --zone=us-central1-a \
  --project=demo-project
```

## Environment Variables

Add these to your `~/.bashrc` or `~/.zshrc` for persistent configuration:

```bash
# GCS Emulator Configuration
export STORAGE_EMULATOR_HOST="http://localhost:8080"
export COMPUTE_EMULATOR_HOST="http://localhost:8080"
export CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE="http://localhost:8080/storage/v1/"
export CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE="http://localhost:8080/compute/v1/"
export CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM="http://localhost:8080/"
export CLOUDSDK_CORE_PROJECT="demo-project"

# Disable SSL verification for local emulator (development only!)
export CLOUDSDK_AUTH_DISABLE_SSL_VALIDATION=true
```

## Troubleshooting

### gcloud not connecting to emulator

1. Verify emulator is running:
   ```bash
   curl http://localhost:8080/health
   ```

2. Check environment variables:
   ```bash
   env | grep CLOUD
   env | grep STORAGE
   ```

3. Clear gcloud config cache:
   ```bash
   gcloud config configurations list
   gcloud config configurations activate default
   ```

### Authentication errors

The emulator uses mock authentication. If you see auth errors:

1. Make sure `MOCK_AUTH_ENABLED=true` in emulator config
2. Use any service account key - the emulator accepts all
3. Or visit the OAuth URL manually: `http://localhost:8080/o/oauth2/v2/auth`

### SSL/TLS errors

```bash
# Disable SSL verification (development only)
export CLOUDSDK_AUTH_DISABLE_SSL_VALIDATION=true
gcloud config set auth/disable_ssl_validation true
```

## Python Client Libraries

For Python code using `google-cloud-storage`:

```python
import os
from google.cloud import storage

# Set emulator host
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'

# Create client (will use emulator)
client = storage.Client(project='demo-project')

# Use normally
buckets = list(client.list_buckets())
print(f"Found {len(buckets)} buckets")
```

## Node.js Client Libraries

For Node.js using `@google-cloud/storage`:

```javascript
const {Storage} = require('@google-cloud/storage');

// Set emulator host
process.env.STORAGE_EMULATOR_HOST = 'http://localhost:8080';

// Create client
const storage = new Storage({
  projectId: 'demo-project'
});

// Use normally
async function listBuckets() {
  const [buckets] = await storage.getBuckets();
  console.log(`Found ${buckets.length} buckets`);
}
```

## Docker Compose Setup

For easier development, use Docker Compose:

```yaml
version: '3.8'

services:
  gcs-emulator:
    build: ./gcp-emulator-package
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/gcs_emulator
      - FLASK_ENV=development
      - MOCK_AUTH_ENABLED=true
    depends_on:
      - db
  
  db:
    image: postgres:16
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=gcs_emulator
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  ui:
    build: ./gcp-emulator-ui
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8080

volumes:
  postgres_data:
```

Then:

```bash
# Start everything
docker-compose up -d

# Configure gcloud
export STORAGE_EMULATOR_HOST="http://localhost:8080"
gcloud config set project demo-project

# Test
gcloud storage buckets list
```

## Notes

1. **Mock Auth**: The emulator bypasses real GCP authentication. All requests are allowed by default when `MOCK_AUTH_ENABLED=true`.

2. **IAM Enforcement**: IAM policies are stored and can be queried, but enforcement is optional (controlled by `MOCK_AUTH_ENABLED`).

3. **Docker Integration**: Compute Engine instances spawn real Docker containers on your machine.

4. **Persistent State**: All data is stored in PostgreSQL - restart safe.

5. **Linux-First**: File paths and networking assume Linux/Unix semantics.

## Next Steps

- Explore the UI at `http://localhost:3000`
- Check API docs at `http://localhost:8080/storage/v1`
- Review IAM policies: `gcloud storage buckets get-iam-policy gs://bucket-name`
- Create compute instances: `gcloud compute instances create test-vm`
