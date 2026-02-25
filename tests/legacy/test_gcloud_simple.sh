#!/bin/bash

# Simple gcloud CLI Test for Cloud Run & Artifact Registry

PROJECT="test-project"
LOCATION="us-central1"
BACKEND_URL="http://localhost:8080"
REPO_NAME="my-docker-repo"
SERVICE_NAME="hello-world"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}GCP Stimulator - Cloud Run & Artifact Registry${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${BLUE}▶ Artifact Registry Tests${NC}"
echo "Creating repository..."
curl -s -X POST "${BACKEND_URL}/v1/projects/${PROJECT}/locations/${LOCATION}/repositories" \
  -H "Content-Type: application/json" \
  -d "{\"repositoryId\": \"$REPO_NAME\", \"format\": \"DOCKER\", \"description\": \"Docker repo\"}" | jq '.'
echo ""

echo "Listing repositories..."
curl -s "${BACKEND_URL}/v1/projects/${PROJECT}/locations/${LOCATION}/repositories" | jq '.'
echo ""

echo "Getting repository details..."
curl -s "${BACKEND_URL}/v1/projects/${PROJECT}/locations/${LOCATION}/repositories/${REPO_NAME}" | jq '.'
echo ""

echo -e "${BLUE}▶ Cloud Run Tests${NC}"
echo "Deploying service..."
curl -s -X POST "${BACKEND_URL}/v2/projects/${PROJECT}/locations/${LOCATION}/services?serviceId=${SERVICE_NAME}" \
  -H "Content-Type: application/json" \
  -d '{
    "template": {
      "containers": [{
        "image": "gcr.io/cloud-builders/gke-deploy:v1",
        "ports": [{"containerPort": 8080}],
        "env": [
          {"name": "ENV", "value": "prod"}
        ]
      }]
    },
    "ingress": "INGRESS_TRAFFIC_ALL"
  }' | jq '.'
echo ""

echo "Listing services..."
curl -s "${BACKEND_URL}/v2/projects/${PROJECT}/locations/${LOCATION}/services" | jq '.'
echo ""

echo -e "${GREEN}✓ Tests completed!${NC}"
echo ""
