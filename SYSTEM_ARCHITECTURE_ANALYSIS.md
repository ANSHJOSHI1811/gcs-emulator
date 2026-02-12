# GCP Simulator - System Architecture Analysis
**Date:** February 12, 2026  
**Analysis Type:** Minimal Working Components, Interconnectivity & Gaps

---

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Smallest Components (Atoms)](#smallest-components-atoms)
3. [Component Interconnectivity](#component-interconnectivity)
4. [Data Flow Diagrams](#data-flow-diagrams)
5. [Identified Gaps & Issues](#identified-gaps--issues)
6. [Dependency Tree](#dependency-tree)
7. [Recommendations](#recommendations)

---

## 1. Architecture Overview

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  React Frontend (Port 3000) - TypeScript + Vite + Tailwind  │
│  ├─ Pages (UI Views)                                         │
│  ├─ Components (Reusable UI)                                 │
│  ├─ API Clients (HTTP requests)                              │
│  └─ Contexts (State management)                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓ HTTP/REST API
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  FastAPI Backend (Port 8080) - Python                       │
│  ├─ API Routes (Endpoints)                                   │
│  ├─ Business Logic                                           │
│  ├─ Docker Manager (Container operations)                    │
│  └─ IP Manager (Network allocation)                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓ SQLAlchemy ORM
┌─────────────────────────────────────────────────────────────┐
│                     PERSISTENCE LAYER                        │
│  SQLite/PostgreSQL Database                                  │
│  ├─ 17 Data Models                                           │
│  └─ Relationships & Constraints                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓ Container Runtime
┌─────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                        │
│  Docker Engine (Local)                                       │
│  ├─ Containers (= VM Instances)                              │
│  ├─ Networks (= VPC Networks)                                │
│  └─ Volumes (= Persistent Disks)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Smallest Components (Atoms)

### 2.1 Database Models (17 Models)

#### ✅ **Fully Implemented & Working**

1. **Project** (`projects` table)
   - Atomic unit: GCP Project
   - Fields: `id`, `name`, `project_number`, `location`, `created_at`
   - Purpose: Top-level resource container
   - Status: ✅ Working

2. **Zone** (`zones` table)
   - Atomic unit: Compute zone
   - Fields: `id`, `name`, `region`, `status`, `description`
   - Purpose: Geographic location for resources
   - Status: ✅ Working (7 zones initialized)

3. **MachineType** (`machine_types` table)
   - Atomic unit: VM hardware configuration
   - Fields: `id`, `name`, `zone`, `guest_cpus`, `memory_mb`
   - Purpose: Define VM sizes
   - Status: ✅ Working (42 types: 6 types × 7 zones)

4. **Instance** (`instances` table)
   - Atomic unit: Virtual Machine
   - Fields: `id`, `name`, `project_id`, `zone`, `machine_type`, `status`, `container_id`, `internal_ip`, `network_url`, `subnet`
   - Purpose: VM instance mapped to Docker container
   - Status: ✅ Working

5. **Network** (`networks` table)
   - Atomic unit: VPC Network
   - Fields: `id`, `name`, `project_id`, `docker_network_name`, `auto_create_subnetworks`, `cidr_range`
   - Purpose: Virtual private cloud mapped to Docker network
   - Status: ✅ Working

6. **Subnet** (`subnets` table)
   - Atomic unit: IP subnet within VPC
   - Fields: `id`, `name`, `network`, `region`, `ip_cidr_range`, `gateway_ip`, `next_available_ip`
   - Purpose: IP address allocation pool
   - Status: ✅ Working

7. **Route** (`routes` table)
   - Atomic unit: Network route
   - Fields: `id`, `name`, `network`, `project_id`, `dest_range`, `priority`, `next_hop_gateway`, `next_hop_ip`, `next_hop_instance`, `next_hop_network`
   - Purpose: Traffic routing rules
   - Status: ✅ Working

8. **Firewall** (`firewalls` table)
   - Atomic unit: Network security rule
   - Fields: `id`, `name`, `network`, `project_id`, `direction`, `priority`, `source_ranges`, `allowed`, `denied`
   - Purpose: Network access control
   - Status: ⚠️ Schema exists, NO DEFAULT RULES CREATED

9. **Bucket** (`buckets` table)
   - Atomic unit: Storage bucket
   - Fields: `id`, `name`, `project_id`, `location`, `storage_class`, `created_at`
   - Purpose: Object storage container
   - Status: ✅ Working

10. **Object** (`objects` table)
    - Atomic unit: Stored file/blob
    - Fields: `id`, `name`, `bucket_id`, `size`, `content_type`, `data`, `generation`, `version_id`
    - Purpose: Actual stored data
    - Status: ✅ Working

11. **SignedUrlSession** (`signed_url_sessions` table)
    - Atomic unit: Temporary access token
    - Fields: `token`, `bucket_name`, `object_name`, `expires_at`
    - Purpose: Time-limited object access
    - Status: ✅ Working

#### ⚠️ **Partially Implemented**

12. **ServiceAccount** (`service_accounts` table)
    - Atomic unit: IAM service account
    - Fields: `id`, `project_id`, `email`, `display_name`, `unique_id`
    - Purpose: Service identity
    - Status: ⚠️ Schema exists, NO ACCOUNTS CREATED

13. **VPCPeering** (`vpc_peerings` table)
    - Atomic unit: VPC connection
    - Fields: `id`, `name`, `project_id`, `local_network`, `peer_network`, `state`
    - Purpose: Connect two VPCs
    - Status: ⚠️ Backend works, UI REMOVED

#### ❌ **Deprecated (To Be Removed)**

14. **RouteTable** (`route_tables` table)
    - Purpose: Route grouping (AWS-style)
    - Status: ❌ DEPRECATED - UI removed, backend still exists
    - Action: Remove from database.py

15. **SubnetRouteTableAssociation** (`subnet_route_table_associations` table)
    - Purpose: Link subnets to route tables
    - Status: ❌ DEPRECATED - Not used in GCP model
    - Action: Remove from database.py

---

### 2.2 Backend API Modules (9 Modules)

#### Core API Files

1. **`compute.py`** ✅
   - Endpoints: 8
   - Functions: `list_zones()`, `list_machine_types()`, `list_instances()`, `get_instance()`, `create_instance()`, `start_instance()`, `stop_instance()`, `delete_instance()`
   - Dependencies: `database.Instance`, `database.Zone`, `database.MachineType`, `docker_manager.py`
   - Status: ✅ Fully working

2. **`vpc.py`** ✅
   - Endpoints: 10
   - Functions: `list_networks()`, `get_network()`, `create_network()`, `delete_network()`, `list_subnets()`, `create_subnet()`, `delete_subnet()`, `ensure_default_network()`
   - Dependencies: `database.Network`, `database.Subnet`, `docker.py`, `ip_manager.py`
   - Status: ✅ Fully working

3. **`routes.py`** ✅
   - Endpoints: 5 (routes) + 5 (route tables - deprecated)
   - Functions: `list_routes()`, `get_route()`, `create_route()`, `delete_route()`
   - Dependencies: `database.Route`, `database.RouteTable` (deprecated)
   - Status: ✅ Routes working, ⚠️ Route tables deprecated

4. **`firewall.py`** ⚠️
   - Endpoints: 4
   - Functions: `list_firewalls()`, `get_firewall()`, `create_firewall()`, `delete_firewall()`
   - Dependencies: `database.Firewall`
   - Status: ⚠️ API works, NO DEFAULT RULES

5. **`storage.py`** ✅
   - Endpoints: 13
   - Functions: `list_buckets()`, `create_bucket()`, `delete_bucket()`, `list_objects()`, `upload_object()`, `get_object()`, `delete_object()`, `generate_signed_url()`, `download_via_signed_url()`
   - Dependencies: `database.Bucket`, `database.Object`, `database.SignedUrlSession`
   - Status: ✅ Fully working

6. **`projects.py`** ✅
   - Endpoints: 3
   - Functions: `list_projects()`, `create_project()`, `delete_project()`
   - Dependencies: `database.Project`
   - Status: ✅ Fully working

7. **`iam.py`** ⚠️
   - Endpoints: 3
   - Functions: `list_service_accounts()`, `create_service_account()`, `get_service_account()`
   - Dependencies: `database.ServiceAccount`
   - Status: ⚠️ API works, NO ACCOUNTS INITIALIZED

8. **`peering.py`** ⚠️
   - Endpoints: 5
   - Functions: `create_peering()`, `list_peerings()`, `get_peering()`, `delete_peering()`, `update_peering()`
   - Dependencies: `database.VPCPeering`, `peering_manager.py`
   - Status: ⚠️ Backend works, UI REMOVED

9. **`main.py`** ✅
   - Purpose: Application entry point
   - Functions: `root()`, `health()`, `init_zones_and_machine_types()`, `startup_event()`
   - Status: ✅ Working

#### Supporting Modules

10. **`docker_manager.py`** ✅
    - Functions: `create_container()`, `stop_container()`, `start_container()`, `delete_container()`, `get_container_status()`
    - Status: ✅ Working

11. **`ip_manager.py`** ✅
    - Functions: `get_gateway_ip()`, `get_ip_at_offset()`, IP allocation logic
    - Status: ✅ Working

12. **`peering_manager.py`** ⚠️
    - Functions: `validate_cidrs_dont_overlap()`, `connect_docker_networks()`, `disconnect_docker_networks()`
    - Status: ⚠️ Working but UI removed

13. **`database.py`** ✅
    - Purpose: SQLAlchemy models & connection
    - Status: ✅ Working (with 2 deprecated models)

---

### 2.3 Frontend Components

#### Pages (16 Active Pages)

1. **HomePage.tsx** ✅ - Landing page
2. **StorageDashboardPage.tsx** ✅ - Storage overview
3. **BucketListPage.tsx** ✅ - List buckets
4. **BucketDetails.tsx** ✅ - Bucket details & objects
5. **ObjectDetailsPage.tsx** ✅ - Object metadata
6. **EventsPage.tsx** ✅ - Activity log
7. **SettingsPage.tsx** ✅ - Storage settings
8. **ComputeDashboardPage.tsx** ✅ - VM instances list
9. **CreateInstancePage.tsx** ✅ - Create VM form
10. **VPCDashboardPage.tsx** ✅ - VPC networks overview
11. **NetworksPage.tsx** ✅ - Not used (redirects to VPCDashboardPage)
12. **SubnetsPage.tsx** ✅ - Subnets management
13. **FirewallsPage.tsx** ✅ - Firewall rules
14. **RoutesPage.tsx** ✅ - Routes management
15. **IAMDashboardPage.tsx** ✅ - IAM overview
16. **PlaceholderServicePage.tsx** ✅ - Generic service page

#### API Clients (11 Client Files)

1. **`client.ts`** ✅ - Axios base client
2. **`buckets.ts`** ✅ - Bucket API calls
3. **`objects.ts`** ✅ - Object API calls
4. **`uploadApi.ts`** ✅ - Upload handling
5. **`objectVersionsApi.ts`** ✅ - Versioning
6. **`signedUrlApi.ts`** ✅ - Signed URLs
7. **`storageStats.ts`** ✅ - Storage metrics
8. **`lifecycle.ts`** ✅ - Lifecycle policies
9. **`events.ts`** ✅ - Activity events
10. **`health.ts`** ✅ - Health checks
11. **`networking.ts`** ✅ - VPC/Compute API calls

#### Reusable Components (23 Components)

- **UI Components**: Badge, Alert, Button, Page, Card, Spinner
- **Common Components**: EmptyState, Pagination, SearchInput, DropdownFilter, SecurityBanner, DeleteConfirmModal
- **Form Components**: FormFields, Input, Select, Modal
- **Domain Components**: BucketCard, CreateBucketModal, UploadObjectModal, BucketSettingsModal, CreateLifecycleRuleModal
- **Navigation Components**: DynamicSidebar, CloudConsoleTopNav, ServicesMegaMenu, ProjectSelector

---

## 3. Component Interconnectivity

### 3.1 Request Flow: Create VM Instance

```
User Action (UI)
      ↓
ComputeDashboardPage.tsx (React Component)
      ↓
networking.ts (API Client)
      │
      └─→ apiClient.post('/compute/v1/projects/{project}/zones/{zone}/instances')
            ↓
      HTTP Request (Port 3000 → Port 8080)
            ↓
FastAPI Router (compute.py)
      │
      ├─→ Validate request body
      ├─→ Check Zone exists (database.Zone)
      ├─→ Check Network exists (database.Network)
      ├─→ Get Subnet for IP allocation (database.Subnet)
      │
      └─→ docker_manager.create_container()
           │
           ├─→ Docker API: Create container
           ├─→ Attach to Docker network
           └─→ Start container
                ↓
      Create Instance record (database.Instance)
            ↓
      SQLAlchemy ORM
            ↓
      SQLite/PostgreSQL: INSERT INTO instances
            ↓
      Return Instance JSON
            ↓
      HTTP Response
            ↓
ComputeDashboardPage.tsx receives data
      ↓
React renders new instance in UI
```

### 3.2 Data Dependencies

#### Instance Creation Dependencies

```
Instance
  ├─ Requires: Project ✅
  ├─ Requires: Zone ✅
  ├─ Requires: MachineType ✅
  ├─ Requires: Network ✅
  ├─ Requires: Subnet ✅ (for IP allocation)
  └─ Creates: Docker Container ✅
```

#### Network Creation Dependencies

```
Network
  ├─ Requires: Project ✅
  ├─ Creates: Docker Network ✅
  ├─ Auto-creates: Default route (0.0.0.0/0) ✅
  └─ Should create: Default subnet ⚠️ (missing for default network)
```

#### Route Creation Dependencies

```
Route
  ├─ Requires: Network ✅
  ├─ Requires: Project ✅
  ├─ Requires: Destination CIDR ✅
  ├─ Requires: Next Hop (gateway/IP/instance/network) ✅
  └─ Optional: Priority (default: 1000) ✅
```

#### Bucket Creation Dependencies

```
Bucket
  ├─ Requires: Project ✅
  ├─ Requires: Unique name ✅
  ├─ Optional: Location (default: "US") ✅
  └─ Optional: Storage class (default: "STANDARD") ✅
```

### 3.3 Cross-Module Dependencies

```
main.py
  ├─→ imports compute.router
  ├─→ imports vpc.router
  ├─→ imports routes.router
  ├─→ imports firewall.router
  ├─→ imports peering.router
  ├─→ imports storage.router
  ├─→ imports projects.router
  ├─→ imports iam.router
  └─→ calls init_zones_and_machine_types() on startup

compute.py
  ├─→ uses database.Instance
  ├─→ uses database.Zone
  ├─→ uses database.MachineType
  ├─→ uses database.Network
  ├─→ uses database.Subnet
  └─→ uses docker_manager

vpc.py
  ├─→ uses database.Network
  ├─→ uses database.Subnet
  ├─→ uses database.Route
  ├─→ uses docker (Docker SDK)
  └─→ uses ip_manager

routes.py
  ├─→ uses database.Route
  ├─→ uses database.RouteTable (deprecated)
  └─→ uses database.SubnetRouteTableAssociation (deprecated)

storage.py
  ├─→ uses database.Bucket
  ├─→ uses database.Object
  └─→ uses database.SignedUrlSession

iam.py
  ├─→ uses database.ServiceAccount
  └─→ uses database.Project

firewall.py
  ├─→ uses database.Firewall
  └─→ uses database.Network

peering.py
  ├─→ uses database.VPCPeering
  ├─→ uses database.Network
  ├─→ uses database.Route
  └─→ uses peering_manager
```

### 3.4 Frontend → Backend API Mapping

| Frontend Page | API Client | Backend Endpoint | Database Model |
|--------------|------------|------------------|----------------|
| ComputeDashboardPage | networking.ts | `/compute/v1/projects/{}/zones/{}/instances` | Instance |
| CreateInstancePage | networking.ts | `POST /compute/v1/projects/{}/zones/{}/instances` | Instance, Zone, MachineType |
| VPCDashboardPage | networking.ts | `/compute/v1/projects/{}/global/networks` | Network |
| SubnetsPage | networking.ts | `/compute/v1/projects/{}/aggregated/subnetworks` | Subnet |
| FirewallsPage | networking.ts | `/compute/v1/projects/{}/global/firewalls` | Firewall |
| RoutesPage | networking.ts | `/compute/v1/projects/{}/global/routes` | Route |
| BucketListPage | buckets.ts | `/storage/v1/b` | Bucket |
| BucketDetails | objects.ts | `/storage/v1/b/{bucket}/o` | Object |
| IAMDashboardPage | client.ts | `/v1/projects/{}/serviceAccounts` | ServiceAccount |

---

## 4. Data Flow Diagrams

### 4.1 VM Instance Lifecycle

```
CREATE
  ↓
[Database: Instance record created]
  ↓
[Docker: Container created & started]
  ↓
[Status: RUNNING]
  │
  ├─→ STOP → [Docker: Container stopped] → [Status: TERMINATED]
  │            ↓
  │            START → [Docker: Container started] → [Status: RUNNING]
  │
  └─→ DELETE → [Docker: Container removed] → [Database: Record deleted]
```

### 4.2 Network & Subnet Relationship

```
Project
  │
  └─→ Network (VPC)
        ├─→ cidr_range: 10.128.0.0/16
        │
        ├─→ Docker Network: project-alpha-default
        │
        ├─→ Subnet 1 (us-central1)
        │    ├─→ ip_cidr_range: 10.128.0.0/20
        │    ├─→ gateway_ip: 10.128.0.1
        │    └─→ next_available_ip: 2 → Increments on each VM
        │
        ├─→ Subnet 2 (us-east1)
        │    └─→ ip_cidr_range: 10.128.16.0/20
        │
        ├─→ Routes
        │    ├─→ default-route-default (0.0.0.0/0 → default-internet-gateway)
        │    └─→ route-subnet-us-central1 (10.128.0.0/20 → local)
        │
        └─→ Firewall Rules
             ├─→ ⚠️ MISSING: allow-ssh
             ├─→ ⚠️ MISSING: allow-http
             └─→ ⚠️ MISSING: allow-internal
```

### 4.3 Storage Hierarchy

```
Project
  │
  └─→ Buckets
        │
        ├─→ Bucket 1 (test-bucket)
        │    ├─→ location: US
        │    ├─→ storageClass: STANDARD
        │    │
        │    └─→ Objects
        │         ├─→ Object 1 (file1.txt)
        │         │    ├─→ data: BLOB
        │         │    ├─→ size: 1024
        │         │    ├─→ content_type: text/plain
        │         │    ├─→ generation: 1
        │         │    └─→ versions: [version_1, version_2]
        │         │
        │         └─→ Object 2 (file2.jpg)
        │
        └─→ Bucket 2 (prod-bucket)
```

---

## 5. Identified Gaps & Issues

### 5.1 Critical Gaps (HIGH PRIORITY) 🔴

#### Gap #1: No Default Firewall Rules
- **Component**: `firewall.py` + `database.Firewall`
- **Issue**: Firewall table is empty, no default rules created
- **Impact**: HIGH - Cannot simulate realistic network security
- **Expected**:
  ```python
  # Default rules that should exist:
  1. allow-ssh (tcp:22, source: 0.0.0.0/0)
  2. allow-http (tcp:80, source: 0.0.0.0/0)
  3. allow-https (tcp:443, source: 0.0.0.0/0)
  4. allow-internal (all, source: 10.0.0.0/8)
  5. allow-icmp (icmp, source: 0.0.0.0/0)
  ```
- **Fix**: Add `init_default_firewall_rules()` in `main.py` startup

#### Gap #2: No Service Accounts Initialized
- **Component**: `iam.py` + `database.ServiceAccount`
- **Issue**: ServiceAccount table is empty
- **Impact**: MEDIUM - IAM features cannot be tested
- **Expected**:
  ```python
  # Default service accounts per project:
  1. {project-number}-compute@developer.gserviceaccount.com
  2. {project-id}@appspot.gserviceaccount.com
  3. service-{project-number}@storage-transfer-service.iam.gserviceaccount.com
  ```
- **Fix**: Add `init_default_service_accounts()` in `main.py` startup

#### Gap #3: Missing Default Subnet for Default Network
- **Component**: `vpc.py` + `database.Subnet`
- **Issue**: Default network has no subnet, VMs can't be created
- **Impact**: HIGH - Breaks VM creation in default network
- **Expected**: Default subnet `default-subnet-us-central1` (10.128.0.0/20)
- **Fix**: Call `ensure_default_subnet()` in `ensure_default_network()`

### 5.2 Moderate Gaps (MEDIUM PRIORITY) 🟡

#### Gap #4: Deprecated RouteTable Models
- **Component**: `database.py` (RouteTable, SubnetRouteTableAssociation)
- **Issue**: Models exist but not used (AWS-style, not GCP)
- **Impact**: LOW - Code bloat, confusion
- **Fix**: Remove from `database.py`

#### Gap #5: VPC Peering Backend Without UI
- **Component**: `peering.py` exists, UI removed
- **Issue**: Backend API accessible but no UI
- **Impact**: LOW - Advanced feature not needed
- **Fix**: Either remove backend or keep dormant

#### Gap #6: gcloud CLI Compatibility
- **Component**: All API endpoints
- **Issue**: API paths match GCP but authentication missing
- **Impact**: MEDIUM - gcloud commands work partially
- **Fix**: Add mock authentication or document limitations

### 5.3 Minor Gaps (LOW PRIORITY) 🟢

#### Gap #7: No Instance Groups Backend
- **Component**: UI link exists (`/services/compute-engine/groups`)
- **Issue**: No backend implementation
- **Impact**: LOW - Advanced feature
- **Fix**: Remove link or implement feature

#### Gap #8: No Disks Management
- **Component**: UI link exists (`/services/compute-engine/disks`)
- **Issue**: No backend implementation
- **Impact**: LOW - All VMs have ephemeral disks
- **Fix**: Remove link or implement persistent disks

#### Gap #9: Large Frontend Bundle
- **Component**: `vite.config.ts`
- **Issue**: Bundle size 665 kB (warning: > 500 kB)
- **Impact**: LOW - Performance
- **Fix**: Implement React.lazy() code-splitting

#### Gap #10: No Monitoring/Logging
- **Component**: None (feature not started)
- **Issue**: No metrics, logs, or monitoring
- **Impact**: LOW - Nice to have
- **Fix**: Add monitoring API + UI

---

## 6. Dependency Tree

### Backend Module Dependencies

```
main.py
├── compute.py
│   ├── database.py (Instance, Zone, MachineType, Network, Subnet)
│   ├── docker_manager.py
│   └── ip_manager.py
│
├── vpc.py
│   ├── database.py (Network, Subnet, Route)
│   ├── docker (Docker SDK)
│   └── ip_manager.py
│
├── routes.py
│   └── database.py (Route, RouteTable ⚠️, SubnetRouteTableAssociation ⚠️)
│
├── firewall.py
│   └── database.py (Firewall)
│
├── storage.py
│   └── database.py (Bucket, Object, SignedUrlSession)
│
├── projects.py
│   └── database.py (Project)
│
├── iam.py
│   └── database.py (ServiceAccount)
│
└── peering.py ⚠️
    ├── database.py (VPCPeering, Network, Route)
    └── peering_manager.py

database.py
└── sqlalchemy (SQLAlchemy ORM)

docker_manager.py
└── docker (Docker SDK)

ip_manager.py
└── ipaddress (Python stdlib)

peering_manager.py
└── docker (Docker SDK)
```

### Frontend Component Dependencies

```
App.tsx (Router)
├── CloudConsoleLayout
│   ├── CloudConsoleTopNav
│   │   ├── ProjectSelector
│   │   └── ServicesMegaMenu
│   └── DynamicSidebar
│
├── Pages (16 pages)
│   ├── ComputeDashboardPage
│   │   ├── networking.ts (API client)
│   │   └── Modal, FormFields
│   │
│   ├── VPCDashboardPage
│   │   ├── networking.ts
│   │   └── Chart components
│   │
│   ├── BucketListPage
│   │   ├── buckets.ts (API client)
│   │   └── BucketCard
│   │
│   └── (other pages...)
│
└── Contexts
    ├── AppContext
    └── ProjectContext

API Clients
├── client.ts (Axios instance)
├── networking.ts → client.ts
├── buckets.ts → client.ts
├── objects.ts → client.ts
└── (other clients...)
```

---

## 7. Recommendations

### Immediate Actions (Week 1)

1. **Fix Critical Gap #1**: Add default firewall rules
   ```python
   # In main.py startup_event():
   init_default_firewall_rules(db)
   ```

2. **Fix Critical Gap #2**: Initialize service accounts
   ```python
   # In main.py startup_event():
   init_default_service_accounts(db)
   ```

3. **Fix Critical Gap #3**: Ensure default subnet exists
   ```python
   # In vpc.py ensure_default_network():
   ensure_default_subnet(db, project, network)
   ```

4. **Remove Deprecated Models**: Clean up database.py
   ```python
   # Delete: RouteTable, SubnetRouteTableAssociation
   ```

### Short-term Actions (Week 2-3)

5. **Document API Limitations**: Create LIMITATIONS.md
   - No authentication/authorization
   - gcloud CLI partial support
   - Docker-based infrastructure

6. **Add Health Checks**: Implement comprehensive health endpoint
   ```python
   @app.get("/health/detailed")
   def health_detailed():
       return {
           "database": "connected",
           "docker": "running",
           "projects": count,
           "instances": count,
           "networks": count
       }
   ```

7. **Implement Code-splitting**: Optimize frontend bundle
   ```typescript
   const BucketDetails = lazy(() => import('./pages/BucketDetails'));
   ```

### Long-term Actions (Month 2+)

8. **Add Monitoring**: Basic metrics endpoint
9. **Implement Disks**: Persistent disk management
10. **Add Load Balancers**: Simple HTTP(S) LB

---

## Summary

### ✅ What's Working Well

- **Database**: 17 models, well-structured, SQLAlchemy ORM
- **Backend**: 9 API modules, 45+ endpoints, FastAPI
- **Frontend**: 16 pages, 23 components, modern React
- **Docker Integration**: VMs = Containers, Networks = Docker networks
- **Storage**: Complete object storage with versioning
- **Compute**: Full VM lifecycle management

### ⚠️ What Needs Attention

- **Firewall**: No default rules (CRITICAL)
- **IAM**: No service accounts (MEDIUM)
- **Subnets**: Missing default subnet (HIGH)
- **Code Cleanup**: Remove deprecated models (LOW)
- **UI**: Remove dead links or implement backends (LOW)

### 🎯 Next Steps

1. Run `init_default_firewall_rules()` on startup
2. Run `init_default_service_accounts()` on startup
3. Call `ensure_default_subnet()` in network creation
4. Remove RouteTable models from database.py
5. Document system limitations in LIMITATIONS.md

---

**Analysis Completed:** February 12, 2026  
**Analyst:** System Architecture Team  
**Review Status:** Ready for Implementation
