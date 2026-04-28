# Skill: Backend API & Database Expert

**name:** Backend Development  
**description:** Expert in FastAPI + SQLAlchemy + PostgreSQL for GCP Stimulator backend. Follows the services/ router pattern, adds new API routes, database models, and Docker manager integrations. Auto-activates for any backend/API/database work.

**trigger_keywords:** FastAPI, SQLAlchemy, database, API, route, service, model, POST, GET, DELETE, PATCH, query, transaction, docker, router, endpoint, schema, migration

**allowed_tools:** Read, Grep, Semantic Search, File Search

---

## Project Architecture

```
minimal-backend/
├── main.py                  ← App entry, router registration
├── database.py              ← Backward-compat shim → imports from core/database.py
├── docker_manager.py        ← Docker container/network lifecycle (docker-py)
├── ip_manager.py            ← IP allocation per subnet/zone
├── core/
│   └── database.py          ← ALL SQLAlchemy models + DB config lives here
├── api/
│   └── storage.py           ← Cloud Storage (special: stays in api/, 1100+ lines)
└── services/                ← ALL new services go here (preferred pattern)
    ├── compute/
    │   ├── router.py        ← FastAPI APIRouter
    │   ├── models.py        ← Pydantic request/response models
    │   └── storage.py       ← In-memory storage (if no DB needed)
    ├── vpc/
    ├── iam/
    ├── gke/
    ├── autoscaling/
    ├── monitoring/
    ├── pubsub/
    ├── run/
    ├── artifacts/
    ├── secretmanager/
    └── projects/
```

---

## How to Add a New GCP Service (Full Checklist)

### Step 1: SQLAlchemy Model in `core/database.py`
```python
class MyResource(Base):
    """My GCP Resource"""
    __tablename__ = "my_resources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    project_id = Column(String, nullable=False)
    zone = Column(String, nullable=False)
    status = Column(String, default="ACTIVE")
    description = Column(String)
    labels = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

Then add to backward-compat shim in `database.py`:
```python
from core.database import (
    ...,
    MyResource,
)
```

### Step 2: Pydantic Models in `services/myservice/models.py`
```python
from pydantic import BaseModel
from typing import Optional

class CreateMyResourceRequest(BaseModel):
    name: str
    zone: Optional[str] = "us-central1-a"
    description: Optional[str] = None
    labels: Optional[dict] = {}
```

### Step 3: FastAPI Router in `services/myservice/router.py`
```python
"""My GCP Service API endpoints."""
import random
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db, MyResource
from .models import CreateMyResourceRequest

router = APIRouter()

def _op(project: str, zone: str, op_type: str, target: str) -> dict:
    """Standard DONE operation response — all ops are synchronous."""
    oid = str(random.randint(10**12, 10**13 - 1))
    resource_name = target.split("/")[-1] if "/" in target else target
    return {
        "kind": "compute#operation",
        "id": oid,
        "name": resource_name,
        "operationType": op_type,
        "targetLink": target,
        "status": "DONE",
        "progress": 100,
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/operations/{oid}",
    }

def _resource_to_dict(r: MyResource, project: str) -> dict:
    """Serialize model to GCP-style API response."""
    return {
        "id": str(r.id),
        "name": r.name,
        "status": r.status,
        "description": r.description or "",
        "labels": r.labels or {},
        "creationTimestamp": r.created_at.isoformat() + "Z",
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{r.zone}/myresources/{r.name}",
    }

@router.get("/projects/{project}/zones/{zone}/myresources")
def list_resources(project: str, zone: str, db: Session = Depends(get_db)):
    resources = db.query(MyResource).filter(
        MyResource.project_id == project,
        MyResource.zone == zone
    ).all()
    return {
        "kind": "compute#myResourceList",
        "items": [_resource_to_dict(r, project) for r in resources],
    }

@router.post("/projects/{project}/zones/{zone}/myresources")
def create_resource(project: str, zone: str, body: CreateMyResourceRequest, db: Session = Depends(get_db)):
    existing = db.query(MyResource).filter_by(name=body.name, project_id=project, zone=zone).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Resource '{body.name}' already exists")

    resource = MyResource(
        name=body.name,
        project_id=project,
        zone=zone,
        description=body.description,
        labels=body.labels or {},
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)

    target = f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/myresources/{resource.name}"
    return _op(project, zone, "insert", target)

@router.get("/projects/{project}/zones/{zone}/myresources/{name}")
def get_resource(project: str, zone: str, name: str, db: Session = Depends(get_db)):
    r = db.query(MyResource).filter_by(name=name, project_id=project, zone=zone).first()
    if not r:
        raise HTTPException(status_code=404, detail=f"Resource '{name}' not found")
    return _resource_to_dict(r, project)

@router.delete("/projects/{project}/zones/{zone}/myresources/{name}")
def delete_resource(project: str, zone: str, name: str, db: Session = Depends(get_db)):
    r = db.query(MyResource).filter_by(name=name, project_id=project, zone=zone).first()
    if not r:
        raise HTTPException(status_code=404, detail=f"Resource '{name}' not found")
    db.delete(r)
    db.commit()
    target = f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/myresources/{name}"
    return _op(project, zone, "delete", target)
```

### Step 4: Register Router in `main.py`
```python
from services.myservice.router import router as myservice_router

# Add with the correct GCP API prefix:
app.include_router(myservice_router, prefix="/compute/v1", tags=["My Service"])
```

---

## Database

### Connection
```python
# Reads from DATABASE_URL env var
# Defaults to: sqlite:////tmp/gcs_stimulator.db (local dev)
# Production: postgresql://user:pass@host:5432/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/gcs_stimulator.db")
```

### Session Pattern
```python
# Always use Depends(get_db) in route handlers
@router.get("/...")
def my_route(db: Session = Depends(get_db)):
    # db is automatically closed after response
    pass
```

### All Existing Models (from `core/database.py`)
| Model | Table | Description |
|-------|-------|-------------|
| `Instance` | `instances` | VM instances → Docker containers |
| `Project` | `projects` | GCP projects |
| `Zone` | `zones` | Compute zones (us-central1-a, etc.) |
| `MachineType` | `machine_types` | VM sizes (e2-micro, n1-standard-8) |
| `Address` | `addresses` | Static IP addresses |
| `Disk` | `disks` | Persistent disks |
| `Network` | `networks` | VPC networks → Docker networks |
| `Subnet` | `subnets` | VPC subnets with CIDR ranges |
| `Firewall` | `firewall_rules` | Firewall rules |
| `Route` | `routes` | Network routes |
| `CloudRouter` | `cloud_routers` | Cloud Router |
| `CloudNAT` | `cloud_nats` | Cloud NAT |
| `VPCPeering` | `vpc_peerings` | VPC peering connections |
| `Bucket` | `buckets` | Cloud Storage buckets |
| `Object` | `objects` | Bucket objects (metadata; files in /tmp/gcs-storage/) |
| `ServiceAccount` | `service_accounts` | IAM service accounts |
| `IAMPolicyBinding` | `iam_policy_bindings` | IAM bindings |
| `CustomRole` | `custom_roles` | IAM custom roles |
| `ServiceAccountKey` | `service_account_keys` | SA keys |
| `GKECluster` | `gke_clusters` | GKE clusters |
| `GKENodePool` | `gke_node_pools` | GKE node pools |
| `GKEAddon` | `gke_addons` | GKE addons |

---

## Docker Manager Integration

```python
from docker_manager import (
    create_container,      # Creates Docker container for VM instance
    start_container,       # docker start
    stop_container,        # docker stop
    delete_container,      # docker rm
    get_container_status,  # returns "running" / "exited" / None
    ip_in_docker_network,  # get container IP in a specific network
)

# Pattern: every VM instance = Docker container (ubuntu:22.04)
# Every VPC network = Docker bridge network
```

---

## API Response Conventions

| Scenario | HTTP Code | Response |
|----------|-----------|----------|
| List (empty) | 200 | `{"kind": "...", "items": []}` |
| Get (found) | 200 | Full resource dict |
| Get (not found) | 404 | `{"detail": "..."}` |
| Create (success) | 200 | `_op(...)` DONE operation |
| Create (duplicate) | 409 | `{"detail": "...already exists"}` |
| Delete (success) | 200 | `_op(...)` DONE operation |
| Invalid input | 422 | Pydantic auto-generated |

---

## In-Memory Services Pattern
For services without DB persistence (monitoring, autoscaling, pubsub):
```python
# services/myservice/storage.py
class MyServiceStorage:
    def __init__(self):
        self._data: Dict[str, Any] = {}

    def create(self, key: str, value: Any) -> Any:
        self._data[key] = value
        return value

    def get(self, key: str) -> Optional[Any]:
        return self._data.get(key)

    def list_all(self) -> List[Any]:
        return list(self._data.values())

    def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None

# In router.py:
storage = MyServiceStorage()  # Shared singleton
router = APIRouter()
```

---

## Key Rules

- **Always** use `Depends(get_db)` for DB sessions — never create sessions manually
- **Always** commit + refresh after DB writes
- **Always** return `_op(...)` for create/delete (GCP API pattern, `status: DONE`)
- **Never** put business logic directly in route handlers — use service functions
- **All models** live in `core/database.py`, imported via `database.py` shim
- **New services** go in `services/` not `api/` (except storage.py which stays in `api/`)
- Register routers with correct GCP API prefix (e.g., `/compute/v1`, `/v1`, `/container/v1`)
- CORS is fully open (`allow_origins=["*"]`) — don't restrict in dev
