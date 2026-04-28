# CloudTester - GCP Simulator Test Suite

Complete testing framework for the GCP Simulator implementation.

## 📁 Structure

```
tests/
├── conftest.py                      # Pytest fixtures & configuration
├── pytest.ini                       # Pytest settings
├── .env-test                        # Test environment variables
├── run_wrapper_tests.sh            # Run tests for specific features (dev)
├── run_full_suite.sh               # Run all tests (regression check)
│
└── CloudTester/
    ├── suites/                      # Finalized test suites (one per service)
    │   ├── test_compute.py          # Compute Engine (20+ tests)
    │   ├── test_storage.py          # Cloud Storage (15+ tests)
    │   ├── test_vpc.py              # VPC Networking (15+ tests)
    │   ├── test_firewall.py         # Firewall Rules (10+ tests)
    │   ├── test_iam.py              # IAM (10+ tests)
    │   ├── test_gke.py              # GKE (20+ tests)
    │   ├── test_cloud_run.py        # Cloud Run (10+ tests)
    │   ├── test_artifacts.py        # Artifact Registry (10+ tests)
    │   ├── test_pubsub.py           # Pub/Sub (10+ tests)
    │   ├── test_monitoring.py       # Monitoring (10+ tests)
    │   ├── test_autoscaling.py      # Autoscaling (10+ tests)
    │   └── test_projects.py         # Projects (5+ tests)
    │
    └── wrappers/                    # Temporary test files during dev
        └── [feature_name]_test.py   # Created during feature development
```

## 🚀 Quick Start

### Prerequisites

```bash
cd /home/ubuntu/gcs-stimulator

# Install test dependencies
pip install pytest pytest-cov pytest-xdist requests

# Ensure backend is running
./minimal-backend/main.py &
# OR in Docker: docker-compose up
```

### Run Tests

#### 1. **Wrapper Tests** (During Feature Development)
```bash
# Test a specific feature in isolation
./tests/run_wrapper_tests.sh firewall

# Expected output:
# ✓ tests/wrappers/firewall_test.py::test_default_rules_exist
# ✓ tests/wrappers/firewall_test.py::test_allow_ssh_rule
# ✓ 3 passed in 2.34s
```

#### 2. **Full Regression Suite** (Before Commit)
```bash
# Run entire test suite across all services
./tests/run_full_suite.sh

# With code coverage report
./tests/run_full_suite.sh --coverage

# Run in parallel (faster)
python -m pip install pytest-xdist
./tests/run_full_suite.sh --parallel

# Expected output:
# ✓ test_compute.py: 20 passed
# ✓ test_storage.py: 15 passed
# ✓ test_vpc.py: 15 passed
# ✓ test_firewall.py: 10 passed (PHASE 1)
# ✓ ... 
# ✓ 140+ passed in 34.67s
# Coverage: 82% (minimal-backend)
```

#### 3. **Run Specific Test File**
```bash
pytest tests/CloudTester/suites/test_compute.py -v

# Run specific test class
pytest tests/CloudTester/suites/test_compute.py::TestInstances -v

# Run specific test
pytest tests/CloudTester/suites/test_compute.py::TestInstances::test_create_instance -v
```

#### 4. **Filter by Marker**
```bash
# Run only Firewall tests
pytest tests/ -m firewall -v

# Run only Compute tests
pytest tests/ -m compute -v

# Run only integration tests (skip unit)
pytest tests/ -m integration -v
```

## 📝 Configuration

### Edit `.env-test` for test settings:

```bash
# API endpoint
TEST_API_URL=http://localhost:8080

# GCP resources
TEST_PROJECT=test-project
TEST_REGION=us-central1
TEST_ZONE=us-central1-a

# Test execution
TEST_TIMEOUT=30
```

## 🔄 DEV → TEST → PUSH Workflow

### Stage 1: Write & test locally
```bash
# Write code in minimal-backend/
vim minimal-backend/api/firewall.py

# Create wrapper test
vim tests/CloudTester/wrappers/firewall_test.py

# Test feature in isolation
./tests/run_wrapper_tests.sh firewall
# ✓ Tests pass
```

### Stage 2: Run full regression suite
```bash
./tests/run_full_suite.sh
# ✓ All 140+ tests pass
# ✓ No regressions introduced
```

### Stage 3: Promote & commit
```bash
# Move wrapper → suite
mv tests/CloudTester/wrappers/firewall_test.py \
   tests/CloudTester/suites/test_firewall.py

# Commit
git add minimal-backend/ tests/CloudTester/suites/test_firewall.py
git commit -m "feat: add default firewall rules"

# Push
git push origin feature/firewall-default-rules
```

## 📊 Test Coverage Report

```bash
./tests/run_full_suite.sh --coverage

# View HTML report
open htmlcov/index.html
```

**Target coverage:** ≥ 80% per service

Current coverage by service:
- Compute Engine: 75%
- Cloud Storage: 72%
- VPC Networking: 68%
- IAM: 60%
- GKE: 70%
- Cloud Run: 50%
- Artifact Registry: 45%
- Firewall: 0% (Phase 1 - will implement)

## 🧩 Available Fixtures

### From `conftest.py`:

```python
def test_something(api_client, test_project, test_zone, sample_instance_payload):
    """
    api_client: APIClient instance for making requests
    test_project: Test project ID (default: test-project)
    test_zone: Test compute zone (default: us-central1-a)
    test_region: Test region (default: us-central1)
    base_url: API base URL
    
    sample_instance_payload: VM instance creation payload
    sample_network_payload: VPC network creation payload
    sample_bucket_payload: Storage bucket creation payload
    sample_firewall_payload: Firewall rule creation payload
    sample_cluster_payload: GKE cluster creation payload
    
    cleanup_resources: Fixture for resource cleanup
    """
    resp = api_client.get(f"/compute/v1/projects/{test_project}")
```

### APIClient Methods:

```python
# Making requests
api_client.get(path: str) → Response
api_client.post(path: str, data: dict) → Response
api_client.patch(path: str, data: dict) → Response
api_client.delete(path: str) → Response

# Special helpers
api_client.wait_for_status(path, expected_status, max_attempts=30, interval=1.0)
```

## ✅ Examples

### Example 1: Test Instance Creation (Compute)
```python
def test_create_instance(api_client, test_project, test_zone, sample_instance_payload):
    path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/instances"
    
    payload = {
        "name": sample_instance_payload["name"],
        "machineType": f"zones/{test_zone}/machineTypes/e2-micro",
        "networkInterfaces": [{"network": "global/networks/default"}]
    }
    
    resp = api_client.post(path, payload)
    assert resp.status_code in [200, 201]
    assert resp.json()["name"] == payload["name"]
```

### Example 2: Test Firewall Default Rules (Phase 1)
```python
def test_default_rules_exist(api_client, test_project):
    path = f"/compute/v1/projects/{test_project}/global/firewalls"
    resp = api_client.get(path)
    
    rules = resp.json().get("items", [])
    rule_names = [r["name"] for r in rules]
    
    expected = ["allow-ssh", "allow-http", "allow-https", "allow-internal", "allow-icmp"]
    for rule_name in expected:
        assert rule_name in rule_names
```

## 🐛 Debugging Tests

### View detailed output
```bash
pytest tests/ -vv -s  # -s shows print() statements
```

### Stop on first failure
```bash
pytest tests/ -x  # Exit immediately on failure
```

### Run with full traceback
```bash
pytest tests/ --tb=long
```

### Debug specific test step-by-step
```bash
pytest tests/CloudTester/suites/test_firewall.py::TestDefaultFirewallRules::test_default_rules_exist -vv --pdb
```

## ⚠️ Common Issues

### Tests can't connect to API
```
Error: API not reachable at http://localhost:8080
```
**Solution:** Ensure backend is running:
```bash
cd /home/ubuntu/gcs-stimulator
python minimal-backend/main.py
```

### Test timeout
```
Error: timed out after 30 seconds
```
**Solution:** Increase timeout in `.env-test`:
```bash
TEST_TIMEOUT=60
```

### Fixture not found
```
Error: fixture 'test_project' not found
```
**Solution:** Ensure `conftest.py` is in `tests/` directory

## 📚 Test Markers

Use markers to categorize and filter tests:

```python
@pytest.mark.firewall
@pytest.mark.slow
def test_something():
    pass

# Run
pytest tests/ -m "firewall and not slow"
```

## 🔄 CI/CD Integration

For GitHub Actions/GitLab CI:

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install pytest pytest-cov
      - run: python -m pytest tests/ --cov=minimal-backend
```

## 📖 Phase 1 Test Coverage

Phase 1 focuses on **Firewall & IAM Default Setup**:

- ✅ `test_firewall.py` - 10 tests
  - Default rules creation (5 rules)
  - Custom rule CRUD
  - Rule validation

- ✅ `test_iam.py` - Extends with (5+ tests)
  - Default service accounts creation
  - Service account validation

- ✅ `test_vpc.py` - Extends with (2 tests)
  - Default network subnet creation

## 🎯 Next Steps

1. ✅ CloudTester package created
2. 🚀 Implement Phase 1 features with tests
3. Build wrapper tests for each feature
4. Promote to suite after verification
5. Add pre-commit hooks
6. Setup CI/CD pipeline

---

**Questions?** Check existing test files in `tests/CloudTester/suites/` for examples.
