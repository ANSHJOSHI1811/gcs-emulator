"""
Tests for Multipart Upload functionality

Tests cover:
1. Multipart parser utility functions
2. Multipart upload endpoint
3. SDK integration with blob.upload_from_filename()
"""
import pytest
import json
from app.utils.multipart import (
    extract_boundary,
    parse_multipart_body,
    create_multipart_body,
    MultipartParseError,
    MultipartUploadData
)


class TestMultipartParser:
    """Tests for multipart parsing utility functions."""
    
    def test_extract_boundary_basic(self):
        """Test extracting boundary from standard Content-Type header."""
        content_type = "multipart/related; boundary=----=_Part_0_123456"
        boundary = extract_boundary(content_type)
        assert boundary == "----=_Part_0_123456"
    
    def test_extract_boundary_with_quotes(self):
        """Test extracting boundary with quoted value."""
        content_type = 'multipart/related; boundary="boundary_string"'
        boundary = extract_boundary(content_type)
        assert boundary == "boundary_string"
    
    def test_extract_boundary_complex(self):
        """Test extracting boundary from SDK-generated headers."""
        # Google SDK often generates complex boundaries
        content_type = "multipart/related; boundary=================8888888888888=="
        boundary = extract_boundary(content_type)
        assert boundary == "================8888888888888=="
    
    def test_extract_boundary_missing(self):
        """Test error when boundary is missing."""
        with pytest.raises(MultipartParseError):
            extract_boundary("multipart/related")
    
    def test_extract_boundary_wrong_type(self):
        """Test error for non-multipart Content-Type."""
        with pytest.raises(MultipartParseError):
            extract_boundary("application/json")
    
    def test_extract_boundary_empty(self):
        """Test error for empty Content-Type."""
        with pytest.raises(MultipartParseError):
            extract_boundary("")
    
    def test_parse_multipart_body_basic(self):
        """Test parsing a basic multipart body."""
        boundary = "boundary123"
        body = b"""--boundary123\r
Content-Type: application/json; charset=UTF-8\r
\r
{"name": "test-object.txt"}\r
--boundary123\r
Content-Type: text/plain\r
\r
Hello, World!\r
--boundary123--\r
"""
        result = parse_multipart_body(body, boundary)
        
        assert isinstance(result, MultipartUploadData)
        assert result.object_name == "test-object.txt"
        assert result.content == b"Hello, World!"
        assert result.content_type == "text/plain"
    
    def test_parse_multipart_body_binary_content(self):
        """Test parsing multipart body with binary content."""
        boundary = "boundary123"
        binary_content = b"\x00\x01\x02\x03\xff\xfe\xfd"
        
        body = b"--boundary123\r\n"
        body += b"Content-Type: application/json\r\n\r\n"
        body += b'{"name": "binary.bin"}\r\n'
        body += b"--boundary123\r\n"
        body += b"Content-Type: application/octet-stream\r\n\r\n"
        body += binary_content
        body += b"\r\n--boundary123--\r\n"
        
        result = parse_multipart_body(body, boundary)
        
        assert result.object_name == "binary.bin"
        assert result.content == binary_content
        assert result.content_type == "application/octet-stream"
    
    def test_parse_multipart_body_with_content_type_in_metadata(self):
        """Test that contentType from metadata is used if not in part headers."""
        boundary = "test-boundary"
        body = b"""--test-boundary\r
Content-Type: application/json\r
\r
{"name": "doc.pdf", "contentType": "application/pdf"}\r
--test-boundary\r
\r
PDF content here\r
--test-boundary--\r
"""
        result = parse_multipart_body(body, boundary)
        
        assert result.object_name == "doc.pdf"
        assert result.content_type == "application/pdf"
    
    def test_parse_multipart_body_missing_name(self):
        """Test error when name is missing from metadata."""
        boundary = "boundary123"
        body = b"""--boundary123\r
Content-Type: application/json\r
\r
{"contentType": "text/plain"}\r
--boundary123\r
Content-Type: text/plain\r
\r
content\r
--boundary123--\r
"""
        with pytest.raises(MultipartParseError) as exc_info:
            parse_multipart_body(body, boundary)
        assert "name" in str(exc_info.value).lower()
    
    def test_parse_multipart_body_single_part(self):
        """Test error when body has only one part."""
        boundary = "boundary123"
        body = b"""--boundary123\r
Content-Type: application/json\r
\r
{"name": "test.txt"}\r
--boundary123--\r
"""
        with pytest.raises(MultipartParseError):
            parse_multipart_body(body, boundary)
    
    def test_create_multipart_body(self):
        """Test creating multipart body for testing."""
        content = b"Test file content"
        body, content_type = create_multipart_body(
            object_name="my-file.txt",
            content=content,
            content_type="text/plain"
        )
        
        assert b"my-file.txt" in body
        assert content in body
        assert "multipart/related" in content_type
        assert "boundary=" in content_type
        
        # Verify it can be parsed back
        boundary = extract_boundary(content_type)
        parsed = parse_multipart_body(body, boundary)
        
        assert parsed.object_name == "my-file.txt"
        assert parsed.content == content
        assert parsed.content_type == "text/plain"
    
    def test_roundtrip_with_metadata(self):
        """Test creating and parsing with additional metadata."""
        content = b"Some content"
        metadata = {"cacheControl": "no-cache", "customKey": "customValue"}
        
        body, content_type = create_multipart_body(
            object_name="meta-test.txt",
            content=content,
            content_type="text/plain",
            metadata=metadata
        )
        
        boundary = extract_boundary(content_type)
        parsed = parse_multipart_body(body, boundary)
        
        assert parsed.object_name == "meta-test.txt"
        assert parsed.metadata.get("cacheControl") == "no-cache"
        assert parsed.metadata.get("customKey") == "customValue"


class TestMultipartUploadEndpoint:
    """Tests for the multipart upload HTTP endpoint."""
    
    def test_multipart_upload_success(self, client, runner):
        """Test successful multipart upload."""
        # Create bucket first
        bucket_name = "multipart-test-bucket"
        client.post(f"/storage/v1/b?project=test-project",
                   json={"name": bucket_name})
        
        # Create multipart request
        content = b"Hello from multipart upload!"
        body, content_type = create_multipart_body(
            object_name="multipart-test.txt",
            content=content,
            content_type="text/plain"
        )
        
        # Upload via multipart
        response = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=multipart",
            data=body,
            headers={"Content-Type": content_type}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "multipart-test.txt"
        # Bucket name in response may have unique suffix
        assert data["bucket"].startswith(bucket_name)
        assert data["size"] == str(len(content))
        assert "generation" in data
        assert "metageneration" in data
    
    def test_multipart_upload_and_download(self, client, runner):
        """Test multipart upload followed by download."""
        bucket_name = "multipart-dl-bucket"
        client.post(f"/storage/v1/b?project=test-project",
                   json={"name": bucket_name})
        
        # Upload
        content = b"Content to download after multipart upload"
        body, content_type = create_multipart_body(
            object_name="download-me.txt",
            content=content,
            content_type="text/plain"
        )
        
        response = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=multipart",
            data=body,
            headers={"Content-Type": content_type}
        )
        assert response.status_code == 200
        
        # Download
        response = client.get(
            f"/storage/v1/b/{bucket_name}/o/download-me.txt?alt=media"
        )
        assert response.status_code == 200
        assert response.data == content
    
    def test_multipart_upload_binary_file(self, client, runner):
        """Test multipart upload with binary content."""
        bucket_name = "multipart-binary-bucket"
        client.post(f"/storage/v1/b?project=test-project",
                   json={"name": bucket_name})
        
        # Binary content
        binary_content = bytes(range(256))  # All byte values
        body, content_type = create_multipart_body(
            object_name="binary.dat",
            content=binary_content,
            content_type="application/octet-stream"
        )
        
        # Upload
        response = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=multipart",
            data=body,
            headers={"Content-Type": content_type}
        )
        assert response.status_code == 200
        
        # Download and verify
        response = client.get(
            f"/storage/v1/b/{bucket_name}/o/binary.dat?alt=media"
        )
        assert response.status_code == 200
        assert response.data == binary_content
    
    def test_multipart_upload_versioning(self, client, runner):
        """Test that multipart uploads create new generations."""
        bucket_name = "multipart-version-bucket"
        client.post(f"/storage/v1/b?project=test-project",
                   json={"name": bucket_name})
        
        # First upload
        body1, ct1 = create_multipart_body("versioned.txt", b"Version 1")
        response1 = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=multipart",
            data=body1,
            headers={"Content-Type": ct1}
        )
        assert response1.status_code == 200
        gen1 = int(response1.get_json()["generation"])
        
        # Second upload (same name)
        body2, ct2 = create_multipart_body("versioned.txt", b"Version 2")
        response2 = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=multipart",
            data=body2,
            headers={"Content-Type": ct2}
        )
        assert response2.status_code == 200
        gen2 = int(response2.get_json()["generation"])
        
        # Second upload should have higher generation
        assert gen2 > gen1
    
    def test_multipart_upload_with_preconditions(self, client, runner):
        """Test multipart upload with precondition headers."""
        bucket_name = "multipart-precond-bucket"
        client.post(f"/storage/v1/b?project=test-project",
                   json={"name": bucket_name})
        
        # Upload first version
        body1, ct1 = create_multipart_body("precond.txt", b"Original")
        response1 = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=multipart",
            data=body1,
            headers={"Content-Type": ct1}
        )
        gen1 = int(response1.get_json()["generation"])
        
        # Upload with correct generation precondition (should succeed)
        body2, ct2 = create_multipart_body("precond.txt", b"Updated")
        response2 = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=multipart&ifGenerationMatch={gen1}",
            data=body2,
            headers={"Content-Type": ct2}
        )
        assert response2.status_code == 200
        
        # Upload with wrong generation precondition (should fail)
        body3, ct3 = create_multipart_body("precond.txt", b"Should fail")
        response3 = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=multipart&ifGenerationMatch={gen1}",
            data=body3,
            headers={"Content-Type": ct3}
        )
        assert response3.status_code == 412  # Precondition Failed
    
    def test_multipart_upload_bucket_not_found(self, client, runner):
        """Test multipart upload to non-existent bucket."""
        body, ct = create_multipart_body("test.txt", b"content")
        response = client.post(
            "/upload/storage/v1/b/nonexistent-bucket/o?uploadType=multipart",
            data=body,
            headers={"Content-Type": ct}
        )
        assert response.status_code == 404
    
    def test_multipart_upload_invalid_name(self, client, runner):
        """Test multipart upload with invalid object name (empty or with newlines)."""
        bucket_name = "multipart-invalid-bucket"
        client.post(f"/storage/v1/b?project=test-project",
                   json={"name": bucket_name})
        
        # Object names cannot contain newlines
        body, ct = create_multipart_body("test\nfile.txt", b"content")
        response = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=multipart",
            data=body,
            headers={"Content-Type": ct}
        )
        assert response.status_code == 400
    
    def test_multipart_upload_missing_boundary(self, client, runner):
        """Test multipart upload without boundary in Content-Type."""
        bucket_name = "multipart-noboundary-bucket"
        client.post(f"/storage/v1/b?project=test-project",
                   json={"name": bucket_name})
        
        response = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=multipart",
            data=b"some data",
            headers={"Content-Type": "multipart/related"}  # Missing boundary
        )
        assert response.status_code == 400
        assert "boundary" in response.get_json()["error"]["message"].lower()
    
    def test_multipart_upload_empty_body(self, client, runner):
        """Test multipart upload with empty body."""
        bucket_name = "multipart-empty-bucket"
        client.post(f"/storage/v1/b?project=test-project",
                   json={"name": bucket_name})
        
        response = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=multipart",
            data=b"",
            headers={"Content-Type": "multipart/related; boundary=test"}
        )
        assert response.status_code == 400


class TestMediaUploadStillWorks:
    """Ensure media upload still works after multipart refactor."""
    
    def test_media_upload_basic(self, client, runner):
        """Test basic media upload still works."""
        bucket_name = "media-still-works-bucket"
        client.post(f"/storage/v1/b?project=test-project",
                   json={"name": bucket_name})
        
        response = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=media&name=test.txt",
            data=b"Media upload content",
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code == 200
        assert response.get_json()["name"] == "test.txt"
    
    def test_media_upload_requires_name_param(self, client, runner):
        """Test that media upload still requires name parameter."""
        bucket_name = "media-name-required-bucket"
        client.post(f"/storage/v1/b?project=test-project",
                   json={"name": bucket_name})
        
        response = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=media",  # Missing name
            data=b"content",
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code == 400
        assert "name" in response.get_json()["error"]["message"].lower()
    
    def test_unsupported_upload_type(self, client, runner):
        """Test that unsupported upload types return proper error."""
        bucket_name = "unsupported-type-bucket"
        client.post(f"/storage/v1/b?project=test-project",
                   json={"name": bucket_name})
        
        response = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=resumable",
            data=b"content"
        )
        
        assert response.status_code == 400
        assert "resumable" in response.get_json()["error"]["message"].lower()
        assert "multipart" in response.get_json()["error"]["message"].lower()
