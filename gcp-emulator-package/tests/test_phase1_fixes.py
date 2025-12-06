"""
Phase 1 Security and Correctness Fixes Tests

Tests for:
1. Path traversal prevention
2. Bucket hard delete
3. Metadata fixes (bucket name instead of ID)
4. CRC32C correctness
"""
import os
import pytest
import base64
import shutil
from pathlib import Path
from app.factory import create_app, db
from app.models.bucket import Bucket
from app.models.object import Object, ObjectVersion
from app.services.bucket_service import BucketService
from app.services.object_versioning_service import ObjectVersioningService
from app.utils.hashing import calculate_crc32c, calculate_md5
import google_crc32c


@pytest.fixture
def app():
    """Create test Flask app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'TEST_DATABASE_URL',
        'postgresql://gcs_user:gcs_password@localhost:5432/gcs_emulator_test'
    )
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        
        # Clean up test storage
        storage_path = os.getenv("STORAGE_PATH", "./storage")
        if os.path.exists(storage_path):
            shutil.rmtree(storage_path)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestPathTraversalPrevention:
    """Test path traversal attack prevention"""
    
    def test_upload_with_parent_directory_traversal_fails(self, app):
        """Upload with '../' in object name must fail"""
        with app.app_context():
            # Create test bucket
            bucket = BucketService.create_bucket("test-project", "test-bucket")
            
            # Attempt to upload with path traversal
            malicious_names = [
                "../../etc/passwd",
                "../../../evil.txt",
                "folder/../../../secret.txt",
                "normal/../../../etc/hosts"
            ]
            
            for name in malicious_names:
                with pytest.raises(ValueError, match="not allowed|path traversal"):
                    ObjectVersioningService.upload_object_with_versioning(
                        bucket_name="test-bucket",
                        object_name=name,
                        content=b"malicious content",
                        content_type="text/plain"
                    )
    
    def test_upload_with_backslash_fails(self, app):
        """Upload with backslashes must fail"""
        with app.app_context():
            bucket = BucketService.create_bucket("test-project", "test-bucket")
            
            with pytest.raises(ValueError, match="backslashes not allowed"):
                ObjectVersioningService.upload_object_versioned(
                    bucket_name="test-bucket",
                    object_name="folder\\..\\evil.txt",
                    content=b"test",
                    content_type="text/plain"
                )
    
    def test_upload_with_absolute_path_fails(self, app):
        """Upload with absolute paths must fail"""
        with app.app_context():
            bucket = BucketService.create_bucket("test-project", "test-bucket")
            
            with pytest.raises(ValueError, match="absolute paths not allowed"):
                ObjectVersioningService.upload_object_versioned(
                    bucket_name="test-bucket",
                    object_name="/etc/passwd",
                    content=b"test",
                    content_type="text/plain"
                )
    
    def test_upload_with_drive_letter_fails(self, app):
        """Upload with Windows drive letters must fail"""
        with app.app_context():
            bucket = BucketService.create_bucket("test-project", "test-bucket")
            
            with pytest.raises(ValueError, match="drive letters not allowed"):
                ObjectVersioningService.upload_object_versioned(
                    bucket_name="test-bucket",
                    object_name="C:\\Windows\\system32\\evil.txt",
                    content=b"test",
                    content_type="text/plain"
                )
    
    def test_upload_with_valid_nested_path_succeeds(self, app):
        """Upload with normal nested paths must succeed"""
        with app.app_context():
            bucket = BucketService.create_bucket("test-project", "test-bucket")
            
            valid_names = [
                "normal/path/file.txt",
                "folder/subfolder/document.pdf",
                "deeply/nested/path/to/file.json"
            ]
            
            for name in valid_names:
                obj = ObjectVersioningService.upload_object_versioned(
                    bucket_name="test-bucket",
                    object_name=name,
                    content=b"valid content",
                    content_type="text/plain"
                )
                assert obj.name == name
                
                # Verify file is in correct location
                storage_path = os.getenv("STORAGE_PATH", "./storage")
                file_path = Path(storage_path) / bucket.id / name / "v1"
                assert file_path.exists()
    
    def test_path_stays_within_storage_root(self, app):
        """Ensure resolved paths never escape storage root"""
        with app.app_context():
            bucket = BucketService.create_bucket("test-project", "test-bucket")
            
            obj = ObjectVersioningService.upload_object_versioned(
                bucket_name="test-bucket",
                object_name="safe/file.txt",
                content=b"content",
                content_type="text/plain"
            )
            
            storage_root = Path(os.getenv("STORAGE_PATH", "./storage")).resolve()
            file_path = Path(obj.file_path).resolve()
            
            # File path must start with storage root
            assert str(file_path).startswith(str(storage_root))


class TestBucketHardDelete:
    """Test bucket hard delete functionality"""
    
    def test_delete_bucket_after_deleting_objects_succeeds(self, app):
        """After deleting all objects, bucket deletion must succeed"""
        with app.app_context():
            # Create bucket and upload objects
            bucket = BucketService.create_bucket("test-project", "delete-test")
            
            for i in range(3):
                ObjectVersioningService.upload_object_versioned(
                    bucket_name="delete-test",
                    object_name=f"file{i}.txt",
                    content=f"content {i}".encode(),
                    content_type="text/plain"
                )
            
            # Delete all objects
            for i in range(3):
                ObjectVersioningService.delete_object_versioned(
                    bucket_name="delete-test",
                    object_name=f"file{i}.txt"
                )
            
            # Now bucket deletion should succeed
            result = BucketService.delete_bucket("delete-test")
            assert result is True
            
            # Verify bucket is gone from database
            deleted_bucket = Bucket.query.filter_by(name="delete-test").first()
            assert deleted_bucket is None
    
    def test_delete_bucket_removes_physical_directory(self, app):
        """Bucket deletion must remove physical storage directory"""
        with app.app_context():
            bucket = BucketService.create_bucket("test-project", "dir-test")
            
            # Upload an object
            ObjectVersioningService.upload_object_versioned(
                bucket_name="dir-test",
                object_name="test.txt",
                content=b"test",
                content_type="text/plain"
            )
            
            # Get directory path before deletion
            storage_path = os.getenv("STORAGE_PATH", "./storage")
            bucket_dir = Path(storage_path) / bucket.id
            assert bucket_dir.exists()
            
            # Delete object then bucket
            ObjectVersioningService.delete_object_versioned(
                bucket_name="dir-test",
                object_name="test.txt"
            )
            BucketService.delete_bucket("dir-test")
            
            # Directory must be gone
            assert not bucket_dir.exists()
    
    def test_delete_bucket_removes_all_versions_from_db(self, app):
        """Bucket deletion must remove all object_versions records"""
        with app.app_context():
            bucket = BucketService.create_bucket("test-project", "versions-test")
            
            # Upload same object multiple times (create versions)
            for i in range(3):
                ObjectVersioningService.upload_object_versioned(
                    bucket_name="versions-test",
                    object_name="versioned.txt",
                    content=f"version {i}".encode(),
                    content_type="text/plain"
                )
            
            bucket_id = bucket.id
            
            # Verify versions exist
            versions_before = ObjectVersion.query.filter_by(bucket_id=bucket_id).count()
            assert versions_before == 3
            
            # Delete object (soft delete) then bucket
            ObjectVersioningService.delete_object_versioned(
                bucket_name="versions-test",
                object_name="versioned.txt"
            )
            BucketService.delete_bucket("versions-test")
            
            # All versions must be removed from database
            versions_after = ObjectVersion.query.filter_by(bucket_id=bucket_id).count()
            assert versions_after == 0
    
    def test_delete_bucket_removes_all_objects_from_db(self, app):
        """Bucket deletion must remove all objects records"""
        with app.app_context():
            bucket = BucketService.create_bucket("test-project", "objects-test")
            
            # Upload multiple objects
            for i in range(5):
                ObjectVersioningService.upload_object_versioned(
                    bucket_name="objects-test",
                    object_name=f"file{i}.txt",
                    content=f"content {i}".encode(),
                    content_type="text/plain"
                )
            
            bucket_id = bucket.id
            
            # Delete all objects
            for i in range(5):
                ObjectVersioningService.delete_object_versioned(
                    bucket_name="objects-test",
                    object_name=f"file{i}.txt"
                )
            
            # Delete bucket
            BucketService.delete_bucket("objects-test")
            
            # All object records must be gone
            objects_after = Object.query.filter_by(bucket_id=bucket_id).count()
            assert objects_after == 0


class TestMetadataCorrectness:
    """Test metadata returns correct bucket name instead of internal ID"""
    
    def test_object_metadata_shows_correct_bucket_name(self, app):
        """Object.to_dict() must return user-provided bucket name"""
        with app.app_context():
            bucket = BucketService.create_bucket("test-project", "my-bucket-name")
            
            obj = ObjectVersioningService.upload_object_versioned(
                bucket_name="my-bucket-name",
                object_name="test.txt",
                content=b"test content",
                content_type="text/plain"
            )
            
            metadata = obj.to_dict()
            
            # Must show bucket name, NOT internal ID
            assert metadata["bucket"] == "my-bucket-name"
            assert metadata["bucket"] != bucket.id
            
            # selfLink must use bucket name
            assert "/b/my-bucket-name/" in metadata["selfLink"]
            assert bucket.id not in metadata["selfLink"]
    
    def test_object_version_metadata_shows_correct_bucket_name(self, app):
        """ObjectVersion.to_dict() must return user-provided bucket name"""
        with app.app_context():
            bucket = BucketService.create_bucket("test-project", "versioned-bucket")
            
            # Create multiple versions
            for i in range(3):
                ObjectVersioningService.upload_object_versioned(
                    bucket_name="versioned-bucket",
                    object_name="versioned.txt",
                    content=f"version {i}".encode(),
                    content_type="text/plain"
                )
            
            # Get a specific version
            version = ObjectVersion.query.filter_by(
                bucket_id=bucket.id,
                name="versioned.txt",
                generation=2
            ).first()
            
            metadata = version.to_dict()
            
            # Must show bucket name
            assert metadata["bucket"] == "versioned-bucket"
            assert metadata["bucket"] != bucket.id
    
    def test_api_response_contains_correct_bucket_name(self, app, client):
        """API responses must contain correct bucket name"""
        with app.app_context():
            bucket = BucketService.create_bucket("test-project", "api-test-bucket")
        
        # Upload via API
        response = client.post(
            "/upload/storage/v1/b/api-test-bucket/o?uploadType=media&name=api-test.txt",
            data=b"test content",
            content_type="text/plain"
        )
        
        assert response.status_code == 200
        json_data = response.get_json()
        
        # Response must show bucket name
        assert json_data["bucket"] == "api-test-bucket"
        
        # Get metadata via API
        response = client.get("/storage/v1/b/api-test-bucket/o/api-test.txt")
        assert response.status_code == 200
        json_data = response.get_json()
        
        assert json_data["bucket"] == "api-test-bucket"


class TestCRC32CCorrectness:
    """Test CRC32C hash calculation correctness"""
    
    def test_crc32c_matches_google_implementation(self):
        """Our CRC32C must match google-crc32c library"""
        test_vectors = [
            b"",
            b"Hello, World!",
            b"The quick brown fox jumps over the lazy dog",
            b"A" * 1000,
            b"\x00\x01\x02\x03\x04\x05",
            b"GCS Emulator Test Data"
        ]
        
        for data in test_vectors:
            # Calculate using our implementation
            our_result = calculate_crc32c(data)
            
            # Calculate using Google's library directly
            checksum = google_crc32c.Checksum()
            checksum.update(data)
            expected_crc = checksum.crc32c
            expected_bytes = expected_crc.to_bytes(4, byteorder='big')
            expected_result = base64.b64encode(expected_bytes).decode('utf-8')
            
            assert our_result == expected_result, f"CRC32C mismatch for data: {data[:50]}"
    
    def test_uploaded_object_has_correct_crc32c(self, app):
        """Uploaded objects must have correct CRC32C in metadata"""
        with app.app_context():
            bucket = BucketService.create_bucket("test-project", "crc-test")
            
            test_content = b"Test content for CRC32C verification"
            
            obj = ObjectVersioningService.upload_object_versioned(
                bucket_name="crc-test",
                object_name="crc-test.txt",
                content=test_content,
                content_type="text/plain"
            )
            
            # Calculate expected CRC32C
            checksum = google_crc32c.Checksum()
            checksum.update(test_content)
            expected_crc = checksum.crc32c
            expected_bytes = expected_crc.to_bytes(4, byteorder='big')
            expected_b64 = base64.b64encode(expected_bytes).decode('utf-8')
            
            # Object must have correct CRC32C
            assert obj.crc32c_hash == expected_b64
    
    def test_crc32c_in_api_response(self, app, client):
        """API responses must include correct CRC32C checksums"""
        with app.app_context():
            BucketService.create_bucket("test-project", "api-crc-test")
        
        test_content = b"API CRC32C test content"
        
        # Upload via API
        response = client.post(
            "/upload/storage/v1/b/api-crc-test/o?uploadType=media&name=test.txt",
            data=test_content,
            content_type="text/plain"
        )
        
        assert response.status_code == 200
        json_data = response.get_json()
        
        # Calculate expected CRC32C
        checksum = google_crc32c.Checksum()
        checksum.update(test_content)
        expected_crc = checksum.crc32c
        expected_bytes = expected_crc.to_bytes(4, byteorder='big')
        expected_b64 = base64.b64encode(expected_bytes).decode('utf-8')
        
        assert json_data["crc32c"] == expected_b64
    
    def test_crc32c_not_equal_to_crc32(self):
        """CRC32C must be different from standard CRC32"""
        import zlib
        
        test_data = b"This is test data for CRC comparison"
        
        # Our CRC32C implementation
        crc32c_result = calculate_crc32c(test_data)
        
        # Standard CRC32 (incorrect)
        crc32_value = zlib.crc32(test_data)
        crc32_bytes = crc32_value.to_bytes(4, byteorder='big')
        crc32_b64 = base64.b64encode(crc32_bytes).decode('utf-8')
        
        # They should be different
        assert crc32c_result != crc32_b64, "CRC32C should not equal standard CRC32"


class TestPhase1Integration:
    """Integration tests for all Phase 1 fixes together"""
    
    def test_complete_workflow_with_all_fixes(self, app, client):
        """Test complete workflow: upload, verify metadata, delete bucket"""
        with app.app_context():
            # Create bucket
            bucket = BucketService.create_bucket("test-project", "integration-test")
            
            # Try invalid upload (should fail due to path traversal)
            with pytest.raises(ValueError, match="not allowed"):
                ObjectVersioningService.upload_object_versioned(
                    bucket_name="integration-test",
                    object_name="../evil.txt",
                    content=b"evil",
                    content_type="text/plain"
                )
            
            # Valid upload
            obj = ObjectVersioningService.upload_object_versioned(
                bucket_name="integration-test",
                object_name="valid/file.txt",
                content=b"valid content",
                content_type="text/plain"
            )
            
            # Verify metadata has correct bucket name
            metadata = obj.to_dict()
            assert metadata["bucket"] == "integration-test"
            
            # Verify CRC32C is correct
            checksum = google_crc32c.Checksum()
            checksum.update(b"valid content")
            expected_crc = checksum.crc32c
            expected_bytes = expected_crc.to_bytes(4, byteorder='big')
            expected_b64 = base64.b64encode(expected_bytes).decode('utf-8')
            assert obj.crc32c_hash == expected_b64
            
            # Delete object
            ObjectVersioningService.delete_object_versioned(
                bucket_name="integration-test",
                object_name="valid/file.txt"
            )
            
            # Delete bucket (hard delete should work)
            result = BucketService.delete_bucket("integration-test")
            assert result is True
            
            # Verify everything is cleaned up
            storage_path = os.getenv("STORAGE_PATH", "./storage")
            bucket_dir = Path(storage_path) / bucket.id
            assert not bucket_dir.exists()
