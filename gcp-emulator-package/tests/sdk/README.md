# GCP Emulator SDK Integration Tests

Comprehensive test suite for the GCP Emulator using official Google Cloud SDKs.

## Overview

This test suite validates that the GCP emulator correctly implements the Google Cloud APIs by using the official Python SDKs:
- `google-cloud-storage` for Cloud Storage
- `google-cloud-compute` for Compute Engine

## Test Structure

```
tests/sdk/
├── conftest.py                     # Pytest fixtures and configuration
├── test_storage.py                 # Cloud Storage SDK tests
├── test_compute.py                 # Compute Engine SDK tests
├── test_database_integrity.py      # Database validation tests
├── requirements-test.txt           # Test dependencies
└── README.md                       # This file
```

## Setup

### 1. Install Dependencies

```bash
cd gcp-emulator-package
pip install -r tests/sdk/requirements-test.txt
```

### 2. Start Services

Ensure the following are running:

**PostgreSQL Database:**
```powershell
wsl -d Ubuntu-24.04 docker ps | findstr postgres
```

**Emulator Backend:**
```powershell
# Update conftest.py if using different port (default: 5000)
# Your actual backend runs on 8080, so update EMULATOR_ENDPOINT
wsl -d Ubuntu-24.04 bash -c "cd /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package && source .venv/bin/activate && python run.py"
```

### 3. Configure Environment

```bash
# Optional: Override defaults
export EMULATOR_ENDPOINT="http://localhost:8080"  # Your actual port
export TEST_DATABASE_URL="postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator"
```

## Running Tests

### Run All Tests

```bash
pytest tests/sdk/ -v
```

### Run Specific Test File

```bash
# Storage tests only
pytest tests/sdk/test_storage.py -v

# Compute tests only
pytest tests/sdk/test_compute.py -v

# Database integrity tests only
pytest tests/sdk/test_database_integrity.py -v
```

### Run Specific Test Class

```bash
pytest tests/sdk/test_storage.py::TestBucketOperations -v
```

### Run Specific Test

```bash
pytest tests/sdk/test_storage.py::TestBucketOperations::test_create_bucket_returns_201 -v
```

### Run with Coverage

```bash
pytest tests/sdk/ --cov=app --cov-report=html -v
```

### Run in Parallel

```bash
pytest tests/sdk/ -n auto -v
```

## Test Categories

### Storage Tests (`test_storage.py`)

#### Bucket Operations
- ✅ Create bucket and verify HTTP 201
- ✅ Create bucket with location
- ✅ Create bucket with storage class
- ✅ List buckets
- ✅ Delete bucket
- ✅ Bucket exists check

#### Blob Operations
- ✅ Upload text blob
- ✅ Upload JSON blob
- ✅ Upload from file
- ✅ List blobs
- ✅ List blobs with prefix
- ✅ Download blob content
- ✅ Download blob to file
- ✅ Delete blob
- ✅ Blob metadata operations
- ✅ Content type handling

#### Integration Tests
- ✅ Delete bucket with blobs (force)
- ✅ Empty bucket list
- ✅ Blob operations on non-existent bucket
- ✅ Multiple buckets isolation

### Compute Tests (`test_compute.py`)

#### Instance Operations
- ✅ Insert instance and verify database storage
- ✅ List instances with status check
- ✅ Get instance details
- ✅ Instance state transitions

#### API Endpoints
- ✅ Compute health endpoint
- ✅ Create instance via REST API

#### Database Integrity
- ✅ Instances table schema
- ✅ Instance constraints
- ✅ Cascade delete behavior

### Database Integrity Tests (`test_database_integrity.py`)

#### Storage Integrity
- ✅ Bucket creation persists to database
- ✅ Bucket metadata stored correctly
- ✅ Bucket deletion removes from database
- ✅ Blob upload persists to database
- ✅ Blob metadata stored correctly
- ✅ Blob deletion removes from database

#### Versioning Integrity
- ✅ Versioning flag persisted
- ✅ Object versions stored

#### Project Integrity
- ✅ Project exists in database
- ✅ Bucket-project association

#### Schema Integrity
- ✅ Required tables exist
- ✅ Foreign key constraints
- ✅ Performance indexes

## Fixtures

### Shared Fixtures (conftest.py)

- `client_options` - ClientOptions with emulator endpoint
- `credentials` - AnonymousCredentials for bypassing auth
- `storage_client` - Configured Storage client
- `compute_client` - Configured Compute client
- `db_engine` - SQLAlchemy engine
- `db_session` - Database session
- `test_bucket_name` - Unique bucket name generator
- `test_instance_name` - Unique instance name generator
- `sample_text_content` - Test file content
- `sample_json_content` - Test JSON content

### Helper Functions

- `wait_for_bucket()` - Wait for bucket availability
- `wait_for_blob()` - Wait for blob availability

## Configuration

### Update Emulator Port

If your emulator runs on a different port (e.g., 8080 instead of 5000):

**Option 1: Environment Variable**
```bash
export EMULATOR_ENDPOINT="http://localhost:8080"
pytest tests/sdk/ -v
```

**Option 2: Edit conftest.py**
```python
EMULATOR_ENDPOINT = os.getenv("EMULATOR_ENDPOINT", "http://localhost:8080")
```

### Update Database Connection

```python
DATABASE_URL = "postgresql://user:pass@localhost:5432/dbname"
```

## Troubleshooting

### Connection Refused

```
requests.exceptions.ConnectionError: Failed to establish connection
```

**Solution**: Ensure emulator backend is running on the configured port.

### Database Connection Failed

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**: Verify PostgreSQL is running:
```powershell
wsl -d Ubuntu-24.04 docker ps | findstr postgres
```

### Authentication Errors

```
google.auth.exceptions.DefaultCredentialsError
```

**Solution**: The tests use `AnonymousCredentials`. If you see this error, verify the fixture is being used.

### Test Failures

1. **Check backend logs** for errors
2. **Verify database schema** matches expected structure
3. **Check API endpoints** are implemented
4. **Review test assumptions** about state

### Skipped Tests

Some tests may be skipped if:
- Compute API not fully implemented
- Database tables missing
- Features not yet available

This is expected for partial implementations.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: SDK Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_USER: gcs_user
          POSTGRES_PASSWORD: gcs_password
          POSTGRES_DB: gcs_emulator
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/sdk/requirements-test.txt
      
      - name: Start emulator
        run: |
          python run.py &
          sleep 5
      
      - name: Run tests
        run: pytest tests/sdk/ -v --cov=app
```

## Contributing

When adding new features:

1. **Add SDK tests** for the feature
2. **Add database integrity tests** to verify persistence
3. **Update conftest.py** if new fixtures needed
4. **Document test coverage** in this README

## Test Coverage Goals

- **Storage API**: 90%+ coverage
- **Compute API**: 80%+ coverage (Phase 1)
- **Database Layer**: 95%+ coverage

## Notes

- Tests use **official Google SDKs** not mock libraries
- **AnonymousCredentials** bypass real authentication
- **Database tests** verify persistence layer
- Tests are **idempotent** (can run multiple times)
- **Cleanup** happens in fixtures and teardown

## Support

For issues or questions:
1. Check backend logs: `gcp-emulator-package/logs/`
2. Review test output with `-vv` flag
3. Check database state manually
4. Verify all services are running
