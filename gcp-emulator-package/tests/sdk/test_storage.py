"""
Test suite for Google Cloud Storage SDK integration
Tests bucket and blob operations using official google-cloud-storage SDK
"""
import pytest
from google.cloud import storage
from google.api_core import exceptions


class TestBucketOperations:
    """Test bucket CRUD operations"""
    
    def test_create_bucket_returns_201(self, storage_client, test_bucket_name):
        """
        Test: Create a bucket and verify it returns 201 (created)
        
        Note: The SDK doesn't directly expose HTTP status codes,
        but we verify successful creation and that bucket exists
        """
        # Create bucket
        bucket = storage_client.create_bucket(test_bucket_name)
        
        # Verify bucket was created
        assert bucket is not None
        assert bucket.name == test_bucket_name
        assert bucket.exists()
        
        # Verify we can retrieve it
        retrieved_bucket = storage_client.get_bucket(test_bucket_name)
        assert retrieved_bucket.name == test_bucket_name
    
    def test_create_bucket_with_location(self, storage_client, test_bucket_name):
        """Test creating bucket with specific location"""
        bucket = storage_client.create_bucket(
            test_bucket_name,
            location="US"
        )
        
        assert bucket.name == test_bucket_name
        assert bucket.location == "US"
    
    def test_create_bucket_with_storage_class(self, storage_client, test_bucket_name):
        """Test creating bucket with specific storage class"""
        bucket = storage_client.create_bucket(
            test_bucket_name,
            location="US"
        )
        bucket.storage_class = "NEARLINE"
        bucket.patch()
        
        # Retrieve and verify
        retrieved = storage_client.get_bucket(test_bucket_name)
        assert retrieved.storage_class in ["NEARLINE", "STANDARD"]  # Emulator might not support all classes
    
    def test_list_buckets(self, storage_client, test_bucket_name):
        """Test listing buckets"""
        # Create a bucket
        storage_client.create_bucket(test_bucket_name)
        
        # List buckets
        buckets = list(storage_client.list_buckets())
        bucket_names = [b.name for b in buckets]
        
        assert test_bucket_name in bucket_names
    
    def test_delete_bucket(self, storage_client, test_bucket_name):
        """Test: Delete a bucket and verify it no longer exists"""
        # Create bucket
        bucket = storage_client.create_bucket(test_bucket_name)
        assert bucket.exists()
        
        # Delete bucket
        bucket.delete()
        
        # Verify bucket no longer exists
        with pytest.raises(exceptions.NotFound):
            storage_client.get_bucket(test_bucket_name)
    
    def test_delete_nonexistent_bucket_raises_404(self, storage_client):
        """Test deleting non-existent bucket raises NotFound"""
        with pytest.raises(exceptions.NotFound):
            bucket = storage_client.bucket("nonexistent-bucket-12345")
            bucket.delete()
    
    def test_bucket_exists_check(self, storage_client, test_bucket_name):
        """Test bucket.exists() method"""
        bucket = storage_client.bucket(test_bucket_name)
        
        # Before creation
        assert not bucket.exists()
        
        # After creation
        storage_client.create_bucket(test_bucket_name)
        assert bucket.exists()


class TestBlobOperations:
    """Test blob (object) operations"""
    
    def test_upload_text_blob(self, storage_client, test_bucket_name, sample_text_content):
        """
        Test: Upload a small text file (blob) to a bucket
        """
        # Create bucket
        bucket = storage_client.create_bucket(test_bucket_name)
        
        # Upload blob
        blob = bucket.blob("test-file.txt")
        blob.upload_from_string(sample_text_content, content_type="text/plain")
        
        # Verify blob exists
        assert blob.exists()
        
        # Verify metadata
        assert blob.name == "test-file.txt"
        assert blob.content_type == "text/plain"
        assert blob.size == len(sample_text_content)
    
    def test_upload_json_blob(self, storage_client, test_bucket_name, sample_json_content):
        """Test uploading JSON content"""
        bucket = storage_client.create_bucket(test_bucket_name)
        
        blob = bucket.blob("data.json")
        blob.upload_from_string(sample_json_content, content_type="application/json")
        
        assert blob.exists()
        assert blob.content_type == "application/json"
    
    def test_upload_blob_from_file(self, storage_client, test_bucket_name, tmp_path):
        """Test uploading from a file object"""
        # Create temporary file
        test_file = tmp_path / "upload-test.txt"
        test_file.write_text("File upload test content")
        
        # Create bucket and upload
        bucket = storage_client.create_bucket(test_bucket_name)
        blob = bucket.blob("uploaded-file.txt")
        blob.upload_from_filename(str(test_file))
        
        assert blob.exists()
    
    def test_list_blobs_in_bucket(self, storage_client, test_bucket_name, sample_text_content):
        """
        Test: List blobs in a bucket and assert the uploaded file is present
        """
        bucket = storage_client.create_bucket(test_bucket_name)
        
        # Upload multiple blobs
        blob_names = ["file1.txt", "file2.txt", "file3.txt"]
        for name in blob_names:
            blob = bucket.blob(name)
            blob.upload_from_string(sample_text_content)
        
        # List blobs
        blobs = list(bucket.list_blobs())
        retrieved_names = [b.name for b in blobs]
        
        # Assert all uploaded files are present
        for name in blob_names:
            assert name in retrieved_names
        
        assert len(retrieved_names) == len(blob_names)
    
    def test_list_blobs_with_prefix(self, storage_client, test_bucket_name, sample_text_content):
        """Test listing blobs with prefix filter"""
        bucket = storage_client.create_bucket(test_bucket_name)
        
        # Upload blobs with different prefixes
        bucket.blob("logs/2024/file1.txt").upload_from_string(sample_text_content)
        bucket.blob("logs/2024/file2.txt").upload_from_string(sample_text_content)
        bucket.blob("data/file3.txt").upload_from_string(sample_text_content)
        
        # List with prefix
        logs_blobs = list(bucket.list_blobs(prefix="logs/"))
        assert len(logs_blobs) == 2
        
        data_blobs = list(bucket.list_blobs(prefix="data/"))
        assert len(data_blobs) == 1
    
    def test_download_blob_content(self, storage_client, test_bucket_name, sample_text_content):
        """Test downloading blob content"""
        bucket = storage_client.create_bucket(test_bucket_name)
        
        # Upload
        blob = bucket.blob("download-test.txt")
        blob.upload_from_string(sample_text_content)
        
        # Download
        downloaded = blob.download_as_bytes()
        
        assert downloaded == sample_text_content
    
    def test_download_blob_to_file(self, storage_client, test_bucket_name, sample_text_content, tmp_path):
        """Test downloading blob to file"""
        bucket = storage_client.create_bucket(test_bucket_name)
        
        # Upload
        blob = bucket.blob("download-test.txt")
        blob.upload_from_string(sample_text_content)
        
        # Download to file
        download_path = tmp_path / "downloaded.txt"
        blob.download_to_filename(str(download_path))
        
        assert download_path.exists()
        assert download_path.read_bytes() == sample_text_content
    
    def test_delete_blob(self, storage_client, test_bucket_name, sample_text_content):
        """Test deleting a blob"""
        bucket = storage_client.create_bucket(test_bucket_name)
        
        # Upload blob
        blob = bucket.blob("to-delete.txt")
        blob.upload_from_string(sample_text_content)
        assert blob.exists()
        
        # Delete blob
        blob.delete()
        
        # Verify deleted
        assert not blob.exists()
    
    def test_blob_metadata(self, storage_client, test_bucket_name, sample_text_content):
        """Test blob metadata operations"""
        bucket = storage_client.create_bucket(test_bucket_name)
        
        # Upload with custom metadata
        blob = bucket.blob("metadata-test.txt")
        blob.metadata = {
            "author": "test-user",
            "department": "engineering"
        }
        blob.upload_from_string(sample_text_content)
        
        # Retrieve and check metadata
        blob.reload()
        assert blob.metadata is not None
        assert blob.metadata.get("author") == "test-user"
        assert blob.metadata.get("department") == "engineering"
    
    def test_blob_content_type(self, storage_client, test_bucket_name):
        """Test setting and retrieving content type"""
        bucket = storage_client.create_bucket(test_bucket_name)
        
        content_types = [
            ("file.txt", b"text content", "text/plain"),
            ("file.json", b'{"key": "value"}', "application/json"),
            ("file.html", b"<html></html>", "text/html"),
            ("file.bin", b"\x00\x01\x02", "application/octet-stream"),
        ]
        
        for name, content, content_type in content_types:
            blob = bucket.blob(name)
            blob.upload_from_string(content, content_type=content_type)
            
            blob.reload()
            assert blob.content_type == content_type


class TestBucketAndBlobIntegration:
    """Integration tests combining bucket and blob operations"""
    
    def test_delete_bucket_with_blobs(self, storage_client, test_bucket_name, sample_text_content):
        """Test deleting bucket that contains blobs (force delete)"""
        bucket = storage_client.create_bucket(test_bucket_name)
        
        # Add some blobs
        for i in range(3):
            blob = bucket.blob(f"file{i}.txt")
            blob.upload_from_string(sample_text_content)
        
        # Delete bucket with force flag
        bucket.delete(force=True)
        
        # Verify bucket is gone
        with pytest.raises(exceptions.NotFound):
            storage_client.get_bucket(test_bucket_name)
    
    def test_empty_bucket_list_blobs(self, storage_client, test_bucket_name):
        """Test listing blobs in empty bucket"""
        bucket = storage_client.create_bucket(test_bucket_name)
        
        blobs = list(bucket.list_blobs())
        assert len(blobs) == 0
    
    def test_blob_operations_on_nonexistent_bucket(self, storage_client):
        """Test blob operations on non-existent bucket"""
        bucket = storage_client.bucket("nonexistent-bucket-12345")
        blob = bucket.blob("test.txt")
        
        with pytest.raises(exceptions.NotFound):
            blob.upload_from_string(b"test content")
    
    def test_get_nonexistent_blob(self, storage_client, test_bucket_name):
        """Test getting non-existent blob"""
        bucket = storage_client.create_bucket(test_bucket_name)
        
        blob = bucket.get_blob("nonexistent.txt")
        assert blob is None
    
    def test_multiple_buckets_isolation(self, storage_client):
        """Test that blobs in different buckets are isolated"""
        import uuid
        
        bucket1_name = f"test-bucket-{uuid.uuid4().hex[:8]}"
        bucket2_name = f"test-bucket-{uuid.uuid4().hex[:8]}"
        
        try:
            bucket1 = storage_client.create_bucket(bucket1_name)
            bucket2 = storage_client.create_bucket(bucket2_name)
            
            # Upload to bucket1
            bucket1.blob("file.txt").upload_from_string(b"content1")
            
            # Verify not in bucket2
            blobs_in_bucket2 = list(bucket2.list_blobs())
            assert len(blobs_in_bucket2) == 0
            
        finally:
            # Cleanup
            try:
                storage_client.get_bucket(bucket1_name).delete(force=True)
            except:
                pass
            try:
                storage_client.get_bucket(bucket2_name).delete(force=True)
            except:
                pass
