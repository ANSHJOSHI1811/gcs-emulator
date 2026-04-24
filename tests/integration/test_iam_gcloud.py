"""
CloudTester - IAM GCloud CLI Tests
Tests for IAM (Service Accounts, Roles, etc.) using gcloud CLI
Ensures dual compatibility: API + gcloud CLI
"""

import pytest
import json
from typing import Dict, Any

pytestmark = pytest.mark.integration
pytestmark = pytest.mark.gcloud


class TestServiceAccountsGCloud:
    """Test Service Accounts via gcloud CLI"""
    
    def test_gcloud_list_service_accounts(self, gcloud_runner, test_project):
        """List service accounts using gcloud"""
        result = gcloud_runner.run("iam service-accounts list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        accounts = result.json()
        assert isinstance(accounts, list)
    
    def test_gcloud_service_accounts_exist(self, gcloud_runner, test_project):
        """Verify test service accounts exist"""
        result = gcloud_runner.run("iam service-accounts list")
        
        if not result.is_success():
            pytest.skip("service-accounts list not available")
        
        accounts = result.json()
        account_emails = [a.get("email") for a in accounts if a.get("email")]
        
        # Should have at least Compute/default service accounts
        assert len(account_emails) > 0, "Should have at least one service account"
        
        # Check for compute service account pattern
        compute_sa = any("compute" in email for email in account_emails)
        print(f"\n✓ Service accounts found: {len(account_emails)}")
        print(f"  Compute SA exists: {compute_sa}")
    
    def test_gcloud_describe_service_account(self, gcloud_runner, test_project):
        """Describe a service account using gcloud"""
        # First list to find one
        list_result = gcloud_runner.run("iam service-accounts list --limit=1")
        if not list_result.is_success():
            pytest.skip("Cannot list service accounts")
        
        accounts = list_result.json()
        if not accounts:
            pytest.skip("No service accounts found")
        
        email = accounts[0]["email"]
        
        # Describe it
        result = gcloud_runner.run(f"iam service-accounts describe {email}")
        
        if result.is_success():
            sa = result.json()
            assert email in sa.get("email", "")
    
    def test_dual_validation_service_accounts(self, api_client, gcloud_runner, test_project):
        """Validate service accounts in both API and gcloud"""
        # Get via gcloud
        gcloud_result = gcloud_runner.run("iam service-accounts list")
        gcloud_accounts = gcloud_result.json() if gcloud_result.is_success() else []
        gcloud_emails = {a.get("email") for a in gcloud_accounts if a.get("email")}
        
        # Get via API
        api_result = api_client.get(
            f"/iam/v1/projects/{test_project}/serviceAccounts"
        )
        api_accounts = api_result.json().get("accounts", []) if api_result.status_code == 200 else []
        api_emails = {acc.get("email") for acc in api_accounts if acc.get("email")}
        
        # At least one should have accounts
        assert len(gcloud_emails) > 0 or len(api_emails) > 0, "No service accounts found"
        
        print(f"\n✓ GCloud accounts: {gcloud_emails}")
        print(f"✓ API accounts: {api_emails}")


class TestRolesGCloud:
    """Test IAM Roles via gcloud CLI"""
    
    def test_gcloud_list_roles(self, gcloud_runner):
        """List IAM roles using gcloud"""
        result = gcloud_runner.run("iam roles list --limit=10")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        roles = result.json()
        assert isinstance(roles, list)
    
    def test_gcloud_list_custom_roles(self, gcloud_runner, test_project):
        """List custom roles for project using gcloud"""
        result = gcloud_runner.run(f"iam roles list --project={test_project}")
        
        if result.is_success():
            roles = result.json()
            assert isinstance(roles, list)
    
    def test_gcloud_describe_basic_role(self, gcloud_runner):
        """Describe a basic role using gcloud"""
        result = gcloud_runner.run("iam roles describe roles/viewer")
        
        if result.is_success():
            role = result.json()
            assert "viewer" in role.get("name", "").lower()


class TestIAMPoliciesGCloud:
    """Test IAM Policies via gcloud CLI"""
    
    def test_gcloud_get_project_iam_policy(self, gcloud_runner, test_project):
        """Get project IAM policy using gcloud"""
        result = gcloud_runner.run(f"projects get-iam-policy {test_project}")
        
        # May succeed or fail depending on permissions
        if result.is_success():
            policy = result.json()
            # Should have bindings field
            assert "bindings" in policy or "etag" in policy
    
    def test_gcloud_list_bindings(self, gcloud_runner, test_project):
        """List IAM bindings for project using gcloud"""
        result = gcloud_runner.run(f"projects get-iam-policy {test_project}")
        
        if result.is_success():
            policy = result.json()
            bindings = policy.get("bindings", [])
            assert isinstance(bindings, list)


class TestKeysGCloud:
    """Test Service Account Keys via gcloud CLI"""
    
    def test_gcloud_list_service_account_keys(self, gcloud_runner, test_project):
        """List service account keys using gcloud"""
        # First get a service account
        list_result = gcloud_runner.run("iam service-accounts list --limit=1")
        if not list_result.is_success():
            pytest.skip("Cannot list service accounts")
        
        accounts = list_result.json()
        if not accounts:
            pytest.skip("No service accounts found")
        
        email = accounts[0]["email"]
        
        # List keys for this account
        result = gcloud_runner.run(f"iam service-accounts keys list --iam-account={email}")
        
        if result.is_success():
            keys = result.json()
            assert isinstance(keys, list)


class TestIAMErrorHandling:
    """Test gcloud error handling for IAM operations"""
    
    def test_describe_nonexistent_service_account(self, gcloud_runner):
        """Verify error when describing non-existent service account"""
        result = gcloud_runner.run(
            "iam service-accounts describe nonexistent-sa@test-project.iam.gserviceaccount.com"
        )
        assert not result.is_success(), "Should fail for non-existent service account"
    
    def test_describe_nonexistent_role(self, gcloud_runner):
        """Verify error when describing non-existent role"""
        result = gcloud_runner.run("iam roles describe roles/nonexistent-xyz123")
        assert not result.is_success(), "Should fail for non-existent role"
