# Project: GCS Emulator

A comprehensive **Google Cloud Platform (GCP) emulator** that simulates GCP services locally with Docker integration.

> **Last Updated**: April 24, 2026  
> **Status**: Active Development with Partial Implementation  
> **Current Focus**: Service Implementation & Testing Framework

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn
- **Database**: PostgreSQL (AWS RDS)
- **ORM**: SQLAlchemy
- **Container Runtime**: Docker API
- **API Format**: REST JSON

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **UI Components**: Lucide Icons, Headless UI
- **State Management**: React Context API
- **HTTP Client**: Axios
- **Forms**: React Hook Form + Zod validation
- **Routing**: React Router DOM v6

### Infrastructure
- **Backend Port**: 8080
- **Frontend Port**: 3000
- **Database**: PostgreSQL (AWS RDS)
- **Container Driver**: Docker (for VM emulation)
- **Storage**: File system + Database hybrid

### Testing & CLI
- **Testing Framework**: Pytest
- **gcloud CLI**: Emulation wrapper (87.5% compatibility)
- **Test Organization**: Service-based suites

---

## Directory Map

```
gcs-emulator/
├── minimal-backend/              # FastAPI Backend
│   ├── main.py                   # App entry, routes setup
│   ├── database.py               # SQLAlchemy models + DB setup
│   ├── docker_manager.py         # Docker container lifecycle
│   ├── api/                      # Route handlers
│   │   ├── storage.py           # Cloud Storage API ✅ WORKING
│   │   ├── compute.py           # Compute Engine/VM instances ✅ WORKING
│   │   ├── vpc.py               # VPC Networks ✅ WORKING
│   │   ├── routes.py            # Route Tables ✅ WORKING
│   │   ├── iam.py               # IAM Service Accounts ✅ WORKING
│   │   ├── projects.py          # Projects ✅ WORKING
│   │   ├── firewall.py          # Firewall rules ⚠️ PARTIAL
│   │   ├── autoscaling.py       # Autoscaling groups ⚠️ PARTIAL
│   │   ├── gke.py               # GKE clusters ⚠️ PARTIAL
│   │   ├── monitoring.py        # Cloud Monitoring ✅ WORKING
│   │   └── [more services]      # Additional services
│   ├── services/                # Business logic & domain services
│   │   ├── storage/             # ✅ COMPLETE
│   │   ├── compute/             # ✅ COMPLETE
│   │   ├── vpc/                 # ✅ COMPLETE
│   │   ├── iam/                 # ✅ COMPLETE
│   │   ├── monitoring/          # ✅ COMPLETE
│   │   ├── autoscaling/         # ⚠️ NEEDS TESTING
│   │   ├── gke/                 # ⚠️ NEEDS TESTING
│   │   └── [others]
│   ├── core/                    # Shared utilities
│   │   └── database.py          # DB connection helpers
│   └── requirements.txt
│
├── gcp-stimulator-ui/            # React Frontend (Vite)
│   ├── src/
│   │   ├── pages/               # Page components
│   │   │   ├── Storage.tsx      # ✅ WORKING
│   │   │   ├── Compute.tsx      # ✅ WORKING
│   │   │   ├── VPC.tsx          # ✅ WORKING
│   │   │   ├── IAM.tsx          # ✅ WORKING
│   │   │   ├── Monitoring.tsx   # ✅ WORKING
│   │   │   ├── Autoscaling.tsx  # ⚠️ PARTIAL
│   │   │   └── [more pages]
│   │   ├── components/          # Reusable UI components
│   │   ├── api/                 # API client functions (axios calls)
│   │   ├── contexts/            # React Context providers
│   │   ├── hooks/               # Custom React hooks
│   │   ├── layouts/             # Layout wrappers
│   │   ├── types/               # TypeScript interfaces
│   │   ├── utils/               # Helper functions
│   │   ├── config/              # Config (API base URL, etc.)
│   │   ├── App.tsx              # Main app component
│   │   └── main.tsx             # React entry point
│   ├── vite.config.ts           # Vite build config
│   ├── tailwind.config.js       # Tailwind CSS config
│   ├── tsconfig.json            # TypeScript config
│   ├── package.json             # Dependencies & scripts
│   └── nginx.conf               # Nginx proxy (for Docker deployment)
│
├── tests/                       # Test suites
│   ├── CloudTester/             # Main test framework
│   │   ├── suites/
│   │   │   ├── storage/         # ✅ COMPLETE
│   │   │   ├── compute/         # ✅ COMPLETE
│   │   │   ├── vpc/             # ✅ COMPLETE
│   │   │   ├── iam/             # ✅ COMPLETE
│   │   │   ├── monitoring/      # ⚠️ PARTIAL
│   │   │   ├── autoscaling/     # ❌ MISSING
│   │   │   └── gke/             # ❌ MISSING
│   │   ├── wrappers/            # gcloud CLI wrappers
│   │   ├── scripts/             # Test automation scripts
│   │   └── base/                # Base test classes
│   └── legacy/                  # Legacy test files (CLEANUP NEEDED)
│
├── docs/                        # Documentation
│   ├── archived/                # Old docs (CLEANUP NEEDED)
│   ├── DEVELOPMENT_RULES.md     # 🆕 Development guidelines
│   ├── SKILLS_ROADMAP.md        # 🆕 AI agent knowledge roadmap
│   └── SERVICE_TEMPLATES.md     # 🆕 New service checklist
│
├── patches/                     # Git patches for external libraries
├── CLAUDE.md                    # Project context (THIS FILE)
├── README.md                    # Main project README
├── CONTEXT_CHECKPOINT.md        # Context history
├── IMPLEMENTATION_TRACKER.md    # Feature tracking
├── pytest.ini                   # Pytest configuration
└── .env-gcloud                  # gcloud CLI environment config
```

---

## Service Implementation Status

| Service | Backend API | gcloud CLI | Frontend | Tests | Docker Support |
|---------|:-----------:|:---------:|:--------:|:-----:|:--------------:|
| **Storage** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Compute** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **VPC** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **IAM** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Monitoring** | ✅ | ⚠️ | ✅ | ⚠️ | ✅ |
| **Autoscaling** | ⚠️ | ⚠️ | ⚠️ | ❌ | ⚠️ |
| **GKE** | ⚠️ | ❌ | ⚠️ | ❌ | ⚠️ |
| **Firewall** | ⚠️ | ⚠️ | ⚠️ | ❌ | ⚠️ |

**Legend:**  
✅ = Complete & tested  
⚠️ = Partial implementation  
❌ = Not implemented / Missing tests  

---

## Architecture

### Backend Architecture
```
Request → uvicorn/FastAPI
         → FastAPI Router (/api/v1/...)
         → Handler (api/storage.py, etc)
         → Service Layer (services/storage/...)
         → Database (SQLAlchemy ORM)
         → Docker Manager (if container op needed)
         → Response (JSON)

Data Flow:
  1. API receives request
  2. Route handler validates input
  3. Service layer executes business logic
  4. Database persists state (SQLAlchemy ORM)
  5. Docker manager manages containers (if VM-related)
  6. Response returned to client
```

### Frontend Architecture
```
Browser → Vite dev server / Nginx (prod)
        → React Router
        → Page Component
        → API Client (axios)
        → (HTTP) → Backend :8080
        → Response handling
        → Context/State update
        → DOM rendering
```

### Docker Integration (How Emulation Works)
```
GCP Concept          →  Docker Mapping
─────────────────────────────────────
VM Instance          →  Docker Container (ubuntu:22.04)
VPC Network          →  Docker Network (bridge)
Machine Type         →  Container resource limits
VM State             →  Container state
Instance Metadata    →  Environment variables

Database tracks:
  - Container ID ↔ Instance ID mapping
  - Network ID ↔ Docker Network mapping
  - State synchronization
```

### Database Schema (Key Tables)
```
Compute:
  - instances (zone, state, machine_type, docker_container_id)
  - machine_types (name, cpu, memory)
  - zones (name, region)

Network:
  - networks (name, cidr_block)
  - subnets (network_id, cidr_range)
  - routes (subnet_id, destination, next_hop)
  - firewall_rules (network_id, direction, priority)

Storage:
  - buckets (name, region, location)
  - objects (bucket_id, name, size, hash, metadata)

IAM:
  - service_accounts (email, unique_id, project_id)
  - iam_bindings (service_account_id, role, resource)

Monitoring:
  - metrics (name, type, labels)
  - metric_values (metric_id, value, timestamp)

Autoscaling:
  - instance_groups (name, template, min_size, max_size)
  - autoscaling_policies (group_id, metric, target_value)
```

---

## Development Workflow

### Local Development Setup
```bash
# Terminal 1: Backend
cd minimal-backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Terminal 2: Frontend
cd gcp-stimulator-ui
npm install
npm run dev

# Terminal 3: Database (if local)
# Ensure PostgreSQL is running with DATABASE_URL set

# Terminal 4: Testing (as needed)
cd tests
python -m pytest CloudTester/suites/{service}/ -v
```

### Access Points
- Frontend: http://localhost:3000
- Backend API: http://localhost:8080
- Swagger Docs: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

---

## Environment Variables

### Backend (.env or export)
```ini
DATABASE_URL=postgresql://user:pass@host:5432/gcs_emulator
DOCKER_HOST=unix:///var/run/docker.sock
DOCKER_TIMEOUT=30
```

### Frontend (.env.local)
```ini
VITE_API_BASE_URL=http://localhost:8080
VITE_API_TIMEOUT=30000
```

### gcloud CLI (.env-gcloud)
```ini
GCLOUD_PROJECT=test-project
GCLOUD_REGION=us-central1
GCLOUD_ZONE=us-central1-a
```

---

## Known Issues & Gotchas

### Critical
1. **Docker Daemon Required**: Backend fails if Docker daemon is not running
   - Check: `docker ps`
   - Fix: Start Docker daemon

2. **Database Connection**: All requests fail without PostgreSQL
   - Check: `psql $DATABASE_URL`
   - Fix: Ensure RDS or local PostgreSQL is running

3. **Port Conflicts**: Ports 3000 & 8080 must be free
   - Check: `lsof -i :3000 && lsof -i :8080`
   - Fix: Kill conflicting processes

### Important
4. **gcloud CLI Compatibility**: Currently 87.5% compatible
   - Some commands may return different output
   - See: `tests/CloudTester/wrappers/` for compatibility matrix

5. **File Storage**: Objects stored in `/tmp/gcs-storage/` (ephemeral)
   - In containers, data is lost on restart
   - Metadata persists in database

6. **Hot Reload Issues**: uvicorn --reload can cause Docker manager issues
   - Workaround: Full restart if container ops fail

7. **CORS Configuration**: Frontend needs CORS for cross-origin requests
   - Check: `minimal-backend/main.py` for CORS setup

8. **Docker Network Mode**: Only bridge driver supported
   - Host network mode will cause issues

---

## Recent Commits & Features

✅ Cloud Monitoring page with metric creation  
✅ Instance groups and enhanced autoscaling UI  
✅ Secret Manager, Autoscaling, Pub/Sub in service catalog  
✅ Service catalog improvements  
✅ Sidebar and proxy fixes  
✅ Monitoring enhancements  

---

## Commands Reference

### Backend
```bash
cd minimal-backend

# Install dependencies
pip install -r requirements.txt

# Run dev server (hot-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Run production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

# Check API docs
curl http://localhost:8080/docs

# Run linting
flake8 . --max-line-length=100
black . --check
```

### Frontend
```bash
cd gcp-stimulator-ui

# Install dependencies
npm install

# Dev server (hot-reload)
npm run dev

# Build production
npm run build

# Lint
npm run lint

# Type check
npm run type-check

# Preview production build
npm run preview
```

### Testing
```bash
cd tests

# Full test suite
bash run_full_suite.sh

# Specific service
cd CloudTester && python -m pytest suites/compute/ -v

# With coverage
pytest --cov=../minimal-backend --cov-report=html

# Watch mode
pytest-watch suites/storage/ -n

# Specific test file
pytest suites/compute/test_instances.py::test_create_instance -v

# gcloud CLI compatibility tests
python -m pytest suites/gcloud_wrappers/ -v
```

### Utilities
```bash
# Test database connectivity
bash test-connectivity.sh

# Generate project context
python generate_context.py

# Check Docker connectivity
docker ps

# List emulated instances
curl http://localhost:8080/api/v1/compute/instances
```

---

## Important Notes for AI Agent

### Context Understanding
When working on THIS repo, the AI agent needs to know:

1. **Emulation Model**: Docker containers = GCP VMs. Docker networks = VPCs
2. **Service Pattern**: Every service needs:
   - Database models (database.py)
   - Service layer (services/{service}/)
   - API routes (api/{service}.py)
   - Frontend page (src/pages/{Service}.tsx)
   - Tests (tests/CloudTester/suites/{service}/)
   - gcloud CLI wrapper (tests/CloudTester/wrappers/{service}.py)

3. **Testing Priority**: gcloud CLI compatibility → API tests → Docker container tests

4. **State Synchronization**: Database ↔ Docker ↔ Frontend must stay in sync

5. **Broken Services**: Autoscaling, GKE, Firewall need tests before considering "done"

---

## Next Steps (Immediate)

1. ✅ Update this CLAUDE.md (you're doing it!)
2. ⏳ Create DEVELOPMENT_RULES.md (strict workflow)
3. ⏳ Create SKILLS_ROADMAP.md (AI agent knowledge requirements)
4. ⏳ Create SERVICE_TEMPLATES.md (checklist for new services)
5. ⏳ Cleanup `tests/legacy/` and `docs/archived/`
6. ⏳ Add missing tests for Autoscaling & GKE
7. ⏳ Update gcloud CLI compatibility to 100%

---

**Current Branch**: `feature/cloud-monitoring`  
**Last Commit**: feat: add metric creation page and monitoring enhancements  
**Maintenance Mode**: Active - requires weekly testing runs
