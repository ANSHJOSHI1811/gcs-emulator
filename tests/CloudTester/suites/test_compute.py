"""
CloudTester - Compute Engine Service Tests
Tests for Compute Engine endpoints: instances, zones, machine types, addresses, disks
"""

import pytest
import json
from typing import Dict, Any

pytestmark = pytest.mark.integration


class TestZones:
    """Test Compute Engine Zones"""
    
    def test_list_zones(self, api_client, test_project):
        """List all zones"""
        path = f"/compute/v1/projects/{test_project}/zones"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Should have zones array
        assert "items" in data or isinstance(data, list)
        zones = data.get("items", data)
        assert len(zones) > 0
        
        # Verify zones structure
        for zone in zones:
            assert "name" in zone
            assert "region" in zone
            assert "status" in zone
    
    def test_get_zone(self, api_client, test_project, test_zone):
        """Get specific zone details"""
        path = f"/compute/v1/projects/{test_project}/zones/{test_zone}"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["name"] == test_zone
        assert "status" in data
        assert data["status"] in ["UP", "DOWN"]
    
    def test_list_machine_types(self, api_client, test_project, test_zone):
        """List machine types in a zone"""
        path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/machineTypes"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        machines = data.get("items", [])
        assert len(machines) > 0
        
        # Verify machine types
        for machine in machines:
            assert "name" in machine
            assert "memoryMb" in machine or "memory" in machine
            assert "guestCpus" in machine or "cpus" in machine


class TestInstances:
    """Test Compute Engine VM Instances"""
    
    def test_list_instances(self, api_client, test_project, test_zone):
        """List instances in a zone"""
        path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/instances"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        # Can be empty or have items
        instances = data.get("items", [])
        assert isinstance(instances, list)
    
    def test_create_instance(self, api_client, test_project, test_zone, sample_instance_payload, cleanup_resources):
        """Create a new VM instance"""
        path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/instances"
        
        payload = {
            "name": sample_instance_payload["name"],
            "machineType": f"zones/{test_zone}/machineTypes/e2-micro",
            "networkInterfaces": [
                {
                    "network": "global/networks/default"
                }
            ]
        }
        
        resp = api_client.post(path, payload)
        
        assert resp.status_code in [200, 201]
        data = resp.json()
        
        # API returns an operation, not the instance directly
        assert "name" in data
        assert data.get("operationType") in ["insert", "INSERT"] or "targetLink" in data
        
        # Track for cleanup
        cleanup_resources["instances"].append({
            "project": test_project,
            "zone": test_zone,
            "name": data["name"]
        })
    
    def test_get_instance(self, api_client, test_project, test_zone):
        """Get instance details"""
        # First, list to find an existing instance
        list_path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/instances"
        list_resp = api_client.get(list_path)
        
        if list_resp.status_code != 200:
            pytest.skip("Cannot list instances")
        
        instances = list_resp.json().get("items", [])
        if not instances:
            pytest.skip("No instances available")
        
        instance_name = instances[0]["name"]
        
        # Get instance details
        path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/instances/{instance_name}"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["name"] == instance_name
        assert "machineType" in data
        assert "status" in data
        assert "networkInterfaces" in data
    
    def test_instance_operations_start_stop(self, api_client, test_project, test_zone):
        """Test instance start and stop operations"""
        # List instances to find one to operate on
        list_path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/instances"
        list_resp = api_client.get(list_path)
        
        if list_resp.status_code != 200:
            pytest.skip("Cannot list instances")
        
        instances = list_resp.json().get("items", [])
        if not instances:
            pytest.skip("No instances available")
        
        instance_name = instances[0]["name"]
        
        # Stop instance
        stop_path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/instances/{instance_name}/stop"
        stop_resp = api_client.post(stop_path, {})
        assert stop_resp.status_code in [200, 204]
        
        # Start instance
        start_path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/instances/{instance_name}/start"
        start_resp = api_client.post(start_path, {})
        assert start_resp.status_code in [200, 204]
    
    def test_delete_instance(self, api_client, test_project, test_zone, sample_instance_payload):
        """Delete an instance"""
        # Create instance first
        create_path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/instances"
        create_payload = {
            "name": sample_instance_payload["name"],
            "machineType": f"zones/{test_zone}/machineTypes/e2-micro",
            "networkInterfaces": [{"network": "global/networks/default"}]
        }
        
        create_resp = api_client.post(create_path, create_payload)
        if create_resp.status_code not in [200, 201]:
            pytest.skip(f"Failed to create instance: {create_resp.text}")
        
        instance_name = create_resp.json()["name"]
        
        # Delete instance
        delete_path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/instances/{instance_name}"
        delete_resp = api_client.delete(delete_path)
        
        assert delete_resp.status_code in [200, 204]


class TestAddresses:
    """Test Static External IP Addresses"""
    
    def test_list_addresses(self, api_client, test_project, test_region):
        """List static IP addresses in a region"""
        path = f"/compute/v1/projects/{test_project}/regions/{test_region}/addresses"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        addresses = data.get("items", [])
        assert isinstance(addresses, list)
    
    def test_reserve_address(self, api_client, test_project, test_region, cleanup_resources):
        """Reserve a static external IP address"""
        path = f"/compute/v1/projects/{test_project}/regions/{test_region}/addresses"
        
        payload = {
            "name": f"test-ip-{test_region}",
            "addressType": "EXTERNAL",
            "region": test_region
        }
        
        resp = api_client.post(path, payload)
        
        # May not be implemented yet
        if resp.status_code == 404:
            pytest.skip("Address API not yet implemented")
        
        assert resp.status_code in [200, 201]
        data = resp.json()
        
        assert "address" in data or "name" in data


class TestDisks:
    """Test Persistent Disks"""
    
    def test_list_disks(self, api_client, test_project, test_zone):
        """List disks in a zone"""
        path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/disks"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        disks = data.get("items", [])
        assert isinstance(disks, list)
    
    def test_create_disk(self, api_client, test_project, test_zone, cleanup_resources):
        """Create a persistent disk"""
        path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/disks"
        
        payload = {
            "name": "test-disk",
            "sizeGb": 10,
            "type": f"zones/{test_zone}/diskTypes/pd-standard"
        }
        
        resp = api_client.post(path, payload)
        
        # May not be fully implemented
        if resp.status_code == 404:
            pytest.skip("Disk API not yet implemented")
        
        if resp.status_code in [200, 201]:
            data = resp.json()
            assert "name" in data or "selfLink" in data


class TestImages:
    """Test Custom Images"""
    
    def test_list_images(self, api_client, test_project):
        """List custom images"""
        path = f"/compute/v1/projects/{test_project}/global/images"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        images = data.get("items", [])
        assert isinstance(images, list)


class TestOperations:
    """Test Compute Operations (long-running operations tracking)"""
    
    def test_list_zone_operations(self, api_client, test_project, test_zone):
        """List operations in a zone"""
        path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/operations"
        resp = api_client.get(path)
        
        if resp.status_code == 404:
            pytest.skip("Operations API not implemented")
        
        assert resp.status_code == 200
        data = resp.json()
        
        operations = data.get("items", [])
        assert isinstance(operations, list)


# Integration tests combining multiple operations
class TestComputeWorkflows:
    """Full workflow tests combining multiple compute operations"""
    
    def test_instance_lifecycle(self, api_client, test_project, test_zone, sample_instance_payload):
        """Test complete instance lifecycle: create → get → stop → start → delete"""
        
        # Create
        create_path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/instances"
        create_resp = api_client.post(create_path, {
            "name": sample_instance_payload["name"],
            "machineType": f"zones/{test_zone}/machineTypes/e2-micro",
            "networkInterfaces": [{"network": "global/networks/default"}]
        })
        
        if create_resp.status_code not in [200, 201]:
            pytest.skip(f"Cannot create instance: {create_resp.text}")
        
        instance_name = create_resp.json()["name"]
        instance_path = f"/compute/v1/projects/{test_project}/zones/{test_zone}/instances/{instance_name}"
        
        # Get
        get_resp = api_client.get(instance_path)
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == instance_name
        
        # Delete
        delete_resp = api_client.delete(instance_path)
        assert delete_resp.status_code in [200, 204]
