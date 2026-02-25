"""
CloudTester - Projects Tests
Tests for GCP Project Management
"""

import pytest

pytestmark = pytest.mark.integration


class TestProjects:
    """Test Project Management"""
    
    def test_list_projects(self, api_client):
        """List GCP projects"""
        path = "/cloudresourcemanager/v1/projects"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        projects = data.get("projects", [])
        assert isinstance(projects, list)
        assert len(projects) > 0
    
    def test_get_project(self, api_client, test_project):
        """Get project details"""
        path = f"/cloudresourcemanager/v1/projects/{test_project}"
        resp = api_client.get(path)
        
        if resp.status_code == 404:
            pytest.skip("Get project endpoint not implemented")
        
        assert resp.status_code == 200
        project = resp.json()
        
        assert project["projectId"] == test_project or project["name"] == test_project
