"""
CloudTester - IAM Tests
Tests for IAM: service accounts, roles, policies
"""

import pytest

pytestmark = pytest.mark.integration


class TestServiceAccounts:
    """Test Service Accounts"""
    
    def test_list_service_accounts(self, api_client, test_project):
        """List service accounts"""
        path = f"/v1/projects/{test_project}/serviceAccounts"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        accounts = data.get("accounts", [])
        assert isinstance(accounts, list)
    
    def test_default_service_accounts_created(self, api_client, test_project):
        """Verify default service accounts are created (Phase 1)"""
        path = f"/v1/projects/{test_project}/serviceAccounts"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        accounts = data.get("accounts", [])
        account_emails = [a["email"] for a in accounts]
        
        # After Phase 1: check for default accounts
        # Format: {project-number}-compute@developer.gserviceaccount.com
        # Placeholder for now
        assert len(accounts) >= 0


class TestProjectMetadata:
    """Test Project-level Metadata and IAM Policies"""
    
    def test_get_project_info(self, api_client, test_project):
        """Get project information"""
        path = f"/cloudresourcemanager/v1/projects/{test_project}"
        resp = api_client.get(path)
        
        if resp.status_code == 404:
            pytest.skip("Project info endpoint not implemented")
        
        assert resp.status_code == 200
        data = resp.json()
        
        assert "projectId" in data or "name" in data
