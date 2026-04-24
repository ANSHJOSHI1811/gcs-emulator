# SKILLS_ROADMAP.md

**AI Agent Knowledge Requirements for GCS Emulator Development**

> **Purpose**: Enable AI agents to work confidently on this repo without repeated context  
> **Target**: Claude (Anthropic AI) or similar LLMs  
> **Last Updated**: April 24, 2026  

---

## 📚 Required Knowledge Areas

### 1️⃣ GCP Service Understanding

The AI agent MUST understand how each GCP service works in reality, then how we emulate it:

#### Google Cloud Storage (Cloud Storage)
**Real GCP Behavior**:
- Bucket: Global namespace storage container
- Objects: Files stored in buckets with key-value metadata
- Access control: IAM-based with per-object ACLs
- Regions: Multi-region, dual-region, or single-region buckets
- Versioning: Can track object version history
- Lifecycle: Auto-delete old versions after N days

**Our Emulation**:
- Buckets stored in database + filesystem
- Objects = database records + files on `/tmp/gcs-storage/`
- Docker containers CAN'T access objects (metadata only)
- Single-region only (no multi-region support yet)
- Version history: Stored in database, file overwrite on new version

**AI Agent Needs to Know**:
- ✅ How gcloud storage commands work (create bucket, upload object, etc)
- ✅ Our filesystem mapping: `/tmp/gcs-storage/{bucket_id}/{object_key}`
- ✅ Database state ≠ actual files (files ephemeral in containers)
- ✅ Where tests go: `tests/CloudTester/suites/storage/`
- ✅ API endpoints: `/api/v1/storage/buckets`, `/api/v1/storage/objects`

---

#### Google Compute Engine (Compute)
**Real GCP Behavior**:
- Instance: Virtual machine with vCPUs, memory, storage
- Machine types: Predefined (e2-micro, n1-standard-8) or custom
- Zones: Geographic locations (us-central1-a, us-central1-b)
- Instance states: PROVISIONING → RUNNING → STOPPED → TERMINATED
- Metadata server: Instance metadata (internal IP, labels, etc)
- SSH/RDP: Remote access to instances

**Our Emulation**:
- Instances = Docker containers (ubuntu:22.04)
- Machine types = Resource limits (CPU, memory) applied to containers
- Zones = Logical grouping (no real geography)
- Instance states = Docker container states
- Metadata server: Environment variables inside container
- SSH/RDP: Can't do real SSH, but gcloud cli works

**AI Agent Needs to Know**:
- ✅ Docker mapping: 1 instance = 1 container
- ✅ Container lifecycle: start = RUNNING, stop = STOPPED
- ✅ Metadata stored in database, exposed via env vars
- ✅ Machine types: limits apply to Docker container resources
- ✅ Zones are just database records (not real locations)
- ✅ API flow: Create instance → Create container → Store in DB
- ✅ State sync: Docker state → Database → Frontend polling

---

#### VPC Networks
**Real GCP Behavior**:
- VPC: Isolated private network with custom subnets
- Subnet: IPv4 CIDR block (10.0.0.0/16)
- Routes: Path to reach specific CIDR blocks
- Firewalls: Allow/deny traffic based on rules
- VPC Peering: Connect two VPCs

**Our Emulation**:
- VPC = Docker network (bridge driver)
- Subnet = CIDR metadata in database
- Routes = Table entries in database (not enforced)
- Firewalls = Rules stored in database (not enforced)
- VPC Peering: Database records only

**AI Agent Needs to Know**:
- ✅ VPC ≠ real network (rules not enforced in Docker)
- ✅ VPC = Docker network, Subnet = CIDR metadata
- ✅ Routes/Firewalls are simulated (rules stored but not applied)
- ✅ Instances connect to VPC via Docker network
- ✅ API stores config but Docker doesn't validate it

---

#### IAM (Identity & Access Management)
**Real GCP Behavior**:
- Service Account: Identity for applications/VMs
- Roles: Permissions (viewer, editor, admin, custom)
- Bindings: Grant role to service account on resource
- Keys: Authentication credentials (JSON keys)

**Our Emulation**:
- Service Account = Database record with email + unique ID
- Roles = Text entries (no real permission enforcement)
- Bindings = Database relationships (not enforced)
- Keys = Generated but not validated

**AI Agent Needs to Know**:
- ✅ Service accounts are simulated (no real auth)
- ✅ Email format: `{name}@{project}.iam.gserviceaccount.com`
- ✅ Unique ID: Auto-generated numeric ID
- ✅ Roles/bindings stored but not enforced anywhere
- ✅ Keys generated but not used for auth validation

---

#### Cloud Monitoring
**Real GCP Behavior**:
- Metrics: Time-series data (CPU, memory, etc)
- Dashboards: Visualize metrics
- Alerting: Trigger alerts when metrics exceed thresholds

**Our Emulation**:
- Metrics = Database records (name, type, labels)
- Values = Stored in metric_values table with timestamps
- Dashboards = Simple UI display
- Alerting = Not implemented yet

**AI Agent Needs to Know**:
- ✅ Metrics are generated manually (not auto-collected from containers)
- ✅ No real CPU/memory collection from Docker
- ✅ All metric values inserted via API
- ✅ Dashboard is read-only display

---

#### Autoscaling & Instance Groups
**Real GCP Behavior**:
- Instance Group: Set of identical instances
- Autoscaling: Auto-add/remove instances based on metrics
- Scaling Policy: Min/max instances, target metric value

**Our Emulation**:
- Instance Group = Database record with template
- Autoscaling = NOT WORKING YET (incomplete)
- Scaling Policy = Database record (not actually applied)

**AI Agent Needs to Know**:
- ⚠️ INCOMPLETE: Tests missing, needs work
- ✅ Instance group template stored in database
- ❌ Autoscaling NOT enforced (no auto create/delete)
- ❌ Needs implementation before using

---

#### GKE (Google Kubernetes Engine)
**Real GCP Behavior**:
- Cluster: Kubernetes cluster with worker nodes
- Nodes: VMs running Kubernetes
- Workloads: Pods, deployments, services

**Our Emulation**:
- Cluster = Database record (not working yet)
- Nodes = Docker containers
- Workloads = NOT IMPLEMENTED

**AI Agent Needs to Know**:
- ❌ GKE is NOT IMPLEMENTED
- ⚠️ Tests missing
- ⚠️ Do not use yet

---

### 2️⃣ gcloud CLI Understanding & Compatibility

**What the AI Agent Must Know About gcloud**:

The emulator wraps gcloud commands. Each command returns output that MUST match real GCP behavior.

#### gcloud Command Structure
```bash
gcloud {service} {resource} {action} [--flags]

Examples:
gcloud compute instances create my-instance --zone=us-central1-a --machine-type=e2-micro
gcloud storage buckets create gs://my-bucket --location=us-central1
gcloud compute networks create my-vpc --subnet-mode=custom
```

#### Current Compatibility Matrix

| Service | Command | Status | Coverage |
|---------|---------|--------|----------|
| **storage** | `gcloud storage buckets create/list/delete` | ✅ | 100% |
| **storage** | `gcloud storage objects upload/download/delete` | ✅ | 100% |
| **compute** | `gcloud compute instances create/list/delete/start/stop` | ✅ | 100% |
| **compute** | `gcloud compute machine-types list` | ✅ | 100% |
| **compute** | `gcloud compute zones list` | ✅ | 100% |
| **compute networks** | `gcloud compute networks create/list/delete` | ✅ | 100% |
| **compute networks** | `gcloud compute networks subnets create/list/delete` | ✅ | 100% |
| **compute routes** | `gcloud compute routes create/list/delete` | ✅ | 100% |
| **compute firewall** | `gcloud compute firewall-rules create/list/delete` | ⚠️ | 75% |
| **iam** | `gcloud iam service-accounts create/list/delete` | ✅ | 100% |
| **iam** | `gcloud projects add-iam-policy-binding` | ⚠️ | 50% |
| **monitoring** | `gcloud monitoring metrics create` | ⚠️ | 60% |
| **autoscaling** | `gcloud compute instance-groups managed create` | ⚠️ | 50% |

**Overall**: 87.5% compatible

**AI Agent Needs to Know**:
- ✅ Output format for each command (JSON vs table)
- ✅ Error messages must match GCP errors
- ✅ Some commands partially implemented (⚠️ flags may be missing)
- ✅ Some commands not implemented (❌)
- ✅ Test compatibility: `tests/CloudTester/wrappers/{service}.py`
- ✅ If command not working, check wrapper first

---

### 3️⃣ Repository Structure & Architecture

**The AI agent MUST understand the folder layout and data flow**:

#### Backend Data Flow
```
Request (Postman/Frontend)
    ↓
uvicorn (FastAPI server on :8080)
    ↓
Router (/api/v1/{service}/{resource})
    ↓
Handler (api/{service}.py function)
    ↓
Service Layer (services/{service}/ business logic)
    ↓
SQLAlchemy ORM (database.py models)
    ↓
PostgreSQL (RDS database)
    ↓ (also for Docker ops)
Docker Manager (docker_manager.py)
    ↓
Docker Daemon (on host machine)
    ↓
Docker Containers (ubuntu:22.04 instances)
    ↓
Response (JSON)
```

**AI Agent Needs to Know**:
- ✅ Separation of concerns: handlers vs services vs database
- ✅ All persistent state in database (PostgreSQL)
- ✅ Docker ops are side effects (container creation doesn't auto-update DB)
- ✅ Frontend polls backend for state updates
- ✅ State must be synced: Docker ↔ Database ↔ Frontend

---

#### Frontend Architecture
```
Browser (http://localhost:3000)
    ↓
React Router (routes defined in App.tsx)
    ↓
Page Component (src/pages/{Service}.tsx)
    ↓
API Client (src/api/{service}.ts with Axios)
    ↓
HTTP Request → Backend :8080
    ↓ ← HTTP Response
State/Context Update
    ↓
Re-render Components
    ↓
UI Displayed to User
```

**AI Agent Needs to Know**:
- ✅ Each service = separate page route
- ✅ API client functions in `src/api/{service}.ts`
- ✅ TypeScript types in `src/types/{service}.ts`
- ✅ UI components in `src/components/`
- ✅ Frontend is read-only (gets data from backend)

---

#### Database Schema Understanding
**AI Agent MUST understand key tables**:

```sql
-- Compute
instances
  ├─ id (UUID)
  ├─ name (string)
  ├─ zone_id (FK to zones)
  ├─ machine_type_id (FK to machine_types)
  ├─ state (PROVISIONING|RUNNING|STOPPED|TERMINATED)
  ├─ docker_container_id (Docker container ID)
  └─ metadata (JSON)

zones
  ├─ id
  ├─ name (us-central1-a)
  └─ region

machine_types
  ├─ id
  ├─ name (e2-micro)
  ├─ cpu
  └─ memory_gb

-- Network
networks
  ├─ id
  ├─ name
  ├─ cidr_block
  └─ docker_network_id

subnets
  ├─ id
  ├─ network_id (FK)
  ├─ cidr_range
  └─ secondary_ranges (JSON)

routes
  ├─ id
  ├─ subnet_id (FK)
  ├─ destination_cidr
  ├─ next_hop
  └─ priority

-- Storage
buckets
  ├─ id
  ├─ name
  ├─ location
  └─ versioning_enabled

objects
  ├─ id
  ├─ bucket_id (FK)
  ├─ key (path)
  ├─ size
  ├─ content_hash
  └─ metadata (JSON)

-- IAM
service_accounts
  ├─ id
  ├─ email (format: {name}@{project}.iam.gserviceaccount.com)
  ├─ unique_id (numeric)
  └─ project_id

-- Monitoring
metrics
  ├─ id
  ├─ name
  ├─ type
  └─ labels (JSON)

metric_values
  ├─ id
  ├─ metric_id (FK)
  ├─ value
  └─ timestamp
```

**AI Agent Needs to Know**:
- ✅ Primary key for each entity (usually UUID)
- ✅ Foreign keys (relationships between tables)
- ✅ Docker mappings: instances → container IDs, networks → network IDs
- ✅ State fields: instance.state, container state must match
- ✅ JSON fields store metadata (labels, tags, etc)

---

### 4️⃣ Testing Framework Understanding

**AI agent MUST understand test organization and execution**:

#### Test Directory Structure
```
tests/
  └─ CloudTester/
      ├─ suites/
      │   ├─ compute/
      │   │   ├─ test_gcloud_cli.py      # gcloud wrapper tests
      │   │   ├─ test_api.py              # API endpoint tests
      │   │   └─ test_integration.py      # End-to-end workflows
      │   ├─ storage/
      │   ├─ vpc/
      │   ├─ iam/
      │   ├─ monitoring/
      │   ├─ autoscaling/                # ⚠️ INCOMPLETE
      │   └─ gke/                        # ❌ MISSING
      │
      ├─ wrappers/
      │   ├─ compute.py                  # gcloud compute wrapper
      │   ├─ storage.py                  # gcloud storage wrapper
      │   ├─ vpc.py                      # gcloud compute networks wrapper
      │   ├─ iam.py                      # gcloud iam wrapper
      │   ├─ monitoring.py               # gcloud monitoring wrapper
      │   ├─ autoscaling.py              # ⚠️ INCOMPLETE
      │   └─ gke.py                      # ❌ NOT IMPLEMENTED
      │
      ├─ base/
      │   └─ test_base.py                # Shared test fixtures
      │
      └─ scripts/
          └─ run_full_suite.sh           # Run all tests

  └─ legacy/
      └─ [old test files to cleanup]
```

**AI Agent Needs to Know**:
- ✅ Three test layers: gcloud → API → integration
- ✅ gcloud tests validate wrapper compatibility (80% min coverage)
- ✅ API tests validate endpoints work (85% min coverage)
- ✅ Integration tests validate full workflows (75% min coverage)
- ✅ Use pytest fixtures for setup (database, Docker, etc)
- ✅ Mock external calls (don't actually call real gcloud)

#### Running Tests
```bash
# Run all tests for a service
pytest tests/CloudTester/suites/compute/ -v

# Run with coverage
pytest tests/CloudTester/suites/compute/ -v --cov

# Run specific test file
pytest tests/CloudTester/suites/compute/test_api.py -v

# Run specific test function
pytest tests/CloudTester/suites/compute/test_api.py::test_create_instance -v

# Watch mode (re-run on code change)
pytest-watch tests/CloudTester/suites/compute/ -n
```

**AI Agent Needs to Know**:
- ✅ Always run tests before committing
- ✅ Tests must pass before feature is "done"
- ✅ Coverage reports show what's not tested
- ✅ Flaky tests (sometimes pass, sometimes fail) are bugs

---

### 5️⃣ Docker Integration Understanding

**AI agent MUST understand how Docker emulates GCP**:

#### Docker Container Mapping
```
GCP Instance ↔ Docker Container

Instance Properties → Container Config:
  - name → container name
  - machine_type → CPU/memory limits
  - zone → (just metadata, no real effect)
  - startup_script → ENTRYPOINT/CMD
  - metadata → environment variables
  - image → ubuntu:22.04

Instance States → Container States:
  PROVISIONING → container starting
  RUNNING → container running
  STOPPED → container stopped/paused
  TERMINATED → container removed
```

#### Docker Network Mapping
```
VPC Network ↔ Docker Network

Network Properties → Docker Network:
  - name → docker network name
  - cidr_block → (metadata only, not enforced)
  - subnets → (metadata only, not enforced)
  
Instances in VPC → Containers in Docker network:
  - Instance.network_id → Docker container connected to network
  - Subnet CIDR → (not validated by Docker)
  - Firewall rules → (not enforced by Docker)
```

**AI Agent Needs to Know**:
- ✅ Containers ≠ real VMs (simplified emulation)
- ✅ Resource limits (CPU/memory) ARE enforced
- ✅ Network rules/firewalls are NOT enforced
- ✅ Docker network is bridge driver (not real networking)
- ✅ State synchronization: Docker → Database → Frontend
- ✅ If container dies, instance state should update in database
- ✅ All persistent data in database, containers are ephemeral

---

### 6️⃣ Development Workflow Understanding

**AI agent MUST follow our development process exactly**:

#### New Service Implementation Order (MANDATORY)
```
1️⃣ gcloud CLI Wrappers (FIRST)
   └─ Create: tests/CloudTester/wrappers/{service}.py
   └─ Test: pytest tests/CloudTester/suites/{service}/test_gcloud_cli.py
   └─ Must: ≥ 80% coverage of commands

2️⃣ Backend API (SECOND)
   └─ Create: minimal-backend/api/{service}.py
   └─ Create: minimal-backend/services/{service}/
   └─ Create: minimal-backend/database.py models
   └─ Test: pytest tests/CloudTester/suites/{service}/test_api.py
   └─ Must: ≥ 85% coverage of endpoints

3️⃣ Frontend UI (THIRD)
   └─ Create: gcp-stimulator-ui/src/pages/{Service}.tsx
   └─ Create: gcp-stimulator-ui/src/api/{service}.ts
   └─ Create: gcp-stimulator-ui/src/types/{service}.ts
   └─ Test: Manual testing in browser
   └─ Must: All CRUD operations work

4️⃣ Integration Tests (FOURTH)
   └─ Create: tests/CloudTester/suites/{service}/test_integration.py
   └─ Test: pytest tests/CloudTester/suites/{service}/ -v
   └─ Must: ≥ 85% overall coverage

5️⃣ Commit Only After All Pass
   └─ Git commit with proper message
   └─ Update: IMPLEMENTATION_TRACKER.md
```

**AI Agent Needs to Know**:
- ✅ MUST follow this order (never skip steps)
- ✅ Each phase has minimum quality thresholds
- ✅ Cannot commit if tests fail
- ✅ Code must be alphabetically ordered (functions)
- ✅ Documentation must be updated

---

#### Code Quality Standards
```
Python (Backend):
  - Functions: Alphabetically ordered
  - Docstrings: Required (description, args, returns, raises)
  - Type hints: Required (def func(x: str) -> bool:)
  - Linting: flake8 must pass
  - Formatting: black must pass

TypeScript (Frontend):
  - Files: lowercase-kebab-case.ts
  - Components: PascalCase.tsx
  - Types: Defined in src/types/{service}.ts
  - Docstrings: JSDoc comments required
  - Type safety: No 'any' types
  - Linting: ESLint must pass
  - Formatting: Prettier must pass
```

**AI Agent Needs to Know**:
- ✅ Code organization matters (alphabetical functions)
- ✅ Type safety is enforced (TypeScript, Python type hints)
- ✅ Documentation is mandatory
- ✅ All linting/formatting must pass before commit

---

## 🎯 How to Use This Document

### When Starting Work on a Service

**Example: Implementing Cloud Monitoring (hypothetically)**

The AI agent should:

1. **Read this document section**: "Google Cloud Monitoring (Cloud Monitoring)"
   - Understand: Real GCP behavior, our emulation, limitations

2. **Check compatibility matrix**: What gcloud commands need wrapping?
   - Understand: `gcloud monitoring metrics create`, `list`, `describe`

3. **Check test examples**: `tests/CloudTester/suites/monitoring/`
   - Understand: Test structure, fixtures, assertions

4. **Follow development workflow**:
   - Phase 1: Create gcloud wrappers → test
   - Phase 2: Create API endpoints → test
   - Phase 3: Create frontend UI → test
   - Phase 4: Create integration tests → test
   - Phase 5: Commit when all tests pass

5. **Update IMPLEMENTATION_TRACKER.md** after commit

---

### When Debugging a Service

The AI agent should:

1. **Check service status**: `CLAUDE.md` or `IMPLEMENTATION_TRACKER.md`
   - Is it ✅ COMPLETE or ⚠️ PARTIAL or ❌ MISSING?

2. **Check data flow**: Is the issue in gcloud/API/database/frontend?
   - Trace the request through backend architecture

3. **Check database state**: Is state correctly persisted?
   - Query database to verify data

4. **Check Docker state**: Do containers match database?
   - Run: `docker ps` to see containers
   - Compare with database instance records

5. **Check tests**: Do tests pass or fail?
   - If tests fail: Root cause in code
   - If tests pass but feature broken: Might be integration issue

---

### When Adding Tests

The AI agent should:

1. **Understand test structure**: gcloud → API → integration
   - Which layer is the bug in?

2. **Use test fixtures**: From `tests/CloudTester/base/test_base.py`
   - Database setup, Docker setup, cleanup

3. **Test all layers**: gcloud wrapper, API endpoint, database state
   - Don't test just the API if gcloud wrapper is wrong

4. **Set expectations correctly**: Real GCP behavior
   - If unsure, check real GCP documentation

5. **Measure coverage**: Coverage must be ≥ 85% overall
   - Use: `pytest --cov=../minimal-backend --cov-report=html`

---

## 📋 Knowledge Checklist for AI Agent

Before working on this repo, the AI agent should confirm understanding of:

- [ ] **Storage**: Buckets vs objects, filesystem mapping, versions
- [ ] **Compute**: Instances = containers, machine types = limits, zones = metadata
- [ ] **VPC**: VPC = Docker network, subnets/routes/firewall = metadata only
- [ ] **IAM**: Service accounts = database records, no real auth enforcement
- [ ] **Monitoring**: Metrics = manual inserts, not auto-collected
- [ ] **Autoscaling**: NOT IMPLEMENTED YET (don't use)
- [ ] **GKE**: NOT IMPLEMENTED YET (don't use)
- [ ] **gcloud CLI**: 87.5% compatible, wrappers in `tests/CloudTester/wrappers/`
- [ ] **Database**: Key tables (instances, networks, buckets, service_accounts, metrics)
- [ ] **Testing**: 3 layers (gcloud → API → integration), 85% min coverage
- [ ] **Docker**: Containers are ephemeral, database is persistent
- [ ] **Workflow**: gcloud → API → frontend → tests → commit (in that order)
- [ ] **Code style**: Alphabetical functions, type hints, docstrings required
- [ ] **Repository**: Backend on :8080, frontend on :3000, database RDS

---

## 🚀 Quick Reference

**When AI agent is asked to work on this repo, provide it with**:

1. **CLAUDE.md** - Current repo status
2. **DEVELOPMENT_RULES.md** - Workflow rules
3. **SKILLS_ROADMAP.md** - This document
4. **IMPLEMENTATION_TRACKER.md** - What's done, what's not
5. **Specific service folder** - If working on particular service

**AI Agent then should**:
- Read the relevant service section from SKILLS_ROADMAP
- Check DEVELOPMENT_RULES for workflow order
- Check IMPLEMENTATION_TRACKER for current status
- Propose approach before coding
- Follow testing requirements strictly
- Update documentation after completion

---

**Document Version**: 1.0  
**Last Updated**: April 24, 2026  
**Maintained by**: Development Team  
**For questions**: Check CLAUDE.md, DEVELOPMENT_RULES.md, or service-specific documentation
