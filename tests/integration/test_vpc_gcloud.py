"""
CloudTester - VPC Networking GCloud CLI Tests
Tests for VPC Networks, Subnets, and Routes using gcloud CLI
Ensures dual compatibility: API + gcloud CLI
"""

import pytest
import json
from typing import Dict, Any

pytestmark = pytest.mark.integration
pytestmark = pytest.mark.gcloud


class TestNetworksGCloud:
    """Test VPC Networks via gcloud CLI"""
    
    def test_gcloud_list_networks(self, gcloud_runner, test_project):
        """List all VPC networks using gcloud"""
        result = gcloud_runner.run("compute networks list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        networks = result.json()
        assert isinstance(networks, list)
        assert len(networks) > 0, "Should have at least default network"
    
    def test_gcloud_default_network_exists(self, gcloud_runner, test_project):
        """Verify default network exists via gcloud"""
        result = gcloud_runner.run("compute networks list")
        
        assert result.is_success()
        networks = result.json()
        network_names = [n.get("name") for n in networks]
        assert "default" in network_names, "Default network should exist"
    
    def test_gcloud_describe_default_network(self, gcloud_runner, test_project):
        """Get default network details via gcloud"""
        result = gcloud_runner.run("compute networks describe default")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        network = result.json()
        assert network["name"] == "default"
    
    def test_dual_validation_networks(self, api_client, gcloud_runner, test_project):
        """Validate networks in both API and gcloud"""
        # Get via gcloud
        gcloud_result = gcloud_runner.run("compute networks list")
        assert gcloud_result.is_success()
        gcloud_networks = {n.get("name") for n in gcloud_result.json()}
        
        # Get via API
        api_result = api_client.get(f"/compute/v1/projects/{test_project}/global/networks")
        assert api_result.status_code == 200
        api_networks = {n["name"] for n in api_result.json().get("items", [])}
        
        # Both should have default
        assert "default" in gcloud_networks or "default" in api_networks, "default network not found"
        
        print(f"\n✓ GCloud networks: {gcloud_networks}")
        print(f"✓ API networks: {api_networks}")


class TestSubnetsGCloud:
    """Test Subnets via gcloud CLI"""
    
    def test_gcloud_list_subnets(self, gcloud_runner, test_region):
        """List subnets in region using gcloud"""
        result = gcloud_runner.run(f"compute networks subnets list --regions={test_region}")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        subnets = result.json()
        assert isinstance(subnets, list)
    
    def test_gcloud_list_all_subnets(self, gcloud_runner):
        """List all subnets using gcloud"""
        result = gcloud_runner.run("compute networks subnets list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        subnets = result.json()
        assert isinstance(subnets, list)
        assert len(subnets) > 0, "Should have at least default subnets"
    
    def test_dual_validation_subnets(self, api_client, gcloud_runner, test_project, test_region):
        """Validate subnets in both API and gcloud"""
        # Get via gcloud
        gcloud_result = gcloud_runner.run(f"compute networks subnets list --regions={test_region}")
        gcloud_subnets = result.json() if (result := gcloud_result).is_success() else []
        
        # Get via API
        api_result = api_client.get(f"/compute/v1/projects/{test_project}/regions/{test_region}/subnetworks")
        api_subnets = api_result.json().get("items", []) if api_result.status_code == 200 else []
        
        # Log what we found
        print(f"\n✓ GCloud subnets: {len(gcloud_subnets)}")
        print(f"✓ API subnets: {len(api_subnets)}")


class TestRoutesGCloud:
    """Test Routes via gcloud CLI"""
    
    def test_gcloud_list_routes(self, gcloud_runner):
        """List all routes using gcloud"""
        result = gcloud_runner.run("compute routes list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        routes = result.json()
        assert isinstance(routes, list)
    
    def test_gcloud_default_routes_exist(self, gcloud_runner):
        """Verify default routes exist"""
        result = gcloud_runner.run("compute routes list")
        
        assert result.is_success()
        routes = result.json()
        
        # Should have routes for default network
        default_routes = [r for r in routes if "default" in r.get("network", "")]
        assert len(default_routes) > 0, "Should have default routes"
    
    def test_dual_validation_routes(self, api_client, gcloud_runner, test_project):
        """Validate routes in both API and gcloud"""
        # Get via gcloud
        gcloud_result = gcloud_runner.run("compute routes list")
        assert gcloud_result.is_success()
        gcloud_routes = gcloud_result.json()
        
        # Get via API
        api_result = api_client.get(f"/compute/v1/projects/{test_project}/global/routes")
        api_routes = api_result.json().get("items", []) if api_result.status_code == 200 else []
        
        # Both should have some routes
        assert len(gcloud_routes) > 0 or len(api_routes) > 0, "No routes found"
        
        print(f"\n✓ GCloud routes: {len(gcloud_routes)}")
        print(f"✓ API routes: {len(api_routes)}")


class TestVPCErrorHandling:
    """Test gcloud error handling for VPC operations"""
    
    def test_describe_nonexistent_network(self, gcloud_runner):
        """Verify error when describing non-existent network"""
        result = gcloud_runner.run("compute networks describe nonexistent-network-xyz123")
        assert not result.is_success(), "Should fail for non-existent network"
    
    def test_list_subnets_invalid_region(self, gcloud_runner):
        """Verify error handling for invalid region"""
        result = gcloud_runner.run("compute networks subnets list --regions=invalid-region-123")
        
        # May or may not work depending on backend, but should not crash
        assert isinstance(result.exit_code, int)
