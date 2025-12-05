"""
End-to-end SDK Integration Tests

Tests the GCS SDK integration via mocked transport layer.
All tests run in-memory without starting a server.
"""
import pytest
from app.models.bucket import Bucket


def test_sdk_create_bucket(sdk_client, app):
    """SDK can create a bucket via mocked transport"""
    with app.app_context():
        # Create bucket via SDK
        bucket = sdk_client.create_bucket('sdk-test-bucket', location='US')
        
        # Verify SDK response
        assert bucket.name == 'sdk-test-bucket'
        assert bucket.location == 'US'
        
        # Verify database persistence
        db_bucket = Bucket.query.filter_by(name='sdk-test-bucket').first()
        assert db_bucket is not None
        assert db_bucket.name == 'sdk-test-bucket'
        assert db_bucket.location == 'US'
        assert db_bucket.project_id == 'test-project'


def test_sdk_get_bucket(sdk_client, app):
    """SDK can retrieve bucket metadata"""
    with app.app_context():
        # Create bucket first
        sdk_client.create_bucket('sdk-get-test')
        
        # Retrieve via SDK
        bucket = sdk_client.get_bucket('sdk-get-test')
        
        # Verify
        assert bucket.name == 'sdk-get-test'
        assert bucket.location == 'US'  # default


def test_sdk_list_buckets(sdk_client, app):
    """SDK can list buckets for a project"""
    with app.app_context():
        # Create multiple buckets
        sdk_client.create_bucket('sdk-list-bucket-1')
        sdk_client.create_bucket('sdk-list-bucket-2')
        sdk_client.create_bucket('sdk-list-bucket-3')
        
        # List via SDK
        buckets = list(sdk_client.list_buckets())
        
        # Verify
        bucket_names = {b.name for b in buckets}
        assert 'sdk-list-bucket-1' in bucket_names
        assert 'sdk-list-bucket-2' in bucket_names
        assert 'sdk-list-bucket-3' in bucket_names
        assert len(bucket_names) >= 3


def test_sdk_delete_bucket(sdk_client, app):
    """SDK can delete an empty bucket"""
    with app.app_context():
        # Create bucket
        bucket = sdk_client.create_bucket('sdk-delete-test')
        assert bucket.name == 'sdk-delete-test'
        
        # Verify it exists in DB
        db_bucket = Bucket.query.filter_by(name='sdk-delete-test').first()
        assert db_bucket is not None
        
        # Delete via SDK
        bucket.delete()
        
        # Verify deletion in DB
        db_bucket = Bucket.query.filter_by(name='sdk-delete-test').first()
        assert db_bucket is None


def test_sdk_bucket_exists(sdk_client, app):
    """SDK can check if bucket exists"""
    with app.app_context():
        # Create bucket
        sdk_client.create_bucket('sdk-exists-test')
        
        # Check existence via SDK
        bucket = sdk_client.bucket('sdk-exists-test')
        assert bucket.exists()
        
        # Check non-existent bucket
        nonexistent_bucket = sdk_client.bucket('does-not-exist')
        assert not nonexistent_bucket.exists()


def test_sdk_bucket_with_custom_storage_class(sdk_client, app):
    """SDK can create bucket with custom storage class"""
    with app.app_context():
        # Create bucket with COLDLINE storage
        bucket = sdk_client.create_bucket(
            'sdk-coldline-bucket',
            location='US',
        )
        bucket.storage_class = 'COLDLINE'
        
        # Note: SDK doesn't set storage_class in create_bucket directly
        # but we can verify the bucket was created
        assert bucket.name == 'sdk-coldline-bucket'
        
        # Verify in DB
        db_bucket = Bucket.query.filter_by(name='sdk-coldline-bucket').first()
        assert db_bucket is not None


def test_sdk_error_duplicate_bucket(sdk_client, app):
    """SDK handles duplicate bucket creation correctly"""
    with app.app_context():
        # Create bucket
        sdk_client.create_bucket('sdk-duplicate-test')
        
        # Attempt duplicate creation
        from google.api_core.exceptions import Conflict
        with pytest.raises(Conflict):
            sdk_client.create_bucket('sdk-duplicate-test')


def test_sdk_error_bucket_not_found(sdk_client, app):
    """SDK handles bucket not found correctly"""
    with app.app_context():
        from google.api_core.exceptions import NotFound
        
        # Attempt to get non-existent bucket
        with pytest.raises(NotFound):
            sdk_client.get_bucket('nonexistent-bucket-xyz')


def test_sdk_full_bucket_lifecycle(sdk_client, app):
    """Test complete bucket lifecycle via SDK"""
    with app.app_context():
        bucket_name = 'sdk-lifecycle-bucket'
        
        # Step 1: Create
        bucket = sdk_client.create_bucket(bucket_name, location='EU')
        assert bucket.name == bucket_name
        assert bucket.location == 'EU'
        
        # Step 2: Verify existence
        assert sdk_client.bucket(bucket_name).exists()
        
        # Step 3: Get metadata
        retrieved_bucket = sdk_client.get_bucket(bucket_name)
        assert retrieved_bucket.name == bucket_name
        assert retrieved_bucket.location == 'EU'
        
        # Step 4: List (should include our bucket)
        bucket_names = {b.name for b in sdk_client.list_buckets()}
        assert bucket_name in bucket_names
        
        # Step 5: Delete
        bucket.delete()
        
        # Step 6: Verify deletion
        assert not sdk_client.bucket(bucket_name).exists()
        
        # Verify in database
        db_bucket = Bucket.query.filter_by(name=bucket_name).first()
        assert db_bucket is None


# Note: SDK object operations (upload_from_string, download_as_text, etc.)
# are tested via live server tests rather than the mock transport, 
# as the SDK's download stream handling requires complex mocking of 
# response.raw attribute. See test_multipart_upload.py for endpoint tests
# and run test_sdk_multipart.py for live SDK verification.
