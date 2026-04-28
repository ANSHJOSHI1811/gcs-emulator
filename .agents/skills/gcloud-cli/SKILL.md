# Skill: gcloud CLI Expert & Infrastructure Checker

**name:** gcloud CLI & Infrastructure Expert  
**description:** Expert in gcloud command compatibility, infrastructure health checks, Docker daemon validation, K3s/K8s status, and database connectivity. Always runs pre-flight checks before CLI operations or tests. Auto-activates for any gcloud/CLI/Docker/K3s/connectivity work.

**trigger_keywords:** gcloud, CLI, command, K3, K3s, K8s, Docker, docker inspect, docker ps, docker logs, docker network, connectivity, check, health, pre-flight, port, daemon, running

**allowed_tools:** Read, Grep, Semantic Search, File Search

---

## Pre-Flight Checklist (Run Before ANY CLI/Test Operation)

### 1. Docker Daemon
```bash
# Is Docker running?
docker info > /dev/null 2>&1 && echo "✅ Docker UP" || echo "❌ Docker DOWN"

# List running containers
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"

# List all containers (including stopped)
docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"

# Docker networks (each VPC = one bridge network)
docker network ls
docker network inspect <network-name>
```

### 2. Backend API
```bash
# Is backend alive on port 8080?
curl -s http://localhost:8080/health | python3 -m json.tool
curl -s http://localhost:8080/ | python3 -m json.tool

# Check port availability
lsof -i :8080
```

### 3. Frontend Dev Server
```bash
# Is frontend alive on port 3000?
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
lsof -i :3000
```

### 4. Database Connectivity
```bash
# SQLite (local dev default)
ls -lh /tmp/gcs_stimulator.db

# PostgreSQL (production)
psql "$DATABASE_URL" -c "SELECT 1 AS connected;"

# Via environment variable check
echo $DATABASE_URL
```

### 5. K3s / Kubernetes
```bash
# K3s service status
sudo systemctl status k3s

# Kubectl cluster access
k3s kubectl get nodes
k3s kubectl get pods --all-namespaces

# Or via standard kubectl if configured
kubectl get nodes
kubectl cluster-info
```

---

## gcloud Command Reference (This Emulator)

### Configuration
```bash
# Load emulator environment
source .env-gcloud

# Point gcloud to local emulator
export CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE=http://localhost:8080/compute/v1/
export CLOUDSDK_CORE_PROJECT=demo-project
```

### Compute Engine
```bash
# List instances
gcloud compute instances list --project=demo-project

# Create instance
gcloud compute instances create my-vm \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --project=demo-project

# Start / Stop / Delete
gcloud compute instances start my-vm --zone=us-central1-a --project=demo-project
gcloud compute instances stop my-vm --zone=us-central1-a --project=demo-project
gcloud compute instances delete my-vm --zone=us-central1-a --project=demo-project --quiet

# List zones and machine types
gcloud compute zones list --project=demo-project
gcloud compute machine-types list --project=demo-project
```

### VPC Networks
```bash
# List networks
gcloud compute networks list --project=demo-project

# Create VPC
gcloud compute networks create my-vpc \
  --subnet-mode=custom \
  --project=demo-project

# Create subnet
gcloud compute networks subnets create my-subnet \
  --network=my-vpc \
  --region=us-central1 \
  --range=10.0.0.0/24 \
  --project=demo-project

# Firewall rules
gcloud compute firewall-rules list --project=demo-project
```

### Cloud Storage
```bash
# List buckets
gcloud storage buckets list --project=demo-project
gcloud storage ls

# Create bucket
gcloud storage buckets create gs://my-bucket --project=demo-project

# Upload / Download / List / Delete objects
gcloud storage cp myfile.txt gs://my-bucket/
gcloud storage ls gs://my-bucket/
gcloud storage cp gs://my-bucket/myfile.txt ./
gcloud storage rm gs://my-bucket/myfile.txt

# Delete bucket
gcloud storage rm -r gs://my-bucket
```

### IAM
```bash
# List service accounts
gcloud iam service-accounts list --project=demo-project

# Create service account
gcloud iam service-accounts create my-sa \
  --display-name="My SA" \
  --project=demo-project

# Delete service account
gcloud iam service-accounts delete my-sa@demo-project.iam.gserviceaccount.com \
  --project=demo-project --quiet
```

### GKE
```bash
# List clusters
gcloud container clusters list --project=demo-project

# Create cluster
gcloud container clusters create my-cluster \
  --zone=us-central1-a \
  --num-nodes=2 \
  --project=demo-project
```

---

## Compatibility Matrix

| Command Group | Compatibility | Notes |
|---------------|---------------|-------|
| `gcloud compute instances` | ✅ 100% | Full CRUD + lifecycle |
| `gcloud compute zones/machine-types` | ✅ 100% | List operations |
| `gcloud compute networks/subnets` | ✅ 100% | Full CRUD |
| `gcloud compute firewall-rules` | ✅ 100% | Full CRUD |
| `gcloud storage` | ✅ ~87.5% | 14/16 commands |
| `gcloud iam service-accounts` | ✅ 100% | Full CRUD |
| `gcloud container clusters` | ✅ 90% | Create/list/delete |
| `gcloud compute instances ssh` | ⚠️ Limited | Docker exec, no real SSH |
| `gcloud auth` | ❌ Not supported | No auth emulation |
| `gcloud config` | ⚠️ Use env vars | Manual override |

---

## Docker Container Inspection (for VM debugging)

```bash
# Each VM instance = Docker container (ubuntu:22.04)
# Container name pattern: instance-{name}

# Find container for a VM instance
docker ps | grep instance-my-vm

# Get container details
docker inspect instance-my-vm

# Get container IP in a specific network
docker inspect instance-my-vm | python3 -c "
import sys, json
data = json.load(sys.stdin)[0]
nets = data['NetworkSettings']['Networks']
for net, info in nets.items():
    print(f'{net}: {info[\"IPAddress\"]}')
"

# View container logs (serial console equivalent)
docker logs instance-my-vm
docker logs --tail 50 instance-my-vm

# Exec into container (gcloud instances ssh equivalent)
docker exec -it instance-my-vm bash

# Container resource usage
docker stats instance-my-vm --no-stream
```

---

## Docker Network Inspection (for VPC debugging)

```bash
# Each VPC network = Docker bridge network
# Network name pattern: vpc-{name} or as stored in DB

# List all Docker networks
docker network ls

# Inspect a VPC network
docker network inspect vpc-my-vpc

# Check which containers are in a network
docker network inspect vpc-my-vpc --format='{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{println}}{{end}}'

# Test connectivity between two instances
docker exec instance-vm1 ping -c 3 <ip-of-vm2>
docker exec instance-vm1 curl -s http://<ip-of-vm2>:80
```

---

## Troubleshooting

### Backend Not Starting
```bash
# Check if port 8080 is in use
lsof -i :8080
kill -9 $(lsof -t -i:8080)

# Check logs
cd minimal-backend && uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### gcloud Commands Failing
```bash
# Verify emulator endpoint is set
echo $CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE

# Test API directly
curl -s "http://localhost:8080/compute/v1/projects/demo-project/zones" | python3 -m json.tool

# Check backend Swagger
curl -s http://localhost:8080/openapi.json | python3 -m json.tool | head -50
```

### Docker Permission Issues
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo
sudo docker ps
```

### K3s Not Accessible
```bash
# Start K3s
sudo systemctl start k3s

# Check K3s logs
sudo journalctl -u k3s -n 50

# Set KUBECONFIG
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
kubectl get nodes
```

---

## Key Rules

- **Always run pre-flight checklist** before any CLI operation or test run
- **Docker must be running** — backend container ops will fail silently otherwise
- **Database must be reachable** — all API calls will 500 without DB
- **Source `.env-gcloud`** before running gcloud commands against the emulator
- **Container names follow pattern**: `instance-{vm-name}`
- **Network names follow pattern**: `vpc-{network-name}` or as stored in DB
- gcloud `--quiet` flag for delete operations to skip confirmations in scripts
