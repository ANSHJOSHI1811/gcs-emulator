# GCP Stimulator - gcloud CLI Commands

Complete reference for using gcloud CLI with the GCP Stimulator.

---

## Quick Setup

```bash
# Configure gcloud to point to the simulator
export CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE=http://localhost:8080/compute/v1/
export CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE=http://localhost:8080/storage/v1/
export CLOUDSDK_API_ENDPOINT_OVERRIDES_CLOUDRESOURCEMANAGER=http://localhost:8080/cloudresourcemanager/v1/

# Set your project
gcloud config set project taskmanager-app-001
```

---

## Projects

```bash
# List all projects
gcloud projects list

# Get project details
gcloud projects describe taskmanager-app-001

# Create a new project (if supported)
gcloud projects create my-new-project --name="My New Project"
```

---

## Compute Engine

### Instances (VMs)

```bash
# List all instances
gcloud compute instances list --project=taskmanager-app-001

# List instances in specific zone
gcloud compute instances list --project=taskmanager-app-001 --zones=us-central1-a

# Get instance details
gcloud compute instances describe web-server-1 \
  --zone=us-central1-a \
  --project=taskmanager-app-001

# Create an instance
gcloud compute instances create my-vm \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=debian-11 \
  --image-project=debian-cloud \
  --project=taskmanager-app-001

# Start an instance
gcloud compute instances start web-server-1 \
  --zone=us-central1-a \
  --project=taskmanager-app-001

# Stop an instance
gcloud compute instances stop web-server-1 \
  --zone=us-central1-a \
  --project=taskmanager-app-001

# Delete an instance
gcloud compute instances delete my-vm \
  --zone=us-central1-a \
  --project=taskmanager-app-001 \
  --quiet
```

### Machine Types

```bash
# List machine types
gcloud compute machine-types list --zones=us-central1-a

# Get machine type details
gcloud compute machine-types describe e2-medium --zone=us-central1-a
```

### Zones and Regions

```bash
# List all zones
gcloud compute zones list

# List all regions
gcloud compute regions list

# Describe a region
gcloud compute regions describe us-central1
```

---

## VPC Networks

### Networks

```bash
# List networks
gcloud compute networks list --project=taskmanager-app-001

# Create a network
gcloud compute networks create my-vpc \
  --subnet-mode=custom \
  --project=taskmanager-app-001

# Describe network
gcloud compute networks describe taskmanager-vpc \
  --project=taskmanager-app-001

# Delete network
gcloud compute networks delete my-vpc \
  --project=taskmanager-app-001 \
  --quiet
```

### Subnets

```bash
# List subnets
gcloud compute networks subnets list --project=taskmanager-app-001

# List subnets for specific network
gcloud compute networks subnets list \
  --network=taskmanager-vpc \
  --project=taskmanager-app-001

# Create subnet
gcloud compute networks subnets create my-subnet \
  --network=taskmanager-vpc \
  --range=10.0.1.0/24 \
  --region=us-central1 \
  --project=taskmanager-app-001

# Describe subnet
gcloud compute networks subnets describe backend-subnet \
  --region=us-central1 \
  --project=taskmanager-app-001

# Delete subnet
gcloud compute networks subnets delete my-subnet \
  --region=us-central1 \
  --project=taskmanager-app-001 \
  --quiet
```

### Firewall Rules

```bash
# List firewall rules
gcloud compute firewall-rules list --project=taskmanager-app-001

# Create firewall rule (allow SSH)
gcloud compute firewall-rules create allow-ssh \
  --network=taskmanager-vpc \
  --allow=tcp:22 \
  --source-ranges=0.0.0.0/0 \
  --project=taskmanager-app-001

# Create firewall rule (allow HTTP/HTTPS)
gcloud compute firewall-rules create allow-web \
  --network=taskmanager-vpc \
  --allow=tcp:80,tcp:443 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=web-server \
  --project=taskmanager-app-001

# Describe firewall rule
gcloud compute firewall-rules describe allow-ssh \
  --project=taskmanager-app-001

# Update firewall rule
gcloud compute firewall-rules update allow-ssh \
  --description="Allow SSH from anywhere" \
  --project=taskmanager-app-001

# Delete firewall rule
gcloud compute firewall-rules delete allow-web \
  --project=taskmanager-app-001 \
  --quiet
```

### Routes

```bash
# List routes
gcloud compute routes list --project=taskmanager-app-001

# Create route
gcloud compute routes create my-route \
  --network=taskmanager-vpc \
  --destination-range=10.0.2.0/24 \
  --next-hop-gateway=default-internet-gateway \
  --project=taskmanager-app-001

# Describe route
gcloud compute routes describe my-route \
  --project=taskmanager-app-001

# Delete route
gcloud compute routes delete my-route \
  --project=taskmanager-app-001 \
  --quiet
```

---

## Cloud Storage

### Buckets

```bash
# List buckets
gcloud storage buckets list --project=taskmanager-app-001

# Create bucket
gcloud storage buckets create gs://my-test-bucket \
  --project=taskmanager-app-001 \
  --location=US \
  --default-storage-class=STANDARD

# Get bucket details
gcloud storage buckets describe gs://taskmanager-data-bucket

# Update bucket (enable versioning)
gcloud storage buckets update gs://taskmanager-data-bucket \
  --versioning

# Delete bucket
gcloud storage buckets delete gs://my-test-bucket --project=taskmanager-app-001
```

### Objects

```bash
# List objects in bucket
gcloud storage ls gs://taskmanager-data-bucket/

# Upload file
echo "Hello World" > test.txt
gcloud storage cp test.txt gs://taskmanager-data-bucket/

# Upload with metadata
gcloud storage cp test.txt gs://taskmanager-data-bucket/data/ \
  --content-type=text/plain

# Download file
gcloud storage cp gs://taskmanager-data-bucket/test.txt ./downloaded.txt

# Copy object within bucket
gcloud storage cp gs://taskmanager-data-bucket/test.txt \
  gs://taskmanager-data-bucket/backup/test.txt

# Delete object
gcloud storage rm gs://taskmanager-data-bucket/test.txt

# Delete multiple objects
gcloud storage rm gs://taskmanager-data-bucket/data/**
```

---

## IAM

### Service Accounts

```bash
# List service accounts
gcloud iam service-accounts list --project=taskmanager-app-001

# Create service account
gcloud iam service-accounts create my-service-account \
  --display-name="My Service Account" \
  --project=taskmanager-app-001

# Describe service account
gcloud iam service-accounts describe my-service-account@taskmanager-app-001.iam.gserviceaccount.com \
  --project=taskmanager-app-001

# Delete service account
gcloud iam service-accounts delete my-service-account@taskmanager-app-001.iam.gserviceaccount.com \
  --project=taskmanager-app-001 \
  --quiet
```

### IAM Policies

```bash
# Get IAM policy for project
gcloud projects get-iam-policy taskmanager-app-001

# Add IAM policy binding
gcloud projects add-iam-policy-binding taskmanager-app-001 \
  --member="serviceAccount:my-service-account@taskmanager-app-001.iam.gserviceaccount.com" \
  --role="roles/compute.viewer"

# Remove IAM policy binding
gcloud projects remove-iam-policy-binding taskmanager-app-001 \
  --member="serviceAccount:my-service-account@taskmanager-app-001.iam.gserviceaccount.com" \
  --role="roles/compute.viewer"
```

---

## Common Options

```bash
# Format output as JSON
gcloud compute instances list --format=json

# Format output as YAML
gcloud compute instances list --format=yaml

# Format output as table
gcloud compute instances list --format="table(name,zone,status)"

# Filter results
gcloud compute instances list --filter="status=RUNNING"

# Limit results
gcloud compute instances list --limit=5

# Sort results
gcloud compute instances list --sort-by=name

# Show URI only
gcloud compute instances list --uri

# Quiet mode (no prompts)
gcloud compute instances delete my-vm --zone=us-central1-a --quiet
```

---

## Multi-Project Workflow

```bash
# List all projects
gcloud projects list

# Switch to taskmanager project
gcloud config set project taskmanager-app-001

# View taskmanager resources
gcloud compute instances list
gcloud storage buckets list
gcloud compute networks list

# Switch to ecommerce project
gcloud config set project ecommerce-platform-002

# View ecommerce resources
gcloud compute instances list
gcloud storage buckets list
gcloud compute networks list

# Verify project isolation
gcloud config get-value project
```

---

## Troubleshooting

```bash
# Check current configuration
gcloud config list

# Check project setting
gcloud config get-value project

# Verify API endpoints
env | grep CLOUDSDK_API_ENDPOINT

# Test connectivity
curl http://localhost:8080/compute/v1/projects/taskmanager-app-001/zones/us-central1-a/instances

# Enable verbose output
gcloud compute instances list --verbosity=debug

# Check gcloud version
gcloud version
```

---

## Testing Commands

```bash
# Complete workflow test
export PROJECT_ID="taskmanager-app-001"

# 1. List resources
echo "=== Projects ==="
gcloud projects list

echo "=== Instances ==="
gcloud compute instances list --project=$PROJECT_ID

echo "=== Buckets ==="
gcloud storage buckets list --project=$PROJECT_ID

echo "=== Networks ==="
gcloud compute networks list --project=$PROJECT_ID

echo "=== Subnets ==="
gcloud compute networks subnets list --project=$PROJECT_ID

echo "=== Firewall Rules ==="
gcloud compute firewall-rules list --project=$PROJECT_ID

# 2. Create test resources
echo "=== Creating Test Bucket ==="
gcloud storage buckets create gs://test-bucket-$RANDOM --project=$PROJECT_ID

echo "=== Uploading Test File ==="
echo "test data" > test.txt
gcloud storage cp test.txt gs://test-bucket-$RANDOM/

# 3. Verify
gcloud storage ls gs://test-bucket-$RANDOM/
```

---

## Notes

- All gcloud commands work with the simulator when environment variables are set
- The simulator supports standard gcloud output formats (json, yaml, table)
- Some advanced gcloud features may not be fully implemented
- Use `--project` flag or `gcloud config set project` to specify project
- Docker containers backing VM instances can be viewed with `docker ps`
- VPC networks map to Docker networks with `gcp-vpc-` prefix

---

## Additional Resources

- Full API examples: `examples/` directory
- Python SDK examples: `examples/python-sdk.md`
- REST API examples: `examples/rest-api.md`
- Main documentation: `README.md`
