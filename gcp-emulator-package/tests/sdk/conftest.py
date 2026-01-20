"""
Pytest configuration and shared fixtures for GCP SDK testing
"""
import os
import pytest
from google.cloud import storage
from google.cloud import compute_v1
from google.api_core.client_options import ClientOptions
from google.auth.credentials import AnonymousCredentials
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


# Test configuration
# Note: Default port is 8080 for this emulator (user specified 5000 in requirements)
EMULATOR_ENDPOINT = os.getenv("EMULATOR_ENDPOINT", "http://localhost:8080")
DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator"
)
PROJECT_ID = "test-project"


@pytest.fixture(scope="session")
def client_options():
    """
    ClientOptions for pointing SDK to local emulator
    """
    return ClientOptions(api_endpoint=EMULATOR_ENDPOINT)


@pytest.fixture(scope="session")
def credentials():
    """
    Anonymous credentials to bypass Google authentication
    """
    return AnonymousCredentials()


@pytest.fixture(scope="function")
def storage_client(client_options, credentials):
    """
    Google Cloud Storage client pointing to local emulator
    
    Function-scoped to ensure clean state per test
    """
    client = storage.Client(
        project=PROJECT_ID,
        credentials=credentials,
        client_options=client_options
    )
    yield client
    
    # Cleanup: Delete all buckets created during test
    try:
        for bucket in client.list_buckets():
            try:
                bucket.delete(force=True)
            except Exception:
                pass
    except Exception:
        pass


@pytest.fixture(scope="function")
def compute_client(client_options, credentials):
    """
    Google Compute Engine client pointing to local emulator
    
    Function-scoped to ensure clean state per test
    """
    client = compute_v1.InstancesClient(
        credentials=credentials,
        client_options=client_options
    )
    yield client
    
    # Cleanup handled by backend or manual cleanup


@pytest.fixture(scope="session")
def db_engine():
    """
    SQLAlchemy engine for direct database access
    
    Session-scoped for performance
    """
    engine = create_engine(DATABASE_URL, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Database session for testing database integrity
    
    Function-scoped to ensure transaction isolation
    """
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def test_bucket_name():
    """
    Generate unique bucket name for testing
    """
    import uuid
    return f"test-bucket-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def test_instance_name():
    """
    Generate unique instance name for testing
    """
    import uuid
    return f"test-instance-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def sample_text_content():
    """
    Sample text content for blob upload tests
    """
    return b"Hello from GCP Emulator! This is a test file."


@pytest.fixture(scope="session")
def sample_json_content():
    """
    Sample JSON content for blob upload tests
    """
    import json
    data = {
        "message": "Test data",
        "timestamp": "2026-01-01T00:00:00Z",
        "nested": {
            "key": "value",
            "number": 42
        }
    }
    return json.dumps(data).encode('utf-8')


# Helper functions for tests
def wait_for_bucket(storage_client, bucket_name, timeout=5):
    """
    Wait for bucket to be available (useful for eventual consistency)
    """
    import time
    start = time.time()
    while time.time() - start < timeout:
        try:
            bucket = storage_client.get_bucket(bucket_name)
            return bucket
        except Exception:
            time.sleep(0.1)
    raise TimeoutError(f"Bucket {bucket_name} not available after {timeout}s")


def wait_for_blob(bucket, blob_name, timeout=5):
    """
    Wait for blob to be available
    """
    import time
    start = time.time()
    while time.time() - start < timeout:
        blob = bucket.get_blob(blob_name)
        if blob is not None:
            return blob
        time.sleep(0.1)
    raise TimeoutError(f"Blob {blob_name} not available after {timeout}s")


# Make helper functions available to tests
@pytest.fixture
def wait_for_bucket_helper():
    return wait_for_bucket


@pytest.fixture
def wait_for_blob_helper():
    return wait_for_blob
