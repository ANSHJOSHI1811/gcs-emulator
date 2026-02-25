# CloudTester Legacy Files

This directory contains archived test files from the legacy testing infrastructure.

These files have been superseded by the comprehensive **CloudTester** framework in `tests/CloudTester/`.

## 📦 Contents

### Legacy Python Tests
- `test_api_direct.py` - Old API integration tests
- `test_monitoring.py` - Legacy monitoring tests
- `test_docker_ip.py` - Docker IP assignment tests
- `test_secret_manager.py` - Secret Manager tests (old format)
- `test_artifact_images.py` - Artifact Registry tests (old format)

### Legacy Shell Scripts
- `run_gcloud_tests.sh` - Old gcloud test runner
- `test_gcloud_integration.sh` - gcloud integration tests
- `test_gcloud_simple.sh` - Simple gcloud tests
- `test_cloud_run_artifacts.sh` - Cloud Run artifact tests
- `test_gke_gcloud.sh` - GKE gcloud tests

## ✅ Migration Status

These files have been replaced by the new **CloudTester** framework:

```
Old Location                          New Location
─────────────────────────────────────────────────────────────
test_monitoring.py            →   tests/CloudTester/suites/test_monitoring.py
test_secret_manager.py        →   tests/CloudTester/suites/test_projects.py
test_artifact_images.py       →   tests/CloudTester/suites/test_artifacts.py
test_api_direct.py            →   tests/CloudTester/suites/test_cloud_run.py
```

## 📚 Reference

If you need to reference the old test format or logic:

1. Check `tests/CloudTester/suites/test_*.py` for modern pytest format
2. See `tests/README.md` for comprehensive testing documentation
3. View `tests/conftest.py` for pytest fixtures and configuration

## 🗑️ Removal

These files can be safely deleted if they are not needed as reference. They are kept here for historical purposes.

Consider deleting this directory after migration is complete and all tests pass.
