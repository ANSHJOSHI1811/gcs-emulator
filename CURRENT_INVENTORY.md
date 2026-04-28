# 📊 GCS Emulator - Current Available Inventory

**Last Updated**: 2026-04-27 10:35:00 UTC  
**System Status**: ✅ OPERATIONAL  
**Docker Mode**: ✅ LIVE (real containers — not stub)  
**Project Scope**: `demo-project` (sanity data)

---

## 📈 Quick Summary

| Resource | Count | Status |
|----------|-------|--------|
| **VM Instances (Compute Engine)** | 4 | ✅ All RUNNING (real Docker containers) |
| **Buckets (Cloud Storage)** | 3 | ✅ All ACTIVE |
| **Bucket Objects** | 5 | ✅ Uploaded via gcloud |
| **VPC Networks** | 2 | ✅ OPERATIONAL |
| **Firewall Rules** | 3 | ✅ ACTIVE |
| **Service Accounts** | 3 | ✅ ACTIVE |
| **Subnets** | 0 | ⚠️ Create endpoint not implemented |

**Total Resources**: **20 resources provisioned via gcloud CLI**

---

## 🖥️ COMPUTE ENGINE - VM INSTANCES

**Total Count**: 4 instances  
**Status**: All RUNNING ✅  
**Zone**: us-central1-a  
**Docker**: Each VM = real `ubuntu:22.04` Docker container

### Instance Details

#### Instance 1: web-server-1
```
Name:           web-server-1
Status:         RUNNING ✅
Zone:           us-central1-a
Machine Type:   e2-medium
Internal IP:    10.128.0.3
Network:        default
Docker Name:    gcp-vm-web-server-1
Docker Image:   ubuntu:22.04
Created By:     gcloud compute instances create
```

#### Instance 2: api-server-1
```
Name:           api-server-1
Status:         RUNNING ✅
Zone:           us-central1-a
Machine Type:   e2-standard-2
Internal IP:    10.128.0.4
Network:        default
Docker Name:    gcp-vm-api-server-1
Docker Image:   ubuntu:22.04
Created By:     gcloud compute instances create
```

#### Instance 3: db-server-1
```
Name:           db-server-1
Status:         RUNNING ✅
Zone:           us-central1-a
Machine Type:   n1-standard-4
Internal IP:    10.128.0.5
Network:        default
Docker Name:    gcp-vm-db-server-1
Docker Image:   ubuntu:22.04
Created By:     gcloud compute instances create
```

#### Instance 4: worker-node-1
```
Name:           worker-node-1
Status:         RUNNING ✅
Zone:           us-central1-a
Machine Type:   e2-micro
Internal IP:    10.128.0.6
Network:        default
Docker Name:    gcp-vm-worker-node-1
Docker Image:   ubuntu:22.04
Created By:     gcloud compute instances create
```

### Verify with Docker
```bash
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}"
```

---

## 📦 CLOUD STORAGE - BUCKETS

**Total Count**: 3 buckets  
**Status**: All ACTIVE ✅

### Bucket 1: demo-app-assets
```
Name:           demo-app-assets
Storage URL:    gs://demo-app-assets/
Location:       US (multi-region)
Storage Class:  STANDARD
Created:        2026-04-27T10:30:19
Objects:        3 (config.json, style.css, index.html)
```

### Bucket 2: demo-user-uploads
```
Name:           demo-user-uploads
Storage URL:    gs://demo-user-uploads/
Location:       US (multi-region)
Storage Class:  STANDARD
Created:        2026-04-27T10:30:20
Objects:        1 (upload1.txt)
```

### Bucket 3: demo-backups
```
Name:           demo-backups
Storage URL:    gs://demo-backups/
Location:       US (multi-region)
Storage Class:  STANDARD
Created:        2026-04-27T10:30:21
Objects:        1 (backup.sql)
```

### Verify objects
```bash
gcloud storage ls gs://demo-app-assets/
gcloud storage ls gs://demo-user-uploads/
gcloud storage ls gs://demo-backups/
```

---

## 🌐 VPC NETWORKS

**Total Count**: 2 networks  
**Project**: demo-project

### Network 1: default (auto-created)
```
Name:                 default
CIDR:                 10.128.0.0/16
Subnet Mode:          LEGACY
Auto-create Subnets:  True
Status:               OPERATIONAL ✅
```

### Network 2: demo-vpc (created via gcloud)
```
Name:                 demo-vpc
CIDR:                 10.200.0.0/16
Subnet Mode:          LEGACY
Status:               OPERATIONAL ✅
Created By:           gcloud compute networks create
```

---

## 🔥 FIREWALL RULES

**Total Count**: 3 rules on demo-vpc + 5 default rules auto-initialized  
**Status**: All ACTIVE ✅

### Rule 1: demo-allow-http
```
Network:        demo-vpc
Direction:      INGRESS
Priority:       1000
Allow:          tcp:80, tcp:443
Source Ranges:  0.0.0.0/0
Disabled:       False
```

### Rule 2: demo-allow-ssh
```
Network:        demo-vpc
Direction:      INGRESS
Priority:       1000
Allow:          tcp:22
Source Ranges:  10.0.0.0/8
Disabled:       False
```

### Rule 3: demo-allow-internal
```
Network:        demo-vpc
Direction:      INGRESS
Priority:       1000
Allow:          tcp, udp, icmp
Source Ranges:  10.10.0.0/16
Disabled:       False
```

---

## 🔑 IAM - SERVICE ACCOUNTS

**Total Count**: 3 service accounts  
**Project**: demo-project  
**Status**: All ACTIVE ✅

### SA 1: demo-web-sa
```
Display Name:   Demo Web Service Account
Email:          demo-web-sa@demo-project.iam.gserviceaccount.com
Disabled:       False
Created By:     gcloud iam service-accounts create
```

### SA 2: demo-storage-sa
```
Display Name:   Demo Storage Service Account
Email:          demo-storage-sa@demo-project.iam.gserviceaccount.com
Disabled:       False
Created By:     gcloud iam service-accounts create
```

### SA 3: demo-ci-sa
```
Display Name:   Demo CI/CD Service Account
Email:          demo-ci-sa@demo-project.iam.gserviceaccount.com
Disabled:       False
Created By:     gcloud iam service-accounts create
```

---

## ⚙️ System State

### Backend
```
URL:            http://localhost:8080
API Docs:       http://localhost:8080/docs
Docker Mode:    LIVE (docker.from_env() connected successfully)
Docker SDK:     7.1.0 (upgraded from 7.0.0 — fixes http+docker URL bug)
Projects Init:  test-project, default (auto-seeded on startup)
```

### Frontend
```
URL:            http://localhost:3000
Framework:      React 18 + Vite
Status:         RUNNING ✅
```

### Docker Containers (live)
```
gcp-vm-web-server-1    Up  ubuntu:22.04
gcp-vm-api-server-1    Up  ubuntu:22.04
gcp-vm-db-server-1     Up  ubuntu:22.04
gcp-vm-worker-node-1   Up  ubuntu:22.04
```

---

## ⚠️ Known Issues

| Issue | Detail | Status |
|-------|--------|--------|
| Subnet create (gcloud) | `gcloud compute networks subnets create` returns 404 | ⚠️ Endpoint not implemented |
| IAM env override | `.env-gcloud` has wrong IAM endpoint — must set `CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM=http://localhost:8080/` | ⚠️ Fix .env-gcloud |
| Multi-zone instances | `us-east1-b` zone returns 404 on instance create | ⚠️ Only us-central1-a works reliably |
| demo-project not pre-seeded | Projects `test-project` and `default` auto-seed, but `demo-project` does not — IAM fails until project exists | ⚠️ Need to fix startup seeding |

---

## 🔧 Quick Commands

```bash
# Source emulator env (add IAM fix)
source /home/ubuntu/gcs-emulator/.env-gcloud
export CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM="http://localhost:8080/"

# List all VMs
gcloud compute instances list --project=demo-project

# List all buckets
gcloud storage buckets list --project=demo-project

# List firewall rules
gcloud compute firewall-rules list --project=demo-project

# List service accounts
gcloud iam service-accounts list --project=demo-project

# See real Docker containers
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
```
