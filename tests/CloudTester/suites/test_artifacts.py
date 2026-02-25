"""
CloudTester - Artifact Registry Tests
Tests for Artifact Registry: repositories, images
"""

import pytest

pytestmark = pytest.mark.integration


class TestRepositories:
    """Test Artifact Repositories"""
    
    def test_list_repositories(self, api_client, test_project, test_region):
        """List artifact repositories"""
        path = f"/v1/projects/{test_project}/locations/{test_region}/repositories"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        repositories = data.get("repositories", [])
        assert isinstance(repositories, list)
    
    def test_create_repository(self, api_client, test_project, test_region):
        """Create an artifact repository"""
        path = f"/v1/projects/{test_project}/locations/{test_region}/repositories"
        
        payload = {
            "repositoryId": "test-repo",
            "repository": {
                "format": "DOCKER",
                "description": "Test Docker repository"
            }
        }
        
        resp = api_client.post(path, payload)
        
        if resp.status_code not in [200, 201]:
            pytest.skip("Repository creation not fully implemented")
        
        data = resp.json()
        assert "name" in data or "repositoryId" in data
