# Skill: QA Expert — Tester & Functionality Checker

**name:** QA Testing & Functionality Verification  
**description:** Expert in comprehensive system testing, functionality verification, and constraint identification for GCP Stimulator. Tests all services end-to-end, verifies autoscaling works, validates connectivity, finds cons/limitations, and runs the CloudTester suite. Auto-activates for testing, verification, or bug-finding tasks.

**trigger_keywords:** test, QA, functionality, verify, autoscaling, connectivity, assert, pytest, integration, e2e, bug, edge case, cons, limitation, check, validation, broken, failing, working

**allowed_tools:** Read, Grep, Semantic Search, File Search

---

## Test Framework

```
tests/
├── conftest.py                  ← pytest fixtures (api_client, test_project, etc.)
├── pytest.ini                   ← pytest config (markers: integration)
├── CloudTester/
│   ├── suites/                  ← Service-specific test files
│   │   ├── test_compute.py
│   │   ├── test_compute_gcloud.py
│   │   ├── test_vpc.py
│   │   ├── test_vpc_gcloud.py
│   │   ├── test_storage.py
│   │   ├── test_storage_gcloud.py
│   │   ├── test_iam.py
│   │   ├── test_iam_gcloud.py
│   │   ├── test_gke.py
│   │   ├── test_gke_gcloud.py
│   │   ├── test_autoscaling.py
│   │   ├── test_monitoring.py
│   │   ├── test_firewall.py
│   │   ├── test_pubsub.py
│   │   ├── test_projects.py
│   │   └── integration/         ← Cross-service integration tests
│   ├── base/                    ← Base test classes and fixtures
│   └── scripts/                 ← Test automation scripts
└── legacy/                      ← Old tests (kept for reference)
```

---

## Running Tests

```bash
# All tests
cd /home/ubuntu/gcs-emulator
pytest tests/ -v

# Integration tests only
pytest tests/ -m integration -v

# Single service
pytest tests/CloudTester/suites/test_compute.py -v
pytest tests/CloudTester/suites/test_vpc.py -v
pytest tests/CloudTester/suites/test_storage.py -v

# gcloud CLI compatibility tests
pytest tests/CloudTester/suites/test_compute_gcloud.py -v

# With output capture disabled (see print statements)
pytest tests/ -v -s

# Run and generate report
pytest tests/ -v --tb=short 2>&1 | tee test_report.txt
```

---

## Service Functionality Verification Checklists

### ✅ Compute Engine
```
[ ] List zones → non-empty response
[ ] List machine types in a zone
[ ] Create instance → returns DONE operation
[ ] Get instance → status RUNNING
[ ] Instance has internal IP assigned
[ ] Instance has Docker container created (docker ps | grep instance-{name})
[ ] Stop instance → status TERMINATED/STOPPED
[ ] Start instance → status RUNNING
[ ] Delete instance → 404 on subsequent GET
[ ] Serial console → docker logs output returned
[ ] Static IP (address) → create + assign to instance
[ ] Labels and tags → set and retrieve
```

### ✅ VPC Networks
```
[ ] Create VPC → Docker bridge network created
[ ] List networks → includes created VPC
[ ] Create subnet with CIDR (e.g., 10.0.0.0/24)
[ ] Instances in same VPC can ping each other
[ ] Subnets have correct gateway address
[ ] Routes list includes default internet gateway
[ ] Cloud Router create/list/delete
[ ] Cloud NAT create/list/delete
[ ] VPC peering create/list/delete
[ ] Delete VPC → Docker network removed
```

### ✅ Cloud Storage
```
[ ] Create bucket → 200 response
[ ] List buckets → includes created bucket
[ ] Upload object → 200 response
[ ] List objects in bucket → includes uploaded object
[ ] Download object → returns correct content
[ ] Object metadata (size, md5, crc32c) correct
[ ] Delete object → 404 on subsequent GET
[ ] Delete bucket → 404 on subsequent GET
[ ] Signed URL generation (if applicable)
```

### ✅ IAM
```
[ ] Create service account → email format: {name}@{project}.iam.gserviceaccount.com
[ ] List service accounts → includes created SA
[ ] Get service account → correct details
[ ] Unique ID assigned (numeric)
[ ] Delete service account → 404 on subsequent GET
[ ] Policy bindings create/list
```

### ✅ GKE
```
[ ] Create cluster → status RUNNING
[ ] List clusters → includes created cluster
[ ] Create node pool
[ ] Get cluster details (nodes, version)
[ ] Delete cluster → 404 on subsequent GET
[ ] gcloud container clusters list works
```

### ✅ Autoscaling
```
[ ] Create instance group
[ ] Create autoscaling policy (min/max replicas)
[ ] Policy attached to instance group
[ ] Scale-up trigger → new instances created
[ ] Scale-down trigger → instances removed
[ ] Respect min/max replica limits
[ ] List autoscalers
[ ] Delete autoscaler
```

### ✅ Monitoring
```
[ ] List metrics → non-empty
[ ] Create custom metric
[ ] Get metric data
[ ] Create alert policy
[ ] List alert policies
[ ] Monitoring dashboard loads in UI
```

### ✅ Pub/Sub
```
[ ] Create topic
[ ] List topics
[ ] Create subscription on topic
[ ] Publish message to topic
[ ] Pull message from subscription
[ ] Delete subscription
[ ] Delete topic
```

### ✅ Secret Manager
```
[ ] Create secret
[ ] Add secret version
[ ] Get secret version (access)
[ ] List secrets
[ ] Delete secret
```

---

## Connectivity Tests

### Instance-to-Instance Connectivity
```bash
# Get IPs of two running instances
INSTANCE_1=$(docker inspect instance-vm1 | python3 -c "import sys,json; d=json.load(sys.stdin)[0]; nets=d['NetworkSettings']['Networks']; print(list(nets.values())[0]['IPAddress'])")
INSTANCE_2=$(docker inspect instance-vm2 | python3 -c "import sys,json; d=json.load(sys.stdin)[0]; nets=d['NetworkSettings']['Networks']; print(list(nets.values())[0]['IPAddress'])")

# Test ping (same VPC)
docker exec instance-vm1 ping -c 3 $INSTANCE_2

# Test cross-network (should FAIL unless peered)
docker exec instance-vm1 ping -c 3 $CROSS_VPC_IP
```

### API Connectivity Test
```python
import httpx

BASE = "http://localhost:8080"
PROJECT = "demo-project"

def check_all_services():
    services = [
        f"/compute/v1/projects/{PROJECT}/zones",
        f"/compute/v1/projects/{PROJECT}/global/networks",
        f"/storage/v1/b?project={PROJECT}",
        f"/v1/projects/{PROJECT}/serviceAccounts",
        f"/container/v1/projects/{PROJECT}/zones/us-central1-a/clusters",
    ]
    for path in services:
        r = httpx.get(f"{BASE}{path}")
        status = "✅" if r.status_code == 200 else "❌"
        print(f"{status} {r.status_code} {path}")
```

---

## Known Constraints & Limitations

### Compute
- SSH into instances uses `docker exec` — not real SSH
- No live network packet inspection (overlay is Docker bridge)
- Instance metadata server (169.254.169.254) not fully emulated
- No GPU/TPU machine types

### Networking
- Docker bridge has limited routing — cross-VPC needs peering record but actual packet routing may not work
- No real firewall enforcement — rules are stored but not enforced at packet level
- CIDR overlap not validated strictly

### Storage
- Objects stored at `/tmp/gcs-storage/` — ephemeral in container envs
- No versioning support
- No bucket-level IAM enforcement
- ~12.5% gcloud storage commands unsupported

### GKE
- Simulated clusters — no actual Kubernetes API server running per cluster
- No pod scheduling or service mesh

### Autoscaling
- Policy evaluation is simulated — actual instance creation triggered by evaluator loop
- Metric-based triggers approximate, not real-time

### General
- No authentication/authorization (CORS open, no auth tokens)
- No quota enforcement
- All operations complete synchronously (status: DONE immediately)
- No audit logging

---

## Test Writing Conventions (Matching CloudTester Pattern)

```python
"""
CloudTester - MyService Tests
"""
import pytest
from typing import Dict, Any

pytestmark = pytest.mark.integration


class TestMyServiceList:
    """Test list operations"""

    def test_list_empty(self, api_client, test_project):
        """Returns empty list when no resources exist"""
        resp = api_client.get(
            f"/compute/v1/projects/{test_project}/zones/us-central1-a/myresources"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data or isinstance(data, list)


class TestMyServiceCRUD:
    """Test create, get, delete lifecycle"""

    def test_create_resource(self, api_client, test_project):
        resp = api_client.post(
            f"/compute/v1/projects/{test_project}/zones/us-central1-a/myresources",
            json={"name": "test-resource-1"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "DONE"  # _op() pattern

    def test_get_resource(self, api_client, test_project):
        resp = api_client.get(
            f"/compute/v1/projects/{test_project}/zones/us-central1-a/myresources/test-resource-1"
        )
        assert resp.status_code == 200

    def test_delete_resource(self, api_client, test_project):
        resp = api_client.delete(
            f"/compute/v1/projects/{test_project}/zones/us-central1-a/myresources/test-resource-1"
        )
        assert resp.status_code == 200
        # Verify gone
        resp2 = api_client.get(
            f"/compute/v1/projects/{test_project}/zones/us-central1-a/myresources/test-resource-1"
        )
        assert resp2.status_code == 404
```

---

## Key Rules

- **Test positive AND negative cases** (404 after delete, 409 on duplicate)
- **Verify state changes** — don't just check status codes, check the data
- **Document all found cons** in test comments
- **Pre-flight checks first** — if Docker is down, many tests will fail silently
- **Use `pytestmark = pytest.mark.integration`** on all test files
- **Fixtures** (`api_client`, `test_project`, `test_zone`) are in `tests/conftest.py`
- **Cleanup after tests** — delete created resources in teardown
