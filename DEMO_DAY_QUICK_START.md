# 🚀 DEMO DAY - QUICK START GUIDE

## STEP 1: Start Services (5 minutes before demo)

### Terminal 1 - Backend
```bash
cd /home/ubuntu/gcs-stimulator/minimal-backend
python3 main.py
```
**Expected:** See ASCII banner with "GCP STIMULATOR BACKEND" on http://0.0.0.0:8080

### Terminal 2 - Frontend
```bash
cd /home/ubuntu/gcs-stimulator/gcp-stimulator-ui
npm run dev
```
**Expected:** See "VITE ready in X ms" and "Local: http://localhost:3000"

### Terminal 3 - Verify
```bash
# Quick health check
curl http://localhost:8080/health
curl http://localhost:3000

# Both should respond successfully
```

---

## STEP 2: Open Browser

Open: **http://localhost:3000**

You should see:
- ✅ GCP Stimulator UI
- ✅ Navigation: Storage, Compute, VPC Networks, IAM & Admin
- ✅ Project selector showing "test-project"

---

## STEP 3: Demo Flow (15 minutes)

### Part 1: Storage (3 minutes)
1. Click "Storage" → Show 2 existing buckets
2. Click "2 buckets" stat → Shows all buckets
3. Click "5 objects" stat → Opens activity modal
4. Click "Create Bucket" → Create "demo-bucket-2026"
5. Click "Upload" → Upload a test file
6. Click object name → Show details modal
7. Click Delete → Confirm deletion

**Talking Points:**
- "Real file storage with MD5/CRC32c hashing"
- "PostgreSQL persistence for metadata"
- "Files stored at /tmp/gcs-storage/"

### Part 2: Compute (4 minutes)
1. Click "Compute Engine" → Show existing instance
2. Click instance name → Show details modal with Docker Container ID
3. Click "Create Instance" → Show form with network selection
4. Create instance → Watch optimistic UI (RUNNING status)
5. Click "Stop" → Watch state change (STOPPING → TERMINATED)
6. Click "Start" → Watch state change (STARTING → RUNNING)
7. Show Docker: `docker ps | grep gcp-vm`
8. Click "Delete" → Confirm deletion

**Talking Points:**
- "Each instance = Real Docker container"
- "Automatic Docker container lifecycle management"
- "Container ID visible in API responses"

### Part 3: VPC Networks (3 minutes)
1. Click "VPC Networks" → Show default network
2. Click network name → Show details with Docker network name
3. Click "Create VPC Network" → Create "demo-vpc"
4. Choose "Custom" subnet mode
5. Show Docker: `docker network ls | grep gcp-vpc`
6. Go back to Compute → Create instance on demo-vpc
7. Show instance has IP in custom network
8. Delete instance, then delete demo-vpc

**Talking Points:**
- "VPC networks = Docker bridge networks"
- "Default VPC uses Docker bridge"
- "Custom VPCs create isolated Docker networks"

### Part 4: IAM (2 minutes)
1. Click "IAM & Admin" → Show service accounts page
2. Click "Create Service Account"
3. Enter: Account ID "demo-sa", Display Name "Demo Service Account"
4. Click Create → Show email format: `demo-sa@test-project.iam.gserviceaccount.com`
5. Click email → Show details modal (Unique ID, Project, etc.)
6. Click Delete → Confirm deletion

**Talking Points:**
- "Full IAM service account management"
- "Auto-generated unique IDs"
- "Standard GCP email format"

### Part 5: gcloud CLI (3 minutes)
```bash
# Setup
source /home/ubuntu/gcs-stimulator/.env-gcloud

# List resources
gcloud compute zones list --project=test-project
gcloud compute instances list --project=test-project
gcloud compute networks list --project=test-project

# Create instance
gcloud compute instances create cli-demo-vm --zone=us-central1-a --project=test-project

# Show in UI (should appear automatically)
# Delete via CLI
gcloud compute instances delete cli-demo-vm --zone=us-central1-a --project=test-project --quiet
```

**Talking Points:**
- "Full gcloud CLI compatibility"
- "Professional workflow support"
- "Same API endpoints as real GCP"

---

## STEP 4: Internet Gateway Demo (Optional - 2 minutes)

```bash
# Show Internet Gateway metadata
curl -s http://localhost:8080/compute/v1/projects/test-project/global/internetGateways | python3 -m json.tool

# Show instance NAT configuration
curl -s http://localhost:8080/compute/v1/projects/test-project/zones/us-central1-a/instances/nat-test-vm | python3 -m json.tool

# Test outbound connectivity from container
docker exec gcp-vm-nat-test-vm curl -I https://www.google.com
```

**Talking Points:**
- "Internet Gateway for network visibility"
- "Control-plane metadata (API completeness)"
- "Docker bridge provides actual NAT"
- "Outbound connectivity works automatically"

---

## STEP 5: Architecture Overview (If Asked)

```
┌─────────────────────────────────────────────────┐
│           FRONTEND (React + Vite)               │
│         http://localhost:3000                   │
│  - Storage, Compute, VPC, IAM pages             │
│  - Modern UI with modals and auto-refresh       │
└───────────────────┬─────────────────────────────┘
                    │ HTTP API
┌───────────────────▼─────────────────────────────┐
│         BACKEND (FastAPI + Python)              │
│         http://localhost:8080                   │
│  - Storage API, Compute API, VPC API, IAM API   │
│  - Docker integration (docker-py)               │
│  - gcloud CLI compatible                        │
└─────┬──────────────────────────────────┬────────┘
      │                                  │
┌─────▼──────────────┐     ┌────────────▼─────────┐
│  PostgreSQL RDS    │     │  Docker Daemon       │
│  - Metadata        │     │  - VM Containers     │
│  - Persistence     │     │  - VPC Networks      │
└────────────────────┘     └──────────────────────┘
```

**Key Points:**
- "React frontend with TypeScript and Tailwind CSS"
- "FastAPI backend with SQLAlchemy ORM"
- "PostgreSQL for metadata, filesystem for object storage"
- "Real Docker containers and networks for compute/networking"

---

## 🚨 TROUBLESHOOTING

### Backend Won't Start
```bash
# Check if port 8080 is in use
lsof -i :8080
# Kill existing process if needed
pkill -f "python3 main.py"
# Restart
cd /home/ubuntu/gcs-stimulator/minimal-backend && python3 main.py
```

### Frontend Won't Start
```bash
# Check if port 3000 is in use
lsof -i :3000
# Kill existing process
pkill -f "vite"
# Restart
cd /home/ubuntu/gcs-stimulator/gcp-stimulator-ui && npm run dev
```

### Database Connection Error
```bash
# Test connection
cd /home/ubuntu/gcs-stimulator/minimal-backend
python3 -c "from database import SessionLocal; db=SessionLocal(); print('✅ Connected'); db.close()"
```

### Docker Issues
```bash
# Check Docker daemon
docker info
# Restart if needed
sudo systemctl restart docker
```

---

## 📊 DEMO METRICS (To Mention)

- **4 Major Services:** Storage, Compute, VPC, IAM
- **20+ API Endpoints:** Full CRUD operations
- **gcloud Compatible:** Professional workflow support
- **Real Docker Integration:** Containers and networks
- **Modern UI:** Consistent design, modals, auto-refresh
- **PostgreSQL Persistence:** All metadata persisted
- **Internet Gateway:** Network visibility and NAT

---

## ✅ FINAL CHECKLIST (Before Demo)

- [ ] Backend running (check http://localhost:8080/health)
- [ ] Frontend running (check http://localhost:3000)
- [ ] Docker daemon operational (docker ps)
- [ ] Test data exists (1 instance, 2 buckets, 2 networks)
- [ ] Browser open to http://localhost:3000
- [ ] Terminal ready for gcloud commands
- [ ] git status shows clean working tree

---

## 🎯 DEMO SUCCESS CRITERIA

✅ Show all 4 service pages working
✅ Demonstrate create/read/update/delete operations
✅ Show Docker container integration
✅ Execute gcloud commands successfully  
✅ Show Internet Gateway metadata
✅ Explain architecture clearly

---

## 💡 CLOSING STATEMENT

"This GCP emulator provides a complete local development environment with:
- Full-stack architecture (React + FastAPI + PostgreSQL)
- Real Docker integration for compute and networking
- gcloud CLI compatibility for professional workflows
- Modern, consistent UI across all services
- Complete API coverage for 4 major GCP services

All code is committed to git and ready for deployment!"

---

**⏰ DEMO TIME BUDGET:**
- Storage: 3 min
- Compute: 4 min
- VPC: 3 min
- IAM: 2 min
- gcloud: 3 min
- **TOTAL: ~15 minutes**

**GOOD LUCK! 🚀**
