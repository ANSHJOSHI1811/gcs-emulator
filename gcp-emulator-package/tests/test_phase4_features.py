"""
Phase 4 Feature Tests

Tests for Object Events, Minimal ACL, and Basic Lifecycle Rules.
"""
import pytest
import time
import json
from datetime import datetime, timedelta
from app.models.bucket import Bucket
from app.models.object import Object, ObjectVersion
from app.models.object_event import ObjectEvent
from app.models.lifecycle_rule import LifecycleRule
from app.services.object_event_service import ObjectEventService, EventType
from app.services.acl_service import ACLService, ACLValue
from app.services.lifecycle_service import LifecycleService, LifecycleAction
from app.factory import db


class TestObjectEvents:
    """Test Object Change Events"""
    
    def test_event_logged_on_upload(self, client, setup_bucket):
        """Test OBJECT_FINALIZE event logged on upload"""
        bucket_name = setup_bucket
        
        # Log finalize event
        ObjectEventService.log_event(
            bucket_name=bucket_name,
            object_name="test.txt",
            event_type=EventType.OBJECT_FINALIZE,
            generation=1,
            metadata={"size": 100}
        )
        
        # Verify event logged
        events = ObjectEventService.get_events(bucket_name=bucket_name)
        assert len(events) == 1
        assert events[0].event_type == EventType.OBJECT_FINALIZE
        assert events[0].object_name == "test.txt"
        assert events[0].generation == 1
        assert events[0].delivered == False
    
    def test_event_logged_on_delete(self, client, setup_bucket):
        """Test OBJECT_DELETE event logged on deletion"""
        bucket_name = setup_bucket
        
        # Log delete event
        ObjectEventService.log_event(
            bucket_name=bucket_name,
            object_name="test.txt",
            event_type=EventType.OBJECT_DELETE,
            generation=1
        )
        
        # Verify event logged
        events = ObjectEventService.get_events(bucket_name=bucket_name)
        assert len(events) == 1
        assert events[0].event_type == EventType.OBJECT_DELETE
        assert events[0].generation == 1
    
    def test_event_logged_on_metadata_update(self, client, setup_bucket):
        """Test OBJECT_METADATA_UPDATE event logged on metadata change"""
        bucket_name = setup_bucket
        
        # Log metadata update event
        ObjectEventService.log_event(
            bucket_name=bucket_name,
            object_name="test.txt",
            event_type=EventType.OBJECT_METADATA_UPDATE,
            generation=1,
            metadata={"contentType": "text/plain"}
        )
        
        # Verify event logged
        events = ObjectEventService.get_events(bucket_name=bucket_name)
        assert len(events) == 1
        assert events[0].event_type == EventType.OBJECT_METADATA_UPDATE
    
    def test_mark_event_delivered(self, client, setup_bucket):
        """Test marking event as delivered"""
        bucket_name = setup_bucket
        
        # Log event
        ObjectEventService.log_event(
            bucket_name=bucket_name,
            object_name="test.txt",
            event_type=EventType.OBJECT_FINALIZE,
            generation=1
        )
        
        # Get event
        events = ObjectEventService.get_events(delivered=False)
        assert len(events) >= 1
        event_id = events[0].event_id
        
        # Mark delivered
        ObjectEventService.mark_delivered(event_id)
        
        # Verify marked
        delivered_events = ObjectEventService.get_events(bucket_name=bucket_name, delivered=True)
        assert len(delivered_events) >= 1


class TestMinimalACL:
    """Test Minimal ACL Simulation"""
    
    def test_default_acl_is_private(self, client, setup_bucket):
        """Test default ACL is private"""
        bucket_name = setup_bucket
        acl = ACLService.get_bucket_acl(bucket_name)
        assert acl == ACLValue.PRIVATE
    
    def test_set_bucket_acl_to_public_read(self, client, setup_bucket):
        """Test setting bucket ACL to publicRead"""
        bucket_name = setup_bucket
        ACLService.set_bucket_acl(bucket_name, ACLValue.PUBLIC_READ)
        acl = ACLService.get_bucket_acl(bucket_name)
        assert acl == ACLValue.PUBLIC_READ
    
    def test_acl_endpoint_set_bucket_acl(self, client, setup_bucket):
        """Test PATCH /storage/v1/b/{bucket}/acl endpoint"""
        bucket_name = setup_bucket
        response = client.patch(
            f"/storage/v1/b/{bucket_name}/acl",
            json={"acl": "publicRead"}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["acl"] == "publicRead"
    
    def test_acl_endpoint_get_bucket_acl(self, client, setup_bucket):
        """Test GET /storage/v1/b/{bucket}/acl endpoint"""
        bucket_name = setup_bucket
        response = client.get(f"/storage/v1/b/{bucket_name}/acl")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["acl"] == "private"  # Default


class TestLifecycleRules:
    """Test Basic Lifecycle Rules"""
    
    def test_create_delete_rule(self, client, setup_bucket):
        """Test creating Delete lifecycle rule"""
        bucket_name = setup_bucket
        rule = LifecycleService.create_rule(bucket_name, LifecycleAction.DELETE, 30)
        
        assert rule.action == LifecycleAction.DELETE
        assert rule.age_days == 30
    
    def test_create_archive_rule(self, client, setup_bucket):
        """Test creating Archive lifecycle rule"""
        bucket_name = setup_bucket
        rule = LifecycleService.create_rule(bucket_name, LifecycleAction.ARCHIVE, 90)
        
        assert rule.action == LifecycleAction.ARCHIVE
        assert rule.age_days == 90
    
    def test_list_rules(self, client, setup_bucket):
        """Test listing lifecycle rules"""
        bucket_name = setup_bucket
        LifecycleService.create_rule(bucket_name, LifecycleAction.DELETE, 30)
        LifecycleService.create_rule(bucket_name, LifecycleAction.ARCHIVE, 90)
        
        rules = LifecycleService.list_rules(bucket_name)
        assert len(rules) >= 2
    
    def test_lifecycle_endpoint_create_rule(self, client, setup_bucket):
        """Test POST /internal/lifecycle/rules endpoint"""
        bucket_name = setup_bucket
        response = client.post(
            "/internal/lifecycle/rules",
            json={
                "bucket": bucket_name,
                "action": "Delete",
                "ageDays": 30
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data["action"] == "Delete"
        assert data["ageDays"] == 30
    
    def test_lifecycle_endpoint_evaluate(self, client, setup_bucket):
        """Test POST /internal/lifecycle/evaluate endpoint"""
        response = client.post("/internal/lifecycle/evaluate")
        
        assert response.status_code == 200
        data = response.get_json()
        assert "rulesEvaluated" in data
        assert "objectsDeleted" in data
        assert "objectsArchived" in data
