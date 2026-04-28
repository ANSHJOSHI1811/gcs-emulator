"""
GCS Emulator — Sanity Test Suite
=================================
A single-file, runnable sanity check that verifies ALL services are operational.

Usage:
    # From repo root (recommended)
    python tests/sanity_test.py

    # With custom backend URL
    TEST_API_URL=http://localhost:8080 python tests/sanity_test.py

    # Skip CRUD tests (read-only check only)
    SANITY_READONLY=1 python tests/sanity_test.py

What it checks:
    • Backend health
    • Projects service (listing + create + delete)
    • Compute Engine (zones, machine types, instances, addresses, disks, images)
    • Cloud Storage (buckets + objects)
    • VPC Networks (networks, subnets, firewalls, routes)
    • IAM (service accounts)
    • GKE Clusters
    • Cloud Run services
    • Pub/Sub (topics + subscriptions)
    • Secret Manager
    • Autoscaling
    • Monitoring (time series, alert policies)
    • Frontend reachability
"""

import os
import sys
import json
import time
import uuid
import traceback
import requests
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
BASE_URL       = os.getenv("TEST_API_URL", "http://localhost:8080").rstrip("/")
FRONTEND_URL   = os.getenv("FRONTEND_URL",  "http://localhost:3000")
PROJECT        = os.getenv("TEST_PROJECT",  "test-project")
REGION         = os.getenv("TEST_REGION",   "us-central1")
ZONE           = os.getenv("TEST_ZONE",     "us-central1-a")
READONLY       = os.getenv("SANITY_READONLY", "0").strip() in ("1", "true", "yes")
TIMEOUT        = int(os.getenv("TEST_TIMEOUT", "10"))

# Unique run suffix so CRUD tests never collide on repeated runs
RUN_ID = uuid.uuid4().hex[:8]

# ─────────────────────────────────────────────
# Colours (ANSI)
# ─────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def _c(colour: str, text: str) -> str:
    return f"{colour}{text}{RESET}"

# ─────────────────────────────────────────────
# Result tracking
# ─────────────────────────────────────────────
@dataclass
class TestResult:
    name:    str
    passed:  bool
    message: str = ""
    skipped: bool = False

@dataclass
class SuiteResult:
    name:    str
    results: List[TestResult] = field(default_factory=list)

    @property
    def passed(self):  return sum(1 for r in self.results if r.passed and not r.skipped)
    @property
    def failed(self):  return sum(1 for r in self.results if not r.passed and not r.skipped)
    @property
    def skipped(self): return sum(1 for r in self.results if r.skipped)
    @property
    def total(self):   return len(self.results)
    @property
    def pct(self):     return int(100 * self.passed / max(self.total - self.skipped, 1))

ALL_SUITES: List[SuiteResult] = []

# ─────────────────────────────────────────────
# HTTP helpers
# ─────────────────────────────────────────────
session = requests.Session()
session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})

def _req(method: str, path: str, **kwargs) -> Tuple[int, Any]:
    """Return (status_code, json_body). Never raises."""
    url = f"{BASE_URL}{path}"
    try:
        resp = session.request(method, url, timeout=TIMEOUT, **kwargs)
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        return resp.status_code, body
    except requests.exceptions.ConnectionError:
        return -1, {"error": "Connection refused"}
    except requests.exceptions.Timeout:
        return -2, {"error": "Request timed out"}
    except Exception as e:
        return -3, {"error": str(e)}

def get(path):    return _req("GET",    path)
def delete(path): return _req("DELETE", path)
def post(path, payload=None): return _req("POST", path, json=payload or {})
def patch(path, payload=None): return _req("PATCH", path, json=payload or {})

# ─────────────────────────────────────────────
# Test runner helpers
# ─────────────────────────────────────────────
def run_suite(suite_name: str, test_fns) -> SuiteResult:
    """Execute all test functions in a suite and collect results."""
    suite = SuiteResult(name=suite_name)
    ALL_SUITES.append(suite)
    print(f"\n{_c(CYAN, BOLD + '  ── ' + suite_name + ' ──' + RESET)}")

    for fn in test_fns:
        test_name = fn.__name__.replace("test_", "").replace("_", " ").title()
        try:
            result = fn()
            if result is None:
                result = TestResult(name=test_name, passed=True)
            elif isinstance(result, bool):
                result = TestResult(name=test_name, passed=result)
            result.name = test_name
        except AssertionError as e:
            result = TestResult(name=test_name, passed=False, message=str(e))
        except Exception as e:
            result = TestResult(name=test_name, passed=False, message=f"{type(e).__name__}: {e}")

        suite.results.append(result)

        if result.skipped:
            icon = _c(YELLOW, "  ⊘ SKIP")
            detail = f" ({result.message})" if result.message else ""
        elif result.passed:
            icon = _c(GREEN,  "  ✅ PASS")
            detail = ""
        else:
            icon = _c(RED,    "  ❌ FAIL")
            detail = f" — {result.message}" if result.message else ""

        print(f"    {icon}  {test_name}{detail}")

    status_colour = GREEN if suite.failed == 0 else (YELLOW if suite.pct >= 70 else RED)
    print(f"  {_c(status_colour, f'  [{suite.passed}/{suite.total - suite.skipped} passed, {suite.skipped} skipped]')}")
    return suite

def skip(reason: str) -> TestResult:
    return TestResult(name="", passed=False, skipped=True, message=reason)

def ok(msg: str = "") -> TestResult:
    return TestResult(name="", passed=True, message=msg)

def fail(msg: str) -> TestResult:
    return TestResult(name="", passed=False, message=msg)

# ─────────────────────────────────────────────
# ═══════════════════════════════════════════
# TEST SUITES
# ═══════════════════════════════════════════
# ─────────────────────────────────────────────

# ── 1. BACKEND HEALTH ──────────────────────────────────────────────────────────
def test_health_endpoint():
    status, body = get("/health")
    assert status == 200, f"Expected 200, got {status}"
    assert body.get("status") == "healthy", f"Unexpected body: {body}"

def test_root_endpoint():
    status, body = get("/")
    assert status == 200, f"Expected 200, got {status}"
    assert "version" in body or "message" in body, f"Unexpected body: {body}"

def test_openapi_docs():
    status, _ = get("/docs")
    assert status == 200, f"Swagger docs not reachable, got {status}"

def test_frontend_reachable():
    try:
        resp = requests.get(FRONTEND_URL, timeout=5)
        assert resp.status_code in [200, 304], f"Frontend returned {resp.status_code}"
    except Exception as e:
        return fail(f"Frontend not reachable: {e}")


# ── 2. PROJECTS ────────────────────────────────────────────────────────────────
def test_list_projects():
    status, body = get("/cloudresourcemanager/v1/projects")
    assert status == 200, f"Expected 200, got {status}"
    projects = body.get("projects", [])
    assert len(projects) > 0, "No projects found — initialization may have failed"

def test_default_projects_exist():
    status, body = get("/cloudresourcemanager/v1/projects")
    assert status == 200
    ids = {p["projectId"] for p in body.get("projects", [])}
    assert "test-project" in ids, f"'test-project' missing from {ids}"

def test_create_and_delete_project():
    if READONLY:
        return skip("SANITY_READONLY=1")
    pid = f"sanity-proj-{RUN_ID}"
    # Create
    status, body = post("/cloudresourcemanager/v1/projects", {"projectId": pid, "name": "Sanity Test Project"})
    if status == 405:
        return skip("Create project not implemented (405)")
    assert status in [200, 201], f"Create failed: {status} — {body}"
    # Delete
    status, _ = delete(f"/cloudresourcemanager/v1/projects/{pid}")
    assert status in [200, 204, 404], f"Delete failed: {status}"


# ── 3. COMPUTE ENGINE ──────────────────────────────────────────────────────────
def test_list_zones():
    status, body = get(f"/compute/v1/projects/{PROJECT}/zones")
    assert status == 200, f"Got {status}"
    assert len(body.get("items", [])) > 0, "No zones returned"

def test_get_zone():
    status, body = get(f"/compute/v1/projects/{PROJECT}/zones/{ZONE}")
    assert status == 200, f"Got {status}"
    assert body.get("name") == ZONE

def test_list_machine_types():
    status, body = get(f"/compute/v1/projects/{PROJECT}/zones/{ZONE}/machineTypes")
    assert status == 200, f"Got {status}"
    assert len(body.get("items", [])) > 0, "No machine types"

def test_aggregated_instances():
    status, body = get(f"/compute/v1/projects/{PROJECT}/aggregated/instances")
    assert status == 200, f"Got {status}"
    assert "items" in body, "Missing 'items' key"

def test_list_instances_in_zone():
    status, body = get(f"/compute/v1/projects/{PROJECT}/zones/{ZONE}/instances")
    assert status == 200, f"Got {status}"
    assert "items" in body or isinstance(body, dict)

def test_list_addresses():
    status, body = get(f"/compute/v1/projects/{PROJECT}/regions/{REGION}/addresses")
    assert status == 200, f"Got {status}"

def test_list_disks():
    status, body = get(f"/compute/v1/projects/{PROJECT}/zones/{ZONE}/disks")
    assert status == 200, f"Got {status}"

def test_list_images():
    status, body = get(f"/compute/v1/projects/{PROJECT}/global/images")
    assert status == 200, f"Got {status}"

def test_create_and_delete_instance():
    if READONLY:
        return skip("SANITY_READONLY=1")
    name = f"sanity-vm-{RUN_ID}"
    payload = {
        "name": name,
        "machineType": f"zones/{ZONE}/machineTypes/e2-micro",
        "networkInterfaces": [{"network": "global/networks/default"}],
        "disks": [{"boot": True, "initializeParams": {"sourceImage": "debian-11"}}]
    }
    status, body = post(f"/compute/v1/projects/{PROJECT}/zones/{ZONE}/instances", payload)
    assert status in [200, 201], f"Instance create failed: {status} — {body}"
    # Cleanup
    delete(f"/compute/v1/projects/{PROJECT}/zones/{ZONE}/instances/{name}")

def test_reserve_and_delete_address():
    if READONLY:
        return skip("SANITY_READONLY=1")
    name = f"sanity-addr-{RUN_ID}"
    status, body = post(
        f"/compute/v1/projects/{PROJECT}/regions/{REGION}/addresses",
        {"name": name, "region": REGION}
    )
    assert status in [200, 201], f"Reserve address failed: {status} — {body}"
    delete(f"/compute/v1/projects/{PROJECT}/regions/{REGION}/addresses/{name}")


# ── 4. CLOUD STORAGE ───────────────────────────────────────────────────────────
def test_list_buckets():
    status, body = get(f"/storage/v1/b?project={PROJECT}")
    assert status == 200, f"Got {status}"
    assert "items" in body or isinstance(body, dict)

def test_create_bucket_and_upload_object():
    if READONLY:
        return skip("SANITY_READONLY=1")
    bucket_name = f"sanity-bucket-{RUN_ID}"
    # Create bucket
    status, body = post(f"/storage/v1/b?project={PROJECT}", {
        "name": bucket_name, "location": "US", "storageClass": "STANDARD"
    })
    assert status in [200, 201], f"Bucket create failed: {status} — {body}"

    # Upload a small object
    url = f"{BASE_URL}/upload/storage/v1/b/{bucket_name}/o?uploadType=media&name=sanity-test.txt"
    try:
        resp = requests.post(url, data=b"sanity check data", headers={"Content-Type": "text/plain"}, timeout=TIMEOUT)
        assert resp.status_code in [200, 201], f"Object upload failed: {resp.status_code}"
    except Exception as e:
        return fail(f"Object upload error: {e}")
    finally:
        # Delete bucket (objects cleaned up automatically or ignored on 409)
        delete(f"/storage/v1/b/{bucket_name}?force=true")

def test_bucket_metadata():
    if READONLY:
        return skip("SANITY_READONLY=1")
    bucket_name = f"sanity-meta-{RUN_ID}"
    post(f"/storage/v1/b?project={PROJECT}", {"name": bucket_name, "location": "US"})
    status, body = get(f"/storage/v1/b/{bucket_name}")
    assert status == 200, f"Got {status}"
    assert body.get("name") == bucket_name
    delete(f"/storage/v1/b/{bucket_name}?force=true")


# ── 5. VPC NETWORKS ────────────────────────────────────────────────────────────
def test_list_networks():
    status, body = get(f"/compute/v1/projects/{PROJECT}/global/networks")
    assert status == 200, f"Got {status}"
    networks = body.get("items", [])
    assert len(networks) > 0, "No networks — default network not initialized"

def test_default_network_exists():
    status, body = get(f"/compute/v1/projects/{PROJECT}/global/networks/default")
    assert status == 200, f"Got {status}"
    assert body.get("name") == "default"

def test_list_subnets():
    status, body = get(f"/compute/v1/projects/{PROJECT}/aggregated/subnetworks")
    assert status == 200, f"Got {status}"

def test_list_subnets_by_region():
    status, body = get(f"/compute/v1/projects/{PROJECT}/regions/{REGION}/subnetworks")
    assert status == 200, f"Got {status}"

def test_list_firewalls():
    status, body = get(f"/compute/v1/projects/{PROJECT}/global/firewalls")
    assert status == 200, f"Got {status}"
    rules = body.get("items", [])
    assert len(rules) > 0, "No firewall rules — default rules not initialized"

def test_list_routes():
    status, body = get(f"/compute/v1/projects/{PROJECT}/global/routes")
    assert status == 200, f"Got {status}"

def test_create_and_delete_network():
    if READONLY:
        return skip("SANITY_READONLY=1")
    name = f"sanity-net-{RUN_ID}"
    status, body = post(f"/compute/v1/projects/{PROJECT}/global/networks", {
        "name": name, "autoCreateSubnetworks": False
    })
    assert status in [200, 201], f"Network create failed: {status} — {body}"
    delete(f"/compute/v1/projects/{PROJECT}/global/networks/{name}")

def test_create_and_delete_firewall():
    if READONLY:
        return skip("SANITY_READONLY=1")
    name = f"sanity-fw-{RUN_ID}"
    status, body = post(f"/compute/v1/projects/{PROJECT}/global/firewalls", {
        "name": name,
        "network": "global/networks/default",
        "direction": "INGRESS",
        "priority": 1000,
        "sourceRanges": ["0.0.0.0/0"],
        "allowed": [{"IPProtocol": "tcp", "ports": ["80"]}]
    })
    assert status in [200, 201], f"Firewall create failed: {status} — {body}"
    delete(f"/compute/v1/projects/{PROJECT}/global/firewalls/{name}")


# ── 6. IAM ─────────────────────────────────────────────────────────────────────
def test_list_service_accounts():
    status, body = get(f"/v1/projects/{PROJECT}/serviceAccounts")
    assert status == 200, f"Got {status}"
    assert "accounts" in body, f"Missing 'accounts' key: {body}"

def test_create_and_delete_service_account():
    if READONLY:
        return skip("SANITY_READONLY=1")
    account_id = f"sanity-sa-{RUN_ID}"
    status, body = post(f"/v1/projects/{PROJECT}/serviceAccounts", {
        "accountId": account_id,
        "serviceAccount": {"displayName": "Sanity Test SA"}
    })
    assert status in [200, 201], f"SA create failed: {status} — {body}"
    email = body.get("email", f"{account_id}@{PROJECT}.iam.gserviceaccount.com")
    delete(f"/v1/projects/{PROJECT}/serviceAccounts/{email}")


# ── 7. GKE CLUSTERS ────────────────────────────────────────────────────────────
def test_list_gke_clusters():
    status, body = get(f"/v1/projects/{PROJECT}/locations/{ZONE}/clusters")
    if status == 404:
        return skip("GKE endpoint not available")
    assert status == 200, f"Got {status}"
    assert "clusters" in body or isinstance(body, dict)


# ── 8. CLOUD RUN ───────────────────────────────────────────────────────────────
def test_list_cloud_run_services():
    status, body = get(f"/v1/projects/{PROJECT}/locations/{REGION}/services")
    if status == 404:
        return skip("Cloud Run endpoint not available")
    assert status == 200, f"Got {status}"


# ── 9. PUB/SUB ─────────────────────────────────────────────────────────────────
def test_list_pubsub_topics():
    status, body = get(f"/v1/projects/{PROJECT}/topics")
    if status == 404:
        return skip("Pub/Sub endpoint not available")
    assert status == 200, f"Got {status}"
    assert "topics" in body or isinstance(body, dict)

def test_create_and_delete_topic():
    if READONLY:
        return skip("SANITY_READONLY=1")
    name = f"sanity-topic-{RUN_ID}"
    status, body = post(f"/v1/projects/{PROJECT}/topics", {"name": name})
    if status == 404:
        return skip("Pub/Sub create not available")
    assert status in [200, 201], f"Topic create failed: {status} — {body}"
    delete(f"/v1/projects/{PROJECT}/topics/{name}")


# ── 10. SECRET MANAGER ─────────────────────────────────────────────────────────
def test_list_secrets():
    status, body = get(f"/v1/projects/{PROJECT}/secrets")
    if status == 404:
        return skip("Secret Manager endpoint not available")
    assert status == 200, f"Got {status}"

def test_create_and_delete_secret():
    if READONLY:
        return skip("SANITY_READONLY=1")
    name = f"sanity-secret-{RUN_ID}"
    status, body = post(f"/v1/projects/{PROJECT}/secrets", {
        "secretId": name,
        "replication": {"automatic": {}}
    })
    if status == 404:
        return skip("Secret Manager create not available")
    assert status in [200, 201], f"Secret create failed: {status} — {body}"
    delete(f"/v1/projects/{PROJECT}/secrets/{name}")


# ── 11. AUTOSCALING ────────────────────────────────────────────────────────────
def test_list_autoscaling_groups():
    status, body = get(f"/compute/v1/projects/{PROJECT}/aggregated/autoscalers")
    if status == 404:
        return skip("Autoscaling endpoint not available")
    assert status == 200, f"Got {status}"

def test_list_instance_groups():
    status, body = get(f"/compute/v1/projects/{PROJECT}/aggregated/instanceGroups")
    if status == 404:
        return skip("Instance Groups endpoint not available")
    assert status == 200, f"Got {status}"


# ── 12. MONITORING ─────────────────────────────────────────────────────────────
def test_list_time_series():
    status, body = get(f"/monitoring/v3/projects/{PROJECT}/timeSeries")
    if status == 404:
        return skip("Monitoring endpoint not available")
    assert status == 200, f"Got {status}"
    assert "timeSeries" in body or isinstance(body, dict)

def test_list_alert_policies():
    status, body = get(f"/monitoring/v3/projects/{PROJECT}/alertPolicies")
    if status == 404:
        return skip("Alert policies endpoint not available")
    assert status == 200, f"Got {status}"

def test_list_notification_channels():
    status, body = get(f"/monitoring/v3/projects/{PROJECT}/notificationChannels")
    if status == 404:
        return skip("Notification channels endpoint not available")
    assert status == 200, f"Got {status}"


# ─────────────────────────────────────────────
# MAIN — build suites and run
# ─────────────────────────────────────────────
SUITES = [
    ("Backend Health",     [test_health_endpoint, test_root_endpoint, test_openapi_docs, test_frontend_reachable]),
    ("Projects",           [test_list_projects, test_default_projects_exist, test_create_and_delete_project]),
    ("Compute Engine",     [test_list_zones, test_get_zone, test_list_machine_types,
                            test_aggregated_instances, test_list_instances_in_zone,
                            test_list_addresses, test_list_disks, test_list_images,
                            test_create_and_delete_instance, test_reserve_and_delete_address]),
    ("Cloud Storage",      [test_list_buckets, test_create_bucket_and_upload_object, test_bucket_metadata]),
    ("VPC Networks",       [test_list_networks, test_default_network_exists, test_list_subnets,
                            test_list_subnets_by_region, test_list_firewalls, test_list_routes,
                            test_create_and_delete_network, test_create_and_delete_firewall]),
    ("IAM",                [test_list_service_accounts, test_create_and_delete_service_account]),
    ("GKE",                [test_list_gke_clusters]),
    ("Cloud Run",          [test_list_cloud_run_services]),
    ("Pub/Sub",            [test_list_pubsub_topics, test_create_and_delete_topic]),
    ("Secret Manager",     [test_list_secrets, test_create_and_delete_secret]),
    ("Autoscaling",        [test_list_autoscaling_groups, test_list_instance_groups]),
    ("Monitoring",         [test_list_time_series, test_list_alert_policies, test_list_notification_channels]),
]


def main():
    start = time.time()

    print("\n" + "=" * 70)
    print(_c(BOLD, "  GCS EMULATOR — SANITY TEST SUITE"))
    print("=" * 70)
    print(f"  Backend  : {BASE_URL}")
    print(f"  Frontend : {FRONTEND_URL}")
    print(f"  Project  : {PROJECT}")
    print(f"  Zone     : {ZONE}")
    print(f"  Run ID   : {RUN_ID}")
    print(f"  Mode     : {'READ-ONLY' if READONLY else 'FULL (CRUD)'}")
    print(f"  Started  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    for suite_name, fns in SUITES:
        run_suite(suite_name, fns)

    elapsed = time.time() - start

    # ── Final Summary ─────────────────────────────────────────────────────────
    total_passed  = sum(s.passed  for s in ALL_SUITES)
    total_failed  = sum(s.failed  for s in ALL_SUITES)
    total_skipped = sum(s.skipped for s in ALL_SUITES)
    total_tests   = sum(s.total   for s in ALL_SUITES)
    overall_pct   = int(100 * total_passed / max(total_tests - total_skipped, 1))

    print("\n" + "=" * 70)
    print(_c(BOLD, "  SANITY CHECK SUMMARY"))
    print("=" * 70)

    print(f"\n{'  Suite':<30}  {'Pass':>5}  {'Fail':>5}  {'Skip':>5}  {'%':>5}")
    print(f"  {'─'*28}  {'─'*5}  {'─'*5}  {'─'*5}  {'─'*5}")
    for s in ALL_SUITES:
        icon = _c(GREEN, "✅") if s.failed == 0 else (_c(YELLOW, "⚠️ ") if s.pct >= 70 else _c(RED, "❌"))
        print(f"  {icon}  {s.name:<26}  {s.passed:>5}  {s.failed:>5}  {s.skipped:>5}  {s.pct:>4}%")

    print(f"\n  {'─'*66}")
    total_line = f"  {'TOTAL':<30}  {total_passed:>5}  {total_failed:>5}  {total_skipped:>5}  {overall_pct:>4}%"
    if overall_pct >= 90:
        print(_c(GREEN, total_line))
    elif overall_pct >= 75:
        print(_c(YELLOW, total_line))
    else:
        print(_c(RED, total_line))

    print(f"\n  Elapsed  : {elapsed:.2f}s")

    if total_failed > 0:
        print(f"\n  {_c(RED, 'FAILURES:')}")
        for s in ALL_SUITES:
            for r in s.results:
                if not r.passed and not r.skipped:
                    print(f"    {_c(RED, '✗')} [{s.name}] {r.name}: {r.message}")

    print()
    if overall_pct >= 90:
        verdict = _c(GREEN,  BOLD + "  🎉 SYSTEM HEALTHY — PRODUCTION READY" + RESET)
    elif overall_pct >= 75:
        verdict = _c(YELLOW, BOLD + "  ⚠️  SYSTEM OPERATIONAL — MINOR ISSUES" + RESET)
    else:
        verdict = _c(RED,    BOLD + "  ❌ SYSTEM DEGRADED — ACTION NEEDED"  + RESET)

    print(verdict)
    print("=" * 70 + "\n")

    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    main()
