# gcloud CLI Examples

**Using official gcloud command-line tool**

These commands work with both real GCP and the GCP Stimulator.

---

## Setup

```bash
# Point gcloud to local stimulator (optional for testing)
export CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE=http://localhost:8080/compute/v1/
export CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE=http://localhost:8080/storage/v1/

# Set default project
gcloud config set project my-project
```

---

## Cloud Storage

### Buckets

```bash
# Create bucket
gcloud storage buckets create gs://my-bucket \
  --project=my-project \
  --location=US \
  --default-storage-class=STANDARD

# List buckets
gcloud storage buckets list --project=my-project

# Get bucket details
gcloud storage buckets describe gs://my-bucket

# Update bucket (enable versioning)
gcloud storage buckets update gs://my-bucket --versioning

# Delete bucket
gcloud storage buckets delete gs://my-bucket
```

### Objects

```bash
# Upload file
gcloud storage cp file.txt gs://my-bucket/

# Upload directory
gcloud storage cp -r ./my-folder gs://my-bucket/

# Upload with metadata
gcloud storage cp file.txt gs://my-bucket/ \
  --content-type=text/plain \
  --cache-control=no-cache

# List objects
gcloud storage ls gs://my-bucket

# List with details
gcloud storage ls -l gs://my-bucket

# Download file
gcloud storage cp gs://my-bucket/file.txt ./downloaded.txt

# Download directory
gcloud storage cp -r gs://my-bucket/folder ./local-folder

# Delete object
gcloud storage rm gs://my-bucket/file.txt

# Delete directory
gcloud storage rm -r gs://my-bucket/folder

# Copy object
gcloud storage cp gs://my-bucket/file.txt gs://dest-bucket/copied-file.txt

# Move object
gcloud storage mv gs://my-bucket/file.txt gs://my-bucket/renamed.txt
```

### Object Versioning

```bash
# Enable versioning
gcloud storage buckets update gs://my-bucket --versioning

# List object versions
gcloud storage ls -a gs://my-bucket/file.txt

# Restore specific version
gcloud storage cp gs://my-bucket/file.txt#1234567890 gs://my-bucket/file.txt
```

---

## Compute Engine

### Zones & Machine Types

```bash
# List zones
gcloud compute zones list

# List machine types in a zone
gcloud compute machine-types list --zones=us-central1-a

# Get machine type details
gcloud compute machine-types describe e2-medium --zone=us-central1-a
```

### VM Instances

```bash
# Create VM instance
gcloud compute instances create my-vm \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=debian-11 \
  --image-project=debian-cloud

# Create VM with custom settings
gcloud compute instances create web-server \
  --zone=us-central1-a \
  --machine-type=e2-standard-2 \
  --subnet=my-subnet \
  --network-tier=PREMIUM \
  --tags=http-server,https-server \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --boot-disk-type=pd-standard

# Create VM with service account
gcloud compute instances create app-vm \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --service-account=my-sa@my-project.iam.gserviceaccount.com \
  --scopes=cloud-platform

# List instances
gcloud compute instances list

# List instances in specific zone
gcloud compute instances list --zones=us-central1-a

# Get instance details
gcloud compute instances describe my-vm --zone=us-central1-a

# Start VM
gcloud compute instances start my-vm --zone=us-central1-a

# Stop VM
gcloud compute instances stop my-vm --zone=us-central1-a

# Reset VM
gcloud compute instances reset my-vm --zone=us-central1-a

# Delete VM
gcloud compute instances delete my-vm --zone=us-central1-a

# Delete multiple VMs
gcloud compute instances delete vm-1 vm-2 vm-3 --zone=us-central1-a
```

### SSH to VM (if supported)

```bash
# SSH into VM
gcloud compute ssh my-vm --zone=us-central1-a

# Run command on VM
gcloud compute ssh my-vm --zone=us-central1-a --command="ls -la"

# Copy file to VM
gcloud compute scp file.txt my-vm:~/remote-file.txt --zone=us-central1-a
```

---

## VPC Networking

### Networks

```bash
# Create auto-mode VPC
gcloud compute networks create my-vpc-auto \
  --subnet-mode=auto \
  --bgp-routing-mode=regional

# Create custom VPC
gcloud compute networks create my-vpc \
  --subnet-mode=custom \
  --bgp-routing-mode=regional \
  --description="Custom VPC network"

# List networks
gcloud compute networks list

# Get network details
gcloud compute networks describe my-vpc

# Delete network
gcloud compute networks delete my-vpc
```

### Subnets

```bash
# Create subnet
gcloud compute networks subnets create my-subnet \
  --network=my-vpc \
  --region=us-central1 \
  --range=10.0.1.0/24

# Create subnet with secondary ranges
gcloud compute networks subnets create my-subnet-advanced \
  --network=my-vpc \
  --region=us-central1 \
  --range=10.0.2.0/24 \
  --secondary-range=pods=10.4.0.0/14 \
  --secondary-range=services=10.0.32.0/20

# List subnets
gcloud compute networks subnets list

# List subnets in specific region
gcloud compute networks subnets list --regions=us-central1

# Get subnet details
gcloud compute networks subnets describe my-subnet --region=us-central1

# Update subnet (expand IP range)
gcloud compute networks subnets expand-ip-range my-subnet \
  --region=us-central1 \
  --prefix-length=20

# Delete subnet
gcloud compute networks subnets delete my-subnet --region=us-central1
```

### Firewall Rules

```bash
# Create firewall rule (allow SSH from anywhere)
gcloud compute firewall-rules create allow-ssh \
  --network=my-vpc \
  --direction=INGRESS \
  --priority=1000 \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=0.0.0.0/0

# Create firewall rule (allow HTTP/HTTPS)
gcloud compute firewall-rules create allow-web \
  --network=my-vpc \
  --allow=tcp:80,tcp:443 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=web-server

# Create firewall rule (allow internal traffic)
gcloud compute firewall-rules create allow-internal \
  --network=my-vpc \
  --allow=tcp:0-65535,udp:0-65535,icmp \
  --source-ranges=10.0.0.0/8

# Create egress rule (deny all)
gcloud compute firewall-rules create deny-all-egress \
  --network=my-vpc \
  --direction=EGRESS \
  --priority=1000 \
  --action=DENY \
  --rules=all \
  --destination-ranges=0.0.0.0/0

# List firewall rules
gcloud compute firewall-rules list

# List firewall rules for specific network
gcloud compute firewall-rules list --filter="network:my-vpc"

# Get firewall rule details
gcloud compute firewall-rules describe allow-ssh

# Update firewall rule
gcloud compute firewall-rules update allow-ssh --priority=500

# Delete firewall rule
gcloud compute firewall-rules delete allow-ssh
```

---

## IAM

### Service Accounts

```bash
# Create service account
gcloud iam service-accounts create my-sa \
  --display-name="My Service Account" \
  --description="Service account for my app"

# List service accounts
gcloud iam service-accounts list

# Get service account details
gcloud iam service-accounts describe my-sa@my-project.iam.gserviceaccount.com

# Update service account
gcloud iam service-accounts update my-sa@my-project.iam.gserviceaccount.com \
  --display-name="Updated Service Account"

# Delete service account
gcloud iam service-accounts delete my-sa@my-project.iam.gserviceaccount.com
```

### Service Account Keys

```bash
# Create key (downloads JSON file)
gcloud iam service-accounts keys create ~/my-sa-key.json \
  --iam-account=my-sa@my-project.iam.gserviceaccount.com

# List keys
gcloud iam service-accounts keys list \
  --iam-account=my-sa@my-project.iam.gserviceaccount.com

# Delete key
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=my-sa@my-project.iam.gserviceaccount.com
```

### IAM Policies

```bash
# Get IAM policy
gcloud iam service-accounts get-iam-policy my-sa@my-project.iam.gserviceaccount.com

# Add IAM binding
gcloud iam service-accounts add-iam-policy-binding my-sa@my-project.iam.gserviceaccount.com \
  --member="user:admin@example.com" \
  --role="roles/iam.serviceAccountUser"

# Remove IAM binding
gcloud iam service-accounts remove-iam-policy-binding my-sa@my-project.iam.gserviceaccount.com \
  --member="user:admin@example.com" \
  --role="roles/iam.serviceAccountUser"

# Set IAM policy from file
gcloud iam service-accounts set-iam-policy my-sa@my-project.iam.gserviceaccount.com policy.json
```

---

## Complete Workflow Example

```bash
#!/bin/bash
# Complete infrastructure setup using gcloud

PROJECT="my-project"
ZONE="us-central1-a"
REGION="us-central1"

# Set project
gcloud config set project $PROJECT

# 1. Create service account
gcloud iam service-accounts create app-sa \
  --display-name="Application Service Account"

# 2. Create custom VPC
gcloud compute networks create app-vpc \
  --subnet-mode=custom

# 3. Create subnet
gcloud compute networks subnets create app-subnet \
  --network=app-vpc \
  --region=$REGION \
  --range=10.1.0.0/24

# 4. Create firewall rules
gcloud compute firewall-rules create allow-ssh \
  --network=app-vpc \
  --allow=tcp:22 \
  --source-ranges=0.0.0.0/0

gcloud compute firewall-rules create allow-http \
  --network=app-vpc \
  --allow=tcp:80,tcp:443 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=web-server

# 5. Create VM instance
gcloud compute instances create app-vm \
  --zone=$ZONE \
  --machine-type=e2-medium \
  --subnet=app-subnet \
  --tags=web-server \
  --service-account=app-sa@$PROJECT.iam.gserviceaccount.com \
  --scopes=cloud-platform

# 6. Create storage bucket
gcloud storage buckets create gs://app-data-$PROJECT \
  --location=US

# 7. Upload application files
gcloud storage cp -r ./app-files gs://app-data-$PROJECT/

echo "✅ Infrastructure created successfully!"
```

---

## Useful Tips

```bash
# Get help for any command
gcloud compute instances create --help

# Use interactive mode
gcloud compute instances create --interactive

# Output as JSON
gcloud compute instances list --format=json

# Output as YAML
gcloud compute instances list --format=yaml

# Filter results
gcloud compute instances list --filter="zone:us-central1-a"

# Sort results
gcloud compute instances list --sort-by=name

# Limit results
gcloud compute instances list --limit=10

# Dry run (preview changes)
gcloud compute instances create my-vm --zone=us-central1-a --dry-run

# Quiet mode (non-interactive)
gcloud compute instances delete my-vm --zone=us-central1-a --quiet
```

---

## Configuration

```bash
# View current configuration
gcloud config list

# Set default project
gcloud config set project my-project

# Set default zone
gcloud config set compute/zone us-central1-a

# Set default region
gcloud config set compute/region us-central1

# Create named configuration
gcloud config configurations create dev

# Switch configuration
gcloud config configurations activate dev

# List configurations
gcloud config configurations list
```
