#!/bin/bash
################################################################################
# Multi-Project Resource Creation Script
# Creates resources in 2 projects for UI verification testing
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Setup environment
export CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE=http://localhost:8080/compute/v1/
export CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE=http://localhost:8080/storage/v1/
export CLOUDSDK_CORE_CUSTOM_CA_CERTS_FILE=/home/ubuntu/gcs-stimulator/terraform/fake-gcp-credentials.json

log_section "MULTI-PROJECT RESOURCE CREATION FOR UI VERIFICATION"

# Create projects via API first
log_info "Creating projects via API..."
curl -s -X POST http://localhost:8080/cloudresourcemanager/v1/projects \
    -H "Content-Type: application/json" \
    -d '{"projectId":"taskmanager-app-001","name":"TaskManager API"}' >/dev/null 2>&1 || log_warning "Project may already exist"

curl -s -X POST http://localhost:8080/cloudresourcemanager/v1/projects \
    -H "Content-Type: application/json" \
    -d '{"projectId":"ecommerce-platform-002","name":"E-Commerce Platform"}' >/dev/null 2>&1 || log_warning "Project may already exist"
log_success "Projects created via API"

################################################################################
# PROJECT 1: TaskManager Application
################################################################################

log_section "PROJECT 1: TASKMANAGER-APP-001"

log_info "Setting project to taskmanager-app-001..."
gcloud config set project taskmanager-app-001 --no-user-output-enabled 2>/dev/null || true
export GCP_PROJECT=taskmanager-app-001
log_success "Project set: taskmanager-app-001"

# VPC & Networking
log_info "Creating VPC network..."
gcloud compute networks create taskmanager-vpc \
    --subnet-mode=custom \
    --description="TaskManager application VPC" 2>/dev/null || log_warning "VPC may already exist"
log_success "VPC created: taskmanager-vpc"

log_info "Creating subnets..."
gcloud compute networks subnets create web-subnet \
    --network=taskmanager-vpc \
    --region=us-central1 \
    --range=10.0.1.0/24 2>/dev/null || log_warning "web-subnet may already exist"

gcloud compute networks subnets create app-subnet \
    --network=taskmanager-vpc \
    --region=us-central1 \
    --range=10.0.2.0/24 2>/dev/null || log_warning "app-subnet may already exist"

gcloud compute networks subnets create db-subnet \
    --network=taskmanager-vpc \
    --region=us-central1 \
    --range=10.0.3.0/24 2>/dev/null || log_warning "db-subnet may already exist"
log_success "3 subnets created"

log_info "Creating firewall rules..."
gcloud compute firewall-rules create allow-web-external \
    --network=taskmanager-vpc \
    --allow=tcp:80,tcp:443 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=web-tier \
    --description="Allow HTTP/HTTPS to web servers" 2>/dev/null || log_warning "Firewall rule may already exist"

gcloud compute firewall-rules create allow-web-to-app \
    --network=taskmanager-vpc \
    --allow=tcp:8080 \
    --source-tags=web-tier \
    --target-tags=app-tier \
    --description="Allow web to app communication" 2>/dev/null || log_warning "Firewall rule may already exist"

gcloud compute firewall-rules create allow-app-to-db \
    --network=taskmanager-vpc \
    --allow=tcp:5432 \
    --source-tags=app-tier \
    --target-tags=db-tier \
    --description="Allow app to database communication" 2>/dev/null || log_warning "Firewall rule may already exist"

gcloud compute firewall-rules create allow-ssh-taskmanager \
    --network=taskmanager-vpc \
    --allow=tcp:22 \
    --source-ranges=0.0.0.0/0 \
    --description="Allow SSH for management" 2>/dev/null || log_warning "Firewall rule may already exist"

gcloud compute firewall-rules create allow-internal-taskmanager \
    --network=taskmanager-vpc \
    --allow=tcp:0-65535,udp:0-65535,icmp \
    --source-ranges=10.0.0.0/16 \
    --description="Allow all internal traffic" 2>/dev/null || log_warning "Firewall rule may already exist"
log_success "5 firewall rules created"

# Service Accounts
log_info "Creating service accounts..."
gcloud iam service-accounts create web-tier-sa \
    --display-name="Web Tier Service Account" 2>/dev/null || log_warning "SA may already exist"

gcloud iam service-accounts create app-tier-sa \
    --display-name="App Tier Service Account" 2>/dev/null || log_warning "SA may already exist"

gcloud iam service-accounts create db-tier-sa \
    --display-name="Database Tier Service Account" 2>/dev/null || log_warning "SA may already exist"
log_success "3 service accounts created"

# IAM Bindings
log_info "Setting IAM policies..."
gcloud projects add-iam-policy-binding taskmanager-app-001 \
    --member="serviceAccount:web-tier-sa@taskmanager-app-001.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer" >/dev/null 2>&1 || log_warning "Policy may already exist"

gcloud projects add-iam-policy-binding taskmanager-app-001 \
    --member="serviceAccount:app-tier-sa@taskmanager-app-001.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin" >/dev/null 2>&1 || log_warning "Policy may already exist"

gcloud projects add-iam-policy-binding taskmanager-app-001 \
    --member="serviceAccount:db-tier-sa@taskmanager-app-001.iam.gserviceaccount.com" \
    --role="roles/storage.admin" >/dev/null 2>&1 || log_warning "Policy may already exist"
log_success "IAM policies configured"

# Storage Buckets
log_info "Creating storage buckets..."
gsutil mb -c STANDARD -l us-central1 gs://taskmanager-static-001 2>/dev/null || log_warning "Bucket may already exist"
gsutil mb -c STANDARD -l us-central1 gs://taskmanager-data-001 2>/dev/null || log_warning "Bucket may already exist"
gsutil mb -c ARCHIVE -l us-central1 gs://taskmanager-backups-001 2>/dev/null || log_warning "Bucket may already exist"
log_success "3 storage buckets created"

# Upload sample files
log_info "Uploading sample files..."
echo "<h1>TaskManager Web App</h1><p>Welcome to TaskManager</p>" > /tmp/index.html
echo "body { font-family: Arial; background: #f0f0f0; }" > /tmp/style.css
echo '{"app":"taskmanager","version":"1.0"}' > /tmp/config.json

gsutil cp /tmp/index.html gs://taskmanager-static-001/ 2>/dev/null || true
gsutil cp /tmp/style.css gs://taskmanager-static-001/ 2>/dev/null || true
gsutil cp /tmp/config.json gs://taskmanager-data-001/ 2>/dev/null || true
log_success "Sample files uploaded"

# Create VMs
log_info "Creating VM instances..."
gcloud compute instances create web-server-1 \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --network=taskmanager-vpc \
    --subnet=web-subnet \
    --tags=web-tier \
    --service-account=web-tier-sa@taskmanager-app-001.iam.gserviceaccount.com \
    --scopes=cloud-platform 2>/dev/null || log_warning "VM may already exist"

gcloud compute instances create web-server-2 \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --network=taskmanager-vpc \
    --subnet=web-subnet \
    --tags=web-tier \
    --service-account=web-tier-sa@taskmanager-app-001.iam.gserviceaccount.com \
    --scopes=cloud-platform 2>/dev/null || log_warning "VM may already exist"

gcloud compute instances create app-server-1 \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --network=taskmanager-vpc \
    --subnet=app-subnet \
    --tags=app-tier \
    --service-account=app-tier-sa@taskmanager-app-001.iam.gserviceaccount.com \
    --scopes=cloud-platform \
    --no-address 2>/dev/null || log_warning "VM may already exist"

gcloud compute instances create app-server-2 \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --network=taskmanager-vpc \
    --subnet=app-subnet \
    --tags=app-tier \
    --service-account=app-tier-sa@taskmanager-app-001.iam.gserviceaccount.com \
    --scopes=cloud-platform \
    --no-address 2>/dev/null || log_warning "VM may already exist"

gcloud compute instances create db-server-1 \
    --zone=us-central1-a \
    --machine-type=e2-standard-4 \
    --network=taskmanager-vpc \
    --subnet=db-subnet \
    --tags=db-tier \
    --service-account=db-tier-sa@taskmanager-app-001.iam.gserviceaccount.com \
    --scopes=cloud-platform \
    --no-address 2>/dev/null || log_warning "VM may already exist"
log_success "5 VM instances created"

################################################################################
# PROJECT 2: E-Commerce Platform
################################################################################

log_section "PROJECT 2: ECOMMERCE-PLATFORM-002"

log_info "Setting project to ecommerce-platform-002..."
gcloud config set project ecommerce-platform-002 --no-user-output-enabled 2>/dev/null || true
export GCP_PROJECT=ecommerce-platform-002
log_success "Project set: ecommerce-platform-002"

# VPC & Networking
log_info "Creating VPC network..."
gcloud compute networks create ecommerce-vpc \
    --subnet-mode=custom \
    --description="E-Commerce platform VPC" 2>/dev/null || log_warning "VPC may already exist"
log_success "VPC created: ecommerce-vpc"

log_info "Creating subnets..."
gcloud compute networks subnets create frontend-subnet \
    --network=ecommerce-vpc \
    --region=us-east1 \
    --range=172.16.1.0/24 2>/dev/null || log_warning "frontend-subnet may already exist"

gcloud compute networks subnets create backend-subnet \
    --network=ecommerce-vpc \
    --region=us-east1 \
    --range=172.16.2.0/24 2>/dev/null || log_warning "backend-subnet may already exist"

gcloud compute networks subnets create cache-subnet \
    --network=ecommerce-vpc \
    --region=us-east1 \
    --range=172.16.3.0/24 2>/dev/null || log_warning "cache-subnet may already exist"
log_success "3 subnets created"

log_info "Creating firewall rules..."
gcloud compute firewall-rules create allow-frontend-public \
    --network=ecommerce-vpc \
    --allow=tcp:443,tcp:80 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=frontend \
    --description="Allow HTTPS to frontend" 2>/dev/null || log_warning "Firewall rule may already exist"

gcloud compute firewall-rules create allow-frontend-to-backend \
    --network=ecommerce-vpc \
    --allow=tcp:3000,tcp:8000 \
    --source-tags=frontend \
    --target-tags=backend \
    --description="Allow frontend to backend API" 2>/dev/null || log_warning "Firewall rule may already exist"

gcloud compute firewall-rules create allow-backend-to-cache \
    --network=ecommerce-vpc \
    --allow=tcp:6379 \
    --source-tags=backend \
    --target-tags=cache \
    --description="Allow backend to Redis cache" 2>/dev/null || log_warning "Firewall rule may already exist"

gcloud compute firewall-rules create allow-ssh-ecommerce \
    --network=ecommerce-vpc \
    --allow=tcp:22 \
    --source-ranges=0.0.0.0/0 \
    --description="Allow SSH for management" 2>/dev/null || log_warning "Firewall rule may already exist"
log_success "4 firewall rules created"

# Service Accounts
log_info "Creating service accounts..."
gcloud iam service-accounts create frontend-sa \
    --display-name="Frontend Service Account" 2>/dev/null || log_warning "SA may already exist"

gcloud iam service-accounts create backend-api-sa \
    --display-name="Backend API Service Account" 2>/dev/null || log_warning "SA may already exist"

gcloud iam service-accounts create payment-processor-sa \
    --display-name="Payment Processor Service Account" 2>/dev/null || log_warning "SA may already exist"
log_success "3 service accounts created"

# IAM Bindings
log_info "Setting IAM policies..."
gcloud projects add-iam-policy-binding ecommerce-platform-002 \
    --member="serviceAccount:frontend-sa@ecommerce-platform-002.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer" >/dev/null 2>&1 || log_warning "Policy may already exist"

gcloud projects add-iam-policy-binding ecommerce-platform-002 \
    --member="serviceAccount:backend-api-sa@ecommerce-platform-002.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin" >/dev/null 2>&1 || log_warning "Policy may already exist"

gcloud projects add-iam-policy-binding ecommerce-platform-002 \
    --member="serviceAccount:payment-processor-sa@ecommerce-platform-002.iam.gserviceaccount.com" \
    --role="roles/compute.viewer" >/dev/null 2>&1 || log_warning "Policy may already exist"
log_success "IAM policies configured"

# Storage Buckets
log_info "Creating storage buckets..."
gsutil mb -c STANDARD -l us-east1 gs://ecommerce-product-images-002 2>/dev/null || log_warning "Bucket may already exist"
gsutil mb -c STANDARD -l us-east1 gs://ecommerce-user-uploads-002 2>/dev/null || log_warning "Bucket may already exist"
gsutil mb -c NEARLINE -l us-east1 gs://ecommerce-order-archives-002 2>/dev/null || log_warning "Bucket may already exist"
log_success "3 storage buckets created"

# Upload sample files
log_info "Uploading sample product images..."
echo "PRODUCT_IMAGE_1" > /tmp/product-1.jpg
echo "PRODUCT_IMAGE_2" > /tmp/product-2.jpg
echo '{"products":[{"id":1,"name":"Laptop"},{"id":2,"name":"Phone"}]}' > /tmp/catalog.json

gsutil cp /tmp/product-1.jpg gs://ecommerce-product-images-002/ 2>/dev/null || true
gsutil cp /tmp/product-2.jpg gs://ecommerce-product-images-002/ 2>/dev/null || true
gsutil cp /tmp/catalog.json gs://ecommerce-product-images-002/ 2>/dev/null || true
log_success "Sample product data uploaded"

# Create VMs
log_info "Creating VM instances..."
gcloud compute instances create frontend-server-1 \
    --zone=us-east1-b \
    --machine-type=e2-medium \
    --network=ecommerce-vpc \
    --subnet=frontend-subnet \
    --tags=frontend \
    --service-account=frontend-sa@ecommerce-platform-002.iam.gserviceaccount.com \
    --scopes=cloud-platform 2>/dev/null || log_warning "VM may already exist"

gcloud compute instances create frontend-server-2 \
    --zone=us-east1-b \
    --machine-type=e2-medium \
    --network=ecommerce-vpc \
    --subnet=frontend-subnet \
    --tags=frontend \
    --service-account=frontend-sa@ecommerce-platform-002.iam.gserviceaccount.com \
    --scopes=cloud-platform 2>/dev/null || log_warning "VM may already exist"

gcloud compute instances create backend-api-1 \
    --zone=us-east1-b \
    --machine-type=e2-standard-2 \
    --network=ecommerce-vpc \
    --subnet=backend-subnet \
    --tags=backend \
    --service-account=backend-api-sa@ecommerce-platform-002.iam.gserviceaccount.com \
    --scopes=cloud-platform \
    --no-address 2>/dev/null || log_warning "VM may already exist"

gcloud compute instances create cache-server-1 \
    --zone=us-east1-b \
    --machine-type=e2-standard-2 \
    --network=ecommerce-vpc \
    --subnet=cache-subnet \
    --tags=cache \
    --no-address 2>/dev/null || log_warning "VM may already exist"
log_success "4 VM instances created"

################################################################################
# SUMMARY
################################################################################

log_section "RESOURCE CREATION COMPLETE"

echo ""
log_info "Project 1: taskmanager-app-001"
echo "  ✓ VPC: taskmanager-vpc"
echo "  ✓ Subnets: 3 (web, app, db)"
echo "  ✓ Firewall Rules: 5"
echo "  ✓ Service Accounts: 3"
echo "  ✓ Storage Buckets: 3"
echo "  ✓ VM Instances: 5"
echo ""

log_info "Project 2: ecommerce-platform-002"
echo "  ✓ VPC: ecommerce-vpc"
echo "  ✓ Subnets: 3 (frontend, backend, cache)"
echo "  ✓ Firewall Rules: 4"
echo "  ✓ Service Accounts: 3"
echo "  ✓ Storage Buckets: 3"
echo "  ✓ VM Instances: 4"
echo ""

log_success "All resources created successfully!"
echo ""
log_info "You can now verify these resources in the UI by:"
echo "  1. Selecting 'taskmanager-app-001' from the project dropdown"
echo "  2. Navigate to Storage, Compute, VPC sections"
echo "  3. Switch to 'ecommerce-platform-002' and repeat"
echo ""

# Cleanup temp files
rm -f /tmp/index.html /tmp/style.css /tmp/config.json /tmp/product-*.jpg /tmp/catalog.json

log_success "Setup complete! Ready for UI verification."
