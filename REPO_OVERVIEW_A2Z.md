# GCP Stimulator – Full Repository Overview (A–Z)

This document describes the entire repository from end to end: what it is trying to do, how it is structured, how the pieces talk to each other, and what is implemented today vs. what is out of scope.

---

## 1. Purpose & High‑Level Concept

**Goal:** Provide a local, Docker-backed emulator for a subset of Google Cloud Platform (GCP) services so that developers can:

- Develop and test against GCP-like APIs without hitting real GCP.
- Use familiar tools (`gcloud`, official SDKs, raw REST) against local endpoints.
- See realistic resources (VMs, networks, buckets, objects, service accounts) with a UI.

**Core ideas:**

- **Compute Engine**: A VM instance = one Docker container.
- **VPC Network**: A GCP VPC = a Docker bridge network.
- **NAT / Internet**: Outbound internet uses Docker's standard bridge NAT on the host.
- **Cloud Storage**: Buckets and objects are stored in PostgreSQL (metadata) + local filesystem (content).
- **IAM**: Basic service account metadata is modeled (no full policy enforcement).
- **Projects**: Simple project records drive multi-project support.

The stack is:

- **Backend**: FastAPI (Python) + SQLAlchemy + PostgreSQL + Docker SDK.
- **Frontend**: React + TypeScript + Vite.
- **Data plane**: Docker engine and local filesystem.

---

## 2. Repository Layout

At the top level you will see (actual structure):

- [README.md](README.md) – High-level description (note: some names are from an earlier "gcp-emulator" variant).
- [examples](examples) – Usage examples with `gcloud`, Python SDK, and raw REST.
- [gcp-stimulator-ui](gcp-stimulator-ui) – React + Vite frontend.
- [minimal-backend](minimal-backend) – FastAPI backend implementing the GCP-like APIs.

Other files may exist in your environment (Docker, scripts, Terraform, etc.); this document focuses on what is present in this workspace.

---

## 3. Backend: `minimal-backend` (FastAPI + PostgreSQL + Docker)

### 3.1 Overview

Key files:

- [minimal-backend/main.py](minimal-backend/main.py) – FastAPI app factory and router registration.
- [minimal-backend/database.py](minimal-backend/database.py) – SQLAlchemy models and DB session.
- [minimal-backend/docker_manager.py](minimal-backend/docker_manager.py) – Helpers for Docker containers & networks (used by Compute/VPC APIs).
- [minimal-backend/api](minimal-backend/api) – All HTTP API modules:
  - [compute.py](minimal-backend/api/compute.py) – Compute Engine-like operations.
  - [vpc.py](minimal-backend/api/vpc.py) – VPC network management.
  - [storage.py](minimal-backend/api/storage.py) – Cloud Storage buckets & objects.
  - [projects.py](minimal-backend/api/projects.py) – Cloud Resource Manager-style projects.
  - [iam.py](minimal-backend/api/iam.py) – Service account CRUD (metadata-level IAM).
- [minimal-backend/FEATURES_VERIFIED.md](minimal-backend/FEATURES_VERIFIED.md) – Human-readable summary of what has been tested and confirmed working.

### 3.2 Application Wiring (`main.py`)

The backend app is defined in [minimal-backend/main.py](minimal-backend/main.py):

- Creates a `FastAPI` app with title "GCP Stimulator" and version `1.0.0`.
- Adds permissive CORS middleware (allow all origins, methods, headers) to make local UI/dev easy.
- Exposes utility endpoints:
  - `GET /` → simple info JSON (`{"message": "GCP Stimulator API", ...}`).
  - `GET /health` → `{ "status": "healthy" }` for health checks.
- Registers routers with GCP-like prefixes:
  - Compute/VPC: `/compute/v1` → [compute.py](minimal-backend/api/compute.py) and [vpc.py](minimal-backend/api/vpc.py).
  - Projects: `/cloudresourcemanager/v1` → [projects.py](minimal-backend/api/projects.py).
  - IAM: `/v1` → [iam.py](minimal-backend/api/iam.py).
  - Storage: no extra prefix; routes are defined directly as `/storage/v1/...` and `/download/storage/v1/...` in [storage.py](minimal-backend/api/storage.py).
- When run as a script, starts `uvicorn` on port `8080` (or `PORT` env var).

**Runtime assumptions:**

- `DATABASE_URL` must point to a running PostgreSQL instance.
- A local Docker daemon must be available for container and network operations.

### 3.3 Database Models (`database.py`)

[database.py](minimal-backend/database.py) defines all persistent models using SQLAlchemy. Main models:

- **Instance** – Represents a Compute Engine VM and maps directly to a Docker container:
  - Key fields: `name`, `project_id`, `zone`, `machine_type`, `status` (`RUNNING` / `TERMINATED`), `container_id`, `container_name`, `internal_ip`, `external_ip`, `network_url`, `created_at`, `updated_at`.
- **Project** – Represents a GCP project record:
  - Fields: `id` (projectId), `name`, `project_number`, `location`, `compute_api_enabled`, timestamps.
- **Zone** – Compute zones:
  - Fields: `id`, `name`, `region`, `status`, `description`.
- **MachineType** – Machine type metadata:
  - Fields: `id`, `name`, `zone`, `guest_cpus`, `memory_mb`, `description`.
- **Network** – Represents a VPC network and its backing Docker network:
  - Fields: `id`, `name`, `project_id`, `docker_network_name`, `auto_create_subnetworks`, `creation_timestamp`.
- **Bucket** – Cloud Storage bucket:
  - Fields: `id` and `name` (bucket name), `project_id`, `location`, `storage_class`, `versioning_enabled`, various config fields (`meta`, `cors`, `notification_configs`, `lifecycle_config`), timestamps.
- **Object** – Cloud Storage object:
  - Fields: `id` (unique object identifier), `bucket_id`, `name`, `generation`, `size`, `content_type`, `md5_hash`, `crc32c_hash`, `file_path`, `metageneration`, `storage_class`, `is_latest`, `deleted`, `time_created`, timestamps, `meta`.
  - Metadata lives in Postgres; actual bytes live on disk under `/tmp/gcs-storage`.
- **ServiceAccount** – Basic IAM service accounts:
  - Fields: `id` (email), `project_id`, `email`, `display_name`, `description`, `unique_id` (numeric), `disabled`, timestamps.

`get_db()` yields a session per request and ensures it is closed afterwards.

Tables are assumed to already exist; `Base.metadata.create_all()` is intentionally commented out.

### 3.4 Compute Engine API (`api/compute.py`)

[compute.py](minimal-backend/api/compute.py) implements Compute Engine-like endpoints:

- **Zones & machine types**:
  - `GET /compute/v1/projects/{project}/zones` → returns zones from `Zone` table.
  - `GET /compute/v1/projects/{project}/zones/{zone}/machineTypes` → returns machine types in a zone.
- **Operations wait**:
  - `POST /compute/v1/projects/{project}/zones/{zone}/operations/{operation}/wait` → returns an immediate `DONE` operation (all operations are effectively synchronous).
- **Internet Gateway (control-plane only)**:
  - Internal helper `_internet_gateway_resource(project)` returns a static gateway document:
    - `kind: compute#internetGateway`, `name: default-internet-gateway`, `backing: docker-bridge-nat`, `network: .../global/networks/default`.
  - `GET /compute/v1/projects/{project}/global/internetGateways` → returns a list with the single default gateway.
  - `GET /compute/v1/projects/{project}/global/internetGateways/default-internet-gateway` → returns that gateway.
  - This is **control-plane only**: it's for visibility and compatibility; all real NAT is handled by Docker bridge on the host.
- **Instances**:
  - `GET /compute/v1/projects/{project}/zones/{zone}/instances`:
    - Loads `Instance` rows for the project/zone.
    - For each with a `container_id`, queries Docker for actual status:
      - `running` → `status = RUNNING`.
      - `exited` → `status = TERMINATED`.
    - Commits updated statuses.
    - Returns `compute#instanceList` with:
      - `dockerContainerId`, `dockerContainerName` for UI use.
      - `networkInterfaces` including:
        - `networkIP` (container IP from Docker network).
        - `network` (network URL stored in DB).
        - `accessConfigs` with a static `ONE_TO_ONE_NAT` entry (`natIP: 127.0.0.1`) to mimic external IP metadata.
  - `GET /compute/v1/projects/{project}/zones/{zone}/instances/{instance_name}`:
    - Similar status refresh from Docker.
    - Returns `compute#instance` with `networkInterfaces` that include a fully qualified network URL and static `accessConfigs`.
  - `POST /compute/v1/projects/{project}/zones/{zone}/instances`:
    - Parses the request body, extracts `name` and `machineType` (falls back to `e2-medium`).
    - Validates that the instance name is unique per project+zone.
    - Determines target network:
      - Default: `default` → `global/networks/default`.
      - Or from `networkInterfaces[0].network` (accepts short or full URLs).
    - Looks up `Network` row for `{project, network_name}` to find `docker_network_name`.
    - Uses `docker_manager.create_container(name, network=docker_network_name)` to:
      - Create a Docker container attached to that Docker network.
      - Retrieve `container_id`, `container_name`, `internal_ip`.
    - Creates an `Instance` row with `status = RUNNING` and network info.
    - Returns a `compute#operation` with status `DONE` and `targetLink` pointing to the created instance.
  - Additional endpoints (not included in the clipped section but present further down the file) handle:
    - `stop_instance` → stops Docker container + updates status.
    - `start_instance` → starts Docker container + updates status.
    - `delete_instance` → deletes Docker container and removes the `Instance` row.

**Key mapping:** One `Instance` row ↔ one Docker container; network selection is driven by the `Network` table.

### 3.5 VPC Network API (`api/vpc.py`)

[vpc.py](minimal-backend/api/vpc.py) manages VPC networks and their Docker counterparts:

- **ensure_default_network(db, project)**:
  - Checks if `Network` with `name="default"` exists for the project.
  - If not, creates a record mapping `default` to Docker's built-in `bridge` network:
    - `docker_network_name = "bridge"`.
    - `auto_create_subnetworks = True`.
- **List networks**:
  - `GET /compute/v1/projects/{project}/global/networks`:
    - Ensures the default network exists.
    - Returns all `Network` rows for the project, including `dockerNetworkName` and `autoCreateSubnetworks` flags.
- **Get a network**:
  - `GET /compute/v1/projects/{project}/global/networks/{network_name}`:
    - Looks up `Network` and returns its details (including `dockerNetworkName`).
- **Create a network**:
  - `POST /compute/v1/projects/{project}/global/networks` with body e.g. `{ "name": "my-vpc", "autoCreateSubnetworks": false }`:
    - Validates uniqueness of `name` per project.
    - Creates a new Docker network using the Docker SDK:
      - Name: `gcp-vpc-{project}-{name}`.
      - Driver: `bridge`.
      - Labels: `gcp-project={project}`, `gcp-network={name}`.
    - Creates a `Network` DB row with that `docker_network_name`.
    - Returns a `compute#operation` with status `DONE`.
- **Delete a network**:
  - `DELETE /compute/v1/projects/{project}/global/networks/{network_name}`:
    - Fails if `network_name == "default"`.
    - Fails if any `Instance` row uses this network (via a `network_url` filter).
    - If the Docker network is not `bridge`, attempts to remove it via Docker SDK.
    - Deletes the `Network` row and returns a `compute#operation` with status `DONE`.

**Key mapping:**

- `default` VPC → Docker `bridge` network.
- Custom VPC `X` in project `P` → Docker network `gcp-vpc-P-X`.

### 3.6 Cloud Storage API (`api/storage.py`)

[storage.py](minimal-backend/api/storage.py) emulates core Cloud Storage behavior:

- **Constants & helpers**:
  - `STORAGE_DIR = "/tmp/gcs-storage"` – base directory on local disk for object bytes.
  - `_now()` – returns an RFC3339 UTC timestamp.
  - `_calc_hashes(content: bytes)` – computes MD5 and CRC32C, returns both as base64 strings.

- **Dashboard stats**:
  - `GET /dashboard/stats`:
    - Aggregates `totalObjects` and `totalStorageBytes` from the `Object` table where `deleted == False`.

- **Buckets**:
  - `GET /storage/v1/b`:
    - Lists buckets, optionally filtered by `?project=`.
    - Returns `storage#buckets` with `timeCreated` and `updated` values.
  - `POST /storage/v1/b`:
    - Accepts JSON matching `BucketCreate` (`name`, optional `location`, `storageClass`).
    - If a bucket already exists, returns its metadata (idempotent behavior).
    - Otherwise, creates a `Bucket` row and a directory at `/tmp/gcs-storage/{bucket}`.
  - `GET /storage/v1/b/{bucket}`:
    - Looks up `Bucket` and returns its metadata; 404 if missing.
  - `DELETE /storage/v1/b/{bucket}`:
    - Deletes all `Object` rows for that bucket and then deletes the `Bucket` row.
    - Marks success with a `204 No Content` response (does not remove filesystem directory recursively; only removes object file entries one-by-one as objects are deleted elsewhere).
  - `GET /storage/v1/b/{bucket}/storageLayout`:
    - Returns a `storage#storageLayout` document with `hierarchicalNamespace.enabled = false`.

- **Objects**:
  - `GET /storage/v1/b/{bucket}/o`:
    - Lists `Object` rows for the bucket where `deleted == False`.
    - Supports an optional `prefix` filter.
    - Returns `storage#objects` with metadata for each object including `md5Hash`, `crc32c`, `generation`, etc.
  - `GET /storage/v1/b/{bucket}/o/{object}` and `GET /download/storage/v1/b/{bucket}/o/{object}`:
    - Handles both metadata and media retrieval based on `alt=media` query param.
    - Resolves URL-encoded object names via `unquote`.
    - **Metadata mode**: returns a `storage#object` document matching DB values.
    - **Media mode** (`alt=media`): reads file from `/tmp/gcs-storage/{bucket}/{object}` and returns raw bytes with headers:
      - `Content-Length`, `x-goog-hash`, `x-goog-generation`, `x-goog-metageneration`, `x-goog-stored-content-length`, `ETag`, and a `Content-Disposition` with attachment filename.
  - `DELETE /storage/v1/b/{bucket}/o/{object}`:
    - Marks the `Object` row as `deleted = True` and deletes the file from disk when present.
    - Returns `204 No Content`.
  - `POST /upload/storage/v1/b/{bucket}/o`:
    - Uploads/creates an object.
    - Accepts either:
      - A raw body (when `name` is given as query string), or
      - A basic multipart-style body where it extracts `name` and the content segment via regex and boundary parsing.
    - Resolves `object_name` from the `name` query param or from JSON-like `"name": "..."` in the body.
    - Writes content to `/tmp/gcs-storage/{bucket}/{object_name}`.
    - Calculates MD5 + CRC32C and persists metadata to the `Object` table.
    - If an object with the same name exists and is not deleted:
      - Updates size, hashes, file_path, `updated_at` and increments `generation`.
    - If it does not exist:
      - Creates a new row with `generation=1`, `metageneration=1`, timestamps, and `deleted=False`.
    - Returns `storage#object` metadata JSON for the uploaded object.
  - `POST /storage/v1/b/{src_bucket}/o/{src_obj}/rewriteTo/b/{dst_bucket}/o/{dst_obj}`:
    - Implements a simplified `rewrite` (copy) operation.
    - Verifies source and destination buckets exist.
    - Copies the file on disk and creates a new `Object` in the destination bucket with `generation=1`.
    - Returns a `storage#rewriteResponse` with `done: true` and the new object resource.

**Storage model:**

- Metadata in PostgreSQL (`Bucket`, `Object` tables).
- Bytes on disk under `/tmp/gcs-storage/{bucket}/{object}`.
- Basic generations and hashes; full object versioning behavior can be expanded as needed.

### 3.7 Projects API (`api/projects.py`)

[projects.py](minimal-backend/api/projects.py) is intentionally small:

- `GET /cloudresourcemanager/v1/projects`:
  - Returns all `Project` rows as `{ "projectId", "name", "projectNumber", "lifecycleState": "ACTIVE" }`.
  - Underpins multi-project support in gcloud/UI.

Other Cloud Resource Manager features such as folders/organizations are not modeled.

### 3.8 IAM API (`api/iam.py`)

[iam.py](minimal-backend/api/iam.py) focuses on service accounts only:

- **Models**: Uses the `ServiceAccount` table in [database.py](minimal-backend/database.py).
- **Data model**:
  - A service account is identified by its email (`{accountId}@{project}.iam.gserviceaccount.com`).
  - Each has a unique numeric `unique_id`, display name, description, disabled flag, and timestamps.

**Endpoints:**

- `GET /v1/projects/{project}/serviceAccounts`:
  - Lists all service accounts for a project.
- `POST /v1/projects/{project}/serviceAccounts`:
  - Accepts a `ServiceAccountRequest` with `accountId` and optional `serviceAccount` (displayName/description).
  - Generates the standard service account email and a random large numeric `unique_id`.
  - Enforces uniqueness (409 if already exists).
  - Returns the newly created service account resource.
- `GET /v1/projects/{project}/serviceAccounts/{email}`:
  - Fetches a service account by its email; 404 if not found.
- `DELETE /v1/projects/{project}/serviceAccounts/{email}`:
  - Deletes a service account record (no soft-delete or key revocation logic).
- `GET /v1/projects/{project}/serviceAccounts/{email}/keys`:
  - Placeholder: checks that the account exists, but always returns `{"keys": []}` (no key management yet).

**Important:**

- There is no real IAM policy or permission enforcement; this is a metadata-layer emulator so clients can list/create/delete service accounts and see realistic responses.

### 3.9 Docker Integration (`docker_manager.py`)

Although not expanded here line-by-line, [docker_manager.py](minimal-backend/docker_manager.py) is responsible for:

- Creating Docker containers for instances with a specified network.
- Starting, stopping, and deleting containers.
- Inspecting containers to get internal IPs and status.

It is used exclusively by [compute.py](minimal-backend/api/compute.py) and [vpc.py](minimal-backend/api/vpc.py) to bind the GCP-like APIs to real Docker networks and containers.

### 3.10 Verified Behaviors (`FEATURES_VERIFIED.md`)

[FEATURES_VERIFIED.md](minimal-backend/FEATURES_VERIFIED.md) documents the features that have been manually verified:

- `gcloud compute` commands (list/create/stop/start/delete instances) work end-to-end.
- Instance ↔ Docker container mapping is correct and reflected in API responses.
- VPC networks ↔ Docker networks mapping works, including default network mapping to `bridge` and custom networks creating `gcp-vpc-{project}-{name}`.
- The UI can display Docker container IDs from API responses.
- A **Network & Internet Gateway Model** section explicitly states:
  - Every VPC network corresponds to a Docker bridge network.
  - Default VPC is backed by Docker `bridge`.
  - Outbound internet uses Docker's NAT; no custom NAT or firewall.
  - Internet Gateway endpoints are control-plane-only; instances receive a static `accessConfigs` entry for external IP metadata, but inbound traffic is not implemented.

---

## 4. Frontend: `gcp-stimulator-ui` (React + Vite + TypeScript)

### 4.1 Overview

[gcp-stimulator-ui](gcp-stimulator-ui) is a React app scaffolded with Vite and TypeScript. Key files and folders:

- [gcp-stimulator-ui/README.md](gcp-stimulator-ui/README.md) – Vite React template notes.
- [gcp-stimulator-ui/src/main.tsx](gcp-stimulator-ui/src/main.tsx) – React entry point.
- [gcp-stimulator-ui/src/App.tsx](gcp-stimulator-ui/src/App.tsx) – Top-level application component.
- [gcp-stimulator-ui/src](gcp-stimulator-ui/src):
  - [api](gcp-stimulator-ui/src/api) – Typed HTTP API clients for backend endpoints.
  - [components](gcp-stimulator-ui/src/components) – Reusable UI components.
  - [config](gcp-stimulator-ui/src/config) – Frontend configuration (e.g., service catalog, API base URLs).
  - [contexts](gcp-stimulator-ui/src/contexts) – React context providers (e.g., project selection, app-level state).
  - [hooks](gcp-stimulator-ui/src/hooks) – Custom hooks that encapsulate API calls and state logic.
  - [layouts](gcp-stimulator-ui/src/layouts) – Page layouts and shells.
  - [pages](gcp-stimulator-ui/src/pages) – Main route/page components.
  - [types](gcp-stimulator-ui/src/types) – Shared TypeScript types and interfaces.
  - [utils](gcp-stimulator-ui/src/utils) – Utility functions.

The UI is designed to:

- Display instances, networks, buckets, and storage stats.
- Allow basic CRUD for those resources via the backend API.
- Provide a dashboard-style experience similar to the GCP console.

### 4.2 API Client Layer (`src/api`)

[gcp-stimulator-ui/src/api](gcp-stimulator-ui/src/api) provides strongly-typed wrappers around backend REST APIs:

- [client.ts](gcp-stimulator-ui/src/api/client.ts) – base HTTP client (likely sets base URL, headers, error handling).
- [health.ts](gcp-stimulator-ui/src/api/health.ts) – hits `/health` on the backend.
- [buckets.ts](gcp-stimulator-ui/src/api/buckets.ts) – Cloud Storage bucket operations (list/create/get/delete).
- [objects.ts](gcp-stimulator-ui/src/api/objects.ts) – List, get, and delete objects.
- [uploadApi.ts](gcp-stimulator-ui/src/api/uploadApi.ts) – Object upload workflows.
- [storageStats.ts](gcp-stimulator-ui/src/api/storageStats.ts) – Dashboard stats `/dashboard/stats`.
- [lifecycle.ts](gcp-stimulator-ui/src/api/lifecycle.ts), [objectVersionsApi.ts](gcp-stimulator-ui/src/api/objectVersionsApi.ts), [signedUrlApi.ts](gcp-stimulator-ui/src/api/signedUrlApi.ts), [events.ts](gcp-stimulator-ui/src/api/events.ts) – additional helpers for lifecycle rules, versioning, signed URLs, and events (implementation may be partial or forward-looking depending on backend support).

Other parts of the UI (components/pages/hooks) compose these APIs to provide interactive views.

---

## 5. Examples (`examples`)

The [examples](examples) folder contains documentation and snippets for using the emulator from different clients:

- [examples/gcloud-cli.md](examples/gcloud-cli.md) – How to configure and use `gcloud` against the local endpoints.
- [examples/python-sdk.md](examples/python-sdk.md) – How to configure the official Python SDK (e.g., `google-cloud-storage`) to use the emulator.
- [examples/rest-api.md](examples/rest-api.md) – Raw HTTP calls (e.g., `curl`/Postman) for buckets, objects, and compute APIs.

These files are the quickest path to copy‑paste ready commands for interacting with the system.

---

## 6. Data & Storage Model (End-to-End)

### 6.1 Database

- Backed by PostgreSQL, configured via `DATABASE_URL` in [minimal-backend/database.py](minimal-backend/database.py).
- Holds metadata for:
  - Compute: projects, zones, machine types, instances, networks.
  - Storage: buckets and objects.
  - IAM: service accounts.

This allows state to persist across backend restarts as long as the DB is persistent.

### 6.2 Filesystem

- Actual object bytes live under `/tmp/gcs-storage` on the backend host.
- Each bucket is a top-level directory: `/tmp/gcs-storage/{bucket}`.
- Each object is a file inside that bucket directory: `/tmp/gcs-storage/{bucket}/{object}`.

### 6.3 Docker

- Each instance is a Docker container, connected to a Docker network that corresponds to a VPC network.
- Default VPC networks share Docker's `bridge` network by design.
- Custom VPCs create their own Docker bridge networks.

---

## 7. Networking & Internet Gateway Model

The emulator models networking at a **control-plane level** while delegating all real data-plane traffic to Docker.

### 7.1 VPC ↔ Docker Network Mapping

- Default project VPC:
  - There is always a `default` VPC per project (ensured on-demand in [vpc.py](minimal-backend/api/vpc.py)).
  - It is backed by Docker's built-in `bridge` network.
- Custom VPC networks:
  - A `POST` to `/compute/v1/projects/{project}/global/networks` creates a new VPC.
  - The backend creates a Docker network `gcp-vpc-{project}-{name}` with driver `bridge`.

### 7.2 Instances & IPs

- When an instance is created, it is attached to one of these Docker networks.
- The Docker SDK provides the container's internal IP address (`internal_ip`), which appears in `networkInterfaces[].networkIP` in API responses.

### 7.3 NAT & Internet Gateway

- **NAT**:
  - There is no custom NAT implementation in the backend.
  - Outbound traffic from containers traverses Docker's bridge NAT on the host (iptables MASQUERADE rules), exactly as in a typical `bridge`-mode Docker setup.
- **Internet Gateway (control-plane only)**:
  - The backend exposes an `internetGateway` resource for compatibility and visibility:
    - `GET /compute/v1/projects/{project}/global/internetGateways`.
    - `GET /compute/v1/projects/{project}/global/internetGateways/default-internet-gateway`.
  - This always returns a single `default-internet-gateway` with `backing: "docker-bridge-nat"` and network pointing to `global/networks/default`.
  - This is **not** a real data-plane gateway; it simply reflects that Docker's bridge NAT is providing outbound connectivity.
- **Instance external IP metadata**:
  - `networkInterfaces[].accessConfigs[]` is populated with a static entry:
    - `type: "ONE_TO_ONE_NAT"`.
    - `natIP: "127.0.0.1"`.
  - This allows clients (and UI) to see a "public IP" field but does **not** implement real inbound connectivity rules.

### 7.4 Limitations

- No explicit routing tables are modeled.
- No firewall rule enforcement is implemented.
- No support yet for multiple external IPs, forwarding rules, or load balancers.
- Inbound traffic to instances is not modeled; containers are not globally reachable by the `natIP` metadata value.

---

## 8. IAM Model & Limitations

The IAM model focuses on service accounts and omits policies and role enforcement.

**What is emulated:**

- Create/list/get/delete service accounts per project.
- See realistic service account emails and numeric IDs.
- List keys endpoint (returns an empty list for now).

**What is NOT emulated (as of now):**

- IAM policy bindings (roles on projects, instances, buckets, etc.).
- Custom roles, organizations, folders.
- Short-lived credentials or OAuth token flows.
- Workload Identity, impersonation, etc.

The intent is to support happy-path flows where a tool or UI expects service accounts to exist but does not rely on actual permission checks.

---

## 9. How to Run (Typical Flow)

Exact commands may vary with your environment, but a typical local run looks like:

1. **Start PostgreSQL** and ensure `DATABASE_URL` is set correctly.
2. **Start the backend** from the repo root:

   ```bash
   cd minimal-backend
   python main.py  # or: uvicorn main:app --host 0.0.0.0 --port 8080
   ```

   - API docs are available at `http://localhost:8080/docs`.
   - Health check at `http://localhost:8080/health`.

3. **Start the frontend**:

   ```bash
   cd gcp-stimulator-ui
   npm install
   npm run dev
   ```

   - UI (Vite dev server) typically runs on `http://localhost:5173`.

4. **Point clients to the emulator** (examples, adjust as needed):

   - Cloud Storage SDKs:
     - Set `STORAGE_EMULATOR_HOST=http://127.0.0.1:8080`.
   - `gcloud` (for compute):
     - Use the examples under [examples/gcloud-cli.md](examples/gcloud-cli.md) along with any required environment tweaks (e.g., using `gcloud` `--endpoint-overrides` or HTTP proxying depending on your setup).

---

## 10. Current Limitations & Future Directions

Some known limitations and possible future work:

- **Networking & Security**:
  - No firewall rules or security policies are enforced.
  - No subnet-level modeling beyond the Docker network association.
  - No load balancers, forwarding rules, or packet mirroring.
- **Compute**:
  - Limited to basic instance lifecycle (create/list/get/start/stop/delete).
  - No disks/snapshots, images, or metadata server.
- **Storage**:
  - Core bucket and object operations are present.
  - Basic generation and metageneration exist, but full multi-versioning semantics (like `versions=true` listings) may not be fully implemented.
  - No signed URL generation on the backend at this time (even though UI/API stubs exist).
- **IAM**:
  - No role-based access control; everything is effectively allowed once the HTTP request reaches the backend.
- **Observability**:
  - Logs and metrics are minimal; no structured logging, tracing, or metrics exports currently.

---

## 11. How to Use This Document

- **New developer onboarding**:
  - Start with sections 1–3 for backend architecture and models.
  - Then read 4–5 for UI and examples.
  - Use 6–8 as a reference when modifying storage, networking, or IAM.
- **Feature work**:
  - Before adding a new GCP feature, decide whether it should be:
    - Pure control-plane (metadata only, like the Internet Gateway), or
    - Backed by real data-plane changes (Docker, filesystem, etc.).
- **Troubleshooting**:
  - Map symptoms (e.g., missing instances, wrong IPs, broken uploads) to the relevant model and API module using this document.

This overview intentionally balances accuracy with brevity. For implementation-level details, always refer back to the source files linked throughout (e.g., [minimal-backend/api/compute.py](minimal-backend/api/compute.py), [minimal-backend/api/storage.py](minimal-backend/api/storage.py), and [minimal-backend/database.py](minimal-backend/database.py)).