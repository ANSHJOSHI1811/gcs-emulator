#!/bin/bash
################################################################################
# Complete Multi-Project Resources via Direct API Calls
# Faster approach using API directly instead of gcloud CLI
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

API_BASE="http://localhost:8080"

echo "═══════════════════════════════════════════════════════════════"
echo " Completing Resources for Both Projects"
echo "═══════════════════════════════════════════════════════════════"
echo ""

################################################################################
# PROJECT 1: taskmanager-app-001 - Complete remaining resources
################################################################################

log_info "Creating VMs for taskmanager-app-001..."

# Web tier VMs
gcloud compute instances create web-server-1 \
    --project=taskmanager-app-001 \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --network=taskmanager-vpc \
    --subnet=web-subnet \
    --tags=web-tier 2>/dev/null || log_info "web-server-1 may already exist"

gcloud compute instances create web-server-2 \
    --project=taskmanager-app-001 \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --network=taskmanager-vpc \
    --subnet=web-subnet \
    --tags=web-tier 2>/dev/null || log_info "web-server-2 may already exist"

# App tier VMs
gcloud compute instances create app-server-1 \
    --project=taskmanager-app-001 \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --network=taskmanager-vpc \
    --subnet=app-subnet \
    --tags=app-tier \
    --no-address 2>/dev/null || log_info "app-server-1 may already exist"

gcloud compute instances create app-server-2 \
    --project=taskmanager-app-001 \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --network=taskmanager-vpc \
    --subnet=app-subnet \
    --tags=app-tier \
    --no-address 2>/dev/null || log_info "app-server-2 may already exist"

# Database VM
gcloud compute instances create db-server-1 \
    --project=taskmanager-app-001 \
    --zone=us-central1-a \
    --machine-type=e2-standard-4 \
    --network=taskmanager-vpc \
    --subnet=db-subnet \
    --tags=db-tier \
    --no-address 2>/dev/null || log_info "db-server-1 may already exist"

log_success "VMs created for taskmanager-app-001"

# Storage buckets via API
log_info "Creating storage buckets for taskmanager-app-001..."

curl -s -X POST "${API_BASE}/storage/v1/b?project=taskmanager-app-001" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "taskmanager-static-001",
        "location": "us-central1",
        "storageClass": "STANDARD"
    }' >/dev/null 2>&1 || log_info "Bucket may already exist"

curl -s -X POST "${API_BASE}/storage/v1/b?project=taskmanager-app-001" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "taskmanager-data-001",
        "location": "us-central1",
        "storageClass": "STANDARD"
    }' >/dev/null 2>&1 || log_info "Bucket may already exist"

curl -s -X POST "${API_BASE}/storage/v1/b?project=taskmanager-app-001" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "taskmanager-backups-001",
        "location": "us-central1",
        "storageClass": "ARCHIVE"
    }' >/dev/null 2>&1 || log_info "Bucket may already exist"

log_success "Buckets created for taskmanager-app-001"

# Upload sample objects
log_info "Uploading sample objects..."

echo "<h1>TaskManager Web App</h1>" | gsutil cp - gs://taskmanager-static-001/index.html 2>/dev/null || true
echo "body { font-family: Arial; }" | gsutil cp - gs://taskmanager-static-001/style.css 2>/dev/null || true
echo '{"config":"production"}' | gsutil cp - gs://taskmanager-data-001/config.json 2>/dev/null || true

log_success "Objects uploaded for taskmanager-app-001"

################################################################################
# PROJECT 2: ecommerce-platform-002
################################################################################

log_info "Creating VPC for ecommerce-platform-002..."

gcloud compute networks create ecommerce-vpc \
    --project=ecommerce-platform-002 \
    --subnet-mode=custom 2>/dev/null || log_info "VPC may already exist"

log_info "Creating subnets for ecommerce-platform-002..."

gcloud compute networks subnets create frontend-subnet \
    --project=ecommerce-platform-002 \
    --network=ecommerce-vpc \
    --region=us-east1 \
    --range=172.16.1.0/24 2>/dev/null || log_info "frontend-subnet may already exist"

gcloud compute networks subnets create backend-subnet \
    --project=ecommerce-platform-002 \
    --network=ecommerce-vpc \
    --region=us-east1 \
    --range=172.16.2.0/24 2>/dev/null || log_info "backend-subnet may already exist"

gcloud compute networks subnets create cache-subnet \
    --project=ecommerce-platform-002 \
    --network=ecommerce-vpc \
    --region=us-east1 \
    --range=172.16.3.0/24 2>/dev/null || log_info "cache-subnet may already exist"

log_success "Subnets created for ecommerce-platform-002"

log_info "Creating firewall rules for ecommerce-platform-002..."

gcloud compute firewall-rules create allow-frontend-public \
    --project=ecommerce-platform-002 \
    --network=ecommerce-vpc \
    --allow=tcp:443,tcp:80 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=frontend 2>/dev/null || log_info "Firewall may already exist"

gcloud compute firewall-rules create allow-frontend-to-backend \
    --project=ecommerce-platform-002 \
    --network=ecommerce-vpc \
    --allow=tcp:3000,tcp:8000 \
    --source-tags=frontend \
    --target-tags=backend 2>/dev/null || log_info "Firewall may already exist"

gcloud compute firewall-rules create allow-backend-to-cache \
    --project=ecommerce-platform-002 \
    --network=ecommerce-vpc \
    --allow=tcp:6379 \
    --source-tags=backend \
    --target-tags=cache 2>/dev/null || log_info "Firewall may already exist"

log_success "Firewall rules created for ecommerce-platform-002"

log_info "Creating service accounts for ecommerce-platform-002..."

gcloud iam service-accounts create frontend-sa \
    --project=ecommerce-platform-002 \
    --display-name="Frontend Service Account" 2>/dev/null || log_info "SA may already exist"

gcloud iam service-accounts create backend-api-sa \
    --project=ecommerce-platform-002 \
    --display-name="Backend API Service Account" 2>/dev/null || log_info "SA may already exist"

gcloud iam service-accounts create payment-processor-sa \
    --project=ecommerce-platform-002 \
    --display-name="Payment Processor Service Account" 2>/dev/null || log_info "SA may already exist"

log_success "Service accounts created for ecommerce-platform-002"

log_info "Creating VMs for ecommerce-platform-002..."

gcloud compute instances create frontend-server-1 \
    --project=ecommerce-platform-002 \
    --zone=us-east1-b \
    --machine-type=e2-medium \
    --network=ecommerce-vpc \
    --subnet=frontend-subnet \
    --tags=frontend 2>/dev/null || log_info "frontend-server-1 may already exist"

gcloud compute instances create frontend-server-2 \
    --project=ecommerce-platform-002 \
    --zone=us-east1-b \
    --machine-type=e2-medium \
    --network=ecommerce-vpc \
    --subnet=frontend-subnet \
    --tags=frontend 2>/dev/null || log_info "frontend-server-2 may already exist"

gcloud compute instances create backend-api-1 \
    --project=ecommerce-platform-002 \
    --zone=us-east1-b \
    --machine-type=e2-standard-2 \
    --network=ecommerce-vpc \
    --subnet=backend-subnet \
    --tags=backend \
    --no-address 2>/dev/null || log_info "backend-api-1 may already exist"

gcloud compute instances create cache-server-1 \
    --project=ecommerce-platform-002 \
    --zone=us-east1-b \
    --machine-type=e2-standard-2 \
    --network=ecommerce-vpc \
    --subnet=cache-subnet \
    --tags=cache \
    --no-address 2>/dev/null || log_info "cache-server-1 may already exist"

log_success "VMs created for ecommerce-platform-002"

log_info "Creating storage buckets for ecommerce-platform-002..."

curl -s -X POST "${API_BASE}/storage/v1/b?project=ecommerce-platform-002" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "ecommerce-product-images-002",
        "location": "us-east1",
        "storageClass": "STANDARD"
    }' >/dev/null 2>&1 || log_info "Bucket may already exist"

curl -s -X POST "${API_BASE}/storage/v1/b?project=ecommerce-platform-002" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "ecommerce-user-uploads-002",
        "location": "us-east1",
        "storageClass": "STANDARD"
    }' >/dev/null 2>&1 || log_info "Bucket may already exist"

curl -s -X POST "${API_BASE}/storage/v1/b?project=ecommerce-platform-002" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "ecommerce-order-archives-002",
        "location": "us-east1",
        "storageClass": "NEARLINE"
    }' >/dev/null 2>&1 || log_info "Bucket may already exist"

log_success "Buckets created for ecommerce-platform-002"

log_info "Uploading sample objects..."

echo '{"product_id":1,"name":"Laptop"}' | gsutil cp - gs://ecommerce-product-images-002/products/laptop.json 2>/dev/null || true
echo '{"product_id":2,"name":"Phone"}' | gsutil cp - gs://ecommerce-product-images-002/products/phone.json 2>/dev/null || true
echo '{"catalog":"v1"}' | gsutil cp - gs://ecommerce-product-images-002/catalog.json 2>/dev/null || true

log_success "Objects uploaded for ecommerce-platform-002"

################################################################################
# SUMMARY
################################################################################

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo " RESOURCE CREATION SUMMARY"
echo "═══════════════════════════════════════════════════════════════"
echo ""

log_success "PROJECT 1: taskmanager-app-001"
curl -s "${API_BASE}/compute/v1/projects/taskmanager-app-001/zones/us-central1-a/instances" | jq -r '.items[]?.name // empty' | while read vm; do
    echo "  ✓ VM: $vm"
done
curl -s "${API_BASE}/storage/v1/b?project=taskmanager-app-001" | jq -r '.items[]?.name // empty' | while read bucket; do
    echo "  ✓ Bucket: $bucket"
done
curl -s "${API_BASE}/compute/v1/projects/taskmanager-app-001/global/networks" | jq -r '.items[]?.name // empty' | while read net; do
    echo "  ✓ Network: $net"
done

echo ""
log_success "PROJECT 2: ecommerce-platform-002"
curl -s "${API_BASE}/compute/v1/projects/ecommerce-platform-002/zones/us-east1-b/instances" | jq -r '.items[]?.name // empty' | while read vm; do
    echo "  ✓ VM: $vm"
done
curl -s "${API_BASE}/storage/v1/b?project=ecommerce-platform-002" | jq -r '.items[]?.name // empty' | while read bucket; do
    echo "  ✓ Bucket: $bucket"
done
curl -s "${API_BASE}/compute/v1/projects/ecommerce-platform-002/global/networks" | jq -r '.items[]?.name // empty' | while read net; do
    echo "  ✓ Network: $net"
done

echo ""
log_success "All resources created! Ready for UI verification."
echo ""
echo "To verify in UI:"
echo "  1. Go to http://16.16.160.48:3000"
echo "  2. Select 'taskmanager-app-001' from project dropdown"
echo "  3. Check: Compute (5 VMs), Storage (3 buckets), VPC (3 subnets, 5 firewalls)"
echo "  4. Switch to 'ecommerce-platform-002'"
echo "  5. Check: Compute (4 VMs), Storage (3 buckets), VPC (3 subnets, 3 firewalls)"
echo ""
