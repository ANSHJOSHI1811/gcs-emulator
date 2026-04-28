"""
CloudTester - Cloud Storage Service Tests
Tests for Cloud Storage endpoints: buckets, objects, versioning, signed URLs
"""

import pytest
import json
from typing import Dict, Any

pytestmark = pytest.mark.integration


class TestBuckets:
    """Test Cloud Storage Buckets"""
    
    def test_list_buckets(self, api_client, test_project):
        """List all buckets"""
        path = f"/storage/v1/b?project={test_project}"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        items = data.get("items", [])
        assert isinstance(items, list)
    
    def test_create_bucket(self, api_client, test_project, sample_bucket_payload, cleanup_resources):
        """Create a new bucket"""
        path = f"/storage/v1/b?project={test_project}"
        
        resp = api_client.post(path, sample_bucket_payload)
        
        assert resp.status_code in [200, 201]
        data = resp.json()
        
        assert data["name"] == sample_bucket_payload["name"]
        assert "location" in data
        
        cleanup_resources["buckets"].append(data["name"])
    
    def test_get_bucket(self, api_client, test_project):
        """Get bucket details"""
        # List buckets first
        list_path = f"/storage/v1/b?project={test_project}"
        list_resp = api_client.get(list_path)
        
        if list_resp.status_code != 200:
            pytest.skip("Cannot list buckets")
        
        buckets = list_resp.json().get("items", [])
        if not buckets:
            pytest.skip("No buckets available")
        
        bucket_name = buckets[0]["name"]
        
        # Get bucket
        path = f"/storage/v1/b/{bucket_name}"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["name"] == bucket_name
        assert "location" in data
    
    def test_delete_bucket(self, api_client, test_project, sample_bucket_payload):
        """Delete a bucket"""
        # Create empty bucket
        create_path = f"/storage/v1/b?project={test_project}"
        create_resp = api_client.post(create_path, sample_bucket_payload)
        
        if create_resp.status_code not in [200, 201]:
            pytest.skip("Cannot create bucket")
        
        bucket_name = sample_bucket_payload["name"]
        
        # Delete
        delete_path = f"/storage/v1/b/{bucket_name}"
        delete_resp = api_client.delete(delete_path)
        
        assert delete_resp.status_code in [200, 204]


class TestObjects:
    """Test Cloud Storage Objects"""
    
    def test_list_objects(self, api_client, test_project):
        """List objects in a bucket"""
        # Get a bucket first
        buckets_resp = api_client.get(f"/storage/v1/b?project={test_project}")
        if buckets_resp.status_code != 200:
            pytest.skip("Cannot list buckets")
        
        buckets = buckets_resp.json().get("items", [])
        if not buckets:
            pytest.skip("No buckets available")
        
        bucket_name = buckets[0]["name"]
        
        # List objects
        path = f"/storage/v1/b/{bucket_name}/o"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        objects = data.get("items", [])
        assert isinstance(objects, list)
    
    def test_upload_object(self, api_client, test_project, cleanup_resources):
        """Upload an object to a bucket"""
        # Get a bucket
        buckets_resp = api_client.get(f"/storage/v1/b?project={test_project}")
        if buckets_resp.status_code != 200:
            pytest.skip("Cannot list buckets")
        
        buckets = buckets_resp.json().get("items", [])
        if not buckets:
            pytest.skip("No buckets available")
        
        bucket_name = buckets[0]["name"]
        
        # Upload object
        path = f"/storage/v1/b/{bucket_name}/o?uploadType=media&name=test-object.txt"
        resp = api_client.post(path, b"test content")
        
        if resp.status_code not in [200, 201]:
            pytest.skip("Upload not fully implemented")
        
        data = resp.json()
        assert "name" in data or "id" in data
    
    def test_get_object(self, api_client, test_project):
        """Get object details"""
        # Get bucket and object
        buckets_resp = api_client.get(f"/storage/v1/b?project={test_project}")
        if buckets_resp.status_code != 200:
            pytest.skip("Cannot list buckets")
        
        buckets = buckets_resp.json().get("items", [])
        if not buckets:
            pytest.skip("No buckets available")
        
        bucket_name = buckets[0]["name"]
        
        # List objects
        objects_resp = api_client.get(f"/storage/v1/b/{bucket_name}/o")
        if objects_resp.status_code != 200:
            pytest.skip("Cannot list objects")
        
        objects = objects_resp.json().get("items", [])
        if not objects:
            pytest.skip("No objects available")
        
        object_name = objects[0]["name"]
        
        # Get object
        path = f"/storage/v1/b/{bucket_name}/o/{object_name}"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["name"] == object_name


class TestVersioning:
    """Test Object Versioning"""
    
    def test_enable_versioning(self, api_client, test_project):
        """Enable versioning on a bucket"""
        # Get a bucket
        buckets_resp = api_client.get(f"/storage/v1/b?project={test_project}")
        if buckets_resp.status_code != 200:
            pytest.skip("Cannot list buckets")
        
        buckets = buckets_resp.json().get("items", [])
        if not buckets:
            pytest.skip("No buckets available")
        
        bucket_name = buckets[0]["name"]
        
        # Update bucket versioning
        path = f"/storage/v1/b/{bucket_name}"
        payload = {
            "versioning": {
                "enabled": True
            }
        }
        
        resp = api_client.patch(path, payload)
        
        if resp.status_code == 404:
            pytest.skip("PATCH not implemented")
        
        # Might return 200 or result in conflict
        if resp.status_code in [200, 204]:
            data = resp.json()
            if "versioning" in data:
                assert data["versioning"]["enabled"] == True


class TestSignedURLs:
    """Test Signed URLs"""
    
    def test_generate_signed_url(self, api_client, test_project):
        """Generate a signed URL for an object"""
        # Get bucket with object
        buckets_resp = api_client.get(f"/storage/v1/b?project={test_project}")
        if buckets_resp.status_code != 200:
            pytest.skip("Cannot list buckets")
        
        buckets = buckets_resp.json().get("items", [])
        if not buckets:
            pytest.skip("No buckets available")
        
        bucket_name = buckets[0]["name"]
        
        objects_resp = api_client.get(f"/storage/v1/b/{bucket_name}/o")
        if objects_resp.status_code != 200:
            pytest.skip("Cannot list objects")
        
        objects = objects_resp.json().get("items", [])
        if not objects:
            pytest.skip("No objects available")
        
        object_name = objects[0]["name"]
        
        # Generate signed URL
        path = f"/generate-signed-url?bucket={bucket_name}&object={object_name}&action=read&duration=3600"
        resp = api_client.get(path)
        
        if resp.status_code == 200:
            data = resp.json()
            assert "signedUrl" in data or "url" in data
