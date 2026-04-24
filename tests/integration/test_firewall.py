"""
CloudTester - Firewall Tests
Tests for Firewall Rules (Phase 1: Default rules creation)
"""

import pytest

pytestmark = pytest.mark.integration


class TestDefaultFirewallRules:
    """Test Default Firewall Rules Creation (Phase 1)"""
    
    def test_list_firewall_rules(self, api_client, test_project):
        """List all firewall rules"""
        path = f"/compute/v1/projects/{test_project}/global/firewalls"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        rules = data.get("items", [])
        assert isinstance(rules, list)
    
    def test_default_rules_exist(self, api_client, test_project):
        """Verify 5 default firewall rules are created"""
        path = f"/compute/v1/projects/{test_project}/global/firewalls"
        resp = api_client.get(path)
        
        assert resp.status_code == 200
        data = resp.json()
        
        rules = data.get("items", [])
        rule_names = [r["name"] for r in rules]
        
        # Phase 1 requirements
        expected_rules = {
            "allow-ssh": {"protocol": "tcp", "ports": ["22"]},
            "allow-http": {"protocol": "tcp", "ports": ["80"]},
            "allow-https": {"protocol": "tcp", "ports": ["443"]},
            "allow-internal": {"protocol": "all"},
            "allow-icmp": {"protocol": "icmp"}
        }
        
        for rule_name in expected_rules.keys():
            assert rule_name in rule_names, f"Missing default rule: {rule_name}"
    
    def test_allow_ssh_rule(self, api_client, test_project):
        """Verify allow-ssh rule configuration"""
        path = f"/compute/v1/projects/{test_project}/global/firewalls/allow-ssh"
        resp = api_client.get(path)
        
        if resp.status_code == 404:
            pytest.skip("allow-ssh rule not yet created")
        
        assert resp.status_code == 200
        rule = resp.json()
        
        assert rule["name"] == "allow-ssh"
        assert rule["direction"] == "INGRESS"
        assert "22" in str(rule.get("allowed", []))
    
    def test_allow_http_rule(self, api_client, test_project):
        """Verify allow-http rule configuration"""
        path = f"/compute/v1/projects/{test_project}/global/firewalls/allow-http"
        resp = api_client.get(path)
        
        if resp.status_code == 404:
            pytest.skip("allow-http rule not yet created")
        
        assert resp.status_code == 200
        rule = resp.json()
        
        assert rule["name"] == "allow-http"
        assert "80" in str(rule.get("allowed", []))
    
    def test_allow_https_rule(self, api_client, test_project):
        """Verify allow-https rule configuration"""
        path = f"/compute/v1/projects/{test_project}/global/firewalls/allow-https"
        resp = api_client.get(path)
        
        if resp.status_code == 404:
            pytest.skip("allow-https rule not yet created")
        
        assert resp.status_code == 200
        rule = resp.json()
        
        assert rule["name"] == "allow-https"
        assert "443" in str(rule.get("allowed", []))
    
    def test_allow_internal_rule(self, api_client, test_project):
        """Verify allow-internal rule configuration"""
        path = f"/compute/v1/projects/{test_project}/global/firewalls/allow-internal"
        resp = api_client.get(path)
        
        if resp.status_code == 404:
            pytest.skip("allow-internal rule not yet created")
        
        assert resp.status_code == 200
        rule = resp.json()
        
        assert rule["name"] == "allow-internal"
        assert rule["sourceRanges"] == ["10.0.0.0/8"]
    
    def test_allow_icmp_rule(self, api_client, test_project):
        """Verify allow-icmp rule configuration"""
        path = f"/compute/v1/projects/{test_project}/global/firewalls/allow-icmp"
        resp = api_client.get(path)
        
        if resp.status_code == 404:
            pytest.skip("allow-icmp rule not yet created")
        
        assert resp.status_code == 200
        rule = resp.json()
        
        assert rule["name"] == "allow-icmp"
        assert "icmp" in str(rule.get("allowed", []))


class TestCustomFirewallRules:
    """Test Custom Firewall Rules"""
    
    def test_create_custom_rule(self, api_client, test_project, sample_firewall_payload):
        """Create a custom firewall rule"""
        path = f"/compute/v1/projects/{test_project}/global/firewalls"
        
        resp = api_client.post(path, sample_firewall_payload)
        
        assert resp.status_code in [200, 201]
        rule = resp.json()
        
        assert rule["name"] == sample_firewall_payload["name"]
    
    def test_delete_custom_rule(self, api_client, test_project, sample_firewall_payload):
        """Delete a custom firewall rule"""
        # Create rule first
        create_path = f"/compute/v1/projects/{test_project}/global/firewalls"
        create_resp = api_client.post(create_path, sample_firewall_payload)
        
        if create_resp.status_code not in [200, 201]:
            pytest.skip("Cannot create rule")
        
        rule_name = sample_firewall_payload["name"]
        
        # Delete rule
        delete_path = f"/compute/v1/projects/{test_project}/global/firewalls/{rule_name}"
        delete_resp = api_client.delete(delete_path)
        
        assert delete_resp.status_code in [200, 204]
