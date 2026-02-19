# GCloud CLI Quick Reference for GCS Stimulator

## ✅ ALL SERVICES NOW SUPPORT GCLOUD CLI!

### Setup (One-time)

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# GCS Stimulator gcloud endpoints
export CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE=http://localhost:8080/compute/v1/
export CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM=http://localhost:8080/
export CLOUDSDK_API_ENDPOINT_OVERRIDES_CONTAINER=http://localhost:8080/container/
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

---

## Common Commands

### Compute Engine

```bash
# List instances
gcloud compute instances list --project=default-project

# Create instance
gcloud compute instances create my-instance \
  --project=default-project \
  --zone=us-central1-a \
  --machine-type=e2-medium

# Delete instance
gcloud compute instances delete my-instance \
  --project=default-project \
  --zone=us-central1-a

# List networks
gcloud compute networks list --project=default-project

# List disks
gcloud compute disks list --project=default-project
```

### IAM & Admin

```bash
# List service accounts
gcloud iam service-accounts list --project=default-project

# Create service account
gcloud iam service-accounts create my-sa \
  --display-name="My Service Account" \
  --project=default-project

# Delete service account
gcloud iam service-accounts delete my-sa@default-project.iam.gserviceaccount.com \
  --project=default-project

# Create key
gcloud iam service-accounts keys create key.json \
  --iam-account=my-sa@default-project.iam.gserviceaccount.com \
  --project=default-project

# Get IAM policy
gcloud projects get-iam-policy default-project
```

### Kubernetes Engine (GKE)

```bash
# List clusters
gcloud container clusters list --project=default-project

# Create cluster
gcloud container clusters create my-cluster \
  --project=default-project \
  --location=us-central1-a \
  --num-nodes=3

# Get cluster details
gcloud container clusters describe my-cluster \
  --project=default-project \
  --location=us-central1-a

# Delete cluster
gcloud container clusters delete my-cluster \
  --project=default-project \
  --location=us-central1-a

# Get credentials (kubeconfig)
gcloud container clusters get-credentials my-cluster \
  --project=default-project \
  --location=us-central1-a
```

### VPC Networking

```bash
# List networks
gcloud compute networks list --project=default-project

# Create network
gcloud compute networks create my-network \
  --project=default-project \
  --subnet-mode=auto

# List subnets
gcloud compute networks subnets list --project=default-project

# List firewall rules
gcloud compute firewall-rules list --project=default-project

# List routers
gcloud compute routers list --project=default-project
```

---

## Troubleshooting

### Debug gcloud requests

Add `--log-http` to see what URLs gcloud is calling:

```bash
gcloud compute instances list \
  --project=default-project \
  --log-http
```

### Verify endpoints

```bash
# Check if compute endpoint works
curl http://localhost:8080/compute/v1/projects/default-project/zones

# Check if IAM endpoint works
curl http://localhost:8080/v1/projects/default-project/serviceAccounts

# Check if GKE endpoint works
curl http://localhost:8080/container/v1/projects/default-project/locations/-/clusters
```

### Common Issues

**Issue**: `404 Not Found` errors

**Solution**: Check that:
1. Backend server is running on port 8080
2. Environment variables are set correctly (see Setup section)
3. Project name is `default-project` (or adjust commands accordingly)

**Issue**: Double `/v1/v1/` in GKE URLs

**Solution**: Use `http://localhost:8080/container/` **NOT** `http://localhost:8080/container/v1/`
- gcloud automatically adds `/v1` to the path

---

## The Solution Explained

### Why It Works Now

The key issue was **incorrect endpoint path construction**:

#### ❌ WRONG (causes double /v1):
```bash
export CLOUDSDK_API_ENDPOINT_OVERRIDES_CONTAINER=http://localhost:8080/container/v1/
# Results in: http://localhost:8080/container/v1/v1/projects/... (DOUBLE v1)
```

#### ✅ CORRECT:
```bash
export CLOUDSDK_API_ENDPOINT_OVERRIDES_CONTAINER=http://localhost:8080/container/
# Results in: http://localhost:8080/container/v1/projects/... (SINGLE v1)
```

### Endpoint Pattern Summary

| Service | Endpoint Override | Why? |
|---------|------------------|------|
| Compute | `.../compute/v1/` | Compute API expects full version path |
| IAM | `.../` (root) | IAM client adds full `/v1/projects/...` path |
| GKE | `.../container/` | gcloud adds `/v1/` automatically |

---

**Status**: ✅ All services fully functional with gcloud CLI!

**Documentation**: See [GCLOUD_TEST_RESULTS.md](GCLOUD_TEST_RESULTS.md) for comprehensive testing results.
