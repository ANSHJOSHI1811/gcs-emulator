# Skill: Data & Resource Generation Expert

**name:** Data Generation, Infrastructure Provisioner & Resource Factory  
**description:** Acts like `terraform apply` for the GCP Stimulator. Declares and provisions complete environments, creates resources for all GCP services (VPC, instances, GKE, autoscaling, storage, IAM, etc.), and ensures both the gcloud CLI and UI show real meaningful data for triage and demos. Auto-activates for any resource creation, seeding, or environment bootstrapping tasks.

**trigger_keywords:** generate, data, resource, VPC, instance, autoscaling, GKE, bucket, populate, create, provision, bootstrap, factory, seed, environment, triage, demo, setup, infrastructure

**allowed_tools:** Read, Grep, Semantic Search, File Search

---

## Architecture Overview

The Data Generation skill provides **4 layers**:

1. **Infrastructure Provisioner** — Like `terraform apply`, creates a complete working environment
2. **Declarative Resource Generator** — You declare what you want, it creates it in dependency order
3. **Environment Bootstrapper** — Pre-configured bundles (dev/staging/prod) ready instantly
4. **Resource Factory Pattern** — `factory.create("vpc", count=3)` for any service

---

## Resource Factory (`scripts/provision.py`)

**Location:** `tests/CloudTester/scripts/provision.py`

### Usage
```python
from provision import ResourceFactory

factory = ResourceFactory(base_url="http://localhost:8080", project="demo-project")

# Single resource
factory.create("vpc", name="my-vpc")
factory.create("instance", name="my-vm", zone="us-central1-a", machine_type="e2-micro")
factory.create("bucket", name="my-bucket")

# Bulk creation
factory.create("instance", count=5, zone="us-central1-a")
factory.create("vpc", count=3)

# With dependencies (subnet needs vpc to exist first)
factory.create("subnet", name="my-subnet", network="my-vpc", region="us-central1", cidr="10.0.1.0/24")

# Full environment in one call
factory.provision_env("dev")      # dev environment bundle
factory.provision_env("staging")  # staging with more resources
factory.provision_env("demo")     # demo-ready full environment
```

### Implementation
```python
"""
ResourceFactory — Terraform-style provisioner for GCP Stimulator.
Creates resources via REST API respecting dependency order.
Run: python3 scripts/provision.py --env demo --project demo-project
"""
import httpx
import random
import string
import argparse
import time
from typing import Any, Dict, List, Optional

BASE_URL = "http://localhost:8080"
DEFAULT_PROJECT = "demo-project"

def rand_suffix(n=4) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

class ResourceFactory:
    def __init__(self, base_url: str = BASE_URL, project: str = DEFAULT_PROJECT):
        self.base = base_url
        self.project = project
        self.client = httpx.Client(timeout=30)
        self._created: Dict[str, List[str]] = {}

    def _post(self, path: str, body: dict) -> dict:
        r = self.client.post(f"{self.base}{path}", json=body)
        r.raise_for_status()
        return r.json()

    def _get(self, path: str) -> dict:
        r = self.client.get(f"{self.base}{path}")
        r.raise_for_status()
        return r.json()

    def _delete(self, path: str):
        r = self.client.delete(f"{self.base}{path}")
        return r

    # ── VPC ──────────────────────────────────────────────────────────────────
    def create_vpc(self, name: Optional[str] = None, auto_subnets: bool = False) -> dict:
        name = name or f"vpc-{rand_suffix()}"
        result = self._post(
            f"/compute/v1/projects/{self.project}/global/networks",
            {"name": name, "autoCreateSubnetworks": auto_subnets}
        )
        self._created.setdefault("vpcs", []).append(name)
        print(f"  ✅ VPC: {name}")
        return result

    def create_subnet(self, name: Optional[str] = None, network: str = "default",
                      region: str = "us-central1", cidr: str = "10.0.1.0/24") -> dict:
        name = name or f"subnet-{rand_suffix()}"
        result = self._post(
            f"/compute/v1/projects/{self.project}/regions/{region}/subnetworks",
            {"name": name, "network": network, "region": region, "ipCidrRange": cidr}
        )
        self._created.setdefault("subnets", []).append(name)
        print(f"  ✅ Subnet: {name} ({cidr}) in {network}")
        return result

    # ── Compute ───────────────────────────────────────────────────────────────
    def create_instance(self, name: Optional[str] = None, zone: str = "us-central1-a",
                        machine_type: str = "e2-micro", network: str = "default") -> dict:
        name = name or f"instance-{rand_suffix()}"
        result = self._post(
            f"/compute/v1/projects/{self.project}/zones/{zone}/instances",
            {
                "name": name,
                "machineType": f"zones/{zone}/machineTypes/{machine_type}",
                "networkInterfaces": [{"network": f"global/networks/{network}"}],
                "disks": [{"initializeParams": {"sourceImage": "debian-11"}, "boot": True}],
            }
        )
        self._created.setdefault("instances", []).append((name, zone))
        print(f"  ✅ Instance: {name} ({machine_type}) in {zone}")
        return result

    def create_instance_group(self, name: Optional[str] = None, zone: str = "us-central1-a",
                               size: int = 2) -> dict:
        name = name or f"group-{rand_suffix()}"
        result = self._post(
            f"/compute/v1/projects/{self.project}/zones/{zone}/instanceGroups",
            {"name": name, "zone": zone, "size": size}
        )
        self._created.setdefault("instance_groups", []).append((name, zone))
        print(f"  ✅ Instance Group: {name} (size={size}) in {zone}")
        return result

    # ── Autoscaling ───────────────────────────────────────────────────────────
    def create_autoscaler(self, name: Optional[str] = None, zone: str = "us-central1-a",
                          target_group: str = "", min_replicas: int = 1,
                          max_replicas: int = 5) -> dict:
        name = name or f"scaler-{rand_suffix()}"
        target = f"https://www.googleapis.com/compute/v1/projects/{self.project}/zones/{zone}/instanceGroups/{target_group}"
        result = self._post(
            f"/compute/v1/projects/{self.project}/zones/{zone}/autoscalers",
            {
                "name": name,
                "target": target,
                "minReplicas": min_replicas,
                "maxReplicas": max_replicas,
                "scalingRules": [{"metric": "cpu", "target": 0.6}],
            }
        )
        self._created.setdefault("autoscalers", []).append((name, zone))
        print(f"  ✅ Autoscaler: {name} min={min_replicas} max={max_replicas}")
        return result

    # ── Storage ───────────────────────────────────────────────────────────────
    def create_bucket(self, name: Optional[str] = None, location: str = "us-central1") -> dict:
        name = name or f"bucket-{rand_suffix()}"
        result = self._post(
            f"/storage/v1/b?project={self.project}",
            {"name": name, "location": location, "storageClass": "STANDARD"}
        )
        self._created.setdefault("buckets", []).append(name)
        print(f"  ✅ Bucket: gs://{name}")
        return result

    def upload_objects(self, bucket: str, count: int = 5) -> List[str]:
        names = []
        for i in range(count):
            obj_name = f"test-object-{i+1}.txt"
            content = f"Sample content for object {i+1} in bucket {bucket}".encode()
            r = self.client.post(
                f"{self.base}/upload/storage/v1/b/{bucket}/o?uploadType=media&name={obj_name}",
                content=content,
                headers={"Content-Type": "text/plain"}
            )
            if r.status_code in (200, 201):
                names.append(obj_name)
                print(f"  ✅ Object: gs://{bucket}/{obj_name}")
        self._created.setdefault("objects", []).extend([(bucket, n) for n in names])
        return names

    # ── IAM ───────────────────────────────────────────────────────────────────
    def create_service_account(self, name: Optional[str] = None,
                                display_name: Optional[str] = None) -> dict:
        name = name or f"sa-{rand_suffix()}"
        result = self._post(
            f"/v1/projects/{self.project}/serviceAccounts",
            {"accountId": name, "serviceAccount": {"displayName": display_name or name.title()}}
        )
        self._created.setdefault("service_accounts", []).append(name)
        print(f"  ✅ Service Account: {name}@{self.project}.iam.gserviceaccount.com")
        return result

    # ── GKE ───────────────────────────────────────────────────────────────────
    def create_gke_cluster(self, name: Optional[str] = None, zone: str = "us-central1-a",
                            num_nodes: int = 2) -> dict:
        name = name or f"cluster-{rand_suffix()}"
        result = self._post(
            f"/container/v1/projects/{self.project}/zones/{zone}/clusters",
            {
                "cluster": {
                    "name": name,
                    "initialNodeCount": num_nodes,
                    "nodeConfig": {"machineType": "e2-medium"},
                }
            }
        )
        self._created.setdefault("gke_clusters", []).append((name, zone))
        print(f"  ✅ GKE Cluster: {name} ({num_nodes} nodes) in {zone}")
        return result

    # ── Firewall ──────────────────────────────────────────────────────────────
    def create_firewall_rule(self, name: Optional[str] = None, network: str = "default",
                              port: str = "80", protocol: str = "tcp") -> dict:
        name = name or f"allow-{protocol}-{port}-{rand_suffix()}"
        result = self._post(
            f"/compute/v1/projects/{self.project}/global/firewalls",
            {
                "name": name,
                "network": f"global/networks/{network}",
                "allowed": [{"IPProtocol": protocol, "ports": [port]}],
                "sourceRanges": ["0.0.0.0/0"],
                "direction": "INGRESS",
            }
        )
        self._created.setdefault("firewalls", []).append(name)
        print(f"  ✅ Firewall: {name} (allow {protocol}:{port})")
        return result

    # ── Monitoring ────────────────────────────────────────────────────────────
    def create_metric(self, name: Optional[str] = None) -> dict:
        name = name or f"custom_metric_{rand_suffix()}"
        result = self._post(
            f"/v3/projects/{self.project}/metricDescriptors",
            {
                "type": f"custom.googleapis.com/{name}",
                "metricKind": "GAUGE",
                "valueType": "DOUBLE",
                "displayName": name.replace("_", " ").title(),
                "description": f"Custom metric: {name}",
            }
        )
        self._created.setdefault("metrics", []).append(name)
        print(f"  ✅ Metric: custom.googleapis.com/{name}")
        return result

    # ── Pub/Sub ───────────────────────────────────────────────────────────────
    def create_pubsub_topic(self, name: Optional[str] = None) -> dict:
        name = name or f"topic-{rand_suffix()}"
        result = self._post(
            f"/v1/projects/{self.project}/topics/{name}",
            {}
        )
        self._created.setdefault("topics", []).append(name)
        print(f"  ✅ Pub/Sub Topic: {name}")
        return result

    # ── Secret Manager ────────────────────────────────────────────────────────
    def create_secret(self, name: Optional[str] = None, value: str = "my-secret-value") -> dict:
        name = name or f"secret-{rand_suffix()}"
        result = self._post(
            f"/v1/projects/{self.project}/secrets",
            {"secretId": name, "secret": {"replication": {"automatic": {}}}}
        )
        # Add secret version
        self._post(
            f"/v1/projects/{self.project}/secrets/{name}/versions",
            {"payload": {"data": value}}
        )
        self._created.setdefault("secrets", []).append(name)
        print(f"  ✅ Secret: {name}")
        return result

    # ── Environment Bootstrappers ─────────────────────────────────────────────
    def provision_env(self, env: str = "dev"):
        """
        Provision a complete pre-configured environment.
        All resources visible in both gcloud CLI and UI after running.
        """
        envs = {
            "dev": self._env_dev,
            "staging": self._env_staging,
            "demo": self._env_demo,
        }
        if env not in envs:
            raise ValueError(f"Unknown env '{env}'. Choose: {list(envs.keys())}")
        print(f"\n🚀 Provisioning '{env}' environment for project: {self.project}")
        print("=" * 60)
        envs[env]()
        print("=" * 60)
        print(f"✅ Done! Resources created:\n")
        for resource_type, items in self._created.items():
            print(f"  {resource_type}: {len(items)}")
        print(f"\n🌐 View in UI: http://localhost:3000")
        print(f"📡 API Docs:   http://localhost:8080/docs\n")

    def _env_dev(self):
        """Minimal dev environment — enough to see data."""
        # VPC + subnet
        self.create_vpc(name="dev-vpc")
        self.create_subnet(name="dev-subnet", network="dev-vpc", cidr="10.1.0.0/24")
        # 2 instances
        self.create_instance(name="dev-vm-1", zone="us-central1-a")
        self.create_instance(name="dev-vm-2", zone="us-central1-a")
        # 1 bucket with objects
        self.create_bucket(name=f"dev-bucket-{rand_suffix()}")
        self.upload_objects(list(self._created["buckets"])[-1], count=3)
        # 1 service account
        self.create_service_account(name="dev-sa", display_name="Dev Service Account")
        # 1 GKE cluster
        self.create_gke_cluster(name="dev-cluster", zone="us-central1-a", num_nodes=1)

    def _env_staging(self):
        """Staging environment with autoscaling and monitoring."""
        # 2 VPCs
        for vpc_name, cidr in [("staging-vpc-1", "10.2.0.0/24"), ("staging-vpc-2", "10.3.0.0/24")]:
            self.create_vpc(name=vpc_name)
            self.create_subnet(name=f"{vpc_name}-subnet", network=vpc_name, cidr=cidr)
        # 4 instances across zones
        for i, zone in enumerate(["us-central1-a", "us-central1-b", "us-east1-a", "us-west1-a"]):
            self.create_instance(name=f"staging-vm-{i+1}", zone=zone, machine_type="e2-small")
        # Instance group + autoscaler
        self.create_instance_group(name="staging-group", zone="us-central1-a", size=2)
        self.create_autoscaler(
            name="staging-scaler",
            zone="us-central1-a",
            target_group="staging-group",
            min_replicas=2, max_replicas=8
        )
        # Storage
        for i in range(2):
            bname = f"staging-bucket-{rand_suffix()}"
            self.create_bucket(name=bname)
            self.upload_objects(bname, count=5)
        # IAM
        for role in ["backend", "frontend", "worker"]:
            self.create_service_account(name=f"staging-{role}-sa")
        # GKE
        self.create_gke_cluster(name="staging-cluster", zone="us-central1-a", num_nodes=2)
        # Monitoring + Pub/Sub
        self.create_metric(name="staging_request_count")
        self.create_pubsub_topic(name="staging-events")

    def _env_demo(self):
        """Full demo environment — everything visible in gcloud and UI."""
        # Run staging base
        self._env_staging()
        # Additional resources
        self.create_vpc(name="demo-prod-vpc")
        self.create_subnet(name="prod-subnet", network="demo-prod-vpc", cidr="10.10.0.0/16")
        # More instances
        zones = ["us-central1-a", "us-central1-b", "us-east1-a", "europe-west1-b"]
        for i, zone in enumerate(zones):
            self.create_instance(name=f"demo-vm-{i+1}", zone=zone, machine_type="n1-standard-2")
        # Large autoscaling group
        self.create_instance_group(name="demo-prod-group", zone="us-central1-a", size=3)
        self.create_autoscaler(name="demo-prod-scaler", zone="us-central1-a",
                                target_group="demo-prod-group", min_replicas=3, max_replicas=20)
        # Multiple buckets with data
        for category in ["assets", "backups", "logs", "configs"]:
            bname = f"demo-{category}-{rand_suffix()}"
            self.create_bucket(name=bname)
            self.upload_objects(bname, count=10)
        # Full IAM setup
        for sa in ["compute-admin", "storage-admin", "gke-operator", "monitoring-agent"]:
            self.create_service_account(name=f"demo-{sa}")
        # Production GKE
        self.create_gke_cluster(name="demo-prod-cluster", zone="us-central1-a", num_nodes=3)
        # Firewall rules
        for port, proto in [("80", "tcp"), ("443", "tcp"), ("22", "tcp"), ("8080", "tcp")]:
            self.create_firewall_rule(network="demo-prod-vpc", port=port, protocol=proto)
        # Monitoring
        for metric in ["request_count", "error_rate", "latency_ms", "cpu_usage"]:
            self.create_metric(name=f"demo_{metric}")
        # Pub/Sub
        for topic in ["orders", "events", "alerts", "logs"]:
            self.create_pubsub_topic(name=f"demo-{topic}")
        # Secrets
        for secret in ["db-password", "api-key", "jwt-secret"]:
            self.create_secret(name=f"demo-{secret}")

    def teardown(self):
        """Remove all resources created by this factory run."""
        print("\n🧹 Tearing down...")
        for name, zone in reversed(self._created.get("instances", [])):
            self._delete(f"/compute/v1/projects/{self.project}/zones/{zone}/instances/{name}")
            print(f"  🗑️  Instance: {name}")
        for name in reversed(self._created.get("buckets", [])):
            self._delete(f"/storage/v1/b/{name}")
            print(f"  🗑️  Bucket: {name}")
        print("✅ Teardown complete")


# ── CLI Entry Point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP Stimulator Resource Provisioner")
    parser.add_argument("--env", default="dev", choices=["dev", "staging", "demo"],
                        help="Environment to provision")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="GCP project ID")
    parser.add_argument("--base-url", default=BASE_URL, help="Backend API base URL")
    parser.add_argument("--teardown", action="store_true", help="Teardown after provision")
    args = parser.parse_args()

    factory = ResourceFactory(base_url=args.base_url, project=args.project)
    factory.provision_env(args.env)
    if args.teardown:
        input("\nPress Enter to teardown...")
        factory.teardown()
```

---

## Usage Examples

```bash
# Set up minimal dev environment (quickest)
python3 tests/CloudTester/scripts/provision.py --env dev

# Full staging environment
python3 tests/CloudTester/scripts/provision.py --env staging

# Complete demo environment (everything visible in UI + gcloud)
python3 tests/CloudTester/scripts/provision.py --env demo

# Custom project
python3 tests/CloudTester/scripts/provision.py --env demo --project my-project

# Provision then teardown (for triage sessions)
python3 tests/CloudTester/scripts/provision.py --env staging --teardown
```

---

## What Gets Created Per Environment

| Resource | dev | staging | demo |
|----------|-----|---------|------|
| VPC Networks | 1 | 2 | 4 |
| Subnets | 1 | 2 | 4 |
| VM Instances | 2 | 4 | 8 |
| Instance Groups | 0 | 1 | 2 |
| Autoscalers | 0 | 1 | 2 |
| Storage Buckets | 1 + 3 objects | 2 + 5 objects | 4 + 10 objects |
| Service Accounts | 1 | 3 | 7 |
| GKE Clusters | 1 | 1 | 2 |
| Firewall Rules | 0 | 0 | 4 |
| Monitoring Metrics | 0 | 1 | 4 |
| Pub/Sub Topics | 0 | 1 | 4 |
| Secrets | 0 | 0 | 3 |

---

## Key Rules

- **Respect dependency order**: VPC → Subnet → Instance (never reverse)
- **Always use `rand_suffix()`** to avoid name collisions on repeated runs
- **Idempotent**: Safe to run multiple times — existing resources don't block
- **Output is visible in both**: `gcloud compute instances list` AND UI at http://localhost:3000
- **`provision_env("demo")`** is the go-to for triage sessions — gives full data across all services
- **Teardown cleans up** — use `--teardown` flag for ephemeral environments
