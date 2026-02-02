# GCP Stimulator - Complete Architectural Analysis

> **Purpose**: Comprehensive analysis of GCP Stimulator architecture for onboarding new developers

**Document Version**: 1.0  
**Last Updated**: February 2, 2026  
**Target Audience**: New developers, technical leads, architects

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Folder & Module Breakdown](#2-folder--module-breakdown)
3. [Component-Level Explanation](#3-component-level-explanation)
4. [Application Flow](#4-application-flow)
5. [Configuration & Environment](#5-configuration--environment)
6. [Error Handling & Logging](#6-error-handling--logging)
7. [Security & Access Control](#7-security--access-control)
8. [Deployment & Runtime](#8-deployment--runtime)
9. [Strengths, Risks & Improvements](#9-strengths-risks--improvements)

---

## 1. High-Level Architecture

### 1.1 System Type

**Modular Monolith with Microservices-Ready Design**

The GCP Stimulator is a **monolithic backend** with **clear module boundaries** that could be extracted into microservices. It follows a **layered architecture** with:

- **Presentation Layer**: REST API endpoints (Flask blueprints)
- **Business Logic Layer**: Services and handlers
- **Data Access Layer**: SQLAlchemy ORM models
- **Infrastructure Layer**: Database, Docker, file storage

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  gcloud CLI │  │  Python SDK │  │  REST API   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │
          └────────┬────────┴────────┬────────┘
                   │                 │
┌──────────────────▼─────────────────▼──────────────────────┐
│            REACT UI (Port 3000/3001)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Storage   │  │   Compute   │  │     IAM     │       │
│  │  Dashboard  │  │  Dashboard  │  │  Dashboard  │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────┬──────────────────────────────────┘
                          │ HTTP/JSON
                          │
┌─────────────────────────▼──────────────────────────────────┐
│          FLASK BACKEND (Port 8080)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API LAYER (Flask Blueprints)                        │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │  │
│  │  │ Storage  │ │ Compute  │ │   IAM    │  ...       │  │
│  │  │   /v1    │ │   /v1    │ │   /v1    │            │  │
│  │  └──────────┘ └──────────┘ └──────────┘            │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │  BUSINESS LOGIC (Services & Handlers)                │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │  │
│  │  │  Bucket  │ │ Instance │ │ Network  │            │  │
│  │  │ Service  │ │ Service  │ │ Service  │            │  │
│  │  └──────────┘ └──────────┘ └──────────┘            │  │
│  └──────────────────────┬───────────────────────────────┘  │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────────┐  │
│  │  DATA LAYER (SQLAlchemy Models)                      │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │  │
│  │  │  Bucket  │ │ Instance │ │ Network  │            │  │
│  │  │  Model   │ │  Model   │ │  Model   │            │  │
│  │  └──────────┘ └──────────┘ └──────────┘            │  │
│  └──────────────────────┬───────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────┘
                          │
┌─────────────────────────▼──────────────────────────────────┐
│           INFRASTRUCTURE LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  PostgreSQL  │  │    Docker    │  │ File System  │    │
│  │  (Port 5432) │  │    Engine    │  │   Storage    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└────────────────────────────────────────────────────────────┘
```

### 1.2 Major Subsystems

#### A. **Storage Emulator** (GCS - Google Cloud Storage)
- **Purpose**: Emulates Google Cloud Storage buckets and objects
- **Components**: Buckets, Objects, ACLs, Lifecycle, Versioning
- **Storage Backend**: File system + PostgreSQL metadata

#### B. **Compute Emulator** (GCE - Google Compute Engine)
- **Purpose**: Emulates VM instances with Docker containers
- **Components**: Instances, Zones, Machine Types, Images
- **Runtime Backend**: Docker Engine

#### C. **Networking Emulator** (VPC)
- **Purpose**: Emulates VPC networks, subnets, firewall rules
- **Components**: Networks, Subnetworks, Firewalls, Routes, IP Addresses
- **Backend**: Docker networks + PostgreSQL

#### D. **IAM Emulator** (Identity & Access Management)
- **Purpose**: Emulates service accounts, roles, policies
- **Components**: Service Accounts, Keys, Policies, Roles
- **Backend**: PostgreSQL with mock authentication

#### E. **Project Management**
- **Purpose**: Emulates GCP projects (Cloud Resource Manager)
- **Components**: Projects, Project metadata
- **Backend**: PostgreSQL

### 1.3 External Dependencies

```yaml
Core Dependencies:
  - PostgreSQL 16: Relational database for metadata
  - Docker Engine: Container runtime for VM emulation
  - File System: Object storage backend

Backend Dependencies (Python):
  - Flask 2.3+: Web framework
  - SQLAlchemy: ORM for database
  - Flask-CORS: Cross-origin support
  - psycopg2: PostgreSQL adapter
  - PyJWT: JWT token auth (security)
  - cryptography: TLS/SSL support
  - bleach: Input sanitization

Frontend Dependencies (TypeScript/React):
  - React 18: UI framework
  - Vite: Build tool
  - TailwindCSS: Styling
  - Lucide React: Icons
  - Axios: HTTP client

External APIs (None):
  - No real Google Cloud APIs used
  - Fully self-contained local emulator

Authentication:
  - Mock OAuth2 (no real Google auth)
  - JWT tokens (optional)
  - API keys (optional)
  - Can be disabled for development
```

---

## 2. Folder & Module Breakdown

### 2.1 Root Structure

```
gcs-stimulator/
├── gcp-stimulator-package/     # Backend (Flask + Python)
├── gcp-stimulator-ui/          # Frontend (React + TypeScript)
├── scripts/                    # Utility scripts
├── terraform/                  # Terraform examples
├── examples/                   # Usage examples (gcloud, Python SDK)
├── docker-compose.yml          # Container orchestration
└── *.sh                        # Service management scripts
```

**Purpose**: Monorepo structure separating backend, frontend, and tooling.

**Problem It Solves**: Clear separation of concerns, easy development workflow, single repository for all components.

### 2.2 Backend Structure (`gcp-stimulator-package/`)

```
gcp-stimulator-package/
├── app/
│   ├── __init__.py
│   ├── factory.py              # Flask app factory
│   ├── config.py               # Configuration classes
│   ├── db.py                   # Database initialization
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── project.py          # Projects table
│   │   ├── bucket.py           # Buckets table
│   │   ├── object.py           # Objects table
│   │   ├── compute.py          # Instances, Zones, MachineTypes
│   │   ├── vpc.py              # Networks, Subnets, Firewall
│   │   ├── service_account.py  # Service accounts & keys
│   │   ├── iam_policy.py       # IAM policies & roles
│   │   └── resumable_session.py # Upload sessions
│   ├── routes/                 # Flask Blueprint definitions
│   │   ├── bucket_routes.py    # Bucket endpoints
│   │   ├── network_routes.py   # VPC network endpoints
│   │   ├── subnet_routes.py    # Subnet endpoints
│   │   ├── firewall_routes.py  # Firewall endpoints
│   │   ├── auth_routes.py      # Auth management (NEW)
│   │   └── ...
│   ├── handlers/               # Request handlers (business logic)
│   │   ├── bucket_handler.py   # Bucket operations
│   │   ├── objects.py          # Object operations
│   │   ├── compute_handler.py  # Instance operations
│   │   ├── network_handler.py  # Network operations
│   │   ├── iam_handler.py      # IAM operations
│   │   └── ...
│   ├── services/               # Business logic services
│   │   ├── bucket_service.py   # Bucket business logic
│   │   ├── compute_service.py  # Compute business logic
│   │   ├── network_service.py  # Network business logic
│   │   └── ...
│   ├── middleware/             # Request/response middleware (NEW)
│   │   ├── auth_middleware.py  # JWT/API key authentication
│   │   ├── rate_limiting.py    # Rate limiting
│   │   ├── input_validation.py # Input sanitization
│   │   ├── security_headers.py # Security headers
│   │   └── tls_config.py       # HTTPS/TLS setup
│   ├── validators/             # Input validation logic
│   │   ├── vpc_validators.py   # VPC validation
│   │   └── ...
│   ├── utils/                  # Utility functions
│   │   ├── ip_utils.py         # IP/CIDR utilities
│   │   ├── operation_utils.py  # GCP operations
│   │   └── ...
│   └── logging/                # Logging configuration
│       └── middleware.py
├── migrations/                 # Database migrations
│   ├── 001_add_object_versioning.py
│   ├── 002_add_resumable_sessions.py
│   ├── 005_add_iam_and_compute.py
│   ├── 008_create_vpc_tables.py
│   └── ...
├── tests/                      # Test suite
│   ├── conftest.py            # Pytest configuration
│   ├── test_*.py              # Unit/integration tests
│   └── sdk/                    # SDK compatibility tests
├── storage/                    # File system storage for objects
├── instance/                   # Flask instance folder
├── Dockerfile                  # Container definition
├── requirements.txt            # Python dependencies
└── run.py                      # Application entry point
```

#### Key Modules Explained:

**`factory.py`** - **Application Factory Pattern**
- **Purpose**: Creates and configures Flask application
- **Problem It Solves**: Allows multiple app instances (testing, production), centralizes config
- **Architecture Fit**: Entry point for entire backend, wires all components together

**`models/`** - **Data Models (ORM)**
- **Purpose**: SQLAlchemy models mapping to PostgreSQL tables
- **Problem It Solves**: Type-safe database access, automatic schema management
- **Architecture Fit**: Data Access Layer, bridges business logic and database

**`routes/`** - **API Endpoint Definitions**
- **Purpose**: Flask Blueprints defining HTTP endpoints
- **Problem It Solves**: Modular API organization, URL routing
- **Architecture Fit**: Presentation Layer, exposes business logic as REST APIs

**`handlers/`** - **Request Handlers**
- **Purpose**: Process HTTP requests, call services, format responses
- **Problem It Solves**: Separates HTTP logic from business logic
- **Architecture Fit**: Controller layer between routes and services

**`services/`** - **Business Logic**
- **Purpose**: Core business operations, reusable logic
- **Problem It Solves**: Business logic reuse across handlers, testability
- **Architecture Fit**: Business Logic Layer, orchestrates operations

**`middleware/`** - **Security & Cross-Cutting Concerns (NEW)**
- **Purpose**: Authentication, rate limiting, validation, security
- **Problem It Solves**: Production-grade security, prevents abuse
- **Architecture Fit**: Cross-cutting layer applied to all requests

**`migrations/`** - **Database Schema Management**
- **Purpose**: Version-controlled schema changes
- **Problem It Solves**: Reproducible database evolution, team synchronization
- **Architecture Fit**: Infrastructure layer, manages data model evolution

### 2.3 Frontend Structure (`gcp-stimulator-ui/`)

```
gcp-stimulator-ui/
├── src/
│   ├── main.tsx                # React entry point
│   ├── App.tsx                 # Main app component
│   ├── api/                    # API client layer
│   │   ├── client.ts           # Axios HTTP client
│   │   ├── storage.ts          # Storage API calls
│   │   ├── compute.ts          # Compute API calls
│   │   ├── iam.ts              # IAM API calls
│   │   └── network.ts          # Network API calls
│   ├── pages/                  # Page components
│   │   ├── StoragePage.tsx     # Storage dashboard
│   │   ├── ComputePage.tsx     # Compute dashboard
│   │   ├── NetworksPage.tsx    # Network dashboard
│   │   └── IAMDashboardPage.tsx
│   ├── components/             # Reusable UI components
│   │   ├── Modal.tsx
│   │   ├── FormFields.tsx
│   │   └── ...
│   └── styles/                 # CSS/Tailwind styles
├── public/                     # Static assets
├── Dockerfile                  # Container definition
├── package.json                # NPM dependencies
├── vite.config.ts              # Vite configuration
└── tailwind.config.js          # Tailwind CSS config
```

**Purpose**: Single Page Application (SPA) for visual management of emulated GCP resources.

**Problem It Solves**: User-friendly interface for developers to interact with emulator without CLI.

**Architecture Fit**: Separate presentation tier, communicates with backend via REST API.

---

## 3. Component-Level Explanation

### 3.1 Core Backend Components

#### A. **factory.py - Application Factory**

**Location**: `gcp-stimulator-package/app/factory.py`

**What It Does**:
```python
def create_app(config_name: str = None) -> Flask:
    # 1. Creates Flask application instance
    # 2. Loads configuration (dev/prod/test)
    # 3. Initializes database connection
    # 4. Registers all blueprints (API routes)
    # 5. Sets up middleware (logging, CORS, auth)
    # 6. Starts background services (lifecycle executor)
    return app
```

**Inputs**:
- `config_name`: Environment name ('development', 'production', 'testing')

**Outputs**:
- Fully configured Flask application instance

**Dependencies**:
- All models (for db.create_all())
- All blueprints (for registration)
- Configuration classes
- Database connection string

**Who Calls It**: 
- `run.py` (entry point)
- Test suite (`conftest.py`)

**When Called**: Application startup

**Side Effects**:
- Database connection established
- Database tables created if missing
- Background threads started (lifecycle executor)
- Logging configured

---

#### B. **Models - Database ORM**

##### **models/bucket.py - Bucket Model**

**What It Does**:
```python
class Bucket(db.Model):
    __tablename__ = "buckets"
    
    id = db.Column(db.String(63), primary_key=True)
    project_id = db.Column(db.String(63), db.ForeignKey("projects.id"))
    name = db.Column(db.String(63), nullable=False)
    location = db.Column(db.String(50), default="US")
    storage_class = db.Column(db.String(50), default="STANDARD")
    versioning_enabled = db.Column(db.Boolean, default=False)
    # ... more fields
```

**Purpose**: Represents a Google Cloud Storage bucket in the database.

**Inputs**: None (ORM model)

**Outputs**: Database table schema, query interface

**Dependencies**:
- SQLAlchemy (db.Model)
- `projects` table (foreign key)

**Who Uses It**:
- `BucketService` (business logic)
- `bucket_handler.py` (request handling)
- Database queries throughout the app

**Side Effects**:
- Creates `buckets` table on first run
- Enforces foreign key constraints
- Maintains referential integrity

---

##### **models/compute.py - Compute Models**

**What It Does**:
```python
class Instance(db.Model):
    __tablename__ = "instances"
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    project_id = db.Column(db.String(63), db.ForeignKey("projects.id"))
    zone = db.Column(db.String(50))
    machine_type = db.Column(db.String(100))
    state = db.Column(db.String(20), default="PROVISIONING")
    container_id = db.Column(db.String(100), unique=True)  # Docker container ID
    # ... networking fields
```

**Purpose**: Represents a Compute Engine VM instance.

**Key Feature**: Links database record to Docker container via `container_id`.

**Side Effects**:
- When instance is deleted, associated Docker container is stopped/removed
- State changes (RUNNING, STOPPED) map to container operations

---

##### **models/vpc.py - VPC Network Models**

**What It Does**:
```python
class Network(db.Model):
    __tablename__ = "networks"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), nullable=False)
    project_id = db.Column(db.String(63), db.ForeignKey("projects.id"))
    auto_create_subnetworks = db.Column(db.Boolean, default=False)
    routing_mode = db.Column(db.String(20), default="REGIONAL")
    docker_network_name = db.Column(db.String(100), unique=True)  # Maps to Docker network
```

**Purpose**: Represents a VPC network, maps to Docker bridge network.

**Key Feature**: `docker_network_name` field links GCP network to actual Docker network.

**Side Effects**:
- Creating network creates Docker bridge network
- Deleting network removes Docker network
- Instances attached to network are added to Docker network

---

#### C. **Services - Business Logic**

##### **services/bucket_service.py - Bucket Operations**

**What It Does**:
```python
class BucketService:
    @staticmethod
    def create_bucket(project_id: str, bucket_name: str, location: str, ...):
        # 1. Validate bucket name (3-63 chars, lowercase, etc.)
        # 2. Check if bucket already exists
        # 3. Create Bucket record in database
        # 4. Create directory on file system (storage/)
        # 5. Return bucket object
        
    @staticmethod
    def list_buckets(project_id: str):
        # Query database for all buckets in project
        # Return list of Bucket objects
```

**Inputs**:
- `create_bucket`: project_id, bucket_name, location, storage_class, versioning
- `list_buckets`: project_id

**Outputs**:
- `create_bucket`: Bucket model instance
- `list_buckets`: List of Bucket model instances

**Dependencies**:
- `Bucket` model (database)
- File system (for storage directory)
- Validators (bucket name validation)

**Who Calls It**:
- `bucket_handler.py` (HTTP request handler)
- Other services needing bucket operations

**Side Effects**:
- Database write (INSERT)
- File system write (mkdir)
- Logging

---

##### **services/compute_service.py - Instance Management**

**What It Does**:
```python
class ComputeService:
    @staticmethod
    def create_instance(project_id, zone, instance_name, machine_type, image, network):
        # 1. Validate instance name
        # 2. Create Docker container with specified resources
        # 3. Create Instance record in database with container_id
        # 4. Attach container to Docker network (if VPC specified)
        # 5. Start container
        # 6. Update instance state to RUNNING
        
    @staticmethod
    def stop_instance(project_id, zone, instance_name):
        # 1. Find instance in database
        # 2. Stop Docker container
        # 3. Update instance state to TERMINATED
```

**Inputs**:
- `create_instance`: project_id, zone, name, machine_type, image, network
- `stop_instance`: project_id, zone, instance_name

**Outputs**:
- Instance model with container_id populated

**Dependencies**:
- `Instance` model (database)
- Docker Python SDK (`docker` package)
- `Network` model (for networking)

**Who Calls It**:
- `compute_handler.py` (HTTP request handler)

**Side Effects**:
- **Docker container created/started/stopped**
- Database writes (INSERT/UPDATE)
- Network attachment (Docker network join)
- **Real system resources used** (CPU, memory from Docker host)

---

##### **services/network_service.py - VPC Network Operations**

**What It Does**:
```python
class NetworkService:
    @staticmethod
    def create_network(project_id, network_name, auto_create_subnetworks, routing_mode):
        # 1. Validate network name
        # 2. Create Docker bridge network
        # 3. Create Network record in database with docker_network_name
        # 4. Return network object
        
    @staticmethod
    def delete_network(project_id, network_name):
        # 1. Check no instances attached
        # 2. Remove Docker network
        # 3. Delete Network record from database
```

**Inputs**:
- Network properties (name, mode, routing)

**Outputs**:
- Network model instance

**Dependencies**:
- `Network` model (database)
- Docker Python SDK
- `Instance` model (to check attachments)

**Side Effects**:
- **Docker bridge network created/deleted**
- Database writes
- Affects instance connectivity

---

#### D. **Handlers - HTTP Request Processing**

##### **handlers/bucket_handler.py - Bucket Endpoints**

**What It Does**:
```python
def handle_create_bucket(request):
    # 1. Extract JSON body from request
    # 2. Get project_id from query params
    # 3. Call BucketService.create_bucket()
    # 4. Format response as GCP-style JSON
    # 5. Return JSON response with 200/400/409 status
    
def handle_list_buckets(request):
    # 1. Get project_id from query params
    # 2. Call BucketService.list_buckets()
    # 3. Format as GCP bucket list response
    # 4. Return JSON
```

**Inputs**:
- Flask `request` object (contains body, query params, headers)

**Outputs**:
- Flask `jsonify()` response object

**Dependencies**:
- `BucketService` (business logic)
- Flask request/response objects

**Who Calls It**:
- Flask routing system (when HTTP request matches route)

**Side Effects**:
- HTTP response sent to client
- Logging

---

##### **handlers/compute_handler.py - Compute Endpoints**

**What It Does**:
```python
@compute_bp.route('/compute/v1/projects/<project_id>/zones/<zone>/instances', methods=['POST'])
def create_instance(project_id, zone):
    # 1. Parse request body
    # 2. Extract machine type, image, network
    # 3. Call ComputeService.create_instance()
    # 4. Return GCP-formatted instance JSON
```

**Inputs**:
- HTTP request with instance configuration

**Outputs**:
- JSON response with instance details

**Dependencies**:
- `ComputeService`
- `Instance` model

**Side Effects**:
- Docker container created and started
- Database record created

---

#### E. **Routes - URL Mapping**

##### **routes/bucket_routes.py - Bucket URL Routes**

**What It Does**:
```python
buckets_bp = Blueprint('buckets', __name__)

@buckets_bp.route("", methods=["GET"])
def list_buckets():
    return handle_list_buckets(request)

@buckets_bp.route("", methods=["POST"])
def create_bucket():
    return handle_create_bucket(request)

@buckets_bp.route("/<bucket>", methods=["GET"])
def get_bucket(bucket):
    return handle_get_bucket(request, bucket)
```

**Purpose**: Maps HTTP methods and URL paths to handler functions.

**Registered As**: `/storage/v1/b` (in factory.py)

**Final URLs**:
- `GET /storage/v1/b?project=PROJECT_ID` → list_buckets()
- `POST /storage/v1/b?project=PROJECT_ID` → create_bucket()
- `GET /storage/v1/b/BUCKET_NAME` → get_bucket()

---

#### F. **Middleware - Security Layer (NEW)**

##### **middleware/auth_middleware.py - Authentication**

**What It Does**:
```python
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Extract JWT token or API key from headers
        # 2. Verify token/key validity
        # 3. Check expiration
        # 4. Attach user_info to request object
        # 5. Call original function
        # 6. Return 401 if auth fails
    return decorated_function
```

**Inputs**: Flask request with Authorization header or X-API-Key header

**Outputs**: Decorates endpoint, adds `request.user_info`

**Dependencies**:
- PyJWT (token verification)
- `APIKey` model (database)

**When Applied**: Before endpoint execution if `@require_auth` decorator used

**Side Effects**:
- Rejects unauthenticated requests with 401
- Logs authentication attempts
- Updates API key last_used_at timestamp

---

##### **middleware/rate_limiting.py - Rate Limiter**

**What It Does**:
```python
def rate_limit(limit=100, window_seconds=60):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # 1. Get client ID (IP or API key)
            # 2. Check request count in time window
            # 3. If exceeded, return 429 Too Many Requests
            # 4. Add rate limit headers to response
            # 5. Execute endpoint if within limit
        return wrapper
    return decorator
```

**Inputs**: Limit (requests), window (seconds)

**Outputs**: Decorated endpoint with rate limiting

**Dependencies**:
- Redis (optional, for distributed rate limiting)
- In-memory storage (fallback)

**Side Effects**:
- Blocks excessive requests with 429 status
- Adds X-RateLimit-* headers
- Logs rate limit violations

---

### 3.2 Frontend Components

#### **api/client.ts - HTTP Client**

**What It Does**:
```typescript
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080',
  timeout: 10000,
  headers: {'Content-Type': 'application/json'}
});
```

**Purpose**: Centralized Axios HTTP client for all API calls.

**Inputs**: Configuration (base URL, timeout)

**Outputs**: Configured axios instance

**Who Uses It**: All API modules (storage.ts, compute.ts, etc.)

---

#### **api/storage.ts - Storage API Client**

**What It Does**:
```typescript
export async function listBuckets(projectId: string): Promise<Bucket[]> {
  const response = await apiClient.get(`/storage/v1/b?project=${projectId}`);
  return response.data.items || [];
}

export async function createBucket(projectId: string, bucketData: CreateBucketRequest): Promise<Bucket> {
  const response = await apiClient.post(`/storage/v1/b?project=${projectId}`, bucketData);
  return response.data;
}
```

**Purpose**: Type-safe API calls for storage operations.

**Inputs**: Function parameters (projectId, bucket data)

**Outputs**: Promise<Bucket> or Promise<Bucket[]>

**Who Calls It**: React components (StoragePage.tsx)

---

#### **pages/StoragePage.tsx - Storage Dashboard**

**What It Does**:
```typescript
const StoragePage = () => {
  const [buckets, setBuckets] = useState<Bucket[]>([]);
  
  useEffect(() => {
    loadBuckets(); // Call API on mount
  }, []);
  
  const loadBuckets = async () => {
    const data = await listBuckets(selectedProject);
    setBuckets(data);
  };
  
  return (<div>
    {/* Render bucket list, create form */}
  </div>);
};
```

**Purpose**: UI for managing storage buckets.

**Inputs**: User interactions (clicks, form submissions)

**Outputs**: Rendered React components

**Dependencies**:
- `api/storage.ts` (API calls)
- React hooks (useState, useEffect)

---

### 3.3 Infrastructure Components

#### **docker-compose.yml - Container Orchestration**

**What It Does**:
```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: gcs_emulator
    ports: ["5432:5432"]
    
  backend:
    build: ./gcp-emulator-package
    depends_on:
      postgres: {condition: service_healthy}
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gcs_emulator
    ports: ["8080:8080"]
    
  frontend:
    build: ./gcp-emulator-ui
    depends_on: [backend]
    ports: ["3000:3000"]
```

**Purpose**: Defines 3 containers and their dependencies.

**Inputs**: docker-compose command

**Outputs**: Running containers

**Side Effects**:
- Creates Docker network (`gcs-emulator-network`)
- Creates volumes for PostgreSQL data and storage
- Starts containers in dependency order

---

## 4. Application Flow

### 4.1 Startup Flow

```
1. User runs: docker-compose up
   │
   ├──> PostgreSQL container starts
   │    └──> Creates gcs_emulator database
   │
   ├──> Backend container starts (waits for DB health)
   │    │
   │    ├──> run.py executed
   │    │
   │    ├──> factory.create_app() called
   │    │    │
   │    │    ├──> Load configuration (dev/prod)
   │    │    ├──> Initialize database connection
   │    │    ├──> Wait for database to be ready (retry loop)
   │    │    ├──> Run db.create_all() (create tables)
   │    │    ├──> Register all blueprints (50+ endpoints)
   │    │    ├──> Setup middleware (CORS, logging, auth)
   │    │    └──> Start background services (lifecycle executor)
   │    │
   │    └──> Flask server starts on port 8080
   │
   └──> Frontend container starts
        │
        ├──> Nginx serves React build
        │
        └──> React app loads on port 3000
```

### 4.2 Request Flow - Create Bucket Example

**Client Request**:
```bash
curl -X POST http://localhost:8080/storage/v1/b?project=my-project \
  -H "Content-Type: application/json" \
  -d '{"name": "my-bucket", "location": "US"}'
```

**Backend Flow**:
```
1. HTTP Request arrives at Flask
   │
   ├──> CORS middleware (add CORS headers)
   ├──> Logging middleware (log request)
   ├──> Auth middleware (if enabled, verify token/API key)
   ├──> Rate limiting (if enabled, check limits)
   │
2. Flask routing matches /storage/v1/b
   │
   └──> Calls buckets_bp blueprint
        │
        └──> POST method matches create_bucket() route
             │
3. Route handler executes
   │
   └──> bucket_routes.create_bucket()
        │
        └──> Calls handle_create_bucket(request)
             │
4. Handler processes request
   │
   ├──> bucket_handler.handle_create_bucket()
   │    │
   │    ├──> Extract request.get_json()
   │    ├──> Get project_id from request.args
   │    ├──> Validate inputs
   │    │
   │    └──> Call BucketService.create_bucket(...)
   │         │
5. Service executes business logic
   │
   └──> BucketService.create_bucket()
        │
        ├──> Validate bucket name format
        ├──> Check if bucket already exists (DB query)
        ├──> Create Bucket model instance
        ├──> Save to database (db.session.add, commit)
        ├──> Create storage directory (os.makedirs)
        │
        └──> Return Bucket object
             │
6. Handler formats response
   │
   └──> Convert Bucket to dict (to_dict())
        │
        └──> Return jsonify(response), 200
             │
7. Flask sends HTTP response
   │
   └──> Response headers added (CORS, security)
        │
        └──> JSON sent to client
```

**Database Operations During Flow**:
```sql
-- Step 4: Check if bucket exists
SELECT * FROM buckets WHERE name = 'my-bucket';

-- Step 5: Insert new bucket
INSERT INTO buckets (id, project_id, name, location, storage_class, created_at)
VALUES ('my-bucket', 'my-project', 'my-bucket', 'US', 'STANDARD', NOW());
```

**File System Operations**:
```bash
# Step 5: Create storage directory
mkdir -p storage/my-project/my-bucket/
```

### 4.3 Request Flow - Create VM Instance Example

**Client Request**:
```bash
curl -X POST http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-vm",
    "machineType": "e2-medium",
    "disks": [{
      "initializeParams": {"sourceImage": "debian-11"}
    }],
    "networkInterfaces": [{
      "network": "projects/my-project/global/networks/my-network"
    }]
  }'
```

**Backend Flow**:
```
1. Flask routes to compute_bp blueprint
   │
2. POST /compute/v1/projects/<project_id>/zones/<zone>/instances
   │
   └──> compute_handler.create_instance(project_id, zone)
        │
3. Handler processes request
   │
   ├──> Parse request body
   ├──> Extract machine_type, image, network
   │
   └──> Call ComputeService.create_instance(...)
        │
4. Service creates VM
   │
   └──> ComputeService.create_instance()
        │
        ├──> Generate instance ID
        ├──> Parse machine type (get CPU/memory)
        │
        ├──> Create Docker container
        │    │
        │    └──> docker.containers.run(
        │             image='debian:11',
        │             name='gcp-my-vm',
        │             detach=True,
        │             mem_limit='2g',
        │             nano_cpus=2000000000,
        │             labels={'gcp-stimulator': 'true', 'instance-name': 'my-vm'},
        │             command='tail -f /dev/null'  # Keep running
        │         )
        │         │
        │         └──> Docker Engine: Creates container
        │              └──> Assigns container_id: 'abc123...'
        │
        ├──> Attach to Docker network (if VPC specified)
        │    │
        │    └──> docker_network.connect(container)
        │
        ├──> Create Instance model
        │    │
        │    ├──> instance = Instance(
        │    │        id='instance-id-123',
        │    │        name='my-vm',
        │    │        project_id='my-project',
        │    │        zone='us-central1-a',
        │    │        machine_type='e2-medium',
        │    │        state='RUNNING',
        │    │        container_id='abc123...',
        │    │        network_name='my-network'
        │    │    )
        │    │
        │    └──> db.session.add(instance)
        │         db.session.commit()
        │
        └──> Return instance object
             │
5. Handler formats GCP-style response
   │
   └──> Return {
            "id": "instance-id-123",
            "name": "my-vm",
            "status": "RUNNING",
            "machineType": "zones/us-central1-a/machineTypes/e2-medium",
            "selfLink": "http://localhost:8080/compute/v1/projects/my-project/zones/us-central1-a/instances/my-vm",
            ...
        }
```

**Side Effects**:
1. **Docker container created** (real system resources allocated)
2. **Container started** (process running on host)
3. **Container joined Docker network** (networking configured)
4. **Database record created** (metadata stored)

**Result**: Real Docker container running on host machine, linked to GCP-style API record.

### 4.4 gcloud CLI Flow

**User Command**:
```bash
gcloud compute instances list --project=my-project
```

**Flow**:
```
1. gcloud CLI (user's machine)
   │
   ├──> Uses configured API endpoint: http://localhost:8080
   │
   └──> Sends HTTP GET: /compute/v1/projects/my-project/aggregated/instances
        │
2. Backend receives request
   │
   └──> Routes to compute_handler.list_instances()
        │
        ├──> Query Instance model: Instance.query.filter_by(project_id='my-project').all()
        │
        ├──> Format as GCP instance list JSON
        │
        └──> Return response
             │
3. gcloud CLI receives response
   │
   └──> Parses JSON and displays table:
   
   NAME    ZONE            MACHINE_TYPE  STATUS
   my-vm   us-central1-a   e2-medium     RUNNING
```

---

## 5. Configuration & Environment

### 5.1 Configuration Files

#### **app/config.py - Application Configuration**

```python
class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://...')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MOCK_AUTH_ENABLED = True
    
class DevelopmentConfig(Config):
    DEBUG = True
    AUTH_MODE = 'disabled'  # No auth required
    RATE_LIMITING_ENABLED = False
    
class ProductionConfig(Config):
    DEBUG = False
    AUTH_MODE = 'required'  # Auth required
    RATE_LIMITING_ENABLED = True
    HTTPS_ENABLED = True
```

**Purpose**: Environment-specific settings.

**How Used**: Selected in `factory.create_app(config_name)`.

---

#### **docker-compose.yml - Container Configuration**

```yaml
services:
  backend:
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gcs_emulator
      FLASK_ENV: production
      STORAGE_EMULATOR_HOST: http://0.0.0.0:8080
```

**Purpose**: Runtime environment variables for containers.

---

#### **.env / .env-gcloud - Environment Files**

```bash
# .env (for backend)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gcs_emulator
FLASK_ENV=development
LOG_LEVEL=DEBUG

# .env-gcloud (for gcloud CLI setup)
CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE=http://127.0.0.1:8080/compute/v1/
CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE=http://127.0.0.1:8080/storage/v1/
CLOUDSDK_AUTH_DISABLE_CREDENTIALS=true
```

**Purpose**: Local development configuration, not committed to git.

---

### 5.2 Environment Variables

| Variable | Purpose | Default | Where Used |
|----------|---------|---------|-----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` | Backend, migrations |
| `FLASK_ENV` | Environment (dev/prod/test) | `development` | Backend config selection |
| `AUTH_MODE` | Authentication mode (disabled/optional/required) | `disabled` | Auth middleware |
| `RATE_LIMITING_ENABLED` | Enable rate limiting | `false` | Rate limiter |
| `HTTPS_ENABLED` | Enable HTTPS/TLS | `false` | TLS config |
| `CORS_ORIGINS` | Allowed CORS origins | `*` | CORS middleware |
| `JWT_SECRET_KEY` | JWT signing secret | Auto-generated | Auth middleware |
| `STORAGE_EMULATOR_HOST` | Storage API base URL | `http://0.0.0.0:8080` | SDK compatibility |
| `LOG_LEVEL` | Logging verbosity | `INFO` | Logging config |
| `VITE_API_BASE_URL` | Frontend API endpoint | `http://localhost:8080` | React app |

---

### 5.3 Multi-Environment Handling

**Development**:
```bash
export FLASK_ENV=development
python run.py
# - No authentication
# - Debug mode ON
# - Verbose logging
# - Hot reload enabled
```

**Production**:
```bash
export FLASK_ENV=production
export AUTH_MODE=required
export HTTPS_ENABLED=true
export JWT_SECRET_KEY=$(openssl rand -hex 32)
python run.py
# - Authentication required
# - Debug mode OFF
# - Production logging
# - HTTPS enforced
```

**Testing**:
```bash
export FLASK_ENV=testing
pytest
# - Uses test database (gcs_emulator_test)
# - Isolated test environment
# - Fast execution
```

---

## 6. Error Handling & Logging

### 6.1 Error Handling Strategy

#### **HTTP Error Responses (GCP-Style)**

```python
def error_response(status_code, error_code, message):
    return jsonify({
        "error": {
            "code": status_code,
            "message": message,
            "status": error_code,  # "NOT_FOUND", "INVALID_ARGUMENT", etc.
            "errors": [{
                "domain": "global",
                "reason": error_code,
                "message": message
            }]
        }
    }), status_code
```

**Example Usage**:
```python
if not bucket:
    return error_response(404, "NOT_FOUND", f"Bucket {bucket_name} not found")

if bucket_name_invalid:
    return error_response(400, "INVALID_ARGUMENT", "Bucket name must be lowercase")
```

---

#### **Global Error Handlers (factory.py)**

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": {"message": "Not found"}}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()  # Rollback failed transaction
    app.logger.error(f"Internal error: {error}")
    return jsonify({"error": {"message": "Internal server error"}}), 500
```

---

### 6.2 Logging Architecture

#### **Logging Setup (factory.py)**

```python
def setup_logging(app):
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/gcs_emulator.log'),
            logging.StreamHandler()  # Console output
        ]
    )
```

**Log Levels**:
- **DEBUG**: Verbose (SQL queries, request details)
- **INFO**: Normal operations (startup, request summaries)
- **WARNING**: Recoverable issues (deprecated API usage)
- **ERROR**: Failures (exceptions, validation errors)

---

#### **Request Logging Middleware**

```python
@app.before_request
def log_request():
    app.logger.info(f"{request.method} {request.path} - User: {request.remote_addr}")

@app.after_request
def log_response(response):
    app.logger.info(f"Response: {response.status_code}")
    return response
```

**Log Output Example**:
```
2026-02-02 12:34:56 - app - INFO - POST /storage/v1/b - User: 172.17.0.1
2026-02-02 12:34:56 - app - INFO - Creating bucket: my-bucket
2026-02-02 12:34:56 - app - INFO - Response: 200
```

---

### 6.3 Retry & Resilience

#### **Database Connection Retry (factory.py)**

```python
def wait_for_database(app):
    retries = 30
    for attempt in range(retries):
        try:
            db.session.execute(text("SELECT 1"))
            return  # Success
        except OperationalError:
            app.logger.warning(f"DB not ready ({attempt}/{retries}), retrying...")
            time.sleep(1)
    raise Exception("Database connection failed")
```

**Purpose**: Handles Docker Compose startup timing (backend starts before PostgreSQL ready).

---

#### **Docker Operation Retry (compute_service.py)**

```python
def create_container_with_retry(image, name, retries=3):
    for attempt in range(retries):
        try:
            return docker_client.containers.run(image=image, name=name, detach=True)
        except DockerException as e:
            if attempt < retries - 1:
                logger.warning(f"Docker create failed (attempt {attempt+1}), retrying...")
                time.sleep(2)
            else:
                raise
```

**Purpose**: Handles transient Docker API failures.

---

### 6.4 Exception Handling Patterns

**Try-Except in Services**:
```python
def create_bucket(project_id, bucket_name):
    try:
        # Business logic
        bucket = Bucket(...)
        db.session.add(bucket)
        db.session.commit()
        return bucket
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Bucket already exists: {e}")
        raise ValueError(f"Bucket {bucket_name} already exists")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create bucket: {e}")
        raise
```

**Handlers Convert Exceptions to HTTP Responses**:
```python
def handle_create_bucket(request):
    try:
        bucket = BucketService.create_bucket(...)
        return jsonify(bucket.to_dict()), 200
    except ValueError as e:
        return error_response(409, "ALREADY_EXISTS", str(e))
    except Exception as e:
        return error_response(500, "INTERNAL", str(e))
```

---

## 7. Security & Access Control

### 7.1 Authentication Mechanisms (NEW)

#### **Mode 1: Development (Default) - No Authentication**

```python
AUTH_MODE = 'disabled'
MOCK_AUTH_ENABLED = True

# All requests accepted without credentials
# Good for: local development, testing
```

#### **Mode 2: Production - JWT Tokens**

```python
AUTH_MODE = 'required'

# Generate token:
POST /auth/tokens
{
  "user_id": "user@example.com",
  "project_id": "my-project"
}

# Response:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 86400
}

# Use token:
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Implementation**:
```python
@require_auth
def protected_endpoint():
    user_info = request.user_info  # Auto-populated by decorator
    # {
    #   'user_id': 'user@example.com',
    #   'project_id': 'my-project',
    #   'scopes': ['*'],
    #   'auth_type': 'jwt'
    # }
```

---

#### **Mode 3: Production - API Keys**

```python
# Generate API key:
POST /auth/api-keys
{
  "project_id": "my-project",
  "name": "My API Key",
  "expires_days": 365
}

# Response:
{
  "api_key": "gcps_abc123...",  # Only shown once!
  "key_id": "key-123",
  "created_at": "2026-02-02T..."
}

# Use API key:
X-API-Key: gcps_abc123...
```

**Storage**:
```sql
-- API keys stored with SHA-256 hash (not plaintext)
CREATE TABLE api_keys (
    id VARCHAR(64) PRIMARY KEY,
    key_hash VARCHAR(128) NOT NULL UNIQUE,  -- SHA-256(api_key)
    project_id VARCHAR(256) NOT NULL,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    is_active BOOLEAN
);
```

---

### 7.2 Authorization (IAM Emulation)

#### **IAM Policy Model**

```python
class IamPolicy(db.Model):
    resource_type = db.Column(db.String(50))  # 'bucket', 'instance', 'project'
    resource_id = db.Column(db.String(256))
    bindings = db.Column(JSON)  # [{"role": "roles/owner", "members": ["user:..."]}]
```

**Example Policy**:
```json
{
  "bindings": [
    {
      "role": "roles/storage.admin",
      "members": [
        "user:admin@example.com",
        "serviceAccount:my-sa@my-project.iam.gserviceaccount.com"
      ]
    },
    {
      "role": "roles/storage.objectViewer",
      "members": ["allUsers"]
    }
  ]
}
```

**Permission Check**:
```python
def check_permission(resource_type, resource_id, permission):
    # 1. Get IAM policy for resource
    # 2. Check if user's role grants permission
    # 3. Return True/False
```

---

### 7.3 Secrets Management

**Development**:
- Secrets in `.env` file (not committed)
- Default/weak secrets for local development

**Production**:
- Secrets from environment variables
- JWT secret auto-generated if not provided
- Database password from secure vault (e.g., AWS Secrets Manager)

```python
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or secrets.token_urlsafe(64)
DATABASE_URL = os.environ.get('DATABASE_URL')  # From secure source
```

---

### 7.4 Security Middleware (NEW)

#### **Rate Limiting**

```python
@rate_limit(limit=100, window_seconds=60)
def list_buckets():
    # Max 100 requests per minute per client
    # Returns 429 if exceeded
```

---

#### **Input Validation**

```python
@validate_request(
    body_schema={
        'name': {'required': True, 'pattern': 'bucket_name'},
        'location': {'required': True, 'pattern': 'region'}
    }
)
def create_bucket():
    # Validates input against schema
    # Blocks SQL injection, XSS attempts
    # Returns 400 if validation fails
```

---

#### **Security Headers**

```python
# All responses include:
X-Frame-Options: DENY                    # Prevent clickjacking
X-Content-Type-Options: nosniff          # Prevent MIME sniffing
Content-Security-Policy: default-src 'self'
Strict-Transport-Security: max-age=31536000  # Force HTTPS
```

---

## 8. Deployment & Runtime

### 8.1 Build Process

#### **Backend Build (Docker)**

```dockerfile
# gcp-emulator-package/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Run application
CMD ["python", "run.py"]
```

**Build Command**:
```bash
docker build -t gcs-backend:latest ./gcp-emulator-package
```

---

#### **Frontend Build (Docker)**

```dockerfile
# gcp-emulator-ui/Dockerfile
FROM node:18 AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

**Build Command**:
```bash
docker build -t gcs-frontend:latest ./gcp-emulator-ui
```

---

### 8.2 Deployment Methods

#### **Method 1: Docker Compose (Current)**

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

**Pros**:
- Simple single-command startup
- Automatic networking
- Volume management

**Cons**:
- Single-host only
- No high availability
- Not production-grade

---

#### **Method 2: Kubernetes (Production)**

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gcs-backend
spec:
  replicas: 3  # High availability
  selector:
    matchLabels:
      app: gcs-backend
  template:
    metadata:
      labels:
        app: gcs-backend
    spec:
      containers:
      - name: backend
        image: gcs-backend:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: AUTH_MODE
          value: "required"
```

**Deploy**:
```bash
kubectl apply -f kubernetes/
```

**Pros**:
- High availability (multiple replicas)
- Auto-scaling
- Health checks
- Load balancing

---

### 8.3 Runtime Dependencies

#### **System Requirements**

| Component | Requirement | Purpose |
|-----------|-------------|---------|
| Docker Engine | v20.10+ | Container runtime |
| Docker Compose | v2.0+ | Orchestration |
| PostgreSQL | v16 | Database |
| Python | 3.12+ | Backend runtime |
| Node.js | 18+ | Frontend build |
| Linux/macOS | Any | Host OS (Docker support) |

#### **Resource Requirements**

```yaml
Minimum:
  CPU: 2 cores
  RAM: 4 GB
  Disk: 10 GB

Recommended:
  CPU: 4 cores
  RAM: 8 GB
  Disk: 50 GB (for storage emulation)
```

---

### 8.4 CI/CD Pipeline (Proposed)

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          docker-compose up -d postgres
          cd gcp-emulator-package
          pytest
          
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker images
        run: |
          docker build -t gcs-backend:${{github.sha}} ./gcp-emulator-package
          docker build -t gcs-frontend:${{github.sha}} ./gcp-emulator-ui
          
      - name: Push to registry
        run: |
          docker push gcs-backend:${{github.sha}}
          docker push gcs-frontend:${{github.sha}}
          
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: |
          kubectl set image deployment/gcs-backend backend=gcs-backend:${{github.sha}}
```

---

## 9. Strengths, Risks & Improvements

### 9.1 Architectural Strengths

#### ✅ **1. Clear Separation of Concerns**

```
Routes (URLs) → Handlers (HTTP) → Services (Logic) → Models (Data)
```

- **Easy to test**: Each layer can be tested independently
- **Easy to maintain**: Changes isolated to specific layers
- **Easy to understand**: Clear responsibility boundaries

---

#### ✅ **2. GCP API Compatibility**

- Matches real GCP API endpoints and response formats
- Works with official `gcloud` CLI without modification
- Works with Google Cloud Python SDK
- Terraform-compatible (with minor adjustments)

**Example - Identical API Surfaces**:
```python
# Real GCP
POST https://storage.googleapis.com/storage/v1/b?project=my-project

# GCP Stimulator
POST http://localhost:8080/storage/v1/b?project=my-project

# Same request/response format!
```

---

#### ✅ **3. Real Infrastructure Mapping**

**Docker Containers = VM Instances**
- Instances aren't just database records
- Real containers with CPU/memory limits
- Actual processes running
- Can SSH into containers (`docker exec`)

**Docker Networks = VPC Networks**
- Networks aren't just logical concepts
- Real Docker bridge networks
- Containers can actually communicate
- Network isolation works

---

#### ✅ **4. Modular Design (Microservices-Ready)**

```
Current: Monolith
│
└──> Easy to extract:
     ├── Storage Service (buckets + objects)
     ├── Compute Service (instances + Docker)
     ├── Network Service (VPC + firewall)
     └── IAM Service (auth + policies)
```

Each service has:
- Own models
- Own routes
- Own handlers
- Own services
- Minimal cross-dependencies

---

#### ✅ **5. Production-Grade Security (NEW)**

- JWT token authentication
- API key management
- Rate limiting
- Input validation (SQL injection, XSS prevention)
- HTTPS/TLS support
- Security headers
- Configurable auth modes (dev/prod)

---

### 9.2 Current Risks & Bottlenecks

#### ⚠️ **1. Single Database Bottleneck**

**Problem**:
```
All API Requests → Single PostgreSQL Instance
```

**Impact**:
- Database becomes bottleneck under high load
- No horizontal scaling
- Single point of failure

**Evidence**:
```python
# All services use same db.session
bucket = BucketService.create_bucket(...)  # DB write
instance = ComputeService.create_instance(...)  # DB write
network = NetworkService.create_network(...)  # DB write

# All competing for same connection pool
```

**Mitigation (Future)**:
- Database read replicas
- Connection pooling (PgBouncer)
- Caching layer (Redis)
- Separate databases per service

---

#### ⚠️ **2. Docker API Dependency**

**Problem**:
- Compute service directly calls Docker API
- If Docker daemon fails, compute service fails
- Docker API is synchronous (blocking)

```python
# Blocking Docker API call
container = docker_client.containers.run(...)  # Can take 5-10 seconds
```

**Impact**:
- Slow instance creation (5-10 seconds per instance)
- No async/parallel instance creation
- Docker API errors propagate to users

**Mitigation (Future)**:
- Async task queue (Celery + Redis)
- Background workers for Docker operations
- Retry logic with exponential backoff

---

#### ⚠️ **3. File System Storage Limitations**

**Current**:
```python
# Objects stored as files
storage/
  project-id/
    bucket-name/
      object-name.txt
```

**Problems**:
- No distributed storage
- Limited to single host disk
- No replication
- Performance degrades with many files

**Impact**:
- Can't scale beyond single host
- Risk of data loss (no redundancy)
- Slow for large buckets (100K+ objects)

**Mitigation (Future)**:
- S3-compatible storage backend (MinIO)
- Distributed file system (GlusterFS, Ceph)
- Object store abstraction layer

---

#### ⚠️ **4. No Transaction Consistency Across Services**

**Problem**:
```python
# What if this sequence fails partway through?
1. Create Instance record in DB
2. Create Docker container
3. Create Network Interface record
4. Attach container to network

# If step 3 fails:
# - Instance exists in DB
# - Container exists in Docker
# - But network interface missing
# = Inconsistent state!
```

**Impact**:
- Orphaned Docker containers
- Database records with no containers
- Manual cleanup required

**Current Mitigation**:
```python
try:
    # Step 1
    instance = create_instance_record()
    # Step 2
    container = create_docker_container()
    # Step 3 (link them)
    instance.container_id = container.id
    db.session.commit()
except Exception:
    # Cleanup on error
    if container:
        container.remove()
    db.session.rollback()
```

**Better Solution (Future)**:
- Saga pattern for distributed transactions
- Compensation logic for rollbacks
- Event sourcing for audit trail

---

#### ⚠️ **5. Limited Concurrency**

**Current**:
- Flask default: single-threaded (not production server)
- No async/await support
- No request queuing

**Evidence**:
```python
# run.py
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)  # Development server!
```

**Impact**:
- One request at a time
- Slow for concurrent users
- Timeouts under load

**Mitigation (Immediate)**:
```python
# Use production WSGI server
if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8080, threads=8)
```

**Better Solution (Future)**:
- Gunicorn with multiple workers
- Async framework (FastAPI)
- Load balancer (Nginx)

---

### 9.3 Technical Debt

#### **1. Manual Migrations**

**Current**:
```bash
# Must run manually
python migrations/001_add_versioning.py
python migrations/002_add_compute.py
# ... (19 migrations)
```

**Should Be**:
```bash
# Use Alembic for automatic migrations
alembic upgrade head
```

---

#### **2. Mixed Responsibilities in Handlers**

**Current**:
```python
# Handler does too much
def handle_create_bucket(request):
    # 1. Parse request (OK)
    # 2. Validate input (should be in validator)
    # 3. Business logic (should be in service)
    # 4. Format response (OK)
```

**Should Be**:
```python
def handle_create_bucket(request):
    # 1. Parse request
    data = parse_request(request)
    # 2. Call service (validation inside)
    bucket = BucketService.create_bucket(**data)
    # 3. Format response
    return format_response(bucket)
```

---

#### **3. Inconsistent Error Handling**

**Current**:
- Some handlers use `error_response()` (good)
- Some return plain `jsonify({'error': ...})` (inconsistent)
- Some raise exceptions (not caught properly)

**Should Be**:
- Standardize on `error_response()` everywhere
- Global exception handler for uncaught errors
- Consistent error codes (GCP-style)

---

#### **4. No Health Checks**

**Current**:
```python
@health_bp.route('/health')
def health():
    return jsonify({"status": "ok"})  # Always returns OK!
```

**Should Be**:
```python
@health_bp.route('/health')
def health():
    checks = {
        'database': check_db_connection(),
        'docker': check_docker_connection(),
        'disk': check_disk_space()
    }
    healthy = all(checks.values())
    return jsonify(checks), 200 if healthy else 503
```

---

### 9.4 Clear Suggestions for Improvement

#### **Phase 1: Immediate (0-1 month)**

**1. Add Production WSGI Server**
```bash
pip install gunicorn

# run.py
if __name__ == '__main__':
    import gunicorn.app.base
    # Run with Gunicorn instead of Flask dev server
```
**Impact**: 10x concurrency improvement

---

**2. Add Health Checks**
```python
# Add to handlers/health.py
@health_bp.route('/health/live')
def liveness():
    return jsonify({"status": "ok"}), 200

@health_bp.route('/health/ready')
def readiness():
    # Check DB, Docker
    if not db_ready() or not docker_ready():
        return jsonify({"status": "not ready"}), 503
    return jsonify({"status": "ready"}), 200
```
**Impact**: Enables Kubernetes health probes

---

**3. Add Prometheus Metrics**
```python
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
# Auto-exposes /metrics endpoint
```
**Impact**: Observability (request rates, latencies, errors)

---

#### **Phase 2: Short-term (1-3 months)**

**4. Migrate to Alembic**
```bash
pip install alembic
alembic init migrations
# Convert manual migrations to Alembic versions
alembic upgrade head
```
**Impact**: Automated, reversible migrations

---

**5. Add Redis Caching**
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@cache.memoize(timeout=300)
def get_bucket(bucket_id):
    return Bucket.query.get(bucket_id)
```
**Impact**: Reduce database load, faster responses

---

**6. Add Async Task Queue**
```python
from celery import Celery

celery = Celery(app.name, broker='redis://localhost:6379')

@celery.task
def create_instance_async(instance_id):
    # Long-running Docker operations
    create_docker_container()
    
# In handler:
task = create_instance_async.delay(instance_id)
return jsonify({"operation_id": task.id}), 202  # Accepted
```
**Impact**: Non-blocking operations, better UX

---

#### **Phase 3: Long-term (3-6 months)**

**7. Extract Microservices**
```
Storage Service (port 8081)
Compute Service (port 8082)
Network Service (port 8083)
IAM Service (port 8084)
API Gateway (port 8080) → Routes to services
```
**Impact**: Independent scaling, better isolation

---

**8. Add Distributed Tracing**
```python
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor

FlaskInstrumentor().instrument_app(app)
# Traces requests across services
```
**Impact**: Debug performance issues, see request flow

---

**9. Add Event Sourcing**
```python
# Instead of updating state directly:
instance.state = "RUNNING"  # Current

# Emit events:
emit_event("InstanceStarted", instance_id)
# Event log becomes source of truth
```
**Impact**: Audit trail, event replay, CQRS patterns

---

### 9.5 Performance Benchmarks (Estimated)

| Operation | Current | After Phase 1 | After Phase 2 | After Phase 3 |
|-----------|---------|---------------|---------------|---------------|
| List Buckets | 50 req/s | 500 req/s | 2000 req/s | 10K req/s |
| Create Instance | 1 instance/10s | 1 instance/10s | 10 instances/s | 100 instances/s |
| Database Queries | 100 q/s | 500 q/s | 5K q/s (cached) | 50K q/s (distributed) |
| Concurrent Users | 10 | 100 | 1000 | 10K |

---

## Summary

### What We Built

**GCP Stimulator** is a **local Google Cloud Platform emulator** that:
- Emulates GCS (Storage), GCE (Compute), VPC (Networking), IAM
- Works with real `gcloud` CLI and Python SDKs
- Uses Docker containers as VM instances
- Uses PostgreSQL for metadata
- Has production-grade security features (NEW)
- Fully self-contained (no internet required)

### Key Architectural Decisions

1. **Monolith with clear module boundaries** (easy to extract microservices later)
2. **Real infrastructure mapping** (Docker containers = VMs, Docker networks = VPCs)
3. **GCP API compatibility** (works with official tooling)
4. **Layered architecture** (Routes → Handlers → Services → Models)
5. **Security-first design** (auth, rate limiting, validation)

### Production Readiness

**Current State**: Demo/Development Ready
- ✅ Core features working
- ✅ Basic security implemented
- ⚠️ Needs production hardening

**To Make Production-Ready**:
- Add Gunicorn/UWSGI server
- Add health checks
- Add metrics/monitoring
- Database connection pooling
- Async task processing
- High availability setup

### Best Use Cases

1. **Local Development**: Test GCP code without cloud costs
2. **CI/CD**: Run integration tests against emulator
3. **Training**: Learn GCP concepts safely
4. **Demos**: Show GCP features without real account
