# GCP Stimulator - gcloud CLI Test Examples

## Overview
This document demonstrates working gcloud commands for testing Cloud Run and Artifact Registry against the GCP Stimulator backend.

## Setup

### Start the Backend
```bash
cd /home/ubuntu/gcs-stimulator/minimal-backend
python3 main.py
# Backend runs on port 8080
```

### Start the Frontend
```bash
cd /home/ubuntu/gcs-stimulator/gcp-stimulator-ui
npm run dev
# Frontend runs on port 3000
```

### Configure gcloud
```bash
gcloud config set project test-project
gcloud config set compute/region us-central1
```

---

## Artifact Registry Examples

### Create a Docker Repository
```bash
curl -X POST "http://localhost:8080/v1/projects/test-project/locations/us-central1/repositories" \
  -H "Content-Type: application/json" \
  -d '{
    "repositoryId": "my-docker-repo",
    "format": "DOCKER",
    "description": "My Docker repository for Cloud Run images"
  }'
```

**Response includes:**
- Repository name
- Registry host: `localhost:5000`
- Docker prefix: `us-central1-docker.pkg.dev/test-project/my-docker-repo`

### List Artifact Repositories
```bash
curl "http://localhost:8080/v1/projects/test-project/locations/us-central1/repositories"
```

### Get Repository Details
```bash
curl "http://localhost:8080/v1/projects/test-project/locations/us-central1/repositories/my-docker-repo"
```

### Docker Commands for Images
```bash
# Tag an image for your repository
docker tag myimage:latest us-central1-docker.pkg.dev/test-project/my-docker-repo/myimage:v1.0.0

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/test-project/my-docker-repo/myimage:v1.0.0

# Pull from Artifact Registry  
docker pull us-central1-docker.pkg.dev/test-project/my-docker-repo/myimage:v1.0.0
```

---

## Cloud Run Examples

### Deploy a Cloud Run Service
```bash
curl -X POST "http://localhost:8080/v2/projects/test-project/locations/us-central1/services?serviceId=my-service" \
  -H "Content-Type: application/json" \
  -d '{
    "template": {
      "containers": [{
        "image": "gcr.io/cloud-builders/gke-deploy:latest",
        "ports": [{"containerPort": 8080}],
        "env": [
          {"name": "ENVIRONMENT", "value": "production"},
          {"name": "DEBUG", "value": "false"}
        ]
      }]
    },
    "ingress": "INGRESS_TRAFFIC_ALL"
  }'
```

### List Cloud Run Services
```bash
curl "http://localhost:8080/v2/projects/test-project/locations/us-central1/services"
```

### Get Service Details
```bash
curl "http://localhost:8080/v2/projects/test-project/locations/us-central1/services/my-service"
```

### gcloud Deploy Command (for real GCP)
```bash
gcloud run deploy my-service \
  --image=us-central1-docker.pkg.dev/test-project/my-docker-repo/myimage:v1.0.0 \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080
```

---

## CI/CD Pipeline Example

### Complete Workflow
```bash
#!/bin/bash

PROJECT="test-project"
LOCATION="us-central1"
REPO="my-docker-repo"
SERVICE="my-app"
IMAGE_TAG="v1.0.0"

echo "1️⃣  Create Artifact Registry Repository"
curl -X POST "http://localhost:8080/v1/projects/${PROJECT}/locations/${LOCATION}/repositories" \
  -H "Content-Type: application/json" \
  -d "{
    \"repositoryId\": \"${REPO}\",
    \"format\": \"DOCKER\"
  }"

echo ""
echo "2️⃣  Build Docker Image"
docker build -t us-central1-docker.pkg.dev/${PROJECT}/${REPO}/app:${IMAGE_TAG} .

echo ""
echo "3️⃣  Push to Artifact Registry"
docker push us-central1-docker.pkg.dev/${PROJECT}/${REPO}/app:${IMAGE_TAG}

echo ""
echo "4️⃣  Deploy to Cloud Run"
curl -X POST "http://localhost:8080/v2/projects/${PROJECT}/locations/${LOCATION}/services?serviceId=${SERVICE}" \
  -H "Content-Type: application/json" \
  -d "{
    \"template\": {
      \"containers\": [{
        \"image\": \"us-central1-docker.pkg.dev/${PROJECT}/${REPO}/app:${IMAGE_TAG}\",
        \"ports\": [{\"containerPort\": 8080}]
      }]
    },
    \"ingress\": \"INGRESS_TRAFFIC_ALL\"
  }"

echo ""
echo "✅ Pipeline Complete!"
```

---

## Query Parameters

### Service Deployment
- `serviceId`: The name of the service to deploy (required)
- Query string format: `?serviceId=my-service`

### Update Service
- `updateMask`: Fields to update (optional)

---

## Response Formats

### Artifact Repository Response
```json
{
  "name": "projects/test-project/locations/us-central1/repositories/my-docker-repo",
  "format": "DOCKER",
  "description": "My Docker repository",
  "registryHost": "localhost:5000",
  "dockerRepositoryPrefix": "us-central1-docker.pkg.dev/test-project/my-docker-repo",
  "createTime": "2026-02-24T12:00:00.000000Z",
  "updateTime": "2026-02-24T12:00:00.000000Z"
}
```

### Cloud Run Service Response
```json
{
  "name": "projects/test-project/locations/us-central1/services/my-service",
  "createTime": "2026-02-24T12:00:00.000000Z",
  "updateTime": "2026-02-24T12:00:00.000000Z",
  "uri": "http://my-service.local.calcs",
  "ingress": "INGRESS_TRAFFIC_ALL",
  "template": {
    "containers": [{
      "image": "gcr.io/cloud-builders/gke-deploy:latest",
      "ports": [{"containerPort": 8080}],
      "env": [...]
    }]
  },
  "traffic": [{"percent": 100, "latestRevision": true}]
}
```

---

## OpenAPI Specification

The GCP Stimulator exposes OpenAPI/Swagger documentation:
```
http://localhost:8080/docs
```

View interactive API documentation and test endpoints directly in the browser.

---

## Testing Tools

### Run Test Suite
```bash
cd /home/ubuntu/gcs-stimulator
./run_gcloud_tests.sh
```

### Direct API Tests
```bash
python3 test_api_direct.py
```

### Simple Tests
```bash
bash test_gcloud_simple.sh
```

---

## Troubleshooting

### Backend Connection Issues
```bash
# Check if backend is running
curl http://localhost:8080/

# Check backend logs (if running in terminal)
# Look for "Application startup complete"
```

### Repository Already Exists Error
This is expected on repeated runs. The repository persists between API calls.

### Cloud Run Service Issues
The service deployment requires proper Docker image pulling. The backend attempts to normalize and validate image references.

---

## Next Steps

1. **Create multiple repositories** for different applications
2. **Deploy multiple services** with different configurations
3. **Test traffic splitting** between revisions
4. **Explore environment variables** and configurations
5. **Integrate with your CI/CD pipeline**

---

## Resources

- **GCP Stimulator Repository**: `/home/ubuntu/gcs-stimulator`
- **Test Reports**: `/tmp/gcp-stimulator-test-report.txt`
- **API Documentation**: `http://localhost:8080/docs`
- **Frontend UI**: `http://localhost:3000`

