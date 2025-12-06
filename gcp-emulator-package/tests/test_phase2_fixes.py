"""
Phase 2 Tests - GCS Compatibility Improvements

Tests for:
1. GCS-Compatible Object Metadata (RFC3339, proper field names)
2. Aligned Error Codes & Error Schema (404, 409, 412 responses)
3. Versioning Metadata Consistency (deletion promotes correctly)
4. List & Filtering Behavior (correct response structure)
"""
import pytest
import json
import re
from datetime import datetime


class TestPhase2GCSMetadata:
    """Test 1: GCS-Compatible Object Metadata"""
    
    def test_object_metadata_bucket_name_not_uuid(self, client, setup_bucket):
        """Verify 'bucket' field shows bucket name, not internal UUID"""
        bucket_name = setup_bucket
        
        # Upload an object
        response = client.post(
            f"/storage/v1/b/{bucket_name}/o?name=test-object.txt",
            data=b"test content",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["bucket"] == bucket_name
        assert "-" in data["bucket"]  # Should be bucket name, not UUID format
        # Bucket name should not look like UUID (no long hex strings)
        assert not re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}', data["bucket"])
    
    def test_object_metadata_selflink_format(self, client, setup_bucket):
        """Verify selfLink follows GCS format: /storage/v1/b/{bucket}/o/{object}"""
        bucket_name = setup_bucket
        object_name = "test/path/file.txt"
        
        response = client.post(
            f"/storage/v1/b/{bucket_name}/o?name={object_name}",
            data=b"content",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 200
        
        data = response.get_json()
        expected_selflink = f"/storage/v1/b/{bucket_name}/o/{object_name}"
        assert data["selfLink"] == expected_selflink
    
    def test_object_metadata_rfc3339_timestamps(self, client, setup_bucket):
        """Verify timestamps follow RFC3339 format: YYYY-MM-DDTHH:MM:SS.sssZ"""
        bucket_name = setup_bucket
        
        response = client.post(
            f"/storage/v1/b/{bucket_name}/o?name=timestamp-test.txt",
            data=b"content",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 200
        
        data = response.get_json()
        
        # Check timeCreated format
        assert "timeCreated" in data
        time_created = data["timeCreated"]
        # RFC3339 format: 2025-12-05T12:34:56.789Z
        rfc3339_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$'
        assert re.match(rfc3339_pattern, time_created), f"timeCreated '{time_created}' doesn't match RFC3339"
        
        # Check updated format
        assert "updated" in data
        updated = data["updated"]
        assert re.match(rfc3339_pattern, updated), f"updated '{updated}' doesn't match RFC3339"
        
        # Verify parseable by Python datetime
        parsed = datetime.strptime(time_created, '%Y-%m-%dT%H:%M:%S.%fZ')
        assert isinstance(parsed, datetime)
    
    def test_bucket_metadata_rfc3339_timestamps(self, client, setup_bucket):
        """Verify bucket timestamps follow RFC3339 format"""
        bucket_name = setup_bucket
        
        response = client.get(f"/storage/v1/b/{bucket_name}")
        assert response.status_code == 200
        
        data = response.get_json()
        rfc3339_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$'
        
        assert "timeCreated" in data
        assert re.match(rfc3339_pattern, data["timeCreated"])
        
        assert "updated" in data
        assert re.match(rfc3339_pattern, data["updated"])
    
    def test_bucket_id_is_bucket_name(self, client, setup_bucket):
        """Verify bucket 'id' field shows bucket name (GCS compatibility)"""
        bucket_name = setup_bucket
        
        response = client.get(f"/storage/v1/b/{bucket_name}")
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["id"] == bucket_name
        assert data["name"] == bucket_name


class TestPhase2ErrorSchema:
    """Test 2: Aligned Error Codes & Error Schema"""
    
    def test_404_bucket_not_found_structure(self, client):
        """Verify 404 error follows GCS JSON schema"""
        response = client.get("/storage/v1/b/nonexistent-bucket-12345")
        assert response.status_code == 404
        
        data = response.get_json()
        assert "error" in data
        error = data["error"]
        
        # Must have code, message, errors array
        assert "code" in error
        assert error["code"] == 404
        assert "message" in error
        assert "errors" in error
        assert isinstance(error["errors"], list)
        assert len(error["errors"]) > 0
        
        # First error must have message, domain, reason
        first_error = error["errors"][0]
        assert "message" in first_error
        assert "domain" in first_error
        assert first_error["domain"] == "global"
        assert "reason" in first_error
        assert first_error["reason"] == "notFound"
    
    def test_404_object_not_found_structure(self, client, setup_bucket):
        """Verify 404 for missing object follows GCS schema"""
        bucket_name = setup_bucket
        
        response = client.get(f"/storage/v1/b/{bucket_name}/o/nonexistent.txt")
        assert response.status_code == 404
        
        data = response.get_json()
        assert "error" in data
        error = data["error"]
        assert error["code"] == 404
        assert "errors" in error
        assert error["errors"][0]["reason"] == "notFound"
    
    def test_409_conflict_structure(self, client, setup_project):
        """Verify 409 conflict error follows GCS schema"""
        project_id = setup_project
        bucket_name = "conflict-test-bucket"
        
        # Create bucket
        response1 = client.post(
            f"/storage/v1/b?project={project_id}",
            json={"name": bucket_name},
            headers={"Content-Type": "application/json"}
        )
        assert response1.status_code == 201
        
        # Try creating same bucket again
        response2 = client.post(
            f"/storage/v1/b?project={project_id}",
            json={"name": bucket_name},
            headers={"Content-Type": "application/json"}
        )
        assert response2.status_code == 409
        
        data = response2.get_json()
        assert "error" in data
        error = data["error"]
        assert error["code"] == 409
        assert "errors" in error
        assert error["errors"][0]["reason"] == "conflict"
    
    def test_412_precondition_failed_structure(self, client, setup_bucket):
        """Verify 412 precondition failed error follows GCS schema"""
        bucket_name = setup_bucket
        
        # Upload object with precondition that will fail
        response = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=media&name=test.txt&ifGenerationMatch=999",
            data=b"content",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 412
        
        data = response.get_json()
        assert "error" in data
        error = data["error"]
        assert error["code"] == 412
        assert "errors" in error
        assert error["errors"][0]["reason"] == "conditionNotMet"
    
    def test_400_invalid_argument_structure(self, client, setup_bucket):
        """Verify 400 bad request error follows GCS schema"""
        bucket_name = setup_bucket
        
        # POST without 'name' parameter
        response = client.post(
            f"/storage/v1/b/{bucket_name}/o",
            data=b"content",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 400
        
        data = response.get_json()
        assert "error" in data
        error = data["error"]
        assert error["code"] == 400
        assert "errors" in error
        assert error["errors"][0]["reason"] == "invalid"


class TestPhase2VersioningConsistency:
    """Test 3: Versioning Metadata Consistency"""
    
    def test_delete_latest_promotes_previous(self, client, setup_bucket_with_versioning):
        """After deleting latest version, previous version becomes latest"""
        bucket_name = setup_bucket_with_versioning
        object_name = "versioned-object.txt"
        
        # Upload version 1
        resp1 = client.post(
            f"/storage/v1/b/{bucket_name}/o?name={object_name}",
            data=b"version 1 content",
            headers={"Content-Type": "text/plain"}
        )
        assert resp1.status_code == 200
        gen1 = int(resp1.get_json()["generation"])
        
        # Upload version 2
        resp2 = client.post(
            f"/storage/v1/b/{bucket_name}/o?name={object_name}",
            data=b"version 2 content",
            headers={"Content-Type": "text/plain"}
        )
        assert resp2.status_code == 200
        gen2 = int(resp2.get_json()["generation"])
        assert gen2 > gen1
        
        # Delete version 2 (latest)
        del_resp = client.delete(f"/storage/v1/b/{bucket_name}/o/{object_name}?generation={gen2}")
        assert del_resp.status_code == 204
        
        # Get object metadata - should now show version 1 as latest
        get_resp = client.get(f"/storage/v1/b/{bucket_name}/o/{object_name}")
        assert get_resp.status_code == 200
        
        data = get_resp.get_json()
        assert int(data["generation"]) == gen1
        assert data["size"] == "17"  # "version 1 content"
    
    def test_delete_all_versions_removes_object(self, client, setup_bucket_with_versioning):
        """After deleting all versions, object disappears"""
        bucket_name = setup_bucket_with_versioning
        object_name = "delete-all-test.txt"
        
        # Upload 2 versions
        resp1 = client.post(
            f"/storage/v1/b/{bucket_name}/o?name={object_name}",
            data=b"v1",
            headers={"Content-Type": "text/plain"}
        )
        assert resp1.status_code == 200
        gen1 = int(resp1.get_json()["generation"])
        
        resp2 = client.post(
            f"/storage/v1/b/{bucket_name}/o?name={object_name}",
            data=b"v2",
            headers={"Content-Type": "text/plain"}
        )
        assert resp2.status_code == 200
        gen2 = int(resp2.get_json()["generation"])
        
        # Delete version 2
        client.delete(f"/storage/v1/b/{bucket_name}/o/{object_name}?generation={gen2}")
        
        # Delete version 1
        client.delete(f"/storage/v1/b/{bucket_name}/o/{object_name}?generation={gen1}")
        
        # Object should not exist anymore
        get_resp = client.get(f"/storage/v1/b/{bucket_name}/o/{object_name}")
        assert get_resp.status_code == 404
    
    def test_is_latest_flag_accurate(self, client, setup_bucket_with_versioning):
        """Verify is_latest flag remains accurate after operations"""
        bucket_name = setup_bucket_with_versioning
        object_name = "latest-flag-test.txt"
        
        # Upload 3 versions
        for i in range(1, 4):
            resp = client.post(
                f"/storage/v1/b/{bucket_name}/o?name={object_name}",
                data=f"version {i}".encode(),
                headers={"Content-Type": "text/plain"}
            )
            assert resp.status_code == 200
        
        # Get latest version
        latest_resp = client.get(f"/storage/v1/b/{bucket_name}/o/{object_name}")
        assert latest_resp.status_code == 200
        latest_gen = int(latest_resp.get_json()["generation"])
        assert latest_gen == 3
        
        # Delete latest
        client.delete(f"/storage/v1/b/{bucket_name}/o/{object_name}?generation=3")
        
        # New latest should be generation 2
        new_latest_resp = client.get(f"/storage/v1/b/{bucket_name}/o/{object_name}")
        assert new_latest_resp.status_code == 200
        assert int(new_latest_resp.get_json()["generation"]) == 2


class TestPhase2ListBehavior:
    """Test 4: List & Filtering Response Structure"""
    
    def test_list_empty_bucket_structure(self, client, setup_bucket):
        """Listing empty bucket returns correct structure"""
        bucket_name = setup_bucket
        
        response = client.get(f"/storage/v1/b/{bucket_name}/o")
        assert response.status_code == 200
        
        data = response.get_json()
        assert "kind" in data
        assert data["kind"] == "storage#objects"
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 0
    
    def test_list_objects_structure(self, client, setup_bucket):
        """Listing objects returns correct structure"""
        bucket_name = setup_bucket
        
        # Upload some objects
        for i in range(3):
            client.post(
                f"/storage/v1/b/{bucket_name}/o?name=file{i}.txt",
                data=f"content {i}".encode(),
                headers={"Content-Type": "text/plain"}
            )
        
        response = client.get(f"/storage/v1/b/{bucket_name}/o")
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["kind"] == "storage#objects"
        assert "items" in data
        assert len(data["items"]) == 3
        
        # Each item should have proper GCS metadata
        for item in data["items"]:
            assert "kind" in item
            assert item["kind"] == "storage#object"
            assert "name" in item
            assert "bucket" in item
            assert item["bucket"] == bucket_name
            assert "generation" in item
            assert "metageneration" in item
    
    def test_list_buckets_structure(self, client, setup_project):
        """Listing buckets returns correct structure"""
        project_id = setup_project
        
        # Create a bucket
        client.post(
            f"/storage/v1/b?project={project_id}",
            json={"name": "test-list-bucket"},
            headers={"Content-Type": "application/json"}
        )
        
        response = client.get(f"/storage/v1/b?project={project_id}")
        assert response.status_code == 200
        
        data = response.get_json()
        assert "kind" in data
        assert data["kind"] == "storage#buckets"
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) >= 1
        
        # Each bucket should have proper structure
        for bucket in data["items"]:
            assert "name" in bucket
            assert "id" in bucket
            assert bucket["id"] == bucket["name"]  # Phase 2 fix
            assert "timeCreated" in bucket
            assert "updated" in bucket
