"""
Comprehensive tests for new features:
1. Bucket name uniqueness (project_id, name)
2. Object Copy API
3. CORS configuration
4. Event delivery webhooks
5. Lifecycle rules engine
"""
import pytest
import requests
import json
import time
from pathlib import Path
from flask import Flask
from app.factory import create_app, db
from app.models.bucket import Bucket
from app.models.project import Project
from app.models.object import Object


@pytest.fixture
def app():
    """Create test Flask application"""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestBucketUniqueness:
    """Test bucket name uniqueness with (project_id, name) constraint"""
    
    def test_same_bucket_name_different_projects(self, client):
        """Test that same bucket name can exist in different projects"""
        # Create bucket in project1
        response1 = client.post(
            "/storage/v1/b?project=project1",
            json={"name": "test-bucket", "location": "US"}
        )
        assert response1.status_code == 201
        
        # Create same bucket name in project2 - should succeed
        response2 = client.post(
            "/storage/v1/b?project=project2",
            json={"name": "test-bucket", "location": "EU"}
        )
        assert response2.status_code == 201
        
        # Verify both exist
        data1 = response1.get_json()
        data2 = response2.get_json()
        assert data1["name"] == "test-bucket"
        assert data2["name"] == "test-bucket"
        assert data1["id"] != data2["id"]  # Different IDs
    
    def test_duplicate_bucket_in_same_project(self, client):
        """Test that duplicate bucket name in same project fails"""
        # Create bucket in project1
        response1 = client.post(
            "/storage/v1/b?project=project1",
            json={"name": "test-bucket", "location": "US"}
        )
        assert response1.status_code == 201
        
        # Try to create same bucket again in project1 - should fail
        response2 = client.post(
            "/storage/v1/b?project=project1",
            json={"name": "test-bucket", "location": "US"}
        )
        assert response2.status_code == 400
        assert "already exists" in response2.get_json()["error"]["message"]


class TestObjectCopy:
    """Test object copy API"""
    
    def test_same_bucket_copy(self, client):
        """Test copying object within the same bucket"""
        # Create bucket
        client.post("/storage/v1/b?project=test-project", json={"name": "copy-bucket"})
        
        # Upload source object
        client.post(
            "/storage/v1/b/copy-bucket/o?name=source.txt",
            data=b"test content",
            headers={"Content-Type": "text/plain"}
        )
        
        # Copy object
        response = client.post(
            "/storage/v1/b/copy-bucket/o/source.txt/copyTo/b/copy-bucket/o/destination.txt"
        )
        assert response.status_code == 201
        
        data = response.get_json()
        assert data["name"] == "destination.txt"
        assert data["size"] == 12
        
        # Verify both objects exist
        list_response = client.get("/storage/v1/b/copy-bucket/o")
        items = list_response.get_json()["items"]
        assert len(items) == 2
        assert any(obj["name"] == "source.txt" for obj in items)
        assert any(obj["name"] == "destination.txt" for obj in items)
    
    def test_cross_bucket_copy(self, client):
        """Test copying object across buckets"""
        # Create two buckets
        client.post("/storage/v1/b?project=test-project", json={"name": "bucket-a"})
        client.post("/storage/v1/b?project=test-project", json={"name": "bucket-b"})
        
        # Upload source object in bucket-a
        client.post(
            "/storage/v1/b/bucket-a/o?name=file.txt",
            data=b"cross bucket",
            headers={"Content-Type": "text/plain"}
        )
        
        # Copy to bucket-b
        response = client.post(
            "/storage/v1/b/bucket-a/o/file.txt/copyTo/b/bucket-b/o/copied-file.txt"
        )
        assert response.status_code == 201
        
        # Verify destination exists
        get_response = client.get("/storage/v1/b/bucket-b/o/copied-file.txt")
        assert get_response.status_code == 200
        assert get_response.get_json()["name"] == "copied-file.txt"
    
    def test_copy_preserves_metadata(self, client):
        """Test that copy preserves content type and checksums"""
        # Create bucket
        client.post("/storage/v1/b?project=test-project", json={"name": "meta-bucket"})
        
        # Upload source with specific content type
        upload_response = client.post(
            "/storage/v1/b/meta-bucket/o?name=original.json",
            data=b'{"key": "value"}',
            headers={"Content-Type": "application/json"}
        )
        source_data = upload_response.get_json()
        
        # Copy object
        copy_response = client.post(
            "/storage/v1/b/meta-bucket/o/original.json/copyTo/b/meta-bucket/o/copy.json"
        )
        copy_data = copy_response.get_json()
        
        # Verify metadata preserved
        assert copy_data["contentType"] == "application/json"
        assert copy_data["md5Hash"] == source_data["md5Hash"]
        assert copy_data["crc32c"] == source_data["crc32c"]
    
    def test_copy_nonexistent_source(self, client):
        """Test copying non-existent source fails"""
        client.post("/storage/v1/b?project=test-project", json={"name": "test-bucket"})
        
        response = client.post(
            "/storage/v1/b/test-bucket/o/missing.txt/copyTo/b/test-bucket/o/dest.txt"
        )
        assert response.status_code == 404


class TestCORSConfiguration:
    """Test CORS configuration API"""
    
    def test_get_empty_cors(self, client):
        """Test getting CORS configuration when none set"""
        client.post("/storage/v1/b?project=test-project", json={"name": "cors-bucket"})
        
        response = client.get("/storage/v1/b/cors-bucket/cors")
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["kind"] == "storage#bucket#cors"
        assert data["cors"] == []
    
    def test_set_cors_rules(self, client):
        """Test setting CORS rules"""
        client.post("/storage/v1/b?project=test-project", json={"name": "cors-bucket"})
        
        cors_rules = [
            {
                "origin": ["https://example.com"],
                "method": ["GET", "POST"],
                "responseHeader": ["Content-Type"],
                "maxAgeSeconds": 3600
            }
        ]
        
        response = client.put(
            "/storage/v1/b/cors-bucket/cors",
            json={"cors": cors_rules}
        )
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data["cors"]) == 1
        assert data["cors"][0]["origin"] == ["https://example.com"]
    
    def test_update_cors_rules(self, client):
        """Test updating existing CORS rules"""
        client.post("/storage/v1/b?project=test-project", json={"name": "cors-bucket"})
        
        # Set initial rules
        client.put(
            "/storage/v1/b/cors-bucket/cors",
            json={"cors": [{"origin": ["https://old.com"], "method": ["GET"]}]}
        )
        
        # Update rules
        new_rules = [
            {"origin": ["https://new.com"], "method": ["GET", "POST", "DELETE"]}
        ]
        response = client.put(
            "/storage/v1/b/cors-bucket/cors",
            json={"cors": new_rules}
        )
        assert response.status_code == 200
        
        # Verify updated
        get_response = client.get("/storage/v1/b/cors-bucket/cors")
        data = get_response.get_json()
        assert data["cors"][0]["origin"] == ["https://new.com"]
        assert len(data["cors"][0]["method"]) == 3
    
    def test_delete_cors_rules(self, client):
        """Test deleting CORS rules"""
        client.post("/storage/v1/b?project=test-project", json={"name": "cors-bucket"})
        
        # Set rules
        client.put(
            "/storage/v1/b/cors-bucket/cors",
            json={"cors": [{"origin": ["*"], "method": ["GET"]}]}
        )
        
        # Delete rules
        response = client.delete("/storage/v1/b/cors-bucket/cors")
        assert response.status_code == 204
        
        # Verify deleted
        get_response = client.get("/storage/v1/b/cors-bucket/cors")
        assert get_response.get_json()["cors"] == []


class TestEventDelivery:
    """Test event delivery webhooks"""
    
    def test_create_notification_config(self, client):
        """Test creating notification configuration"""
        client.post("/storage/v1/b?project=test-project", json={"name": "notify-bucket"})
        
        response = client.post(
            "/storage/v1/b/notify-bucket/notificationConfigs",
            json={
                "webhookUrl": "https://example.com/webhook",
                "eventTypes": ["OBJECT_FINALIZE", "OBJECT_DELETE"]
            }
        )
        assert response.status_code == 201
        
        data = response.get_json()
        assert "id" in data
        assert data["webhookUrl"] == "https://example.com/webhook"
        assert len(data["eventTypes"]) == 2
    
    def test_list_notification_configs(self, client):
        """Test listing notification configurations"""
        client.post("/storage/v1/b?project=test-project", json={"name": "notify-bucket"})
        
        # Create two configs
        client.post(
            "/storage/v1/b/notify-bucket/notificationConfigs",
            json={"webhookUrl": "https://example.com/webhook1"}
        )
        client.post(
            "/storage/v1/b/notify-bucket/notificationConfigs",
            json={"webhookUrl": "https://example.com/webhook2"}
        )
        
        response = client.get("/storage/v1/b/notify-bucket/notificationConfigs")
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data["items"]) == 2
    
    def test_delete_notification_config(self, client):
        """Test deleting notification configuration"""
        client.post("/storage/v1/b?project=test-project", json={"name": "notify-bucket"})
        
        # Create config
        create_response = client.post(
            "/storage/v1/b/notify-bucket/notificationConfigs",
            json={"webhookUrl": "https://example.com/webhook"}
        )
        config_id = create_response.get_json()["id"]
        
        # Delete config
        response = client.delete(
            f"/storage/v1/b/notify-bucket/notificationConfigs/{config_id}"
        )
        assert response.status_code == 204
        
        # Verify deleted
        list_response = client.get("/storage/v1/b/notify-bucket/notificationConfigs")
        assert len(list_response.get_json()["items"]) == 0


class TestLifecycleRules:
    """Test lifecycle rules configuration and execution"""
    
    def test_set_lifecycle_rules(self, client):
        """Test setting lifecycle rules"""
        client.post("/storage/v1/b?project=test-project", json={"name": "lifecycle-bucket"})
        
        rules = [
            {"action": "Delete", "ageDays": 30},
            {"action": "Archive", "ageDays": 90}
        ]
        
        response = client.put(
            "/storage/v1/b/lifecycle-bucket/lifecycle",
            json={"rule": rules}
        )
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data["rule"]) == 2
        assert data["rule"][0]["action"] == "Delete"
        assert data["rule"][1]["ageDays"] == 90
    
    def test_get_lifecycle_rules(self, client):
        """Test getting lifecycle rules"""
        client.post("/storage/v1/b?project=test-project", json={"name": "lifecycle-bucket"})
        
        # Set rules
        rules = [{"action": "Delete", "ageDays": 60}]
        client.put(
            "/storage/v1/b/lifecycle-bucket/lifecycle",
            json={"rule": rules}
        )
        
        # Get rules
        response = client.get("/storage/v1/b/lifecycle-bucket/lifecycle")
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data["rule"]) == 1
        assert data["rule"][0]["action"] == "Delete"
    
    def test_delete_lifecycle_rules(self, client):
        """Test deleting lifecycle rules"""
        client.post("/storage/v1/b?project=test-project", json={"name": "lifecycle-bucket"})
        
        # Set rules
        client.put(
            "/storage/v1/b/lifecycle-bucket/lifecycle",
            json={"rule": [{"action": "Delete", "ageDays": 30}]}
        )
        
        # Delete rules
        response = client.delete("/storage/v1/b/lifecycle-bucket/lifecycle")
        assert response.status_code == 204
        
        # Verify deleted
        get_response = client.get("/storage/v1/b/lifecycle-bucket/lifecycle")
        assert get_response.get_json()["rule"] == []
    
    def test_lifecycle_execution_idempotence(self, client, app):
        """Test that lifecycle execution is idempotent"""
        from app.services.lifecycle_executor import LifecycleExecutor
        from datetime import datetime, timedelta
        
        with app.app_context():
            # Create bucket with lifecycle rule
            client.post("/storage/v1/b?project=test-project", json={"name": "old-bucket"})
            
            # Set lifecycle rule: delete after 1 day
            client.put(
                "/storage/v1/b/old-bucket/lifecycle",
                json={"rule": [{"action": "Delete", "ageDays": 1}]}
            )
            
            # Upload object
            client.post(
                "/storage/v1/b/old-bucket/o?name=old-file.txt",
                data=b"old content"
            )
            
            # Manually set object created_at to 2 days ago
            bucket = Bucket.query.filter_by(name="old-bucket").first()
            obj = Object.query.filter_by(bucket_id=bucket.id, name="old-file.txt").first()
            obj.created_at = datetime.utcnow() - timedelta(days=2)
            db.session.commit()
            
            # Execute lifecycle rules
            executor = LifecycleExecutor(app, interval_minutes=1)
            actions1 = executor.execute_lifecycle_rules()
            assert actions1 == 1  # One object deleted
            
            # Execute again - should be idempotent (no more actions)
            actions2 = executor.execute_lifecycle_rules()
            assert actions2 == 0  # No more objects to delete


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
