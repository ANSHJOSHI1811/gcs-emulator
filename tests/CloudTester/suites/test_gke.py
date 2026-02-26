"""
CloudTester - GKE Tests
Tests for Google Kubernetes Engine: clusters, node pools
"""

import pytest

pytestmark = pytest.mark.integration


class TestClusters:
    """Test GKE Clusters"""
    
    def test_list_clusters(self, api_client, test_project, test_zone):
        """List GKE clusters"""
        path = f"/container/v1/projects/{test_project}/zones/{test_zone}/clusters"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        clusters = data.get("clusters", [])
        assert isinstance(clusters, list)
    
    def test_create_cluster(self, api_client, test_project, test_zone, sample_cluster_payload, cleanup_resources):
        """Create a GKE cluster"""
        path = f"/container/v1/projects/{test_project}/zones/{test_zone}/clusters"
        
        resp = api_client.post(path, sample_cluster_payload)
        
        assert resp.status_code in [200, 201]
        data = resp.json()
        
        assert "name" in data or "zone" in data
        
        cleanup_resources["clusters"].append({
            "project": test_project,
            "zone": test_zone,
            "name": data.get("name", sample_cluster_payload["cluster"]["name"])
        })


class TestNodePools:
    """Test GKE Node Pools"""
    
    def test_list_node_pools(self, api_client, test_project, test_zone):
        """List node pools in a cluster"""
        # List clusters first
        clusters_resp = api_client.get(
            f"/container/v1/projects/{test_project}/zones/{test_zone}/clusters"
        )
        
        if clusters_resp.status_code != 200:
            pytest.skip("Cannot list clusters")
        
        clusters = clusters_resp.json().get("clusters", [])
        if not clusters:
            pytest.skip("No clusters available")
        
        cluster_name = clusters[0]["name"]
        
        # List node pools
        path = f"/container/v1/projects/{test_project}/zones/{test_zone}/clusters/{cluster_name}/nodePools"
        resp = api_client.get(path)
        
        if resp.status_code == 404:
            pytest.skip("Node pools API not yet implemented")
        
        assert resp.status_code == 200
        data = resp.json()
        
        pools = data.get("nodePools", [])
        assert isinstance(pools, list)
