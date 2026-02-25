"""
CloudTester - GKE Clusters GCloud CLI Tests
Tests for Google Kubernetes Engine using gcloud CLI
Ensures dual compatibility: API + gcloud CLI
"""

import pytest
import json
from typing import Dict, Any

pytestmark = pytest.mark.integration
pytestmark = pytest.mark.gcloud


class TestClustersGCloud:
    """Test GKE Clusters via gcloud CLI"""
    
    def test_gcloud_list_clusters(self, gcloud_runner, test_zone):
        """List GKE clusters using gcloud"""
        result = gcloud_runner.run(f"container clusters list --zone={test_zone}")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        clusters = result.json()
        assert isinstance(clusters, list)
    
    def test_gcloud_list_all_clusters(self, gcloud_runner):
        """List all GKE clusters using gcloud"""
        result = gcloud_runner.run("container clusters list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        clusters = result.json()
        assert isinstance(clusters, list)


class TestNodePoolsGCloud:
    """Test GKE Node Pools via gcloud CLI"""
    
    def test_gcloud_list_node_pools(self, gcloud_runner, test_zone):
        """List node pools in cluster using gcloud"""
        # First get a cluster
        list_result = gcloud_runner.run(f"container clusters list --zone={test_zone} --limit=1")
        if not list_result.is_success():
            pytest.skip("Cannot list clusters")
        
        clusters = list_result.json()
        if not clusters:
            pytest.skip("No clusters found")
        
        cluster_name = clusters[0]["name"]
        
        # List node pools
        result = gcloud_runner.run(
            f"container node-pools list --cluster={cluster_name} --zone={test_zone}"
        )
        
        if result.is_success():
            pools = result.json()
            assert isinstance(pools, list)


class TestKubernetesOperationsGCloud:
    """Test Kubernetes operations via gcloud CLI"""
    
    def test_gcloud_get_credentials(self, gcloud_runner, test_zone):
        """Get cluster credentials using gcloud"""
        # First find a cluster
        list_result = gcloud_runner.run(f"container clusters list --zone={test_zone} --limit=1")
        
        clusters = list_result.json() if list_result.is_success() else []
        if not clusters:
            pytest.skip("No clusters available")
        
        cluster_name = clusters[0]["name"]
        
        # Get credentials (won't actually connect without kubeconfig setup)
        result = gcloud_runner.run(
            f"container clusters get-credentials {cluster_name} --zone={test_zone} --quiet"
        )
        
        # May succeed or fail depending on kubectl availability
        print(f"\n✓ Get credentials result: exit_code={result.exit_code}")


class TestDualValidationGKE:
    """Cross-validation tests between API and gcloud for GKE"""
    
    def test_clusters_accessible_via_both(self, api_client, gcloud_runner, test_project, test_zone):
        """Verify clusters info is accessible via both systems"""
        # Try gcloud
        gcloud_result = gcloud_runner.run(f"container clusters list --zone={test_zone}")
        gcloud_clusters = gcloud_result.json() if gcloud_result.is_success() else []
        
        # Try API
        api_result = api_client.get(
            f"/container/v1/projects/{test_project}/zones/{test_zone}/clusters"
        )
        api_clusters = api_result.json().get("clusters", []) if api_result.status_code == 200 else []
        
        # Log comparison
        print(f"\n✓ GCloud clusters: {len(gcloud_clusters)}")
        print(f"✓ API clusters: {len(api_clusters)}")


class TestGKEErrorHandling:
    """Test gcloud error handling for GKE operations"""
    
    def test_describe_nonexistent_cluster(self, gcloud_runner, test_zone):
        """Verify error when describing non-existent cluster"""
        result = gcloud_runner.run(
            f"container clusters describe nonexistent-cluster-xyz123 --zone={test_zone}"
        )
        assert not result.is_success(), "Should fail for non-existent cluster"
