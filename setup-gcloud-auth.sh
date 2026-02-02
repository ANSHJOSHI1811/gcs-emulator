#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  GCP Stimulator - gcloud CLI Authentication Setup"
echo "════════════════════════════════════════════════════════════"
echo ""

# Configure gcloud to work with local simulator
echo "✓ Configuring gcloud for local simulator..."

# Disable credentials (no need for real GCP auth)
gcloud config set auth/disable_credentials true --quiet

# Set API endpoints to local simulator
gcloud config set api_endpoint_overrides/compute http://127.0.0.1:8080/compute/v1/ --quiet
gcloud config set api_endpoint_overrides/storage http://127.0.0.1:8080/storage/v1/ --quiet
gcloud config set api_endpoint_overrides/cloudresourcemanager http://localhost:8080/cloudresourcemanager/ --quiet

# Set default project
gcloud config set project taskmanager-app-001 --quiet

echo "✅ Configuration complete!"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Testing gcloud Commands"
echo "════════════════════════════════════════════════════════════"
echo ""

# Test networks
echo "[TEST 1] List VPC Networks:"
gcloud compute networks list --project=taskmanager-app-001
echo ""

# Test projects
echo "[TEST 2] List Projects:"
gcloud projects list --limit=3
echo ""

# Test storage
echo "[TEST 3] List Storage Buckets:"
gcloud storage buckets list --project=taskmanager-app-001
echo ""

echo "════════════════════════════════════════════════════════════"
echo "✅ Setup Complete! You can now use gcloud commands."
echo ""
echo "Example commands:"
echo "  gcloud projects list"
echo "  gcloud compute networks list"
echo "  gcloud storage buckets list"
echo "════════════════════════════════════════════════════════════"
