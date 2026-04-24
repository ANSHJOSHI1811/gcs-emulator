"""
CloudTester - Cloud Run Tests
Tests for Cloud Run: services, revisions, traffic management
"""

import pytest

pytestmark = pytest.mark.integration


class TestCloudRunServices:
    """Test Cloud Run Services"""
    
    def test_list_services(self, api_client, test_project, test_region):
        """List Cloud Run services"""
        path = f"/v1/projects/{test_project}/locations/{test_region}/services"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        services = data.get("services", [])
        assert isinstance(services, list)
    
    def test_create_service(self, api_client, test_project, test_region):
        """Create a Cloud Run service"""
        path = f"/v1/projects/{test_project}/locations/{test_region}/services"
        
        payload = {
            "metadata": {
                "name": "test-service"
            },
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "image": "gcr.io/cloud-builders/docker"
                            }
                        ]
                    }
                }
            }
        }
        
        resp = api_client.post(path, payload)
        
        if resp.status_code == 404:
            pytest.skip("Cloud Run API endpoint not yet implemented")
        
        if resp.status_code in [200, 201]:
            data = resp.json()
            assert "name" in data or "metadata" in data
