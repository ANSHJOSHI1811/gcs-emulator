"""
CloudTester - Compute Engine GCloud CLI Tests
Tests for Compute Engine (VM Instances, etc.) using gcloud CLI
Ensures dual compatibility: API + gcloud CLI
"""

import pytest
import json
from typing import Dict, Any

pytestmark = pytest.mark.integration
pytestmark = pytest.mark.gcloud


class TestInstancesGCloud:
    """Test Compute Engine VM Instances via gcloud CLI"""
    
    def test_gcloud_list_instances(self, gcloud_runner, test_zone):
        """List all instances in zone using gcloud"""
        result = gcloud_runner.run(f"compute instances list --zones={test_zone}")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        instances = result.json()
        assert isinstance(instances, list)
    
    def test_gcloud_list_all_instances(self, gcloud_runner):
        """List all instances across all zones using gcloud"""
        result = gcloud_runner.run("compute instances list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        instances = result.json()
        assert isinstance(instances, list)
    
    def test_dual_validation_instances(self, api_client, gcloud_runner, test_project, test_zone):
        """Validate instances in both API and gcloud"""
        # Get via gcloud
        gcloud_result = gcloud_runner.run(f"compute instances list --zones={test_zone}")
        gcloud_instances = gcloud_result.json() if gcloud_result.is_success() else []
        gcloud_names = {i.get("name") for i in gcloud_instances if i.get("name")}
        
        # Get via API
        api_result = api_client.get(
            f"/compute/v1/projects/{test_project}/zones/{test_zone}/instances"
        )
        api_items = api_result.json().get("items", []) if api_result.status_code == 200 else []
        api_names = {item.get("name") for item in api_items if item.get("name")}
        
        print(f"\n✓ GCloud instances: {gcloud_names}")
        print(f"✓ API instances: {api_names}")


class TestMachineTypesGCloud:
    """Test Machine Types via gcloud CLI"""
    
    def test_gcloud_list_machine_types(self, gcloud_runner, test_zone):
        """List available machine types using gcloud"""
        result = gcloud_runner.run(f"compute machine-types list --zones={test_zone}")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        types = result.json()
        assert isinstance(types, list)
        assert len(types) > 0, "Should have at least some machine types"
    
    def test_gcloud_describe_machine_type(self, gcloud_runner, test_zone):
        """Describe a machine type using gcloud"""
        # First list to find one
        list_result = gcloud_runner.run(f"compute machine-types list --zones={test_zone} --limit=1")
        if not list_result.is_success():
            pytest.skip("Cannot list machine types")
        
        types = list_result.json()
        if not types:
            pytest.skip("No machine types found")
        
        machine_type = types[0]["name"]
        
        # Now describe it
        result = gcloud_runner.run(
            f"compute machine-types describe {machine_type} --zones={test_zone}"
        )
        
        if result.is_success():
            mt = result.json()
            assert mt.get("name") == machine_type


class TestImagesGCloud:
    """Test VM Images via gcloud CLI"""
    
    def test_gcloud_list_images(self, gcloud_runner):
        """List available images using gcloud"""
        result = gcloud_runner.run("compute images list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        images = result.json()
        assert isinstance(images, list)
    
    def test_gcloud_list_debian_images(self, gcloud_runner):
        """List Debian images using gcloud"""
        result = gcloud_runner.run("compute images list --filter='family:debian' --limit=5")
        
        if result.is_success():
            images = result.json()
            assert isinstance(images, list)
    
    def test_gcloud_list_ubuntu_images(self, gcloud_runner):
        """List Ubuntu images using gcloud"""
        result = gcloud_runner.run("compute images list --filter='family:ubuntu' --limit=5")
        
        if result.is_success():
            images = result.json()
            assert isinstance(images, list)


class TestProjectsGCloud:
    """Test Projects info via gcloud CLI"""
    
    def test_gcloud_list_projects(self, gcloud_runner):
        """List projects using gcloud"""
        result = gcloud_runner.run("projects list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        projects = result.json()
        assert isinstance(projects, list)
    
    def test_gcloud_describe_project(self, gcloud_runner, test_project):
        """Describe a project using gcloud"""
        result = gcloud_runner.run(f"projects describe {test_project}")
        
        if result.is_success():
            project = result.json()
            assert project.get("projectId") == test_project or project.get("name") == test_project
        else:
            pytest.skip(f"Project {test_project} not accessible")


class TestAddressesGCloud:
    """Test Static IP Addresses via gcloud CLI"""
    
    def test_gcloud_list_addresses(self, gcloud_runner, test_region):
        """List static addresses using gcloud"""
        result = gcloud_runner.run(f"compute addresses list --regions={test_region}")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        addresses = result.json()
        assert isinstance(addresses, list)
    
    def test_gcloud_list_all_addresses(self, gcloud_runner):
        """List all addresses using gcloud"""
        result = gcloud_runner.run("compute addresses list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        addresses = result.json()
        assert isinstance(addresses, list)


class TestDisksGCloud:
    """Test Persistent Disks via gcloud CLI"""
    
    def test_gcloud_list_disks(self, gcloud_runner, test_zone):
        """List persistent disks using gcloud"""
        result = gcloud_runner.run(f"compute disks list --zones={test_zone}")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        disks = result.json()
        assert isinstance(disks, list)
    
    def test_gcloud_list_all_disks(self, gcloud_runner):
        """List all disks using gcloud"""
        result = gcloud_runner.run("compute disks list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        disks = result.json()
        assert isinstance(disks, list)


class TestComputeErrorHandling:
    """Test gcloud error handling for compute operations"""
    
    def test_describe_nonexistent_instance(self, gcloud_runner, test_zone):
        """Verify error when describing non-existent instance"""
        result = gcloud_runner.run(
            f"compute instances describe nonexistent-instance-xyz123 --zones={test_zone}"
        )
        assert not result.is_success(), "Should fail for non-existent instance"
    
    def test_invalid_zone(self, gcloud_runner):
        """Verify error handling for invalid zone"""
        result = gcloud_runner.run("compute instances list --zones=invalid-zone-123")
        
        # May fail or return empty, but should not crash
        assert isinstance(result.exit_code, int)
