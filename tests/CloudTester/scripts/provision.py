#!/usr/bin/env python3
"""
ResourceFactory — Terraform-style provisioner for GCP Stimulator.
Creates resources via REST API respecting dependency order.

Usage:
    python3 provision.py --env demo --project demo-project
    python3 provision.py --env dev --project my-project
    python3 provision.py --env staging --project staging-proj
"""

import httpx
import random
import string
import argparse
import time
import sys
from typing import Any, Dict, List, Optional

BASE_URL = "http://localhost:8080"
DEFAULT_PROJECT = "resource-generation-demo"

def rand_suffix(n=4) -> str:
    """Generate random suffix for resource names."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

class ResourceFactory:
    """
    Resource provisioner for GCP Stimulator.
    Supports bulk creation, dependency ordering, and environment bundles.
    """

    def __init__(self, base_url: str = BASE_URL, project: str = DEFAULT_PROJECT):
        self.base = base_url
        self.project = project
        self.client = httpx.Client(timeout=30)
        self._created: Dict[str, List[Any]] = {}

    def _post(self, path: str, body: dict) -> dict:
        """POST request to API."""
        try:
            r = self.client.post(f"{self.base}{path}", json=body)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"    ⚠️  Error: {str(e)}")
            return {}

    def _get(self, path: str) -> dict:
        """GET request to API."""
        try:
            r = self.client.get(f"{self.base}{path}")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"    ⚠️  Error: {str(e)}")
            return {}

    def _delete(self, path: str):
        """DELETE request to API."""
        try:
            r = self.client.delete(f"{self.base}{path}")
            return r
        except Exception as e:
            print(f"    ⚠️  Error: {str(e)}")

    # ────────────────────────────────────────────────────────────────────────
    # VPC & Networks
    # ────────────────────────────────────────────────────────────────────────

    def create_vpc(self, name: Optional[str] = None, auto_subnets: bool = False) -> dict:
        """Create a VPC network."""
        name = name or f"vpc-{rand_suffix()}"
        result = self._post(
            f"/compute/v1/projects/{self.project}/global/networks",
            {"name": name, "autoCreateSubnetworks": auto_subnets}
        )
        if result:
            self._created.setdefault("vpcs", []).append(name)
            print(f"  ✅ VPC: {name}")
        return result

    def create_subnet(self, name: Optional[str] = None, network: str = "default",
                      region: str = "us-central1", cidr: Optional[str] = None) -> dict:
        """Create a subnet."""
        name = name or f"subnet-{rand_suffix()}"
        # Auto-generate CIDR if not provided, ensuring it's within VPC range
        if not cidr:
            # Use a subnet within the VPC's 10.200.0.0/16 range
            subnet_num = len(self._created.get("subnets", [])) + 1
            start_octet = 200 + (subnet_num // 16)
            end_octet = (subnet_num % 16) * 16
            cidr = f"10.{start_octet}.{end_octet}.0/20"
        
        result = self._post(
            f"/compute/v1/projects/{self.project}/regions/{region}/subnetworks",
            {"name": name, "network": network, "region": region, "ipCidrRange": cidr}
        )
        if result:
            self._created.setdefault("subnets", []).append(name)
            print(f"  ✅ Subnet: {name} ({cidr}) in {network}")
        return result

    # ────────────────────────────────────────────────────────────────────────
    # Compute Engine
    # ────────────────────────────────────────────────────────────────────────

    def create_instance(self, name: Optional[str] = None, zone: str = "us-central1-a",
                        machine_type: str = "e2-micro", network: str = "default") -> dict:
        """Create a VM instance."""
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
        if result:
            self._created.setdefault("instances", []).append((name, zone))
            print(f"  ✅ Instance: {name} ({machine_type}) in {zone}")
        return result

    def create_instance_group(self, name: Optional[str] = None, zone: str = "us-central1-a",
                               size: int = 2) -> dict:
        """Create an instance group."""
        name = name or f"group-{rand_suffix()}"
        result = self._post(
            f"/compute/v1/projects/{self.project}/zones/{zone}/instanceGroups",
            {"name": name, "zone": zone, "size": size}
        )
        if result:
            self._created.setdefault("instance_groups", []).append((name, zone))
            print(f"  ✅ Instance Group: {name} (size={size}) in {zone}")
        return result

    # ────────────────────────────────────────────────────────────────────────
    # Autoscaling
    # ────────────────────────────────────────────────────────────────────────

    def create_autoscaler(self, name: Optional[str] = None, zone: str = "us-central1-a",
                          target_group: str = "", min_replicas: int = 1,
                          max_replicas: int = 5) -> dict:
        """Create an autoscaler."""
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
        if result:
            self._created.setdefault("autoscalers", []).append((name, zone))
            print(f"  ✅ Autoscaler: {name} min={min_replicas} max={max_replicas}")
        return result

    # ────────────────────────────────────────────────────────────────────────
    # Cloud Storage
    # ────────────────────────────────────────────────────────────────────────

    def create_bucket(self, name: Optional[str] = None, location: str = "us-central1") -> dict:
        """Create a storage bucket."""
        name = name or f"bucket-{rand_suffix()}"
        result = self._post(
            f"/storage/v1/b?project={self.project}",
            {"name": name, "location": location, "storageClass": "STANDARD"}
        )
        if result:
            self._created.setdefault("buckets", []).append(name)
            print(f"  ✅ Bucket: gs://{name}")
        return result

    def upload_objects(self, bucket: str, count: int = 5) -> List[str]:
        """Upload sample objects to a bucket."""
        names = []
        for i in range(count):
            obj_name = f"test-object-{i+1}.txt"
            content = f"Sample content for object {i+1} in bucket {bucket}".encode()
            try:
                r = self.client.post(
                    f"{self.base}/upload/storage/v1/b/{bucket}/o?uploadType=media&name={obj_name}",
                    content=content,
                    headers={"Content-Type": "text/plain"}
                )
                if r.status_code in (200, 201):
                    names.append(obj_name)
                    print(f"  ✅ Object: gs://{bucket}/{obj_name}")
            except Exception as e:
                print(f"    ⚠️  Upload error: {str(e)}")
        self._created.setdefault("objects", []).extend([(bucket, n) for n in names])
        return names

    # ────────────────────────────────────────────────────────────────────────
    # IAM
    # ────────────────────────────────────────────────────────────────────────

    def create_service_account(self, name: Optional[str] = None,
                                display_name: Optional[str] = None) -> dict:
        """Create a service account."""
        name = name or f"sa-{rand_suffix()}"
        result = self._post(
            f"/iam/v1/projects/{self.project}/serviceAccounts",
            {"accountId": name, "displayName": display_name or name.title()}
        )
        if result:
            self._created.setdefault("service_accounts", []).append(name)
            print(f"  ✅ Service Account: {name}@{self.project}.iam.gserviceaccount.com")
        return result

    # ────────────────────────────────────────────────────────────────────────
    # GKE
    # ────────────────────────────────────────────────────────────────────────

    def create_gke_cluster(self, name: Optional[str] = None, zone: str = "us-central1-a",
                            num_nodes: int = 2) -> dict:
        """Create a GKE cluster."""
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
        if result:
            self._created.setdefault("gke_clusters", []).append((name, zone))
            print(f"  ✅ GKE Cluster: {name} ({num_nodes} nodes) in {zone}")
        return result

    # ────────────────────────────────────────────────────────────────────────
    # Firewall
    # ────────────────────────────────────────────────────────────────────────

    def create_firewall_rule(self, name: Optional[str] = None, network: str = "default",
                              port: str = "80", protocol: str = "tcp") -> dict:
        """Create a firewall rule."""
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
        if result:
            self._created.setdefault("firewalls", []).append(name)
            print(f"  ✅ Firewall: {name} (allow {protocol}:{port})")
        return result

    # ────────────────────────────────────────────────────────────────────────
    # Cloud Monitoring
    # ────────────────────────────────────────────────────────────────────────

    def create_metric(self, name: Optional[str] = None) -> dict:
        """Create a custom metric."""
        name = name or f"custom_metric_{rand_suffix()}"
        result = self._post(
            f"/monitoring/v3/projects/{self.project}/metricDescriptors",
            {
                "type": f"custom.googleapis.com/{name}",
                "metricKind": "GAUGE",
                "valueType": "DOUBLE",
                "displayName": name.replace("_", " ").title(),
                "description": f"Custom metric: {name}",
            }
        )
        if result:
            self._created.setdefault("metrics", []).append(name)
            print(f"  ✅ Metric: custom.googleapis.com/{name}")
        return result

    # ────────────────────────────────────────────────────────────────────────
    # Pub/Sub
    # ────────────────────────────────────────────────────────────────────────

    def create_pubsub_topic(self, name: Optional[str] = None) -> dict:
        """Create a Pub/Sub topic."""
        name = name or f"topic-{rand_suffix()}"
        result = self._post(
            f"/pubsub/v1/projects/{self.project}/topics",
            {"name": f"projects/{self.project}/topics/{name}"}
        )
        if result:
            self._created.setdefault("topics", []).append(name)
            print(f"  ✅ Pub/Sub Topic: {name}")
        return result

    def create_pubsub_subscription(self, name: Optional[str] = None, topic: Optional[str] = None) -> dict:
        """Create a Pub/Sub subscription."""
        name = name or f"sub-{rand_suffix()}"
        topic = topic or (self._created.get("topics", ["topic-default"])[0])
        result = self._post(
            f"/pubsub/v1/projects/{self.project}/subscriptions",
            {
                "name": f"projects/{self.project}/subscriptions/{name}",
                "topic": f"projects/{self.project}/topics/{topic}",
            }
        )
        if result:
            self._created.setdefault("subscriptions", []).append(name)
            print(f"  ✅ Pub/Sub Subscription: {name}")
        return result

    # ────────────────────────────────────────────────────────────────────────
    # Secret Manager
    # ────────────────────────────────────────────────────────────────────────

    def create_secret(self, name: Optional[str] = None, value: str = "my-secret-value") -> dict:
        """Create a secret."""
        name = name or f"secret-{rand_suffix()}"
        result = self._post(
            f"/secretmanager/v1/projects/{self.project}/secrets",
            {"secretId": name, "replication": {"automatic": {}}}
        )
        if result:
            # Add secret version
            self._post(
                f"/secretmanager/v1/projects/{self.project}/secrets/{name}/versions",
                {"payload": {"data": value}}
            )
            self._created.setdefault("secrets", []).append(name)
            print(f"  ✅ Secret: {name}")
        return result

    # ────────────────────────────────────────────────────────────────────────
    # Environment Bootstrappers
    # ────────────────────────────────────────────────────────────────────────

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
        print("=" * 70)
        envs[env]()
        print("=" * 70)
        self._print_summary()

    def _env_dev(self):
        """Minimal dev environment — enough to see data."""
        print("📦 Setting up minimal dev environment...\n")
        
        # VPC + subnet
        self.create_vpc(name="dev-vpc")
        self.create_subnet(name="dev-subnet", network="dev-vpc", region="us-central1", cidr="10.200.0.0/20")
        
        # 2 instances
        self.create_instance(name="dev-vm-1", zone="us-central1-a", machine_type="e2-micro", network="dev-vpc")
        self.create_instance(name="dev-vm-2", zone="us-east1-a", machine_type="e2-micro", network="dev-vpc")
        
        # 1 bucket with objects
        bucket = f"dev-bucket-{rand_suffix()}"
        self.create_bucket(name=bucket)
        self.upload_objects(bucket, count=3)
        
        # 1 service account
        self.create_service_account(name="dev-sa", display_name="Dev Service Account")
        
        # 1 GKE cluster
        self.create_gke_cluster(name="dev-cluster", zone="us-central1-a", num_nodes=1)
        
        # Firewall
        self.create_firewall_rule(name="dev-allow-http", network="dev-vpc", port="80", protocol="tcp")

    def _env_staging(self):
        """Staging environment with autoscaling and monitoring."""
        print("📦 Setting up staging environment...\n")
        
        # Ensure default network and subnet exist
        self.create_vpc(name="default")
        self.create_subnet(name="default", network="default", region="us-central1", cidr="10.200.0.0/20")
        
        # 2 custom VPCs (will use default network for instances)
        vpcs = []
        for i, (vpc_name, cidr) in enumerate([("staging-vpc-1", "10.2.0.0/16"), ("staging-vpc-2", "10.3.0.0/16")]):
            self.create_vpc(name=vpc_name)
            self.create_subnet(name=f"{vpc_name}-subnet", network=vpc_name, cidr="10.2.0.0/20" if i == 0 else "10.3.0.0/20")
            vpcs.append(vpc_name)
        
        # 4 instances across zones (using default network)
        zones = ["us-central1-a", "us-central1-b", "us-east1-a", "us-west1-a"]
        for i, zone in enumerate(zones):
            self.create_instance(name=f"staging-vm-{i+1}", zone=zone, machine_type="e2-small", network="default")
        
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
            self.create_service_account(name=f"staging-{role}-sa", display_name=f"Staging {role.title()}")
        
        # GKE
        self.create_gke_cluster(name="staging-cluster", zone="us-central1-a", num_nodes=2)
        
        # Monitoring
        self.create_metric(name="staging_request_count")
        self.create_metric(name="staging_error_rate")
        
        # Pub/Sub
        self.create_pubsub_topic(name="staging-events")
        self.create_pubsub_subscription(name="staging-events-sub", topic="staging-events")
        
        # Firewall rules
        for vpc in vpcs:
            self.create_firewall_rule(name=f"allow-http-{vpc}", network=vpc, port="80", protocol="tcp")

    def _env_demo(self):
        """Full demo environment — everything visible in gcloud and UI."""
        print("📦 Setting up comprehensive demo environment...\n")
        
        # Run staging base first
        self._env_staging()
        
        # Additional production VPC
        self.create_vpc(name="demo-prod-vpc")
        self.create_subnet(name="prod-subnet", network="demo-prod-vpc", region="us-central1", cidr="10.10.0.0/20")
        
        # More instances in production zones
        zones = ["us-central1-a", "us-central1-b", "us-east1-a", "europe-west1-b"]
        for i, zone in enumerate(zones):
            self.create_instance(name=f"demo-vm-{i+1}", zone=zone, machine_type="n1-standard-2", network="demo-prod-vpc")
        
        # Large autoscaling group
        self.create_instance_group(name="demo-prod-group", zone="us-central1-a", size=3)
        self.create_autoscaler(
            name="demo-prod-scaler",
            zone="us-central1-a",
            target_group="demo-prod-group",
            min_replicas=3, max_replicas=20
        )
        
        # Multiple buckets with data
        for category in ["assets", "backups", "logs", "configs"]:
            bname = f"demo-{category}-{rand_suffix()}"
            self.create_bucket(name=bname)
            self.upload_objects(bname, count=10)
        
        # Full IAM setup
        for sa in ["compute-admin", "storage-admin", "gke-operator", "monitoring-agent"]:
            self.create_service_account(name=f"demo-{sa}", display_name=f"Demo {sa.replace('-', ' ').title()}")
        
        # Production GKE
        self.create_gke_cluster(name="demo-prod-cluster", zone="us-central1-a", num_nodes=3)
        
        # Firewall rules
        for port, proto in [("80", "tcp"), ("443", "tcp"), ("22", "tcp"), ("8080", "tcp")]:
            self.create_firewall_rule(name=f"demo-allow-{proto}-{port}", network="demo-prod-vpc", port=port, protocol=proto)
        
        # Comprehensive monitoring
        for metric in ["request_count", "error_rate", "latency_ms", "cpu_usage", "memory_usage", "disk_io"]:
            self.create_metric(name=f"demo_{metric}")
        
        # Pub/Sub topics and subscriptions
        for topic in ["orders", "events", "alerts", "logs"]:
            self.create_pubsub_topic(name=f"demo-{topic}")
            self.create_pubsub_subscription(name=f"demo-{topic}-sub", topic=f"demo-{topic}")
        
        # Secrets
        for secret in ["db-password", "api-key", "jwt-secret", "oauth-client-id"]:
            self.create_secret(name=f"demo-{secret}", value=f"demo-value-{rand_suffix()}")

    def _print_summary(self):
        """Print summary of created resources."""
        print(f"\n✅ Environment provisioning complete!")
        print(f"\n📊 Resources Created:")
        print("=" * 70)
        for resource_type, items in sorted(self._created.items()):
            if items:
                print(f"  {resource_type.replace('_', ' ').title():.<40} {len(items):>3}")
        print("=" * 70)
        print(f"\n🌐 View in UI:     http://localhost:3000")
        print(f"📡 API Docs:       http://localhost:8080/docs")
        print(f"📚 Project:        {self.project}\n")

    def teardown(self):
        """Remove all resources created by this factory run."""
        print("\n🧹 Tearing down resources...")
        # Instances
        for name, zone in reversed(self._created.get("instances", [])):
            self._delete(f"/compute/v1/projects/{self.project}/zones/{zone}/instances/{name}")
            print(f"  🗑️  Instance: {name}")
        # Buckets
        for name in reversed(self._created.get("buckets", [])):
            self._delete(f"/storage/v1/b/{name}")
            print(f"  🗑️  Bucket: {name}")
        print("✅ Teardown complete\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Provision GCP Stimulator resources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 provision.py --env dev
  python3 provision.py --env staging --project my-project
  python3 provision.py --env demo --project demo-proj
        """
    )
    parser.add_argument("--env", choices=["dev", "staging", "demo"], default="dev",
                        help="Environment template to provision (default: dev)")
    parser.add_argument("--project", default=DEFAULT_PROJECT,
                        help=f"GCP project ID (default: {DEFAULT_PROJECT})")
    parser.add_argument("--url", default=BASE_URL,
                        help=f"Backend API URL (default: {BASE_URL})")
    parser.add_argument("--teardown", action="store_true",
                        help="Remove all resources after provisioning")

    args = parser.parse_args()

    try:
        factory = ResourceFactory(base_url=args.url, project=args.project)
        factory.provision_env(args.env)
        
        if args.teardown:
            time.sleep(2)
            factory.teardown()
    except Exception as e:
        print(f"\n❌ Error: {e}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
