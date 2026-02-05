# 🔧 How GCP Stimulator Works

**A deep dive into the architecture and internal workings of GCP Stimulator**

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Layers](#architecture-layers)
3. [Request Flow](#request-flow)
4. [Compute Engine Implementation](#compute-engine-implementation)
5. [VPC Networks Implementation](#vpc-networks-implementation)
6. [Cloud Storage Implementation](#cloud-storage-implementation)
7. [IAM Implementation](#iam-implementation)
8. [Database Design](#database-design)
9. [Docker Integration](#docker-integration)
10. [Frontend Integration](#frontend-integration)
11. [gcloud CLI Integration](#gcloud-cli-integration)

---

## 🌐 System Overview

GCP Stimulator is a **local GCP emulator** that simulates Google Cloud Platform services without requiring actual GCP credentials or cloud resources. It achieves this through:

1. **API Emulation** - FastAPI backend mimics GCP REST APIs
2. **Docker Integration** - VM instances run as real Docker containers
3. **Database Persistence** - PostgreSQL stores all metadata
4. **File System Storage** - Objects stored locally on disk
5. **Frontend UI** - React dashboard for visual management

```
┌─────────────────────────────────────────────────────────────┐
│                      GCP Stimulator                          │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React)          Backend (FastAPI)                 │
│  Port 3000                 Port 8080                         │
│  ┌──────────────┐         ┌──────────────────┐             │
│  │  Storage UI  │────────▶│  Storage API     │             │
│  │  Compute UI  │────────▶│  Compute API     │────┐        │
│  │  VPC UI      │────────▶│  VPC API         │    │        │
│  │  IAM UI      │────────▶│  IAM API         │    │        │
│  └──────────────┘         └──────────────────┘    │        │
│                                  │                 │        │
│                                  ▼                 ▼        │
│                           ┌──────────────┐  ┌──────────┐   │
│                           │ PostgreSQL   │  │  Docker  │   │
│                           │   RDS        │  │  Engine  │   │
│                           └──────────────┘  └──────────┘   │
│                                  │                 │        │
│                                  ▼                 ▼        │
│                           ┌──────────────┐  ┌──────────┐   │
│                           │  Metadata    │  │Container │   │
│                           │  (8 tables)  │  │ Instances│   │
│                           └──────────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture Layers

### Layer 1: API Gateway (FastAPI)

**File:** `minimal-backend/main.py`

```python
from fastapi import FastAPI
from api import storage, compute, vpc, projects

app = FastAPI()

# Mount all service APIs
app.include_router(storage.router)
app.include_router(compute.router)
app.include_router(vpc.router)
app.include_router(projects.router)
```

**Purpose:**
- Receives HTTP requests from gcloud CLI or frontend
- Routes requests to appropriate service handlers
- Returns GCP-compatible JSON responses

### Layer 2: Service Handlers

**Files:**
- `minimal-backend/api/storage.py` - Cloud Storage logic
- `minimal-backend/api/compute.py` - Compute Engine logic
- `minimal-backend/api/vpc.py` - VPC Networks logic
- `minimal-backend/api/projects.py` - Projects logic

**Purpose:**
- Implement GCP API business logic
- Interact with database and Docker
- Format responses to match GCP API specs

### Layer 3: Docker Manager

**File:** `minimal-backend/docker_manager.py`

```python
import docker

docker_client = docker.from_env()

def create_container(name, network, image="ubuntu:22.04"):
    """Create Docker container for GCP VM instance"""
    container = docker_client.containers.run(
        image=image,
        name=f"gcp-vm-{name}",
        network=network,
        detach=True,
        tty=True
    )
    return container
```

**Purpose:**
- Manages Docker container lifecycle
- Maps GCP instances to containers
- Handles networking and IP assignment

### Layer 4: Database Layer

**File:** `minimal-backend/database.py`

```python
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Instance(Base):
    __tablename__ = "instances"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    container_id = Column(String)
    status = Column(String, default="RUNNING")
```

**Purpose:**
- ORM models for all GCP resources
- Persistent storage of metadata
- Relationships between resources

---

## 🔄 Request Flow

### Example: Creating a VM Instance via gcloud

```
┌─────────────┐
│ gcloud CLI  │
└──────┬──────┘
       │ POST /compute/v1/projects/test-project/zones/us-central1-a/instances
       ▼
┌──────────────────────────────────────────────────┐
│  FastAPI Backend (Port 8080)                     │
│  ┌────────────────────────────────────────────┐  │
│  │  1. Receive Request                        │  │
│  │     - Parse project, zone, instance params │  │
│  │     - Validate machine type exists         │  │
│  └────────────────────────────────────────────┘  │
│                      │                            │
│                      ▼                            │
│  ┌────────────────────────────────────────────┐  │
│  │  2. Create Docker Container                │  │
│  │     - docker_client.containers.run()       │  │
│  │     - Attach to VPC network                │  │
│  │     - Get internal IP from Docker          │  │
│  └────────────────────────────────────────────┘  │
│                      │                            │
│                      ▼                            │
│  ┌────────────────────────────────────────────┐  │
│  │  3. Save to Database                       │  │
│  │     - Create Instance record               │  │
│  │     - Store container_id, IPs, status      │  │
│  └────────────────────────────────────────────┘  │
│                      │                            │
│                      ▼                            │
│  ┌────────────────────────────────────────────┐  │
│  │  4. Return GCP-formatted Response          │  │
│  │     {                                      │  │
│  │       "name": "my-vm",                     │  │
│  │       "status": "RUNNING",                 │  │
│  │       "networkInterfaces": [{...}]         │  │
│  │     }                                      │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│ gcloud CLI  │
│ Success!    │
└─────────────┘
```

---

## 💻 Compute Engine Implementation

### How VM Instances Work

**1. Instance Creation:**

```python
# File: minimal-backend/api/compute.py

@router.post("/compute/v1/projects/{project}/zones/{zone}/instances")
def create_instance(project: str, zone: str, payload: dict):
    # Step 1: Extract parameters
    instance_name = payload["name"]
    machine_type = payload["machineType"]
    network = payload.get("networkInterfaces", [{}])[0].get("network", "default")
    
    # Step 2: Create Docker container
    container_name = f"gcp-vm-{instance_name}"
    docker_network = f"gcp-vpc-{project}-{network}"
    
    container = docker_client.containers.run(
        image="ubuntu:22.04",
        name=container_name,
        network=docker_network,
        detach=True,
        tty=True,
        command="/bin/bash"
    )
    
    # Step 3: Get IPs from Docker
    container.reload()
    internal_ip = container.attrs['NetworkSettings']['Networks'][docker_network]['IPAddress']
    external_ip = "127.0.0.1"  # Simulated NAT
    
    # Step 4: Save to database
    instance = Instance(
        name=instance_name,
        project_id=project,
        zone=zone,
        machine_type=machine_type,
        status="RUNNING",
        container_id=container.id,
        container_name=container_name,
        internal_ip=internal_ip,
        external_ip=external_ip,
        network_url=f"global/networks/{network}"
    )
    db.add(instance)
    db.commit()
    
    # Step 5: Return GCP-formatted response
    return {
        "kind": "compute#instance",
        "name": instance_name,
        "status": "RUNNING",
        "machineType": f"zones/{zone}/machineTypes/{machine_type}",
        "networkInterfaces": [{
            "network": f"global/networks/{network}",
            "networkIP": internal_ip,
            "accessConfigs": [{
                "type": "ONE_TO_ONE_NAT",
                "name": "External NAT",
                "natIP": external_ip
            }]
        }]
    }
```

**2. Instance Status Operations:**

```python
# Stop Instance
@router.post("/compute/v1/projects/{project}/zones/{zone}/instances/{instance}/stop")
def stop_instance(project: str, zone: str, instance: str):
    # Get instance from DB
    db_instance = db.query(Instance).filter_by(name=instance).first()
    
    # Stop Docker container
    container = docker_client.containers.get(db_instance.container_id)
    container.stop()
    
    # Update database
    db_instance.status = "STOPPED"
    db.commit()
    
    return {"status": "success"}

# Start Instance
@router.post("/compute/v1/projects/{project}/zones/{zone}/instances/{instance}/start")
def start_instance(project: str, zone: str, instance: str):
    db_instance = db.query(Instance).filter_by(name=instance).first()
    
    # Start Docker container
    container = docker_client.containers.get(db_instance.container_id)
    container.start()
    
    # Update database
    db_instance.status = "RUNNING"
    db.commit()
    
    return {"status": "success"}
```

**3. Instance to Container Mapping:**

```
GCP Instance "my-vm"
    ├── Database Record (instances table)
    │   ├── id: 1
    │   ├── name: "my-vm"
    │   ├── container_id: "a1b2c3d4..."
    │   ├── status: "RUNNING"
    │   └── internal_ip: "172.17.0.2"
    │
    └── Docker Container "gcp-vm-my-vm"
        ├── Container ID: a1b2c3d4...
        ├── Image: ubuntu:22.04
        ├── Network: gcp-vpc-test-project-default
        ├── IP: 172.17.0.2
        └── Status: running
```

---

## 🌐 VPC Networks Implementation

### How VPCs Map to Docker Networks

**1. Network Creation:**

```python
# File: minimal-backend/api/vpc.py

@router.post("/compute/v1/projects/{project}/global/networks")
def create_network(project: str, payload: dict):
    network_name = payload["name"]
    auto_create = payload.get("autoCreateSubnetworks", True)
    
    # Step 1: Create Docker network
    docker_network_name = f"gcp-vpc-{project}-{network_name}"
    
    docker_network = docker_client.networks.create(
        name=docker_network_name,
        driver="bridge",
        options={
            "com.docker.network.bridge.name": docker_network_name[:15]
        }
    )
    
    # Step 2: Save to database
    network = Network(
        name=network_name,
        project_id=project,
        docker_network_name=docker_network_name,
        auto_create_subnetworks=auto_create
    )
    db.add(network)
    db.commit()
    
    return {
        "kind": "compute#network",
        "name": network_name,
        "autoCreateSubnetworks": auto_create,
        "selfLink": f"global/networks/{network_name}"
    }
```

**2. Instance-to-Network Attachment:**

When creating an instance with a specific network:

```python
# In create_instance()
network_name = payload.get("networkInterfaces", [{}])[0].get("network", "default")

# Look up Docker network
db_network = db.query(Network).filter_by(name=network_name).first()
docker_network_name = db_network.docker_network_name

# Create container on that network
container = docker_client.containers.run(
    image="ubuntu:22.04",
    name=f"gcp-vm-{instance_name}",
    network=docker_network_name,  # Attach to VPC's Docker network
    detach=True
)
```

**3. Network Mapping:**

```
GCP VPC "my-vpc"
    ├── Database Record (networks table)
    │   ├── id: 1
    │   ├── name: "my-vpc"
    │   ├── docker_network_name: "gcp-vpc-test-project-my-vpc"
    │   └── auto_create_subnetworks: true
    │
    └── Docker Network "gcp-vpc-test-project-my-vpc"
        ├── Driver: bridge
        ├── Subnet: 172.18.0.0/16 (auto-assigned by Docker)
        ├── Gateway: 172.18.0.1
        └── Containers: [gcp-vm-instance-1, gcp-vm-instance-2]
```

**4. Internet Gateway:**

```python
# Internet Gateway is metadata-only (no real routing)
@router.get("/compute/v1/projects/{project}/global/internetGateways")
def list_internet_gateways(project: str):
    return {
        "kind": "compute#internetGatewayList",
        "items": [{
            "kind": "compute#internetGateway",
            "name": "default-internet-gateway",
            "network": f"global/networks/default",
            "status": "ACTIVE",
            "backing": "docker-bridge-nat"  # Docker provides NAT
        }]
    }
```

---

## 💾 Cloud Storage Implementation

### How Storage Works with File System

**1. Bucket Creation:**

```python
# File: minimal-backend/api/storage.py

@router.post("/storage/v1/b")
def create_bucket(payload: dict, project: str = Query(None)):
    bucket_name = payload["name"]
    location = payload.get("location", "US")
    
    # Step 1: Create directory on file system
    bucket_dir = f"/tmp/gcs-storage/{bucket_name}"
    os.makedirs(bucket_dir, exist_ok=True)
    
    # Step 2: Save to database
    bucket = Bucket(
        id=bucket_name,
        name=bucket_name,
        project_id=project,
        location=location,
        storage_class="STANDARD"
    )
    db.add(bucket)
    db.commit()
    
    return {
        "kind": "storage#bucket",
        "name": bucket_name,
        "location": location
    }
```

**2. Object Upload:**

```python
@router.post("/upload/storage/v1/b/{bucket}/o")
async def upload_object(bucket: str, request: Request, name: str = Query(None)):
    # Step 1: Read uploaded content
    raw_body = await request.body()
    
    # Step 2: Parse multipart data (if needed)
    content = parse_multipart_content(raw_body)
    object_name = name or extract_name_from_body(raw_body)
    
    # Step 3: Write to file system
    file_path = f"/tmp/gcs-storage/{bucket}/{object_name}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Step 4: Calculate hashes
    md5_hash = base64.b64encode(hashlib.md5(content).digest()).decode()
    crc32c = calculate_crc32c(content)
    
    # Step 5: Save metadata to database
    obj = Object(
        id=f"{bucket}/{object_name}",
        bucket_id=bucket,
        name=object_name,
        size=len(content),
        content_type="application/octet-stream",
        md5_hash=md5_hash,
        crc32c_hash=crc32c,
        file_path=file_path  # Store path, not content
    )
    db.add(obj)
    db.commit()
    
    return {
        "kind": "storage#object",
        "name": object_name,
        "bucket": bucket,
        "size": str(len(content)),
        "md5Hash": md5_hash
    }
```

**3. Object Download:**

```python
@router.get("/storage/v1/b/{bucket}/o/{object:path}")
def get_object(bucket: str, object: str, alt: str = Query(None)):
    # Step 1: Get metadata from database
    db_obj = db.query(Object).filter_by(
        bucket_id=bucket, 
        name=object
    ).first()
    
    if alt == "media":
        # Step 2: Read from file system
        file_path = f"/tmp/gcs-storage/{bucket}/{db_obj.name}"
        
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # Step 3: Return binary content
        return Response(
            content=file_content,
            media_type=db_obj.content_type or "application/octet-stream",
            headers={
                "Content-Length": str(len(file_content)),
                "x-goog-hash": f"crc32c={db_obj.crc32c_hash},md5={db_obj.md5_hash}"
            }
        )
    else:
        # Return JSON metadata
        return {
            "kind": "storage#object",
            "name": db_obj.name,
            "bucket": bucket,
            "size": str(db_obj.size),
            "md5Hash": db_obj.md5_hash
        }
```

**4. Storage Architecture:**

```
Object Upload Flow:
┌──────────────┐
│ gcloud CLI   │
└──────┬───────┘
       │ POST /upload/storage/v1/b/my-bucket/o?name=file.txt
       │ Content-Type: multipart/related
       │ Body: [binary data]
       ▼
┌─────────────────────────────────────────┐
│  FastAPI Storage API                    │
│  1. Parse multipart data                │
│  2. Write to /tmp/gcs-storage/          │
│  3. Calculate MD5 & CRC32C              │
│  4. Save metadata to PostgreSQL         │
└─────────────────────────────────────────┘
       │
       ▼
┌──────────────────┐         ┌──────────────────┐
│  File System     │         │  PostgreSQL      │
│                  │         │  objects table   │
│  /tmp/gcs-       │         │  ┌────────────┐  │
│  storage/        │         │  │ id         │  │
│  └─my-bucket/    │         │  │ bucket_id  │  │
│    └─file.txt    │◄────────┤  │ name       │  │
│      [binary]    │         │  │ file_path──┼──┤
│                  │         │  │ md5_hash   │  │
└──────────────────┘         │  │ size       │  │
                             │  └────────────┘  │
                             └──────────────────┘
```

---

## 👤 IAM Implementation

### Service Accounts

**1. Service Account Creation:**

```python
# File: minimal-backend/api/projects.py

@router.post("/v1/projects/{project}/serviceAccounts")
def create_service_account(project: str, payload: dict):
    account_id = payload["accountId"]
    display_name = payload["serviceAccount"].get("displayName", "")
    
    # Step 1: Generate email and unique ID
    email = f"{account_id}@{project}.iam.gserviceaccount.com"
    unique_id = str(random.randint(100000000000000000000, 999999999999999999999))
    
    # Step 2: Save to database
    sa = ServiceAccount(
        id=email,
        project_id=project,
        email=email,
        display_name=display_name,
        unique_id=unique_id,
        disabled=False
    )
    db.add(sa)
    db.commit()
    
    # Step 3: Return GCP-formatted response
    return {
        "name": f"projects/{project}/serviceAccounts/{email}",
        "projectId": project,
        "uniqueId": unique_id,
        "email": email,
        "displayName": display_name,
        "disabled": False
    }
```

**2. Service Account Lifecycle:**

```
Create → List → Get → Delete

┌─────────────────────────────────────────────────┐
│  PostgreSQL service_accounts table              │
│  ┌───────────────────────────────────────────┐  │
│  │ id (PK): sa@project.iam.gserviceaccount..│  │
│  │ project_id: test-project                  │  │
│  │ email: sa@project.iam.gserviceaccount.com│  │
│  │ display_name: "My Service Account"        │  │
│  │ unique_id: "123456789012345678901"        │  │
│  │ disabled: false                           │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 🗄️ Database Design

### Schema Overview

```sql
-- instances: VM instances with Docker container mapping
CREATE TABLE instances (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    project_id VARCHAR NOT NULL,
    zone VARCHAR NOT NULL,
    machine_type VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'RUNNING',
    container_id VARCHAR,           -- Docker container ID
    container_name VARCHAR,          -- gcp-vm-{name}
    internal_ip VARCHAR,             -- Docker network IP
    external_ip VARCHAR,             -- NAT IP (127.0.0.1)
    network_url VARCHAR DEFAULT 'global/networks/default',
    created_at TIMESTAMP DEFAULT NOW()
);

-- networks: VPC networks with Docker network mapping
CREATE TABLE networks (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    project_id VARCHAR NOT NULL,
    docker_network_name VARCHAR,     -- gcp-vpc-{project}-{name}
    auto_create_subnetworks BOOLEAN DEFAULT true,
    creation_timestamp TIMESTAMP DEFAULT NOW()
);

-- buckets: Cloud Storage buckets
CREATE TABLE buckets (
    id VARCHAR PRIMARY KEY,          -- bucket name
    name VARCHAR NOT NULL UNIQUE,
    project_id VARCHAR,
    location VARCHAR DEFAULT 'US',
    storage_class VARCHAR DEFAULT 'STANDARD',
    created_at TIMESTAMP DEFAULT NOW()
);

-- objects: Cloud Storage objects (metadata only)
CREATE TABLE objects (
    id VARCHAR PRIMARY KEY,
    bucket_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    size INTEGER,
    content_type VARCHAR,
    md5_hash VARCHAR,
    crc32c_hash VARCHAR,
    file_path VARCHAR,               -- /tmp/gcs-storage/{bucket}/{name}
    deleted BOOLEAN DEFAULT false,
    time_created TIMESTAMP,
    FOREIGN KEY (bucket_id) REFERENCES buckets(id)
);

-- projects: GCP projects
CREATE TABLE projects (
    id VARCHAR PRIMARY KEY,          -- project ID
    name VARCHAR NOT NULL,
    project_number INTEGER,
    location VARCHAR DEFAULT 'us-central1',
    created_at TIMESTAMP DEFAULT NOW()
);

-- zones: Compute zones (pre-seeded)
CREATE TABLE zones (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    region VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'UP'
);

-- machine_types: VM machine types (pre-seeded)
CREATE TABLE machine_types (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    zone VARCHAR NOT NULL,
    guest_cpus INTEGER DEFAULT 1,
    memory_mb INTEGER DEFAULT 1024
);

-- service_accounts: IAM service accounts
CREATE TABLE service_accounts (
    id VARCHAR PRIMARY KEY,          -- email address
    project_id VARCHAR NOT NULL,
    email VARCHAR,
    display_name VARCHAR,
    unique_id VARCHAR NOT NULL UNIQUE,
    disabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Relationships

```
projects (1) ──────► (N) instances
                     (N) networks
                     (N) buckets
                     (N) service_accounts

buckets (1) ────────► (N) objects

networks (1) ───────► (N) instances (via network_url)

zones (1) ──────────► (N) instances
                      (N) machine_types
```

---

## 🐳 Docker Integration

### Container Lifecycle Management

**1. Docker Client Initialization:**

```python
# File: minimal-backend/docker_manager.py

import docker

# Connect to Docker daemon
docker_client = docker.from_env()

def get_docker_client():
    """Get Docker client instance"""
    return docker_client
```

**2. Container Operations:**

```python
# Create container
def create_gcp_container(name: str, network: str = "bridge"):
    container = docker_client.containers.run(
        image="ubuntu:22.04",
        name=f"gcp-vm-{name}",
        network=network,
        detach=True,
        tty=True,
        stdin_open=True,
        command="/bin/bash"
    )
    return container

# Stop container
def stop_container(container_id: str):
    container = docker_client.containers.get(container_id)
    container.stop()

# Start container
def start_container(container_id: str):
    container = docker_client.containers.get(container_id)
    container.start()

# Delete container
def delete_container(container_id: str):
    container = docker_client.containers.get(container_id)
    container.remove(force=True)

# Get container IP
def get_container_ip(container_id: str, network: str):
    container = docker_client.containers.get(container_id)
    container.reload()
    return container.attrs['NetworkSettings']['Networks'][network]['IPAddress']
```

**3. Network Operations:**

```python
# Create Docker network
def create_docker_network(name: str):
    network = docker_client.networks.create(
        name=name,
        driver="bridge",
        options={
            "com.docker.network.bridge.name": name[:15]
        }
    )
    return network

# Delete Docker network
def delete_docker_network(name: str):
    network = docker_client.networks.get(name)
    network.remove()

# List networks
def list_docker_networks():
    return docker_client.networks.list()
```

**4. Container-Instance Mapping:**

```
User Action: Create VM "my-vm" in zone us-central1-a

Step 1: API receives request
  ↓
Step 2: Create Docker container
  - Name: gcp-vm-my-vm
  - Image: ubuntu:22.04
  - Network: gcp-vpc-test-project-default
  - Command: /bin/bash
  ↓
Step 3: Get container details
  - Container ID: a1b2c3d4e5f6...
  - Internal IP: 172.17.0.2 (from Docker)
  - Status: running
  ↓
Step 4: Save to database
  - instances.name = "my-vm"
  - instances.container_id = "a1b2c3d4e5f6..."
  - instances.internal_ip = "172.17.0.2"
  - instances.status = "RUNNING"
  ↓
Step 5: Return GCP response
  {
    "name": "my-vm",
    "status": "RUNNING",
    "networkInterfaces": [{
      "networkIP": "172.17.0.2"
    }]
  }
```

---

## 🎨 Frontend Integration

### React UI Architecture

**1. API Client Layer:**

```typescript
// File: gcp-stimulator-ui/src/api/client.ts

const API_BASE_URL = 'http://localhost:8080';

export const apiClient = {
  async get(endpoint: string) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    return response.json();
  },
  
  async post(endpoint: string, data: any) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }
};
```

**2. Service-Specific Clients:**

```typescript
// File: gcp-stimulator-ui/src/api/instances.ts

export const instancesApi = {
  async list(project: string, zone: string) {
    return apiClient.get(
      `/compute/v1/projects/${project}/zones/${zone}/instances`
    );
  },
  
  async create(project: string, zone: string, data: any) {
    return apiClient.post(
      `/compute/v1/projects/${project}/zones/${zone}/instances`,
      data
    );
  },
  
  async stop(project: string, zone: string, instance: string) {
    return apiClient.post(
      `/compute/v1/projects/${project}/zones/${zone}/instances/${instance}/stop`,
      {}
    );
  }
};
```

**3. React Components:**

```typescript
// File: gcp-stimulator-ui/src/pages/ComputePage.tsx

import { useState, useEffect } from 'react';
import { instancesApi } from '../api/instances';

export function ComputePage() {
  const [instances, setInstances] = useState([]);
  
  // Load instances on mount
  useEffect(() => {
    loadInstances();
  }, []);
  
  async function loadInstances() {
    const data = await instancesApi.list('test-project', 'us-central1-a');
    setInstances(data.items || []);
  }
  
  async function handleCreate() {
    await instancesApi.create('test-project', 'us-central1-a', {
      name: 'new-vm',
      machineType: 'e2-micro'
    });
    loadInstances(); // Refresh list
  }
  
  return (
    <div>
      <button onClick={handleCreate}>Create Instance</button>
      <ul>
        {instances.map(instance => (
          <li key={instance.name}>{instance.name} - {instance.status}</li>
        ))}
      </ul>
    </div>
  );
}
```

**4. Data Flow:**

```
┌──────────────────────────────────────────────────────┐
│  React Component (ComputePage)                       │
│  ┌────────────────────────────────────────────────┐  │
│  │  1. User clicks "Create Instance"              │  │
│  │  2. Call instancesApi.create()                 │  │
│  └────────────────┬───────────────────────────────┘  │
└───────────────────┼──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│  API Client (instancesApi)                           │
│  ┌────────────────────────────────────────────────┐  │
│  │  POST http://localhost:8080/compute/v1/...     │  │
│  │  Body: { name: "new-vm", machineType: "..." } │  │
│  └────────────────┬───────────────────────────────┘  │
└───────────────────┼──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│  FastAPI Backend                                     │
│  ┌────────────────────────────────────────────────┐  │
│  │  1. Create Docker container                    │  │
│  │  2. Save to PostgreSQL                         │  │
│  │  3. Return response                            │  │
│  └────────────────┬───────────────────────────────┘  │
└───────────────────┼──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│  React Component                                     │
│  ┌────────────────────────────────────────────────┐  │
│  │  4. Response received                          │  │
│  │  5. Update UI state                            │  │
│  │  6. Refresh instance list                      │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

---

## 🖥️ gcloud CLI Integration

### Environment Configuration

**1. API Endpoint Override:**

```bash
# File: .env-gcloud

# Override GCP API endpoints to point to local emulator
export CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE=http://localhost:8080/compute/v1/
export CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE=http://localhost:8080/storage/v1/

# Set default project
export CLOUDSDK_CORE_PROJECT=test-project
```

**2. How gcloud Commands Work:**

```
User runs: gcloud compute instances list --zones=us-central1-a

Step 1: gcloud reads environment variables
  ↓
Step 2: Instead of https://compute.googleapis.com
        Uses: http://localhost:8080/compute/v1/
  ↓
Step 3: Makes API request to local backend
  GET http://localhost:8080/compute/v1/projects/test-project/zones/us-central1-a/instances
  ↓
Step 4: Backend returns GCP-formatted JSON
  {
    "kind": "compute#instanceList",
    "items": [...]
  }
  ↓
Step 5: gcloud parses response and displays table
  NAME     ZONE           MACHINE_TYPE  STATUS
  my-vm    us-central1-a  e2-micro      RUNNING
```

**3. Command Translation:**

```bash
# gcloud command
gcloud compute instances create my-vm \
  --zone=us-central1-a \
  --machine-type=e2-micro

# Translates to HTTP request
POST http://localhost:8080/compute/v1/projects/test-project/zones/us-central1-a/instances
Content-Type: application/json

{
  "name": "my-vm",
  "machineType": "zones/us-central1-a/machineTypes/e2-micro",
  "networkInterfaces": [{
    "network": "global/networks/default"
  }]
}
```

**4. Response Format Compatibility:**

```python
# Backend must return exact GCP API format
@router.post("/compute/v1/projects/{project}/zones/{zone}/instances")
def create_instance(...):
    # ... create container ...
    
    # CRITICAL: Must match GCP API response structure
    return {
        "kind": "compute#operation",  # Must have this
        "targetLink": f".../{instance}",
        "operationType": "insert",
        "status": "DONE",
        # ... more GCP-specific fields
    }
```

---

## 🔐 Security & Authentication

### Mock Authentication

```python
# No real authentication required - all requests accepted
# Simulates already-authenticated environment

@router.post("/storage/v1/b")
def create_bucket(payload: dict):
    # No auth check - accepts all requests
    bucket = Bucket(**payload)
    db.add(bucket)
    db.commit()
    return {"status": "created"}
```

### CORS Configuration

```python
# File: minimal-backend/main.py

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Performance Considerations

### Database Queries

```python
# Use indexes for frequent queries
class Instance(Base):
    __tablename__ = "instances"
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)  # Index for fast lookups
    project_id = Column(String, index=True)
    zone = Column(String, index=True)
```

### File System Storage

```python
# Objects stored on disk, not in database
# Advantages:
# - No database size limits
# - Fast binary read/write
# - Standard file operations work

# File path: /tmp/gcs-storage/{bucket}/{object}
file_path = f"/tmp/gcs-storage/{bucket_name}/{object_name}"
```

### Docker Performance

```python
# Containers use minimal resources
docker_client.containers.run(
    image="ubuntu:22.04",
    detach=True,
    tty=True,
    # No resource limits = fast creation
)
```

---

## 🎯 Summary

### Key Concepts

1. **API Emulation** - FastAPI mimics GCP REST APIs with exact response formats
2. **Docker Integration** - VMs are containers, VPCs are Docker networks
3. **Hybrid Storage** - Metadata in PostgreSQL, files on disk
4. **gcloud Compatibility** - Environment variable override redirects to local backend
5. **No Authentication** - Open access for local development

### Data Flow

```
User Action → gcloud/UI → FastAPI → Docker/DB/FileSystem → Response → Display
```

### Architecture Benefits

- ✅ **No GCP credentials needed** - Fully local
- ✅ **No cloud costs** - Everything runs locally
- ✅ **Real containers** - Actual Docker containers, not simulated
- ✅ **Persistent data** - PostgreSQL RDS for metadata
- ✅ **API compatible** - Works with real gcloud CLI
- ✅ **Visual UI** - React dashboard for easy management

---

**Last Updated:** February 5, 2026  
**Version:** 1.0.0
