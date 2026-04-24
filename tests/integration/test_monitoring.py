"""
CloudTester - Monitoring Tests
Tests for Cloud Monitoring: metrics, alerts
"""

import pytest

pytestmark = pytest.mark.integration


class TestMetrics:
    """Test Monitoring Metrics"""
    
    def test_list_metrics(self, api_client, test_project):
        """List custom metrics"""
        path = f"/v3/projects/{test_project}/timeSeries"
        resp = api_client.get(path)
        
        if resp.status_code == 404:
            pytest.skip("Monitoring API not implemented")
        
        assert resp.status_code == 200
        data = resp.json()
        
        timeseries = data.get("timeSeries", [])
        assert isinstance(timeseries, list)


class TestAlerts:
    """Test Alert Policies"""
    
    def test_list_alert_policies(self, api_client, test_project):
        """List alert policies"""
        path = f"/v3/projects/{test_project}/alertPolicies"
        resp = api_client.get(path)
        
        if resp.status_code == 404:
            pytest.skip("Alert policies API not implemented")
        
        assert resp.status_code == 200
        data = resp.json()
        
        policies = data.get("alertPolicies", [])
        assert isinstance(policies, list)
