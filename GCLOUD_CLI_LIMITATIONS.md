# gcloud CLI Compatibility & Limitations

**Last Updated:** February 12, 2026

## Overview

This GCP Simulator provides a REST API that mimics Google Cloud Platform endpoints, enabling partial compatibility with the `gcloud` CLI tool. However, there are important limitations to understand.

---

## ✅ What Works

### API Endpoint Compatibility

The simulator implements GCP-compatible REST endpoints that can be accessed directly via HTTP:

```bash
# Backend URL
http://localhost:8080

# Example endpoints:
GET  /compute/v1/projects/{project}/zones/{zone}/instances
POST /compute/v1/projects/{project}/zones/{zone}/instances
GET  /storage/v1/b
POST /storage/v1/b/{bucket}/o
```

### Services Implemented

| Service | API Compatibility | Notes |
|---------|------------------|-------|
| **Compute Engine** | ✅ Partial | VMs map to Docker containers |
| **VPC Networks** | ✅ Partial | Networks map to Docker networks |
| **Subnets** | ✅ Partial | IP allocation from CIDR ranges |
| **Routes** | ✅ Partial | Next hop types supported |
| **Firewall Rules** | ✅ Schema only | Rules exist but not enforced |
| **Cloud Storage** | ✅ Partial | In-memory + SQLite storage |
| **IAM & Admin** | ✅ Schema only | Service accounts exist but no auth |
| **Projects** | ✅ Full | Project management works |

---

## ❌ What Doesn't Work

### 1. Authentication & Authorization

**Issue:** No OAuth2, service accounts, or API key validation

```bash
# This will FAIL
gcloud auth login
gcloud auth application-default login

# This will also FAIL
gcloud compute instances list --project=my-project
```

**Why:** The simulator has:
- No Google OAuth2 integration
- No token validation
- No IAM permissions enforcement
- No service account key verification

**Workaround:** Use direct HTTP requests without authentication:

```bash
# Use curl instead
curl http://localhost:8080/compute/v1/projects/project-alpha/zones/us-central1-a/instances
```

### 2. gcloud Configuration

**Issue:** Cannot configure gcloud to use localhost backend

```bash
# This doesn't work
gcloud config set api_endpoint_overrides/compute http://localhost:8080/compute/v1
```

**Why:** 
- gcloud expects Google's production endpoints
- No mechanism to override all endpoint URLs
- TLS/SSL certificate validation fails on localhost
- Authentication is mandatory in gcloud

**Workaround:** Use HTTP client tools:

```bash
# Use httpie
http GET localhost:8080/compute/v1/projects/project-alpha/zones/us-central1-a/instances

# Or curl with jq
curl -s http://localhost:8080/compute/v1/projects/project-alpha/global/networks | jq
```

### 3. gcloud Commands

**Status:** Most gcloud commands will fail

```bash
# These commands DON'T WORK with the simulator
gcloud compute instances list
gcloud storage buckets list
gcloud iam service-accounts create my-sa
gcloud compute networks create my-vpc
```

**Why:**
- Commands require authentication
- gcloud uses production GCP endpoints
- No localhost backend support
- Certificate validation errors

### 4. Resource Quotas & Limits

**Issue:** No quota enforcement

**Missing:**
- CPU/memory limits (other than Docker host)
- API rate limiting
- Storage size limits
- Maximum instances per project

### 5. Advanced Features

**Not Implemented:**

| Feature | Status | Reason |
|---------|--------|--------|
| Load Balancers | ❌ Not implemented | Complex multi-container setup |
| Cloud DNS | ❌ Not implemented | Requires DNS server |
| VPC Peering | ⚠️ Removed | Backend existed but UI removed |
| Instance Groups | ❌ Not implemented | Auto-scaling complexity |
| Persistent Disks | ❌ Not implemented | VMs use ephemeral storage |
| Snapshots | ❌ Not implemented | No disk management |
| IAM Policies | ⚠️ Schema only | No permission enforcement |
| Billing | ❌ Not implemented | Simulator is free |
| Monitoring | ❌ Not implemented | No metrics collection |
| Logging | ❌ Not implemented | No log aggregation |

---

## 🔧 Workarounds & Alternatives

### Use HTTP Clients

#### curl (Basic)

```bash
# List instances
curl http://localhost:8080/compute/v1/projects/project-alpha/zones/us-central1-a/instances

# Create instance
curl -X POST http://localhost:8080/compute/v1/projects/project-alpha/zones/us-central1-a/instances \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-instance",
    "machineType": "e2-medium",
    "network": "default"
  }'
```

#### httpie (Prettier)

```bash
# Install httpie
pip install httpie

# List buckets
http GET localhost:8080/storage/v1/b

# Create bucket
http POST localhost:8080/storage/v1/b project_id=project-alpha name=test-bucket
```

#### Python SDK

```python
import requests

BASE_URL = "http://localhost:8080"

# List zones
response = requests.get(f"{BASE_URL}/compute/v1/projects/project-alpha/zones")
zones = response.json()
print(zones)

# Create network
response = requests.post(
    f"{BASE_URL}/compute/v1/projects/project-alpha/global/networks",
    json={
        "name": "my-vpc",
        "autoCreateSubnetworks": False,
        "cidrRange": "10.0.0.0/16"
    }
)
print(response.json())
```

### Use the Web UI

The simulator includes a React-based web interface at `http://localhost:3000` that provides:

- ✅ VM instance management
- ✅ VPC networks and subnets
- ✅ Route configuration
- ✅ Firewall rules (display only)
- ✅ Cloud Storage buckets and objects
- ✅ IAM service accounts (display only)

---

## 🎯 Recommended Use Cases

### ✅ Good For:

1. **Local Development**
   - Test GCP API integrations before deploying
   - Develop applications that use GCP services
   - Learn GCP concepts without cloud costs

2. **CI/CD Testing**
   - Run tests against mock GCP services
   - Validate infrastructure-as-code (Terraform)
   - Integration tests for cloud-native apps

3. **Training & Education**
   - Teach GCP concepts without real accounts
   - Demonstrate cloud architecture patterns
   - Practice API interactions

4. **Prototyping**
   - Rapid application development
   - Proof-of-concept projects
   - Demo environments

### ❌ Not Good For:

1. **Production Use**
   - No security features
   - No data persistence guarantees
   - No high availability

2. **Performance Testing**
   - Limited by Docker and SQLite
   - No distributed systems
   - No cloud-scale performance

3. **Security Testing**
   - No authentication/authorization
   - No encryption
   - No audit logs

4. **Full gcloud CLI Testing**
   - gcloud commands don't work
   - No OAuth2 integration
   - Must use HTTP directly

---

## 📝 Implementation Notes

### API Path Compatibility

The simulator uses GCP's actual API paths:

```
✅ /compute/v1/projects/{project}/zones/{zone}/instances
✅ /compute/v1/projects/{project}/global/networks
✅ /storage/v1/b
✅ /storage/v1/b/{bucket}/o
✅ /cloudresourcemanager/v1/projects
✅ /v1/projects/{project}/serviceAccounts
```

This ensures responses match GCP's JSON format for easier testing.

### Response Format Compatibility

The simulator returns GCP-compatible JSON:

```json
{
  "kind": "compute#instance",
  "id": "123",
  "name": "test-instance",
  "zone": "us-central1-a",
  "machineType": "e2-medium",
  "status": "RUNNING",
  "selfLink": "https://www.googleapis.com/compute/v1/projects/project-alpha/zones/us-central1-a/instances/test-instance"
}
```

### Docker Integration

- **VMs = Docker Containers**: Each VM instance runs as a Docker container
- **Networks = Docker Networks**: VPC networks map to Docker bridge networks
- **IPs = Container IPs**: Internal IPs allocated from Docker network subnets
- **Storage = SQLite + Filesystem**: Objects stored in SQLite with file references

---

## 🚀 Future Enhancements

Potential improvements for gcloud compatibility:

1. **Mock Authentication Server**
   - Stub OAuth2 endpoints
   - Accept any token
   - No actual validation

2. **gcloud Proxy**
   - Intercept gcloud HTTP requests
   - Redirect to localhost
   - Translate API calls

3. **Certificate Management**
   - Self-signed certificates
   - Trust store configuration
   - TLS support

4. **Environment Variables**
   - `CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE`
   - `CLOUDSDK_AUTH_ACCESS_TOKEN`
   - Bypass authentication

---

## 📚 References

- [GCP REST API Documentation](https://cloud.google.com/compute/docs/reference/rest/v1)
- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference)
- [GCP Simulator Repository](https://github.com/your-repo/gcs-stimulator)

---

## 🐛 Known Issues

1. **No Default Firewall Rules**: Firewall schema exists but no rules auto-created
2. **No Service Accounts**: IAM schema exists but accounts not initialized
3. **RouteTable Deprecated**: Old AWS-style route tables removed from codebase
4. **VPC Peering Removed**: Backend existed but UI removed, may re-add later
5. **Large Frontend Bundle**: 665 kB bundle size (warning threshold: 500 kB)

---

**Summary**: Use the simulator for local development with direct HTTP requests or the web UI. Do not expect gcloud CLI commands to work without significant modifications.
