# Google Cloud Stimulator — Gap Analysis & Implementation Plan
> Reference baseline: AWS Simulator (`/home/ubuntu/aws-simulator/`)
> Scope: Compute Engine, VPC Network, IAM, GKE
> Constraint: **No implementation begins until this plan is approved.**

---

## 1. Current State Snapshot

| Service | Backend Endpoints | Frontend Handlers | Frontend Lines |
|---|---|---|---|
| **Compute Engine** | 11 | 1 | 531 |
| **VPC (Networks)** | 9 | 3 | 647 |
| **Firewall** | 5 | 2 | 210 |
| **Routes** | 5 | 2 | 182 |
| **IAM** | 5 | 2 | 399 |
| **GKE** | 21 | 9+4 | 805 + 374 |
| **TOTAL GCP** | **56** | | |

### AWS Simulator Reference Depth

| Service | Backend Functions | Frontend Handlers | Frontend States |
|---|---|---|---|
| **EC2** | 53 | 10 | 26 |
| **VPC** | 25 | 21 | 54 |
| **IAM** | 22 | 38 | 68 |
| **EKS** | 27 | 8 | 44 |
| **TOTAL AWS (4 services)** | **127** | | |

**Overall parity: ~44%** (56 of ~127 equivalent endpoints)

---

## 2. SERVICE 1: Compute Engine (vs EC2)

### 2.1 Backend Gaps

| # | Missing Feature | GCP API Route | Priority |
|---|---|---|---|
| B1 | Static External IPs (allocate/release/assign) | `GET/POST/DELETE /projects/{p}/regions/{r}/addresses` | 🔴 High |
| B2 | SSH Key pairs (project-level) | `GET/POST /projects/{p}/global/sshKeys` via metadata | 🔴 High |
| B3 | Instance tags (`setTags`) | `POST .../instances/{n}/setTags` | 🔴 High |
| B4 | Instance metadata (`setMetadata`) | `POST .../instances/{n}/setMetadata` | 🟡 Mid |
| B5 | Persistent disks CRUD | `GET/POST/DELETE .../disks` | 🟡 Mid |
| B6 | Disk attach/detach | `POST .../instances/{n}/attachDisk`, `detachDisk` | 🟡 Mid |
| B7 | Instance templates CRUD | `GET/POST/DELETE .../instanceTemplates` | 🟡 Mid |
| B8 | Serial port output | `GET .../instances/{n}/serialPort` | 🟡 Mid |
| B9 | Snapshots CRUD | `GET/POST/DELETE .../snapshots` | 🟢 Low |
| B10 | Custom images | `GET/POST/DELETE .../images` | 🟢 Low |
| B11 | Pagination (maxResults/pageToken) | all list endpoints | 🟡 Mid |
| B12 | Network interfaces modify | `POST .../instances/{n}/updateNetworkInterface` | 🟢 Low |

### 2.2 Frontend Gaps

| # | Missing Feature | Current | Target |
|---|---|---|---|
| F1 | Launch modal (full config) | CreateInstancePage exists but sparse | Modal with: name, zone, machine type, network/subnet, SSH key, boot disk, startup script, tags, external IP |
| F2 | Instance detail side-panel | Not present | Tabs: Overview \| Disks \| Network \| SSH Keys \| Serial Console |
| F3 | External IP management tab | Not present | Reserve/release static IPs, assign to instance |
| F4 | Instance tags editor | Not present | Inline tag add/remove |
| F5 | Disk management sub-page | Not present | List disks, create, delete, attach/detach |
| F6 | Instance templates page | Not present | List, create, delete templates |
| F7 | Pagination on instance table | None | maxResults + Next / Prev |
| F8 | Bulk actions | None | Checkbox multi-select → start/stop/delete |
| F9 | Filter by zone/status/machine type | None | Dropdown filters on table |

### 2.3 Current vs Target State

```
Current:  [List] [Start] [Stop] [Delete]   ← 1 handler, no detail
Target:   [List] [Create▼] [Bulk▼] + Detail Drawer (5 tabs) + External IPs + Disks tabs
```

---

## 3. SERVICE 2: VPC Network (vs AWS VPC)

### 3.1 Backend Gaps

| # | Missing Feature | GCP API Route | Priority |
|---|---|---|---|
| B1 | Cloud NAT (Cloud Router + NAT) | `GET/POST/DELETE .../routers` + `routers/{r}/nats` | 🔴 High |
| B2 | Static External IPs (regional) | `GET/POST/DELETE .../regions/{r}/addresses` | 🔴 High |
| B3 | VPC Peering | `POST .../networks/{n}/addPeering`, `removePeering` | 🟡 Mid |
| B4 | Flow Logs enable/disable | `PATCH subnetworks/{s}` (logConfig field) | 🟡 Mid |
| B5 | Cloud Router CRUD | `GET/POST/DELETE .../routers` | 🟡 Mid |
| B6 | Network ACLs equiv (VPC Service Controls) | `GET/POST .../accessPolicies` | 🟢 Low |
| B7 | Shared VPC (XPN) | `GET/POST .../projects/{p}/enableXpnHost` | 🟢 Low |
| B8 | Private Service Connect | `GET/POST .../serviceAttachments` | 🟢 Low |
| B9 | Subnet expand CIDR | `PATCH subnetworks/{s}` (ipCidrRange expand) | 🟡 Mid |

**Note**: GCP Firewalls already implemented (5 endpoints). GCP has no "security groups" — firewall rules with target tags serve that role. Frontend should present them as "Firewall Rules" not "Security Groups."

### 3.2 Frontend Gaps

| # | Missing Feature | Current | Target |
|---|---|---|---|
| F1 | Tab layout | Separate pages (Networks, Firewalls, Subnets, Routes) | Unified tabbed VPC Console: Networks \| Subnets \| Firewall Rules \| Routes \| Cloud NAT \| Static IPs \| VPC Peering |
| F2 | Cloud NAT tab | Not present | List routers + NAT configs, create, delete |
| F3 | Static IPs tab | Not present | Reserve regional/global IP, release, assign to resource |
| F4 | VPC Peering tab | Not present | Add/remove peering, show peering state |
| F5 | Flow Logs toggle | Not present | Checkbox on subnet row to enable/disable |
| F6 | Subnet CIDR expand | Not present | Edit subnet to widen CIDR |
| F7 | Firewall rules improved | Basic CRUD | Protocol/port/tag filter, direction badge, priority sort |
| F8 | Network detail page | Not present | Click network → subnets + firewall rules + peerings scoped to that VPC |

### 3.3 Current vs Target State

```
Current:  4 separate sidebar items (Networks, Subnets, Firewalls, Routes) — each sparse
Target:   Single VPC Console page with 7 tabs, unified UX
```

---

## 4. SERVICE 3: IAM (vs AWS IAM)

### 4.1 Backend Gaps

| # | Missing Feature | GCP API Route | Priority |
|---|---|---|---|
| B1 | Predefined roles catalog | `GET https://iam.googleapis.com/v1/roles` | 🔴 High |
| B2 | Custom roles CRUD | `GET/POST/PATCH/DELETE .../projects/{p}/roles` | 🔴 High |
| B3 | Project IAM policy (`getIamPolicy`) | `POST .../projects/{p}:getIamPolicy` | 🔴 High |
| B4 | Project IAM policy (`setIamPolicy`) | `POST .../projects/{p}:setIamPolicy` | 🔴 High |
| B5 | Service account key create | `POST .../serviceAccounts/{e}/keys` | 🔴 High |
| B6 | Service account key delete | `DELETE .../serviceAccounts/{e}/keys/{keyId}` | 🔴 High |
| B7 | Workload Identity binding | `POST .../serviceAccounts/{e}:setIamPolicy` | 🟡 Mid |
| B8 | IAM conditions on bindings | field in binding object | 🟡 Mid |
| B9 | IAM deny policies | `GET/POST .../policies` (v2 API) | 🟢 Low |
| B10 | Audit log viewer | `GET .../projects/{p}/logs` | 🟢 Low |

**Note**: GCP has no "Users" or "Groups" in the IAM-direct sense. The GCP equiv is:
- Users → Google Accounts (principals: `user:email@domain.com`)
- Groups → Google Groups (`group:name@domain.com`)
- Service Accounts → `serviceAccount:sa@project.iam.gserviceaccount.com`
The IAM policy binding is the union point. We simulate this with a DB-backed policy store.

### 4.2 Frontend Gaps

| # | Missing Feature | Current | Target |
|---|---|---|---|
| F1 | Tab layout | Single page, only Service Accounts | 4 tabs: Members & Permissions \| Roles \| Service Accounts \| Audit Logs |
| F2 | Members & Permissions tab | Not present | Table of principals+roles, Add Member (principal + role), Remove Member |
| F3 | Roles browser tab | Not present | List predefined roles with descriptions; filter by category (Compute, Storage, etc.) |
| F4 | Custom roles editor | Not present | Create/edit role with permission checklist |
| F5 | Service account key management | Not present | Per-SA: list keys (truncated), create new (download JSON), delete |
| F6 | Role detail modal | Not present | Click role → view included permissions |
| F7 | IAM policy condition editor | Not present | Condition expression input on binding |
| F8 | Workload Identity toggle | Not present | Enable/configure on service account row |

### 4.3 Current vs Target State

```
Current:  service_account = { name, email } — create / delete only
Target:   Full IAM console: Principals ↔ Roles ↔ Policies + SA key lifecycle
```

---

## 5. SERVICE 4: GKE (vs EKS)

### 5.1 Backend Gaps

| # | Missing Feature | GCP API Route (kubectl-backed) | Priority |
|---|---|---|---|
| B1 | Workloads API (Pods, Deployments, StatefulSets) | `GET .../clusters/{c}/workloads?namespace=all` → `kubectl get all -A -o json` | 🔴 High |
| B2 | Pod logs | `GET .../clusters/{c}/namespaces/{ns}/pods/{pod}/logs` | 🔴 High |
| B3 | Namespace CRUD | `GET/POST/DELETE .../clusters/{c}/namespaces` | 🔴 High |
| B4 | Kubernetes Services list | `GET .../clusters/{c}/services` | 🔴 High |
| B5 | YAML apply | `POST .../clusters/{c}/apply` (body: yaml string) | 🔴 High |
| B6 | Cluster version upgrade | `POST .../clusters/{c}:upgrade` | 🟡 Mid |
| B7 | Node pool config PATCH | `PATCH .../nodePools/{p}` (management, labels, taints) | 🟡 Mid |
| B8 | Describe addon versions | `GET .../addonVersions` | 🟡 Mid |
| B9 | Node cordon/drain | `POST .../clusters/{c}/nodes/{n}:cordon` | 🟢 Low |
| B10 | Kubernetes Events | `GET .../clusters/{c}/events` | 🟢 Low |
| B11 | ConfigMaps list | `GET .../clusters/{c}/configmaps` | 🟢 Low |
| B12 | Persistent Volumes list | `GET .../clusters/{c}/persistentvolumes` | 🟢 Low |

**Implementation note**: All workloads endpoints are thin wrappers over `kubectl` via the k3s Docker container, same pattern as existing `/kubectl` endpoint.

### 5.2 Frontend Gaps

| # | Missing Feature | Current | Target |
|---|---|---|---|
| F1 | Workloads sub-page | Not present | `/services/gke/clusters/:name/workloads` — tabs: Deployments \| Pods \| StatefulSets |
| F2 | Pod logs drawer | Not present | Click pod row → slide-out drawer with live `kubectl logs` output |
| F3 | Namespaces tab (in cluster detail) | Not present | List, create, delete namespaces |
| F4 | K8s Services tab (in cluster detail) | Not present | ClusterIP / NodePort / LoadBalancer service rows |
| F5 | YAML Apply modal | Not present | Textarea + "Apply" button → `kubectl apply -f -` |
| F6 | Cluster upgrade button | Not present | Dropdown version selector in cluster header bar |
| F7 | Node pool config edit | Only resize supported | Edit: machine type (add worker profile), management toggles, taints/labels |
| F8 | Dedicated Node Pools page | Dead route | `/services/gke/node-pools` — aggregated view across all clusters |
| F9 | Addon version selector | Fixed `latest` | Dropdown with available versions on addon install |
| F10 | Events tab | Not present | `kubectl get events -A` in cluster detail |

### 5.3 Current vs Target State

```
Current:  Cluster list + detail (overview + nodes + node pools + addons) + kubectl terminal
Target:   + Workloads page + Pod logs + Namespaces tab + Services tab + YAML Apply modal
```

---

## 6. Prioritized Sprint Plan

### SPRINT 1 — Compute Engine Parity
**Goal**: Launch modal + instance detail panel + External IPs + Disks
**Backend** (6 new endpoints):
1. `GET/POST/DELETE /projects/{p}/regions/{r}/addresses` — static external IPs
2. `POST .../instances/{n}/setTags` — instance tags
3. `POST .../instances/{n}/setMetadata` — instance metadata
4. `GET/POST/DELETE .../disks` — persistent disks
5. `POST .../instances/{n}/attachDisk` + `detachDisk`
6. `GET .../instances/{n}/serialPort` — serial console

**Frontend** (2 major components):
1. Overhaul `ComputeDashboardPage.tsx` — rich launch modal (with VPC/subnet/SSH/disk/tags selectors), instance detail side-drawer (5 tabs), bulk actions
2. New `StaticIPsPage.tsx` — allocate, release, assign IPs

**Acceptance criteria**: Create instance with custom tags → see them in detail drawer; allocate a static IP → assign to running instance

---

### SPRINT 2 — VPC Network Parity
**Goal**: Tabbed VPC console, Cloud NAT, Static IPs, VPC Peering
**Backend** (8 new endpoints):
1. `GET/POST/DELETE .../routers` — Cloud Router
2. `GET/POST/DELETE .../routers/{r}/nats` — Cloud NAT sub-resource
3. `GET/POST/DELETE .../regions/{r}/addresses` — regional static IPs
4. `POST .../networks/{n}/addPeering` + `removePeering` — VPC Peering
5. `PATCH .../subnetworks/{s}` extended — flow logs toggle + CIDR expand

**Frontend** (1 major refactor + 3 new tabs):
1. Merge network pages into single `VPCConsolePage.tsx` with 7 tabs (Networks, Subnets, Firewall Rules, Routes, Cloud NAT, Static IPs, VPC Peering)
2. Cloud NAT tab — list routers + NAT configs, create, delete
3. Static IPs tab — reserve, release, assign
4. VPC Peering tab — add peering, show state (ACTIVE/INACTIVE)

**Acceptance criteria**: Create a Cloud Router + NAT gateway; reserve a static IP; set up VPC peering between two networks

---

### SPRINT 3 — IAM Parity
**Goal**: Policy bindings, custom roles, service account key lifecycle
**Backend** (6 new endpoints):
1. `GET /projects/{p}:getIamPolicy` — return simulated IAM policy bindings
2. `POST /projects/{p}:setIamPolicy` — add/remove member-role bindings
3. `GET /roles` — predefined roles catalog (seeded from static JSON)
4. `GET/POST/PATCH/DELETE /projects/{p}/roles` — custom roles CRUD
5. `POST .../serviceAccounts/{e}/keys` — create SA key (return mock JSON payload)
6. `DELETE .../serviceAccounts/{e}/keys/{keyId}` — delete SA key

**Frontend** (1 major overhaul):
1. Rebuild `IAMDashboardPage.tsx` with 4 tabs:
   - **Members & Permissions**: principal table, add member (email + role selector), remove
   - **Roles**: predefined role browser + custom role editor (permissions checklist)
   - **Service Accounts**: existing list + per-row key management (create/download/delete)
   - **Audit Logs**: stub table (last 50 policy change events)

**Database**: Add `iam_policy_bindings` table `(project, principal, role, condition?)` + `custom_roles` table + `sa_keys` table

**Acceptance criteria**: Add `user:dev@example.com` as `roles/compute.viewer` → see in members tab; create custom role with 3 permissions; create SA key and delete it

---

### SPRINT 4 — GKE Parity
**Goal**: Workloads visibility, pod logs, namespaces, services, YAML apply
**Backend** (5 new endpoints):
1. `GET .../clusters/{c}/workloads?namespace=all` → `kubectl get all -A -o json` parsed response
2. `GET .../clusters/{c}/namespaces/{ns}/pods/{pod}/logs` → `kubectl logs {pod} -n {ns} --tail=200`
3. `GET/POST/DELETE .../clusters/{c}/namespaces` → namespace CRUD via kubectl
4. `GET .../clusters/{c}/services` → `kubectl get services -A -o json`
5. `POST .../clusters/{c}/apply` → `kubectl apply -f -` (YAML string body)
Plus: `POST .../clusters/{c}:upgrade` and `PATCH .../nodePools/{p}`

**Frontend** (3 new pages/components):
1. New `GKEWorkloadsPage.tsx` at `/services/gke/clusters/:name/workloads`
   - Tabs: Deployments | Pods | StatefulSets
   - Click Pod row → `PodLogsDrawer` (slide-out panel, auto-refresh)
2. Add to `GKEClusterDetailPage.tsx`:
   - Tab: **Namespaces** — list + create + delete
   - Tab: **Services** — ClusterIP / NodePort / LB service table
   - Tab: **Events** — `kubectl get events -A` output
   - Button: **Apply YAML** → modal with textarea and Apply button
3. Fix `/services/gke/node-pools` → `GKENodePoolsPage.tsx` (cross-cluster aggregated view)

**Acceptance criteria**: Deploy `kubectl apply` of a simple nginx Deployment via modal → see Pod appear in Workloads tab → click Pod → see log output in drawer

---

## 7. Work Not In Scope (Deferred)

These gaps exist but are **not** part of Sprint 1–4:

| Feature | Reason Deferred |
|---|---|
| Cloud SQL | Separate service, no AWS analog in current 4-service scope |
| Cloud Run | Container-as-a-service, large scope |
| Pub/Sub | Messaging layer, not in the 4 target services |
| Instance templates (Compute) | Mid-priority, Sprint 1 extension candidate |
| Snapshots / Images (Compute) | Low priority |
| Shared VPC / XPN | Low usage complexity |
| Private Service Connect | Advanced use-case |
| IAM deny policies | Advanced, requires v2 API |
| Node cordon/drain (GKE) | Low operational priority |
| GKE Autopilot mode | Requires different provisioning model |
| Fargate equiv (GKE) | Out of scope for k3s-based simulator |

---

## 8. Execution Order Rationale

1. **Compute first** — most visible to new users; launch modal is the entry point for everything
2. **VPC second** — needed to make Compute launch modal meaningful (network/subnet picker populates from VPC)
3. **IAM third** — service accounts are referenced in Compute and GKE; policy bindings unlock per-resource security simulation
4. **GKE last** — already the most complete service; workloads API is the final major gap

---

## 9. Approval Checklist

Before implementation begins, confirm:

- [ ] Sprint order is acceptable (Compute → VPC → IAM → GKE)
- [ ] Each sprint is one focused session (backend + frontend together)
- [ ] Scope for Sprint 1 backend is the 6 endpoints listed above
- [ ] Database schema additions (Sprint 3: iam_policy_bindings, custom_roles, sa_keys) are acceptable
- [ ] "Google Cloud Stimulator" is the project name throughout UI
- [ ] kubectl-backed workloads API approach (Sprint 4) is acceptable

---

*Document generated: 2026-02-05 | Last commit: `3bf09dd` — `feat: GKE agent nodes, resize, project selector fix`*
