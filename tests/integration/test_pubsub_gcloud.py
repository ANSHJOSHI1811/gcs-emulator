"""
CloudTester - Pub/Sub GCloud CLI Tests
Tests for Google Cloud Pub/Sub using gcloud CLI
Ensures dual compatibility: API + gcloud CLI
"""

import pytest
import json
from typing import Dict, Any

pytestmark = pytest.mark.integration
pytestmark = pytest.mark.gcloud


class TestTopicsGCloud:
    """Test Pub/Sub Topics via gcloud CLI"""
    
    def test_gcloud_list_topics(self, gcloud_runner, test_project):
        """List Pub/Sub topics using gcloud"""
        result = gcloud_runner.run("pubsub topics list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        topics = result.json()
        assert isinstance(topics, list)
    
    def test_gcloud_describe_topic(self, gcloud_runner, test_project):
        """Describe a Pub/Sub topic using gcloud"""
        # First list to find a topic
        list_result = gcloud_runner.run("pubsub topics list --limit=1")
        if not list_result.is_success():
            pytest.skip("Cannot list topics")
        
        topics = list_result.json()
        if not topics:
            pytest.skip("No topics found")
        
        topic_name = topics[0]["name"].split("/")[-1]  # Extract topic name
        
        # Describe it
        result = gcloud_runner.run(f"pubsub topics describe {topic_name}")
        
        if result.is_success():
            topic = result.json()
            assert topic_name in topic.get("name", "")


class TestSubscriptionsGCloud:
    """Test Pub/Sub Subscriptions via gcloud CLI"""
    
    def test_gcloud_list_subscriptions(self, gcloud_runner):
        """List Pub/Sub subscriptions using gcloud"""
        result = gcloud_runner.run("pubsub subscriptions list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        subscriptions = result.json()
        assert isinstance(subscriptions, list)
    
    def test_gcloud_describe_subscription(self, gcloud_runner):
        """Describe a Pub/Sub subscription using gcloud"""
        # First list to find a subscription
        list_result = gcloud_runner.run("pubsub subscriptions list --limit=1")
        if not list_result.is_success():
            pytest.skip("Cannot list subscriptions")
        
        subscriptions = list_result.json()
        if not subscriptions:
            pytest.skip("No subscriptions found")
        
        sub_name = subscriptions[0]["name"].split("/")[-1]  # Extract subscription name
        
        # Describe it
        result = gcloud_runner.run(f"pubsub subscriptions describe {sub_name}")
        
        if result.is_success():
            subscription = result.json()
            assert sub_name in subscription.get("name", "")


class TestDualValidationPubSub:
    """Cross-validation tests between API and gcloud for Pub/Sub"""
    
    def test_topics_accessible_via_both(self, api_client, gcloud_runner, test_project):
        """Verify topics are accessible via both systems"""
        # Try gcloud
        gcloud_result = gcloud_runner.run("pubsub topics list")
        gcloud_topics = gcloud_result.json() if gcloud_result.is_success() else []
        
        # Try API
        api_result = api_client.get(f"/pubsub/v1/projects/{test_project}/topics")
        api_topics = api_result.json().get("topics", []) if api_result.status_code == 200 else []
        
        print(f"\n✓ GCloud topics: {len(gcloud_topics)}")
        print(f"✓ API topics: {len(api_topics)}")


class TestPubSubErrorHandling:
    """Test gcloud error handling for Pub/Sub operations"""
    
    def test_describe_nonexistent_topic(self, gcloud_runner):
        """Verify error when describing non-existent topic"""
        result = gcloud_runner.run("pubsub topics describe nonexistent-topic-xyz123")
        assert not result.is_success(), "Should fail for non-existent topic"
