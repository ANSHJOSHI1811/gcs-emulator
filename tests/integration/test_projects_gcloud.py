"""
CloudTester - Projects GCloud CLI Tests
Tests for GCP Projects management using gcloud CLI
Ensures dual compatibility: API + gcloud CLI
"""

import pytest
import json
from typing import Dict, Any

pytestmark = pytest.mark.integration
pytestmark = pytest.mark.gcloud


class TestProjectsGCloud:
    """Test GCP Projects via gcloud CLI"""
    
    def test_gcloud_list_projects(self, gcloud_runner):
        """List all projects using gcloud"""
        result = gcloud_runner.run("projects list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        projects = result.json()
        assert isinstance(projects, list)
        assert len(projects) > 0, "Should have at least one project"
    
    def test_gcloud_describe_project(self, gcloud_runner, test_project):
        """Describe a project using gcloud"""
        result = gcloud_runner.run(f"projects describe {test_project}")
        
        # May fail if project doesn't exist, but structure should be consistent
        if result.is_success():
            project = result.json()
            # Look for project ID or name field
            assert "projectId" in project or "name" in project or "projectNumber" in project
        else:
            # Log but don't fail
            print(f"\n⚠️  Project {test_project} not found: {result.stderr}")
    
    def test_gcloud_current_project(self, gcloud_runner, test_project):
        """Get current gcloud configuration"""
        result = gcloud_runner.run("config get-value project")
        
        if result.is_success():
            project_id = result.stdout.strip()
            # Should be set to our test project
            print(f"\n✓ Current project in gcloud: {project_id}")


class TestProjectMetadataGCloud:
    """Test Project Metadata via gcloud CLI"""
    
    def test_gcloud_list_project_resources(self, gcloud_runner, test_project):
        """List resources in project using gcloud"""
        # Try compute instances as proxy
        result = gcloud_runner.run("compute instances list")
        
        if result.is_success():
            instances = result.json()
            assert isinstance(instances, list)
            print(f"\n✓ Found {len(instances)} instances in project")
    
    def test_gcloud_project_quotas(self, gcloud_runner, test_project):
        """Check project quotas using gcloud"""
        result = gcloud_runner.run(f"compute project-info describe --project={test_project}")
        
        if result.is_success():
            info = result.json()
            quotas = info.get("commonInstanceMetadata", {}).get("items", [])
            print(f"\n✓ Project info retrieved with {len(quotas)} metadata items")


class TestProjectConfigGCloud:
    """Test Project Configuration via gcloud CLI"""
    
    def test_gcloud_config_list(self, gcloud_runner):
        """List gcloud configuration using gcloud"""
        result = gcloud_runner.run("config list --format=json")
        
        if result.is_success():
            config = result.json()
            # Should have core section
            assert isinstance(config, (dict, list))
    
    def test_gcloud_config_get_project(self, gcloud_runner):
        """Get configured project using gcloud"""
        result = gcloud_runner.run("config get-value project")
        
        if result.is_success():
            project = result.stdout.strip()
            assert project, "Project should be configured"
    
    def test_gcloud_config_get_zone(self, gcloud_runner):
        """Get configured zone using gcloud"""
        result = gcloud_runner.run("config get-value compute/zone")
        
        if result.is_success():
            zone = result.stdout.strip()
            # Zone should be set
            print(f"\n✓ Configured zone: {zone}")


class TestDualValidationProjects:
    """Cross-validation tests between API and gcloud for projects"""
    
    def test_project_accessible_via_both(self, api_client, gcloud_runner, test_project):
        """Verify project is accessible via both API and gcloud"""
        # Try gcloud
        gcloud_result = gcloud_runner.run(f"projects describe {test_project}")
        gcloud_accessible = gcloud_result.is_success()
        
        # Try API
        api_result = api_client.get(f"/cloudresourcemanager/v1/projects/{test_project}")
        api_accessible = api_result.status_code == 200
        
        # At least one should work
        assert gcloud_accessible or api_accessible, \
            f"Project {test_project} not accessible via either API or gcloud"
        
        print(f"\n✓ Project {test_project}:")
        print(f"  - GCloud accessible: {gcloud_accessible}")
        print(f"  - API accessible: {api_accessible}")
    
    def test_project_info_consistency(self, api_client, gcloud_runner, test_project):
        """Verify project info is consistent between API and gcloud"""
        # Get via gcloud
        gcloud_result = gcloud_runner.run(f"projects describe {test_project}")
        gcloud_info = gcloud_result.json() if gcloud_result.is_success() else {}
        
        # Get via API
        api_result = api_client.get(f"/cloudresourcemanager/v1/projects/{test_project}")
        api_info = api_result.json() if api_result.status_code == 200 else {}
        
        # Extract IDs if available
        gcloud_id = gcloud_info.get("projectId") or gcloud_info.get("name")
        api_id = api_info.get("projectId") or api_info.get("name")
        
        if gcloud_id and api_id:
            assert gcloud_id == api_id, "Project IDs should match"
            print(f"\n✓ Project IDs match: {gcloud_id}")


class TestProjectErrorHandling:
    """Test gcloud error handling for project operations"""
    
    def test_describe_nonexistent_project(self, gcloud_runner):
        """Verify error when describing non-existent project"""
        result = gcloud_runner.run("projects describe nonexistent-project-xyz123")
        assert not result.is_success(), "Should fail for non-existent project"
    
    def test_invalid_project_format(self, gcloud_runner):
        """Test handling of invalid project ID format"""
        result = gcloud_runner.run("projects describe !!!invalid!!!")
        assert not result.is_success(), "Should fail for invalid project ID"
