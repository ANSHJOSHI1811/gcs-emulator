# REST API Examples

**Direct HTTP/REST API calls using curl**

Use these examples to interact directly with the GCP Stimulator REST API endpoints.

**Base URL**: `http://localhost:8080`

---

## Cloud Storage

### Buckets

```bash
# Create bucket
curl -X POST "http://localhost:8080/storage/v1/b?project=my-project" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-bucket", "location": "US", "storageClass": "STANDARD"}'

# List buckets
curl "http://localhost:8080/storage/v1/b?project=my-project"

# Get bucket details
curl "http://localhost:8080/storage/v1/b/my-bucket"

# Delete bucket
curl -X DELETE "http://localhost:8080/storage/v1/b/my-bucket"

# Update bucket (enable versioning)
curl -X PATCH "http://localhost:8080/storage/v1/b/my-bucket" \
  -H "Content-Type: application/json" \
  -d '{"versioning": {"enabled": true}}'
```

### Objects

```bash
# Upload object (simple)
curl -X POST "http://localhost:8080/upload/storage/v1/b/my-bucket/o?uploadType=media&name=file.txt" \
  -H "Content-Type: text/plain" \
  --data-binary "Hello World"

# Upload from file
curl -X POST "http://localhost:8080/upload/storage/v1/b/my-bucket/o?uploadType=media&name=document.pdf" \
  -H "Content-Type: application/pdf" \
  --data-binary @document.pdf

# List objects
curl "http://localhost:8080/storage/v1/b/my-bucket/o"

# Get object metadata
curl "http://localhost:8080/storage/v1/b/my-bucket/o/file.txt"

# Download object
curl "http://localhost:8080/storage/v1/b/my-bucket/o/file.txt?alt=media" -o downloaded-file.txt

# Delete object
curl -X DELETE "http://localhost:8080/storage/v1/b/my-bucket/o/file.txt"

# Copy object
curl -X POST "http://localhost:8080/storage/v1/b/my-bucket/o/file.txt/copyTo/b/dest-bucket/o/copied-file.txt"
```

### Resumable Uploads

```bash
# 1. Initiate resumable upload
UPLOAD_URL=$(curl -i -X POST "http://localhost:8080/upload/storage/v1/b/my-bucket/o?uploadType=resumable&name=large-file.bin" \
  -H "Content-Type: application/octet-stream" \
  -H "X-Upload-Content-Length: 10485760" | grep -i Location | cut -d' ' -f2 | tr -d '\r')

# 2. Upload chunk
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Range: bytes 0-1048575/10485760" \
  --data-binary @chunk1.bin

# 3. Query upload status
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Range: bytes */10485760"
```

---

## Compute Engine

### VM Instances

```bash
# Create VM instance (creates Docker container)
curl -X POST "http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-vm",
    "machineType": "zones/us-central1-a/machineTypes/e2-medium",
    "disks": [{
      "boot": true,
      "initializeParams": {
        "sourceImage": "projects/debian-cloud/global/images/debian-11"
      }
    }],
    "networkInterfaces": [{
      "network": "global/networks/default"
    }]
  }'

# List instances
curl "http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances"

# Get instance details
curl "http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances/my-vm"

# Start VM
curl -X POST "http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances/my-vm/start"

# Stop VM
curl -X POST "http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances/my-vm/stop"

# Delete VM
curl -X DELETE "http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances/my-vm"
```

### Zones & Machine Types

```bash
# List zones
curl "http://localhost:8080/compute/v1/projects/my-project/zones"

# List machine types
curl "http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/machineTypes"

# Get machine type details
curl "http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/machineTypes/e2-medium"
```

---

## VPC Networking

### Networks

```bash
# Create custom VPC network
curl -X POST "http://localhost:8080/compute/v1/projects/my-project/global/networks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-vpc",
    "autoCreateSubnetworks": false,
    "description": "Custom VPC network"
  }'

# List networks
curl "http://localhost:8080/compute/v1/projects/my-project/global/networks"

# Get network details
curl "http://localhost:8080/compute/v1/projects/my-project/global/networks/my-vpc"

# Delete network
curl -X DELETE "http://localhost:8080/compute/v1/projects/my-project/global/networks/my-vpc"
```

### Subnets

```bash
# Create subnet
curl -X POST "http://localhost:8080/compute/v1/projects/my-project/regions/us-central1/subnetworks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-subnet",
    "network": "projects/my-project/global/networks/my-vpc",
    "ipCidrRange": "10.0.1.0/24",
    "region": "us-central1"
  }'

# List subnets
curl "http://localhost:8080/compute/v1/projects/my-project/regions/us-central1/subnetworks"

# Delete subnet
curl -X DELETE "http://localhost:8080/compute/v1/projects/my-project/regions/us-central1/subnetworks/my-subnet"
```

### Firewall Rules

```bash
# Create firewall rule (allow SSH)
curl -X POST "http://localhost:8080/compute/v1/projects/my-project/global/firewalls" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "allow-ssh",
    "network": "projects/my-project/global/networks/my-vpc",
    "direction": "INGRESS",
    "priority": 1000,
    "allowed": [{
      "IPProtocol": "tcp",
      "ports": ["22"]
    }],
    "sourceRanges": ["0.0.0.0/0"]
  }'

# List firewall rules
curl "http://localhost:8080/compute/v1/projects/my-project/global/firewalls"

# Update firewall rule
curl -X PATCH "http://localhost:8080/compute/v1/projects/my-project/global/firewalls/allow-ssh" \
  -H "Content-Type: application/json" \
  -d '{"priority": 500}'

# Delete firewall rule
curl -X DELETE "http://localhost:8080/compute/v1/projects/my-project/global/firewalls/allow-ssh"
```

---

## IAM

### Service Accounts

```bash
# Create service account
curl -X POST "http://localhost:8080/iam/v1/projects/my-project/serviceAccounts" \
  -H "Content-Type: application/json" \
  -d '{
    "accountId": "my-sa",
    "serviceAccount": {
      "displayName": "My Service Account",
      "description": "Service account for my app"
    }
  }'

# List service accounts
curl "http://localhost:8080/iam/v1/projects/my-project/serviceAccounts"

# Get service account
curl "http://localhost:8080/iam/v1/projects/my-project/serviceAccounts/my-sa@my-project.iam.gserviceaccount.com"

# Delete service account
curl -X DELETE "http://localhost:8080/iam/v1/projects/my-project/serviceAccounts/my-sa@my-project.iam.gserviceaccount.com"
```

### Service Account Keys

```bash
# Create key
curl -X POST "http://localhost:8080/iam/v1/projects/my-project/serviceAccounts/my-sa@my-project.iam.gserviceaccount.com/keys" \
  -H "Content-Type: application/json"

# Create key with specific algorithm
curl -X POST "http://localhost:8080/iam/v1/projects/my-project/serviceAccounts/my-sa@my-project.iam.gserviceaccount.com/keys" \
  -H "Content-Type: application/json" \
  -d '{
    "keyAlgorithm": "KEY_ALG_RSA_4096",
    "privateKeyType": "TYPE_GOOGLE_CREDENTIALS_FILE"
  }'

# List keys
curl "http://localhost:8080/iam/v1/projects/my-project/serviceAccounts/my-sa@my-project.iam.gserviceaccount.com/keys"

# Delete key
curl -X DELETE "http://localhost:8080/iam/v1/projects/my-project/serviceAccounts/my-sa@my-project.iam.gserviceaccount.com/keys/KEY_ID"
```

---

## Complete Workflow Example

```bash
#!/bin/bash
PROJECT="my-project"
ZONE="us-central1-a"
BASE_URL="http://localhost:8080"

# 1. Create service account
curl -X POST "$BASE_URL/iam/v1/projects/$PROJECT/serviceAccounts" \
  -H "Content-Type: application/json" \
  -d '{"accountId": "app-sa", "serviceAccount": {"displayName": "App SA"}}'

# 2. Create custom VPC
curl -X POST "$BASE_URL/compute/v1/projects/$PROJECT/global/networks" \
  -H "Content-Type: application/json" \
  -d '{"name": "app-vpc", "autoCreateSubnetworks": false}'

# 3. Create subnet
curl -X POST "$BASE_URL/compute/v1/projects/$PROJECT/regions/us-central1/subnetworks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "app-subnet",
    "network": "projects/'$PROJECT'/global/networks/app-vpc",
    "ipCidrRange": "10.1.0.0/24"
  }'

# 4. Create firewall rule
curl -X POST "$BASE_URL/compute/v1/projects/$PROJECT/global/firewalls" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "allow-http",
    "network": "projects/'$PROJECT'/global/networks/app-vpc",
    "allowed": [{"IPProtocol": "tcp", "ports": ["80", "443"]}],
    "sourceRanges": ["0.0.0.0/0"]
  }'

# 5. Create VM with service account
curl -X POST "$BASE_URL/compute/v1/projects/$PROJECT/zones/$ZONE/instances" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "app-vm",
    "machineType": "zones/'$ZONE'/machineTypes/e2-medium",
    "serviceAccounts": [{
      "email": "app-sa@'$PROJECT'.iam.gserviceaccount.com"
    }],
    "networkInterfaces": [{
      "subnetwork": "projects/'$PROJECT'/regions/us-central1/subnetworks/app-subnet"
    }]
  }'

# 6. Create storage bucket
curl -X POST "$BASE_URL/storage/v1/b?project=$PROJECT" \
  -H "Content-Type: application/json" \
  -d '{"name": "app-data-bucket"}'

# 7. Upload configuration file
curl -X POST "$BASE_URL/upload/storage/v1/b/app-data-bucket/o?uploadType=media&name=config.json" \
  -H "Content-Type: application/json" \
  --data-binary '{"environment": "production"}'

echo "✅ Infrastructure created successfully!"
```

---

## Response Formats

### Success Response
```json
{
  "kind": "compute#operation",
  "id": "operation-1234567890",
  "name": "operation-abc123",
  "status": "DONE",
  "progress": 100,
  "insertTime": "2026-01-28T08:00:00.000Z",
  "endTime": "2026-01-28T08:00:01.000Z"
}
```

### Error Response
```json
{
  "error": {
    "code": 404,
    "message": "The resource 'my-vm' does not exist.",
    "errors": [{
      "domain": "global",
      "reason": "notFound",
      "message": "The resource 'my-vm' does not exist."
    }]
  }
}
```

---

## Testing Tips

```bash
# Pretty print JSON responses
curl "http://localhost:8080/storage/v1/b?project=test" | jq .

# Save response to file
curl "http://localhost:8080/compute/v1/projects/test/zones" -o zones.json

# Include response headers
curl -i "http://localhost:8080/health"

# Verbose output for debugging
curl -v "http://localhost:8080/storage/v1/b?project=test"
```
