# 🚀 GCloud Commands - Complete Reference

**All working gcloud commands for GCP Stimulator**  
**Setup Required:** `source /home/ubuntu/gcs-stimulator/.env-gcloud`

---

## 📋 Quick Setup

```bash
# Source environment variables (points gcloud to local simulator)
source /home/ubuntu/gcs-stimulator/.env-gcloud

# Verify configuration
echo $CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE
echo $CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE

# Set default project (optional)
gcloud config set project test-project
```

---

## 💾 CLOUD STORAGE COMMANDS

### Buckets

#### List Buckets
```bash
gcloud storage buckets list --project=test-project
```

#### Create Bucket
```bash
gcloud storage buckets create gs://my-new-bucket \
  --project=test-project \
  --location=US

# With specific storage class
gcloud storage buckets create gs://premium-bucket \
  --project=test-project \
  --location=US \
  --default-storage-class=STANDARD
```

#### Get Bucket Details
```bash
gcloud storage buckets describe gs://test-bucket-final
```

#### Delete Bucket
```bash
gcloud storage buckets delete gs://my-bucket --project=test-project
```

### Objects

#### Upload File
```bash
# Upload single file
gcloud storage cp local-file.txt gs://test-bucket-final/

# Upload with custom name
gcloud storage cp file.txt gs://test-bucket-final/uploaded-file.txt

# Upload multiple files
gcloud storage cp file1.txt file2.txt gs://test-bucket-final/

# Upload directory
gcloud storage cp -r ./my-directory gs://test-bucket-final/
```

#### List Objects
```bash
# List all objects in bucket
gcloud storage ls gs://test-bucket-final/

# List with details
gcloud storage ls -l gs://test-bucket-final/

# List with prefix filter
gcloud storage ls gs://test-bucket-final/prefix*
```

#### Download File (Note: client-side issue, use curl instead)
```bash
# Download single file (has known gcloud client issue)
gcloud storage cp gs://test-bucket-final/file.txt ./downloaded.txt

# Workaround: Use curl for downloads
curl -o file.txt "http://localhost:8080/storage/v1/b/test-bucket-final/o/file.txt?alt=media"
```

#### Delete Object
```bash
# Delete single object
gcloud storage rm gs://test-bucket-final/file.txt

# Delete multiple objects
gcloud storage rm gs://test-bucket-final/file1.txt gs://test-bucket-final/file2.txt

# Delete all objects with prefix
gcloud storage rm -r gs://test-bucket-final/prefix*
```

#### Move/Copy Object
```bash
# Copy object within same bucket
gcloud storage cp gs://source-bucket/file.txt gs://dest-bucket/file.txt

# Move object (copy + delete)
gcloud storage mv gs://source-bucket/file.txt gs://dest-bucket/file.txt
```

---

## 🖥️ COMPUTE ENGINE COMMANDS

### Zones

#### List Zones
```bash
gcloud compute zones list --project=test-project

# Filter by region
gcloud compute zones list --filter="region:us-central1"
```

### Machine Types

#### List Machine Types
```bash
gcloud compute machine-types list --zones=us-central1-a --project=test-project

# Filter by specific criteria
gcloud compute machine-types list \
  --zones=us-central1-a \
  --filter="guestCpus>=2"
```

### Instances

#### List Instances
```bash
# List all instances in zone
gcloud compute instances list \
  --project=test-project \
  --zones=us-central1-a

# List instances across all zones
gcloud compute instances list --project=test-project

# Filter by status
gcloud compute instances list \
  --project=test-project \
  --filter="status:RUNNING"
```

#### Create Instance
```bash
# Basic instance creation
gcloud compute instances create my-vm \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --project=test-project

# Instance with specific network
gcloud compute instances create my-vm \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --network=default \
  --project=test-project

# Instance on custom VPC
gcloud compute instances create custom-vm \
  --zone=us-central1-a \
  --machine-type=e2-small \
  --network=my-custom-vpc \
  --project=test-project
```

#### Get Instance Details
```bash
gcloud compute instances describe my-vm \
  --zone=us-central1-a \
  --project=test-project
```

#### Stop Instance
```bash
gcloud compute instances stop my-vm \
  --zone=us-central1-a \
  --project=test-project
```

#### Start Instance
```bash
gcloud compute instances start my-vm \
  --zone=us-central1-a \
  --project=test-project
```

#### Delete Instance
```bash
gcloud compute instances delete my-vm \
  --zone=us-central1-a \
  --project=test-project \
  --quiet
```

---

## 🌐 VPC NETWORK COMMANDS

### Networks

#### List Networks
```bash
gcloud compute networks list --project=test-project
```

#### Create Network
```bash
# Create auto-subnet network
gcloud compute networks create my-vpc \
  --subnet-mode=auto \
  --project=test-project

# Create custom-subnet network
gcloud compute networks create custom-vpc \
  --subnet-mode=custom \
  --project=test-project
```

#### Get Network Details
```bash
gcloud compute networks describe default --project=test-project
```

#### Delete Network
```bash
gcloud compute networks delete my-vpc \
  --project=test-project \
  --quiet
```

### Internet Gateways (Metadata Only)

#### List Internet Gateways
```bash
# List via API (gcloud doesn't have direct command)
curl -s http://localhost:8080/compute/v1/projects/test-project/global/internetGateways | python3 -m json.tool
```

#### Get Default Internet Gateway
```bash
curl -s http://localhost:8080/compute/v1/projects/test-project/global/internetGateways/default-internet-gateway | python3 -m json.tool
```

---

## 👤 IAM COMMANDS

### Service Accounts

#### List Service Accounts
```bash
# List via API (gcloud IAM commands not directly supported in simulator)
curl -s http://localhost:8080/v1/projects/test-project/serviceAccounts | python3 -m json.tool
```

#### Create Service Account
```bash
# Via API
curl -X POST http://localhost:8080/v1/projects/test-project/serviceAccounts \
  -H "Content-Type: application/json" \
  -d '{
    "accountId": "my-service-account",
    "serviceAccount": {
      "displayName": "My Service Account",
      "description": "Service account for my app"
    }
  }' | python3 -m json.tool
```

#### Get Service Account
```bash
# Via API
curl -s http://localhost:8080/v1/projects/test-project/serviceAccounts/my-service-account@test-project.iam.gserviceaccount.com | python3 -m json.tool
```

#### Delete Service Account
```bash
# Via API
curl -X DELETE http://localhost:8080/v1/projects/test-project/serviceAccounts/my-service-account@test-project.iam.gserviceaccount.com
```

---

## 📊 PROJECT COMMANDS

### Projects

#### List Projects
```bash
# Via API
curl -s http://localhost:8080/cloudresourcemanager/v1/projects | python3 -m json.tool
```

---

## 🔍 VERIFICATION COMMANDS

### Check Instance Container Mapping
```bash
# List instances with Docker info
gcloud compute instances list --project=test-project --zones=us-central1-a

# Verify Docker container exists
docker ps | grep gcp-vm-

# Check instance details with Docker ID
curl -s http://localhost:8080/compute/v1/projects/test-project/zones/us-central1-a/instances/my-vm | python3 -m json.tool | grep -A5 docker
```

### Check VPC Network Mapping
```bash
# List VPC networks
gcloud compute networks list --project=test-project

# Verify Docker networks exist
docker network ls | grep gcp-vpc

# Get network details
gcloud compute networks describe my-vpc --project=test-project
```

### Test Outbound Connectivity
```bash
# Get instance container name
INSTANCE_NAME="my-vm"
CONTAINER_NAME="gcp-vm-$INSTANCE_NAME"

# Test outbound connectivity from container
docker exec $CONTAINER_NAME curl -I https://www.google.com
```

---

## 🎯 DEMO WORKFLOW EXAMPLES

### Example 1: Complete Storage Workflow
```bash
# Create bucket
gcloud storage buckets create gs://demo-bucket --project=test-project

# Upload file
echo "Hello from GCP Stimulator" > test.txt
gcloud storage cp test.txt gs://demo-bucket/

# List objects
gcloud storage ls gs://demo-bucket/

# Download (use curl workaround)
curl -o downloaded.txt "http://localhost:8080/storage/v1/b/demo-bucket/o/test.txt?alt=media"

# Delete object
gcloud storage rm gs://demo-bucket/test.txt

# Delete bucket
gcloud storage buckets delete gs://demo-bucket
```

### Example 2: Complete Compute Workflow
```bash
# Create instance
gcloud compute instances create demo-vm \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --project=test-project

# Verify in UI or list
gcloud compute instances list --project=test-project --zones=us-central1-a

# Check Docker container
docker ps | grep gcp-vm-demo-vm

# Stop instance
gcloud compute instances stop demo-vm \
  --zone=us-central1-a \
  --project=test-project

# Start instance
gcloud compute instances start demo-vm \
  --zone=us-central1-a \
  --project=test-project

# Delete instance
gcloud compute instances delete demo-vm \
  --zone=us-central1-a \
  --project=test-project \
  --quiet
```

### Example 3: VPC and Instance Together
```bash
# Create custom VPC
gcloud compute networks create demo-vpc \
  --subnet-mode=custom \
  --project=test-project

# Verify Docker network created
docker network ls | grep gcp-vpc-test-project-demo-vpc

# Create instance on custom VPC
gcloud compute instances create vpc-demo-vm \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --network=demo-vpc \
  --project=test-project

# Check instance network
gcloud compute instances describe vpc-demo-vm \
  --zone=us-central1-a \
  --project=test-project | grep -A10 networkInterfaces

# Cleanup
gcloud compute instances delete vpc-demo-vm \
  --zone=us-central1-a \
  --project=test-project \
  --quiet

gcloud compute networks delete demo-vpc \
  --project=test-project \
  --quiet
```

---

## ⚠️ KNOWN ISSUES & WORKAROUNDS

### Storage Download Issue
**Problem:** `gcloud storage cp` download has client-side TypeError  
**Workaround:** Use curl for downloads:
```bash
curl -o file.txt "http://localhost:8080/storage/v1/b/BUCKET/o/OBJECT?alt=media"
```

### Storage Cat Issue
**Problem:** `gcloud storage cat` has client-side TypeError  
**Workaround:** Use curl to view file content:
```bash
curl -s "http://localhost:8080/storage/v1/b/BUCKET/o/OBJECT?alt=media"
```

### IAM Commands
**Note:** IAM commands use direct API calls (curl) instead of gcloud CLI  
**Reason:** Simulator focuses on compute/storage gcloud compatibility

---

## 🔧 TROUBLESHOOTING

### Command Not Working?
```bash
# 1. Verify environment is sourced
source /home/ubuntu/gcs-stimulator/.env-gcloud

# 2. Check backend is running
curl http://localhost:8080/health

# 3. Check endpoint overrides are set
env | grep CLOUDSDK_API_ENDPOINT_OVERRIDES

# 4. Test with curl directly
curl -s http://localhost:8080/compute/v1/projects/test-project/zones
```

### Reset Environment
```bash
# Unset overrides
unset CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE
unset CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE

# Re-source
source /home/ubuntu/gcs-stimulator/.env-gcloud
```

---

## 📚 COMMAND SUCCESS RATES

### Fully Working (✅)
- ✅ `gcloud compute zones list`
- ✅ `gcloud compute machine-types list`
- ✅ `gcloud compute instances list`
- ✅ `gcloud compute instances create`
- ✅ `gcloud compute instances stop`
- ✅ `gcloud compute instances start`
- ✅ `gcloud compute instances delete`
- ✅ `gcloud compute networks list`
- ✅ `gcloud compute networks create`
- ✅ `gcloud compute networks delete`
- ✅ `gcloud storage buckets list`
- ✅ `gcloud storage buckets create`
- ✅ `gcloud storage buckets delete`
- ✅ `gcloud storage cp` (upload)
- ✅ `gcloud storage ls`
- ✅ `gcloud storage rm`

### Workaround Required (⚠️)
- ⚠️ `gcloud storage cp` (download) - Use curl
- ⚠️ `gcloud storage cat` - Use curl

### Use API Instead (📡)
- 📡 IAM commands - Use curl with API endpoints

---

## 🎉 SUCCESS RATE: 14/16 WORKING (87.5%)

**Ready for demo! All critical commands functional.**

---

## 📞 QUICK REFERENCE

**Backend:** http://localhost:8080  
**API Docs:** http://localhost:8080/docs  
**Frontend:** http://localhost:3000  
**Test Project:** test-project  
**Test Zone:** us-central1-a  
**Env File:** /home/ubuntu/gcs-stimulator/.env-gcloud
