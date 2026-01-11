# GCP Emulator - Current Implementation & Working Architecture

## Executive Summary

Your GCP Emulator is a **LocalStack-style cloud simulator** for Google Cloud Platform that runs completely on your local Windows machine. It simulates three major GCP services: **Storage (GCS)**, **IAM**, and **Compute Engine** - all without needing real GCP credentials or incurring cloud costs.

## What Runs on Your Machine

### 1. **Backend Server** (Python Flask)
- **Location**: `C:\Users\ansh.joshi\gcp_emulator\gcp-emulator-package`
- **Port**: 8080
- **Technology**: Flask 2.3.3, Python 3.12
- **Database**: PostgreSQL (running in Docker container)
- **Execution**: Runs directly in Windows or WSL2 Ubuntu

### 2. **Frontend UI** (React/TypeScript)
- **Location**: `C:\Users\ansh.joshi\gcp_emulator\gcp-emulator-ui`
- **Port**: 3000 (Vite dev server)
- **Technology**: React 18, TypeScript, TailwindCSS
- **Purpose**: Web-based dashboard to manage buckets, objects, service accounts, and compute instances

### 3. **Docker Engine** (WSL2)
- **Purpose**: Simulates GCP Compute Engine VMs using Docker containers
- **Location**: WSL2 Ubuntu subsystem
- **Socket**: `/var/run/docker.sock`
- **Containers**: 
  - `gcp-postgres` - PostgreSQL database
  - `gcs-compute-*` - Simulated VM instances

### 4. **PostgreSQL Database**
- **Container**: `gcp-postgres`
- **Port**: 5432
- **Purpose**: Stores all metadata (buckets, objects, service accounts, instances, etc.)
- **Connection**: `postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator`

### 5. **File Storage**
- **Location**: `/home/anshjoshi/gcp_emulator_storage` (in WSL2) or `./storage` (Windows)
- **Purpose**: Actual object/file data storage (bucket contents)
- **Structure**: Files organized by bucket/object paths

---

## How It Actually Works

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WINDOWS MACHINE                              │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Web Browser (http://localhost:3000)                           │ │
│  │  React UI - Manage buckets, objects, VMs                       │ │
│  └────────────────────────┬───────────────────────────────────────┘ │
│                           │ HTTP Requests                            │
│                           ↓                                          │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Flask Backend (http://localhost:8080)                         │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  REST API Endpoints                                       │ │ │
│  │  │  ├─ /storage/v1/*        → Storage Service               │ │ │
│  │  │  ├─ /v1/projects/*       → IAM Service                    │ │ │
│  │  │  └─ /compute/v1/*        → Compute Service               │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  Services Layer                                           │ │ │
│  │  │  ├─ BucketService       → Bucket CRUD                    │ │ │
│  │  │  ├─ ObjectService       → Object upload/download         │ │ │
│  │  │  ├─ IAMService          → Service accounts, keys         │ │ │
│  │  │  └─ ComputeService      → VM lifecycle management        │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  Data Layer                                               │ │ │
│  │  │  ├─ SQLAlchemy ORM     → Database models                 │ │ │
│  │  │  └─ File System        → Object storage                  │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  └─────────────┬───────────────────────┬──────────────────────────┘ │
│                │ SQL Queries           │ Docker API Calls           │
│                ↓                       ↓                            │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              WSL2 UBUNTU SUBSYSTEM                             │ │
│  │  ┌──────────────────────┐    ┌───────────────────────────┐   │ │
│  │  │  PostgreSQL          │    │  Docker Engine             │   │ │
│  │  │  Container           │    │  (/var/run/docker.sock)    │   │ │
│  │  │  (gcp-postgres)      │    │  ┌──────────────────────┐ │   │ │
│  │  │  Port: 5432          │    │  │ Compute Containers   │ │   │ │
│  │  │  ┌────────────────┐ │    │  │ gcs-compute-xxx      │ │   │ │
│  │  │  │ Tables:        │ │    │  │ (Simulated VMs)      │ │   │ │
│  │  │  │ - buckets      │ │    │  └──────────────────────┘ │   │ │
│  │  │  │ - objects      │ │    │                            │   │ │
│  │  │  │ - instances    │ │    │                            │   │ │
│  │  │  │ - service_acts │ │    │                            │   │ │
│  │  │  └────────────────┘ │    └───────────────────────────┘   │ │
│  │  └──────────────────────┘                                     │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │  File Storage: /home/anshjoshi/gcp_emulator_storage/    │ │ │
│  │  │  ├── bucket1/                                            │ │ │
│  │  │  │   ├── file1.txt                                       │ │ │
│  │  │  │   └── folder/file2.pdf                                │ │ │
│  │  │  └── bucket2/                                            │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘

      ┌──────────────────────────────────────────────────────┐
      │  GCP SDK / gcloud CLI (Optional)                     │
      │  Uses CLOUDSDK_API_ENDPOINT_OVERRIDES_* env vars     │
      │  to redirect commands to localhost:8080              │
      └──────────────────────────────────────────────────────┘
```

---

## Detailed Component Breakdown

### 1. Flask Backend Server

**File**: `app/factory.py` → Creates the Flask application

**What it does**:
1. Loads configuration from environment variables
2. Initializes PostgreSQL database connection
3. Sets up CORS for frontend communication
4. Registers API routes (blueprints)
5. Starts background workers

**Key Components**:

#### A. **Routes/Blueprints** (`app/routes/`)
- `bucket_routes.py` - GCS bucket operations
- `compute_routes.py` - Compute instance management
- `compute_v1_routes.py` - GCP Compute API v1 compatible endpoints
- `vpc_routes.py` - Network/VPC operations

#### B. **Services** (`app/services/`)

**Storage Services**:
- `bucket_service.py` - Creates, lists, deletes buckets in PostgreSQL
- `object_service.py` - Handles file upload/download, stores files on disk
- `resumable_upload_service.py` - Large file uploads in chunks
- `object_versioning_service.py` - Object version management

**IAM Services**:
- `iam_service.py` - Service account creation, key generation (JSON/P12)

**Compute Services**:
- `compute_service.py` - VM instance lifecycle (create, start, stop, terminate)
- `docker_driver.py` - Talks to Docker Engine, manages containers
- `compute_sync_worker.py` - Background thread that syncs Docker container state with database every 5 seconds

#### C. **Models** (`app/models/`)
SQLAlchemy ORM models that map to PostgreSQL tables:
- `bucket.py` → `buckets` table
- `object.py` → `objects` table
- `instance.py` → `instances` table
- `service_account.py` → `service_accounts` table

---

### 2. How Each Service Works

#### **Storage (GCS) Flow**

**Example: Uploading a file**

```
User (UI or SDK)
    ↓ POST /storage/v1/b/my-bucket/o?uploadType=media
Flask Route (bucket_routes.py)
    ↓ Calls ObjectService.create_object()
ObjectService
    ├─ Validates bucket exists (PostgreSQL)
    ├─ Generates unique object ID
    ├─ Saves file to disk: /storage/my-bucket/file.txt
    ├─ Calculates MD5 and CRC32C checksums
    └─ Creates database record in 'objects' table
    ↓ Returns JSON response
```

**Database Record**:
```sql
INSERT INTO objects (
    id, bucket_id, name, size, content_type, 
    md5_hash, crc32c, storage_path, generation
) VALUES (...);
```

**File on Disk**:
```
/home/anshjoshi/gcp_emulator_storage/my-bucket/file.txt
```

---

#### **IAM Service Flow**

**Example: Creating a service account**

```
User
    ↓ POST /v1/projects/test-project/serviceAccounts
Flask Route
    ↓ Calls IAMService.create_service_account()
IAMService
    ├─ Generates unique email: sa@test-project.iam.gserviceaccount.com
    ├─ Creates database record in 'service_accounts' table
    └─ Returns service account JSON
    ↓ Response
```

**Example: Creating a key**

```
User
    ↓ POST /v1/projects/.../serviceAccounts/.../keys
IAMService.create_key()
    ├─ Generates RSA key pair (2048-bit)
    ├─ Stores private key in database
    └─ Returns JSON key file (contains private_key_id, private_key, etc.)
```

**Note**: Keys are **fake** - they don't work with real GCP but allow you to test authentication flows locally.

---

#### **Compute Engine Flow**

**Example: Creating a VM instance**

```
User (UI)
    ↓ POST /compute/instances
    {
      "name": "my-vm",
      "image": "alpine:latest",
      "cpu": 1,
      "memory_mb": 512
    }
Flask Route (compute_routes.py)
    ↓ Calls ComputeService.run_instance()
ComputeService
    ├─ Creates record in 'instances' table (state: pending)
    ├─ Calls DockerDriver.create_container()
    │
    ↓ DockerDriver talks to Docker Engine via socket
DockerDriver
    ├─ Pulls Docker image if needed: docker pull alpine:latest
    ├─ Creates container: docker run -d --name gcs-compute-abc123 alpine
    └─ Returns container_id
    ↓
ComputeService
    ├─ Updates instance.container_id = "abc123..."
    ├─ Updates instance.state = "running"
    └─ Commits to database
    ↓ Returns instance JSON
```

**Docker Container Created**:
```bash
# In WSL2
docker ps
CONTAINER ID   IMAGE           STATUS    NAMES
abc123456789   alpine:latest   Up 2 min  gcs-compute-abc12345
```

**Database Record**:
```sql
instances table:
id: abc-123-uuid
name: my-vm
image: alpine:latest
cpu: 1
memory_mb: 512
container_id: abc123456789
state: running
```

**Background Sync Worker**:
Every 5 seconds, a background thread runs:
```python
# compute_sync_worker.py
while True:
    instances = db.query(Instance).all()
    for instance in instances:
        container_state = docker.inspect(instance.container_id)
        if container_state == "exited":
            instance.state = "stopped"
            db.commit()
    sleep(5)
```

This keeps the database state in sync with actual Docker containers.

---

### 3. React Frontend UI

**File**: `gcp-emulator-ui/src/`

**What it does**:
- Provides web interface similar to Google Cloud Console
- Makes HTTP requests to Flask backend (localhost:8080)
- Displays buckets, objects, service accounts, compute instances

**Key Files**:

```
src/
├── api/
│   ├── compute.ts          → fetch('/compute/instances')
│   ├── storage.ts          → fetch('/storage/v1/b')
│   └── iam.ts              → fetch('/v1/projects/.../serviceAccounts')
├── pages/
│   ├── ComputeInstancesPage.tsx    → Lists VMs, shows state
│   ├── StoragePage.tsx              → Lists buckets
│   └── IAMPage.tsx                  → Lists service accounts
├── components/
│   └── compute/
│       └── CreateInstanceModal.tsx  → Form to create VM
└── App.tsx                          → Main app, routing
```

**Example Flow** (Creating VM from UI):

```
User clicks "Create Instance" button
    ↓
CreateInstanceModal opens (form)
    ↓
User fills: name="test-vm", image="nginx:latest", cpu=2, memory=1024
    ↓
User clicks "Create"
    ↓
React component calls API function:
    createInstance({ name, image, cpu, memory_mb })
    ↓
Frontend sends: POST http://localhost:8080/compute/instances
    ↓
Backend receives request
    ↓
ComputeService creates Docker container
    ↓
Backend returns: { id, name, state: "running", ... }
    ↓
React updates UI - new instance appears in list
    ↓
Auto-refresh every 5 seconds fetches latest state
```

---

### 4. Database Schema (PostgreSQL)

**Key Tables**:

```sql
-- Buckets
CREATE TABLE buckets (
    id VARCHAR(63) PRIMARY KEY,
    name VARCHAR(63) UNIQUE NOT NULL,
    project_id VARCHAR(63),
    location VARCHAR(50) DEFAULT 'US',
    storage_class VARCHAR(50) DEFAULT 'STANDARD',
    versioning_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    ...
);

-- Objects (files)
CREATE TABLE objects (
    id VARCHAR(36) PRIMARY KEY,
    bucket_id VARCHAR(63) REFERENCES buckets(id),
    name VARCHAR(1024) NOT NULL,
    size BIGINT,
    content_type VARCHAR(255),
    md5_hash VARCHAR(32),
    crc32c VARCHAR(20),
    storage_path TEXT,  -- Path to actual file on disk
    generation BIGINT,  -- For versioning
    created_at TIMESTAMP,
    ...
);

-- Compute Instances
CREATE TABLE instances (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    project_id VARCHAR(255),
    zone VARCHAR(100) DEFAULT 'us-central1-a',
    machine_type VARCHAR(100) DEFAULT 'e2-micro',
    image VARCHAR(500) NOT NULL,  -- Docker image
    cpu INTEGER DEFAULT 1,
    memory_mb INTEGER DEFAULT 512,
    container_id VARCHAR(100) UNIQUE,  -- Docker container ID
    state VARCHAR(20) DEFAULT 'pending',  -- pending|running|stopped|terminated
    created_at TIMESTAMP,
    ...
);

-- Service Accounts
CREATE TABLE service_accounts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    project_id VARCHAR(255),
    unique_id VARCHAR(255),
    created_at TIMESTAMP,
    ...
);

-- Service Account Keys
CREATE TABLE service_account_keys (
    id SERIAL PRIMARY KEY,
    service_account_id INTEGER REFERENCES service_accounts(id),
    key_id VARCHAR(255) UNIQUE,
    private_key TEXT,  -- RSA private key (PEM format)
    public_key TEXT,
    key_type VARCHAR(20) DEFAULT 'USER_MANAGED',
    created_at TIMESTAMP,
    ...
);
```

---

### 5. Docker Integration (Compute VMs)

**How VMs are Simulated**:

1. **VM = Docker Container**
   - Each GCP compute instance is a Docker container
   - Container image = VM disk image
   - Container resources (CPU, memory) = VM resources

2. **Container Naming Convention**:
   ```
   gcs-compute-{instance_id_first_8_chars}
   Example: gcs-compute-abc12345
   ```

3. **Docker Commands** (What happens behind the scenes):

   **Create VM**:
   ```bash
   docker run -d \
     --name gcs-compute-abc12345 \
     --cpus=1 \
     --memory=512m \
     alpine:latest \
     /bin/sh
   ```

   **Stop VM**:
   ```bash
   docker stop gcs-compute-abc12345
   ```

   **Start VM**:
   ```bash
   docker start gcs-compute-abc12345
   ```

   **Terminate VM**:
   ```bash
   docker rm -f gcs-compute-abc12345
   ```

4. **State Synchronization**:
   - Background worker checks Docker container state every 5 seconds
   - Updates database to match actual container state
   - Example: If container crashes, database state becomes "stopped"

---

## How to Use the Emulator

### Option 1: Use the Web UI

```powershell
# Terminal 1: Start backend
cd gcp-emulator-package
python run.py

# Terminal 2: Start frontend
cd gcp-emulator-ui
npm run dev

# Open browser: http://localhost:3000
```

### Option 2: Use GCP SDK (gcloud CLI)

```powershell
# Configure environment variables
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE = "http://127.0.0.1:8080"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_IAM = "http://127.0.0.1:8080"
$env:CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE = "http://127.0.0.1:8080"
$env:CLOUDSDK_CORE_PROJECT = "test-project"

# Now use gcloud normally - it hits your local emulator!
gcloud storage buckets create gs://my-bucket
gcloud storage cp file.txt gs://my-bucket/
gcloud iam service-accounts list
gcloud compute instances list
```

### Option 3: Use Python SDK

```python
from google.cloud import storage

# Set environment variable first
# export STORAGE_EMULATOR_HOST=http://localhost:8080

# SDK automatically uses emulator
client = storage.Client(project="test-project")
bucket = client.create_bucket("my-bucket")
blob = bucket.blob("file.txt")
blob.upload_from_filename("local-file.txt")
```

---

## Data Flow Example: Complete Request Lifecycle

**Scenario**: User uploads a file via web UI

```
1. USER ACTION
   User clicks "Upload" in browser
   Selects file: document.pdf (2 MB)

2. FRONTEND (React)
   ├─ File selected via <input type="file" />
   ├─ JavaScript reads file as ArrayBuffer
   ├─ Constructs FormData with file
   └─ Sends: POST http://localhost:8080/storage/v1/b/my-bucket/o
      Body: multipart/form-data
      File data: document.pdf binary

3. NETWORK
   HTTP request travels through Windows network stack
   Destination: localhost:8080 (Flask server)

4. FLASK BACKEND RECEIVES REQUEST
   ├─ CORS middleware checks origin (allows localhost:3000)
   ├─ Request logging middleware logs: "POST /storage/v1/b/my-bucket/o"
   └─ Routes to: bucket_routes.upload_object()

5. ROUTE HANDLER (bucket_routes.py)
   def upload_object():
       bucket_name = "my-bucket"
       file = request.files['file']
       file_name = "document.pdf"
       
       # Call service layer
       result = object_service.create_object(
           bucket_id=bucket_name,
           name=file_name,
           data=file.stream,
           content_type="application/pdf",
           size=2097152  # 2 MB
       )
       return jsonify(result), 201

6. SERVICE LAYER (object_service.py)
   def create_object():
       # Step A: Validate bucket exists
       bucket = db.query(Bucket).filter_by(name="my-bucket").first()
       if not bucket:
           raise NotFoundError("Bucket not found")
       
       # Step B: Generate unique ID and path
       object_id = str(uuid.uuid4())  # "f47ac10b-58cc-4372-a567-0e02b2c3d479"
       storage_path = "/storage/my-bucket/document.pdf"
       
       # Step C: Save file to disk
       os.makedirs("/storage/my-bucket", exist_ok=True)
       with open(storage_path, 'wb') as f:
           f.write(file_data)
       
       # Step D: Calculate checksums
       md5_hash = hashlib.md5(file_data).hexdigest()
       crc32c_hash = calculate_crc32c(file_data)
       
       # Step E: Create database record
       obj = Object(
           id=object_id,
           bucket_id=bucket.id,
           name="document.pdf",
           size=2097152,
           content_type="application/pdf",
           md5_hash=md5_hash,
           crc32c=crc32c_hash,
           storage_path=storage_path,
           generation=1,
           created_at=datetime.utcnow()
       )
       db.session.add(obj)
       db.session.commit()
       
       # Step F: Return object metadata
       return obj.to_dict()

7. DATABASE UPDATE
   PostgreSQL executes:
   INSERT INTO objects (id, bucket_id, name, size, ...)
   VALUES ('f47ac10b...', 'my-bucket', 'document.pdf', 2097152, ...);

8. FILE SYSTEM UPDATE
   File saved to:
   /home/anshjoshi/gcp_emulator_storage/my-bucket/document.pdf

9. RESPONSE TRAVELS BACK
   Flask returns JSON:
   {
     "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
     "name": "document.pdf",
     "bucket": "my-bucket",
     "size": 2097152,
     "contentType": "application/pdf",
     "md5Hash": "5d41402abc4b2a76b9719d911017c592",
     "crc32c": "yZRlqg==",
     "generation": "1",
     "timeCreated": "2026-01-10T10:30:00.000Z",
     "selfLink": "http://localhost:8080/storage/v1/b/my-bucket/o/document.pdf"
   }

10. FRONTEND RECEIVES RESPONSE
    React component updates state:
    ├─ Adds new object to objects array
    ├─ UI re-renders
    └─ User sees "document.pdf" in file list
```

**Result**:
- ✅ File stored on disk: `/storage/my-bucket/document.pdf`
- ✅ Metadata in database: `objects` table
- ✅ User sees file in UI
- ✅ Can be downloaded later via GET request

---

## Key Implementation Details

### 1. **Why WSL2 for Compute?**
- Docker Engine runs natively on Linux
- Better performance than Windows Docker Desktop
- Direct socket access: `/var/run/docker.sock`
- Flask server can run in Windows but talks to WSL2 Docker

### 2. **Thread Safety**
- Database: SQLAlchemy handles connection pooling
- Docker: Each operation creates fresh client (`docker.from_env()`)
- File I/O: Uses `pathlib` for cross-platform paths

### 3. **No Real GCP Credentials Needed**
- Mock authentication: Any token accepted
- Service account keys are fake (generated locally)
- No network calls to real GCP APIs (unless proxy mode enabled)

### 4. **Proxy Mode (Optional)**
- Can route specific APIs to real GCP
- Example: Storage local, Compute real GCP
- Configured via environment variables

---

## System Requirements

**What you need installed**:
1. ✅ Python 3.12+
2. ✅ PostgreSQL (Docker container or native)
3. ✅ WSL2 Ubuntu (for Docker)
4. ✅ Docker Engine (in WSL2)
5. ✅ Node.js 18+ (for frontend)

**Optional**:
- gcloud CLI (to use command-line tools)
- google-cloud-storage Python SDK

---

## Performance Characteristics

- **Storage**: Fast - files written directly to disk
- **Database**: PostgreSQL - production-grade, handles thousands of objects
- **Compute**: Lightweight - Docker containers start in ~2 seconds
- **UI**: Responsive - React with auto-refresh every 5 seconds

---

## Limitations (What's NOT Simulated)

1. **Real GCP Features**:
   - ❌ No Google authentication (uses mock tokens)
   - ❌ No IAM permissions enforcement (all operations allowed)
   - ❌ No billing/quotas
   - ❌ No regional replication
   - ❌ Compute VMs don't have public IPs (containers on local network)

2. **Compute Engine**:
   - ❌ No persistent disks (containers are ephemeral)
   - ❌ No networking between VMs
   - ❌ No SSH access to VMs
   - ❌ Limited to Docker images (not GCE images)

3. **Storage**:
   - ❌ No object ACLs (all objects publicly accessible locally)
   - ❌ No signed URLs
   - ❌ No Cloud CDN integration

---

## Summary

Your GCP Emulator is a **complete local simulator** that:

✅ **Runs entirely on your machine** (Windows + WSL2)
✅ **Simulates 3 GCP services** (Storage, IAM, Compute)
✅ **Uses real technologies**: Flask, PostgreSQL, Docker, React
✅ **Works with GCP SDKs** via endpoint override environment variables
✅ **Stores data locally**: Database + file system
✅ **Has a web UI** similar to Google Cloud Console
✅ **Costs nothing** - no cloud charges
✅ **Fast development** - instant feedback, no network latency

**Perfect for**:
- Developing cloud applications locally
- Testing GCP integrations without cloud costs
- Learning GCP APIs
- CI/CD pipelines (run tests against emulator)
- Offline development

The implementation is **production-quality code** with proper architecture (MVC pattern), database migrations, error handling, and comprehensive testing. It's essentially a mini-version of GCP running on your laptop! 🚀
