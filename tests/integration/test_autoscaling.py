"""
CloudTester - Autoscaling Tests
Tests for Compute Autoscaling: policies, metrics
"""

import pytest

pytestmark = pytest.mark.integration


class TestAutoscalingPolicies:
    """Test Autoscaling Policies"""
    
    def test_list_autoscalers(self, api_client, test_project, test_zone):
        """List autoscaling policies"""
        path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/autoscalers"
        resp = api_client.get(path)
        
        if resp.status_code == 404:
            pytest.skip("Autoscaling API not implemented")
        
        assert resp.status_code == 200
        data = resp.json()
        
        autoscalers = data.get("items", [])
        assert isinstance(autoscalers, list)
