# GKE (Google Kubernetes Engine) Implementation Plan

## Overview

Add a full GKE emulator to the GCP Stimulator. Clusters and Node Pools will use **real Docker containers** (k3s-in-Docker) for the control plane, with realistic **status transitions** (PROVISIONING → RUNNING → STOPPING → STOPPED) driven by background threads. A **kubeconfig download** endpoint returns a usable YAML pointing to the container's IP. A new **Containers** sidebar category houses the GKE section in the frontend.

---

## Architecture Decision

| Concern | Decision | Reason |
|---|---|---|
| K8s runtime | **k3s** (single container) | No Docker-in-Docker complexity; k3s boots in ~20s |
| Status transitions | **Background threading** | Same pattern as `compute.py` for VM start/stop |
| API path format | `/container/v1/projects/{p}/locations/{l}/clusters` | Matches real GKE REST API |
| DB backend | SQLite (SQLAlchemy) | Consistent with rest of the project |
| Frontend nav | New **Containers** category | Faithful to real GCP console structure |
| Kubeconfig | Extract from container via Docker exec | Replaces `localhost` with the container's bridge IP |

---

## Phase 1 — Backend

### 1.1 Database Models (`minimal-backend/database.py`)

Add two new SQLAlchemy models at the bottom of the file, before `Base.metadata.create_all(engine)`.

#### `GKECluster`

```python
class GKECluster(Base):
    __tablename__ = "gke_clusters"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    name            = Column(String, nullable=False)
    project_id      = Column(String, nullable=False)
    location        = Column(String, nullable=False)          # zone or region, e.g. us-central1-a
    status          = Column(String, default="PROVISIONING")  # PROVISIONING | RUNNING | RECONCILING | STOPPING | ERROR
    master_version  = Column(String, default="1.28.0")
    node_count      = Column(Integer, default=3)
    machine_type    = Column(String, default="e2-medium")
    disk_size_gb    = Column(Integer, default=100)
    network         = Column(String, default="default")
    subnetwork      = Column(String, default="default")
    container_id    = Column(String)                          # Docker container ID of the k3s control plane
    endpoint        = Column(String)                          # IP of the k3s container (fake API endpoint)
    kubeconfig      = Column(String)                          # Raw kubeconfig YAML text
    description     = Column(String)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### `NodePool`

```python
class NodePool(Base):
    __tablename__ = "gke_node_pools"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    name            = Column(String, nullable=False)
    cluster_name    = Column(String, nullable=False)          # FK → gke_clusters.name
    project_id      = Column(String, nullable=False)
    location        = Column(String, nullable=False)
    status          = Column(String, default="PROVISIONING")  # same states as cluster
    node_count      = Column(Integer, default=3)
    machine_type    = Column(String, default="e2-medium")
    disk_size_gb    = Column(Integer, default=100)
    container_ids   = Column(JSON, default=list)              # Docker IDs for node containers
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Why:** `Base.metadata.create_all(engine)` at the bottom of `database.py` auto-creates these tables on first import — no migration script needed.

---

### 1.2 Docker Manager (`minimal-backend/docker_manager.py`)

Add three new methods to the existing `DockerManager` class (or as standalone functions if the class is thin):

#### `create_k3s_cluster(cluster_name: str) → dict`

```
1. Pull image rancher/k3s:latest if not present
2. Run container:
   docker run -d
     --name gke-<cluster_name>
     --privileged
     -e K3S_KUBECONFIG_OUTPUT=/output/kubeconfig.yaml
     -e K3S_KUBECONFIG_MODE=666
     rancher/k3s server
3. Wait up to 30s for the API server to respond (poll /readyz)
4. Return { container_id, endpoint_ip }  where endpoint_ip = container's bridge IP
```

#### `get_k3s_kubeconfig(container_id: str, endpoint_ip: str) → str`

```
1. docker exec <container_id> cat /etc/rancher/k3s/k3s.yaml
2. Replace all occurrences of "127.0.0.1" and "localhost" with endpoint_ip
3. Return the modified YAML string
```

#### `delete_k3s_cluster(container_id: str) → None`

```
1. docker stop <container_id>
2. docker rm <container_id>
```

---

### 1.3 GKE API Router (`minimal-backend/api/gke.py`) — new file

**Router prefix:** `/container/v1`  
**Tag:** `GKE`

#### Endpoints

| Method | Path | Action |
|---|---|---|
| `GET` | `/projects/{project}/locations/{location}/clusters` | List all clusters for project |
| `POST` | `/projects/{project}/locations/{location}/clusters` | Create cluster |
| `GET` | `/projects/{project}/locations/{location}/clusters/{cluster}` | Describe a cluster |
| `DELETE` | `/projects/{project}/locations/{location}/clusters/{cluster}` | Delete a cluster |
| `GET` | `/projects/{project}/locations/{location}/clusters/{cluster}/kubeconfig` | Download kubeconfig |
| `PATCH` | `/projects/{project}/locations/{location}/clusters/{cluster}` | Update cluster (node count) |
| `GET` | `/projects/{project}/locations/{location}/clusters/{cluster}/nodePools` | List node pools |
| `POST` | `/projects/{project}/locations/{location}/clusters/{cluster}/nodePools` | Create node pool |
| `GET` | `/projects/{project}/locations/{location}/clusters/{cluster}/nodePools/{nodePool}` | Describe node pool |
| `DELETE` | `/projects/{project}/locations/{location}/clusters/{cluster}/nodePools/{nodePool}` | Delete node pool |

#### Status Transition Logic (background threads)

**Create cluster flow:**
```
Request arrives → DB row inserted with status=PROVISIONING → HTTP 200 returned immediately
    ↓ (background thread)
docker_manager.create_k3s_cluster() runs
    ↓ success (~20-30s)
DB row updated: status=RUNNING, container_id=<id>, endpoint=<ip>
kubeconfig extracted and stored in DB
    ↓ failure
DB row updated: status=ERROR
```

**Delete cluster flow:**
```
Request arrives → DB row status set to STOPPING → HTTP 200 returned immediately
    ↓ (background thread)
docker_manager.delete_k3s_cluster(container_id)
    ↓ done
DB row deleted
```

#### Request body (POST /clusters)

```python
class CreateClusterRequest(BaseModel):
    cluster: dict          # GCP-style nested object
    # cluster.name         str
    # cluster.description  str (optional)
    # cluster.initialNodeCount  int (default 3)
    # cluster.nodeConfig.machineType  str (default 'e2-medium')
    # cluster.nodeConfig.diskSizeGb   int (default 100)
    # cluster.masterVersion  str (default '1.28.0')
    # cluster.network        str (default 'default')
    # cluster.subnetwork     str (default 'default')
```

#### Response shape (follows GKE REST API style)

```json
{
  "name": "my-cluster",
  "status": "RUNNING",
  "location": "us-central1-a",
  "masterVersion": "1.28.0",
  "endpoint": "172.17.0.5",
  "nodeConfig": {
    "machineType": "e2-medium",
    "diskSizeGb": 100
  },
  "currentNodeCount": 3,
  "network": "default",
  "subnetwork": "default",
  "selfLink": "https://container.googleapis.com/v1/projects/{p}/locations/{l}/clusters/{name}",
  "createTime": "2026-02-18T10:00:00Z"
}
```

---

### 1.4 Register Router (`minimal-backend/main.py`)

**Change:** Add two lines to the existing import and router registration block:

```python
# Before (existing line):
from api import compute, projects, vpc, storage, iam, firewall, routes

# After:
from api import compute, projects, vpc, storage, iam, firewall, routes, gke

# Add after existing app.include_router calls:
app.include_router(gke.router, prefix="/container/v1", tags=["GKE"])
```

---

## Phase 2 — Frontend

### 2.1 API Client (`gcp-stimulator-ui/src/api/gke.ts`) — new file

Typed async functions wrapping `apiClient` (same pattern as `buckets.ts`, `objects.ts`):

```typescript
export interface GKECluster {
  name: string;
  status: 'PROVISIONING' | 'RUNNING' | 'RECONCILING' | 'STOPPING' | 'ERROR';
  location: string;
  masterVersion: string;
  endpoint: string;
  currentNodeCount: number;
  network: string;
  subnetwork: string;
  createTime: string;
  nodeConfig: { machineType: string; diskSizeGb: number };
}

export interface NodePool {
  name: string;
  status: string;
  nodeCount: number;
  machineType: string;
}

// Functions:
listClusters(project: string, location?: string): Promise<GKECluster[]>
createCluster(project: string, location: string, payload: object): Promise<GKECluster>
getCluster(project: string, location: string, clusterName: string): Promise<GKECluster>
deleteCluster(project: string, location: string, clusterName: string): Promise<void>
getKubeconfig(project: string, location: string, clusterName: string): Promise<string>
listNodePools(project: string, location: string, clusterName: string): Promise<NodePool[]>
createNodePool(project: string, location: string, clusterName: string, payload: object): Promise<NodePool>
deleteNodePool(project: string, location: string, clusterName: string, nodePoolName: string): Promise<void>
```

All functions use `apiClient` from `./client` and pass `getCurrentProject()` for the project param.

---

### 2.2 Pages

#### `GKEDashboardPage.tsx` (modelled on `ComputeDashboardPage.tsx`)

**Layout:**
- Hero header with title "Kubernetes Engine — Clusters" and a **+ Create** button
- 4 stat cards: Total Clusters / Running / Total Nodes / Errors
- Table columns: Name | Location | Status (badge) | Nodes | Master Version | Created | Actions
- Status badge colours:
  - `RUNNING` → green
  - `PROVISIONING` / `RECONCILING` → yellow + spinner
  - `STOPPING` → orange + spinner
  - `ERROR` → red
- Actions per row: **Connect** (opens kubeconfig modal), **Delete** (confirm dialog)
- **Polling:** `setInterval` every 5 seconds while any cluster is in a transient state (PROVISIONING/STOPPING/RECONCILING)

**State:** `clusters[]`, `loading`, `error`, `pollingActive`

#### `CreateClusterPage.tsx` (modelled on `CreateInstancePage.tsx`)

**Form fields:**

| Field | Type | Default |
|---|---|---|
| Cluster name | text input | `my-cluster` |
| Location | select (zones from existing zone list) | `us-central1-a` |
| Master version | select | `1.28.0`, `1.27.0`, `1.26.0` |
| Node pool name | text | `default-pool` |
| Number of nodes | number | `3` |
| Machine type | select (reuse existing machine type list) | `e2-medium` |
| Disk size (GB) | number | `100` |
| Network | select (reuse VPC list) | `default` |
| Description | textarea | optional |

**On submit:** calls `createCluster()`, then navigates to `/services/gke/clusters` with a toast notification.

#### `GKEClusterDetailPage.tsx`

**Layout:**
- Breadcrumb: Kubernetes Engine > Clusters > `{clusterName}`
- Info cards: Status, Endpoint, Master Version, Node Count, Network, Location, Created
- Node Pools section: table with Name | Nodes | Machine Type | Status | Actions (delete)
- **Download kubeconfig** button: calls `getKubeconfig()` then triggers browser file download as `{clusterName}-kubeconfig.yaml`
- **Add Node Pool** button: inline form slide-in or modal

---

### 2.3 Service Catalog (`gcp-stimulator-ui/src/config/serviceCatalog.ts`)

Add a new entry to the `services` array:

```typescript
{
  id: 'gke',
  name: 'Kubernetes Engine',
  icon: Container,          // from lucide-react (or 'Box' icon if Container unavailable)
  description: 'Managed Kubernetes service',
  category: 'Containers',   // new category
  enabled: true,
  sidebarLinks: [
    { label: 'Clusters',   path: '/services/gke/clusters',  icon: Server   },
    { label: 'Node Pools', path: '/services/gke/node-pools', icon: Layers  },
  ]
}
```

The `CloudConsoleLayout` or wherever categories are grouped will naturally render a new **Containers** section since the category string is new.

---

### 2.4 Routing (`gcp-stimulator-ui/src/App.tsx`)

Add the following inside the `<CloudConsoleLayout>` outlet's route tree:

```tsx
{/* GKE */}
<Route path="/services/gke"                                          element={<GKEDashboardPage />} />
<Route path="/services/gke/clusters"                                 element={<GKEDashboardPage />} />
<Route path="/services/gke/clusters/create"                          element={<CreateClusterPage />} />
<Route path="/services/gke/clusters/:clusterName"                    element={<GKEClusterDetailPage />} />
<Route path="/services/gke/node-pools"                               element={<GKEDashboardPage />} />
```

---

## Phase 3 — Verification Checklist

| Test | Expected |
|---|---|
| `POST /container/v1/projects/demo/locations/us-central1-a/clusters` | Returns `status: PROVISIONING` immediately |
| Poll `GET .../clusters/my-cluster` every 5s | Status transitions to `RUNNING` within ~30s |
| `GET .../clusters/my-cluster/kubeconfig` | Returns YAML with server IP matching the container's bridge IP |
| `kubectl --kubeconfig=<file> get nodes` | Returns nodes if k3s booted successfully |
| `DELETE .../clusters/my-cluster` | Status goes to `STOPPING`, then cluster disappears from list |
| UI: Create cluster form | Redirects to cluster list after submit, new row shows PROVISIONING badge |
| UI: Status badges poll | Badge auto-updates to RUNNING without page refresh |
| UI: Download kubeconfig | Browser downloads `my-cluster-kubeconfig.yaml` |
| UI: Containers nav category | Renders as its own section separate from Compute |
| UI: Delete from table | Opens confirm dialog, row disappears after deletion |

---

## File Change Summary

### New Files

| File | Purpose |
|---|---|
| `minimal-backend/api/gke.py` | GKE API router (~300 lines) |
| `gcp-stimulator-ui/src/api/gke.ts` | Typed API functions (~80 lines) |
| `gcp-stimulator-ui/src/pages/GKEDashboardPage.tsx` | Cluster list page (~400 lines) |
| `gcp-stimulator-ui/src/pages/CreateClusterPage.tsx` | Create cluster form (~350 lines) |
| `gcp-stimulator-ui/src/pages/GKEClusterDetailPage.tsx` | Cluster detail + node pools (~300 lines) |

### Modified Files

| File | Change |
|---|---|
| `minimal-backend/database.py` | Add `GKECluster` and `NodePool` models (+40 lines) |
| `minimal-backend/docker_manager.py` | Add `create_k3s_cluster`, `get_k3s_kubeconfig`, `delete_k3s_cluster` (+80 lines) |
| `minimal-backend/main.py` | Import `gke`, register router (+2 lines) |
| `gcp-stimulator-ui/src/config/serviceCatalog.ts` | Add GKE service entry (+15 lines) |
| `gcp-stimulator-ui/src/App.tsx` | Add GKE routes (+5 lines) |

---

## Notes / Risks

- **k3s Docker image size:** `rancher/k3s` is ~200 MB. First cluster creation will be slow if not pre-pulled.
- **Privileged containers:** k3s requires `--privileged` flag. This is fine for a local dev simulator but not suitable for production environments.
- **Port conflicts:** If multiple clusters are created, each k3s container uses port 6443. Since containers are on the Docker bridge network and we use the container IP directly in kubeconfig (not host port mappings), there are no host port conflicts.
- **k3s readiness polling:** The background thread should poll the k3s API server (`GET https://<ip>:6443/readyz`) with a timeout of 60s before marking the cluster RUNNING. On failure, status is set to ERROR.
- **SQLite concurrency:** Background threads updating the DB require care with SQLite. Each thread should open its own `SessionLocal()` session rather than sharing one — same pattern already used in `compute.py`.
