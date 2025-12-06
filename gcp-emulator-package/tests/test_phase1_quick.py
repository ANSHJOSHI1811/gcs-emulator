"""
Phase 1 Quick Verification Tests
Simplified tests to verify core fixes work
"""
import os
import pytest
import base64
import google_crc32c
from pathlib import Path


def test_crc32c_implementation():
    """Test CRC32C implementation matches Google's"""
    from app.utils.hashing import calculate_crc32c
    
    test_data = b"Hello, World!"
    
    # Our implementation
    our_result = calculate_crc32c(test_data)
    
    # Google's implementation
    checksum = google_crc32c.Checksum()
    checksum.update(test_data)
    expected_result = base64.b64encode(checksum.digest()).decode('utf-8')
    
    assert our_result == expected_result, f"CRC32C mismatch: {our_result} != {expected_result}"
    print("✓ CRC32C implementation correct")


def test_path_traversal_validation():
    """Test path traversal validation logic"""
    from app.services.object_versioning_service import ObjectVersioningService
    
    # These should raise ValueError
    malicious_names = [
        "../../etc/passwd",
        "../secret.txt",
        "folder/../../../x",
        "C:\\Windows\\system32\\file.txt",
        "/etc/passwd",
        "folder\\..\\evil.txt"
    ]
    
    for name in malicious_names:
        try:
            ObjectVersioningService._validate_object_name_for_path_traversal(name)
            assert False, f"Should have rejected: {name}"
        except ValueError as e:
            assert "not allowed" in str(e).lower() or "path traversal" in str(e).lower()
    
    # These should pass
    valid_names = [
        "normal/path/file.txt",
        "folder/subfolder/doc.pdf",
        "simple.txt"
    ]
    
    for name in valid_names:
        ObjectVersioningService._validate_object_name_for_path_traversal(name)
    
    print("✓ Path traversal validation working")


def test_metadata_bucket_name():
    """Test that Object.to_dict() returns bucket name not ID"""
    from app.models.object import Object
    from app.models.bucket import Bucket  
    from app.factory import create_app, db
    
    app = create_app()
    with app.app_context():
        # Create test bucket
        bucket = Bucket(
            id="test-bucket-abc123",
            project_id="test-project",
            name="my-actual-bucket-name",
            location="US",
            storage_class="STANDARD"
        )
        db.session.add(bucket)
        db.session.flush()
        
        # Create test object
        obj = Object(
            id="obj-1",
            bucket_id=bucket.id,
            name="test.txt",
            generation=1,
            size=100,
            content_type="text/plain"
        )
        db.session.add(obj)
        db.session.flush()
        
        # Check to_dict() returns bucket name
        metadata = obj.to_dict()
        
        assert metadata["bucket"] == "my-actual-bucket-name", f"Expected 'my-actual-bucket-name', got '{metadata['bucket']}'"
        assert "abc123" not in metadata["bucket"], "Internal ID should not appear in bucket field"
        assert "/b/my-actual-bucket-name/" in metadata["selfLink"], "selfLink should use bucket name"
        
        db.session.rollback()
    
    print("✓ Metadata returns correct bucket name")


if __name__ == "__main__":
    print("Running Phase 1 Quick Verification Tests...\n")
    
    test_crc32c_implementation()
    test_path_traversal_validation()
    test_metadata_bucket_name()
    
    print("\n✅ All quick verification tests passed!")
