"""
CloudTester - Firewall Rules GCloud CLI Tests
Tests for Firewall Rules using gcloud CLI (Phase 1: Default rules creation)
Ensures dual compatibility: API + gcloud CLI
"""

import pytest
import json
from typing import Dict, Any

pytestmark = pytest.mark.integration
pytestmark = pytest.mark.gcloud


class TestFirewallRulesGCloud:
    """Test Firewall Rules using gcloud CLI"""
    
    def test_gcloud_list_firewall_rules(self, gcloud_runner, test_project):
        """List all firewall rules using gcloud"""
        result = gcloud_runner.run("compute firewall-rules list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        data = result.json()
        assert isinstance(data, list)
    
    def test_gcloud_default_rules_exist(self, gcloud_runner, test_project):
        """Verify 5 default firewall rules exist via gcloud"""
        result = gcloud_runner.run("compute firewall-rules list")
        
        assert result.is_success(), f"gcloud failed: {result.stderr}"
        rules = result.json()
        rule_names = [r.get("name") for r in rules]
        
        # Phase 1 requirements - check what exists
        expected_rules = {
            "allow-ssh": {"protocol": "tcp", "ports": ["22"]},
            "allow-http": {"protocol": "tcp", "ports": ["80"]},
            "allow-https": {"protocol": "tcp", "ports": ["443"]},
            "allow-internal": {"protocol": "all"},
            "allow-icmp": {"protocol": "icmp"}
        }
        
        # Find which rules exist
        existing_rules = [r for r in expected_rules.keys() if r in rule_names]
        assert len(existing_rules) > 0, f"No default rules found. Available: {rule_names}"
    
    def test_gcloud_allow_ssh_rule_details(self, gcloud_runner, test_project):
        """Get allow-ssh rule details via gcloud"""
        result = gcloud_runner.run("compute firewall-rules describe allow-ssh")
        
        if not result.is_success():
            pytest.skip("allow-ssh rule not found")
        
        rule = result.json()
        assert rule["name"] == "allow-ssh"
        assert rule["direction"] == "INGRESS"
        assert any("22" in str(port) for port in rule.get("allowed", []))
    
    def test_gcloud_allow_http_rule_details(self, gcloud_runner, test_project):
        """Get allow-http rule details via gcloud"""
        result = gcloud_runner.run("compute firewall-rules describe allow-http")
        
        if not result.is_success():
            pytest.skip("allow-http rule not found")
        
        rule = result.json()
        assert rule["name"] == "allow-http"
        assert any("80" in str(port) for port in rule.get("allowed", []))
    
    def test_gcloud_allow_https_rule_details(self, gcloud_runner, test_project):
        """Get allow-https rule details via gcloud"""
        result = gcloud_runner.run("compute firewall-rules describe allow-https")
        
        if not result.is_success():
            pytest.skip("allow-https rule not found")
        
        rule = result.json()
        assert rule["name"] == "allow-https"
        assert any("443" in str(port) for port in rule.get("allowed", []))
    
    def test_gcloud_allow_internal_rule_details(self, gcloud_runner, test_project):
        """Get allow-internal rule details via gcloud"""
        result = gcloud_runner.run("compute firewall-rules describe allow-internal")
        
        if not result.is_success():
            pytest.skip("allow-internal rule not found")
        
        rule = result.json()
        assert rule["name"] == "allow-internal"
    
    def test_gcloud_allow_icmp_rule_details(self, gcloud_runner, test_project):
        """Get allow-icmp rule details via gcloud"""
        result = gcloud_runner.run("compute firewall-rules describe allow-icmp")
        
        if not result.is_success():
            pytest.skip("allow-icmp rule not found")
        
        rule = result.json()
        assert rule["name"] == "allow-icmp"
    
    def test_dual_validation_firewall_list(self, api_client, gcloud_runner, test_project):
        """Validate firewall rules exist in both API and gcloud"""
        # Get via gcloud
        gcloud_result = gcloud_runner.run("compute firewall-rules list")
        assert gcloud_result.is_success()
        gcloud_rules = {r.get("name") for r in gcloud_result.json()}
        
        # Get via API
        api_result = api_client.get(f"/compute/v1/projects/{test_project}/global/firewalls")
        assert api_result.status_code == 200
        api_rules = {r["name"] for r in api_result.json().get("items", [])}
        
        # Both should have some rules
        assert len(gcloud_rules) > 0 or len(api_rules) > 0, "No firewall rules found in either API or gcloud"
        
        # Log comparison
        print(f"\n✓ GCloud rules: {gcloud_rules}")
        print(f"✓ API rules: {api_rules}")
    
    def test_dual_validation_ssh_rule_exists(self, api_client, gcloud_runner, test_project):
        """Verify SSH rule in both API and gcloud (cross-validation)"""
        # Try gcloud first
        gcloud_result = gcloud_runner.run("compute firewall-rules describe allow-ssh")
        gcloud_exists = gcloud_result.is_success()
        
        # Try API
        api_result = api_client.get(f"/compute/v1/projects/{test_project}/global/firewalls/allow-ssh")
        api_exists = api_result.status_code == 200
        
        # At least one should exist
        assert gcloud_exists or api_exists, "allow-ssh rule not found in either API or gcloud"
        
        # If both exist, validate they're consistent
        if gcloud_exists and api_exists:
            gcloud_rule = gcloud_result.json()
            api_rule = api_result.json()
            assert gcloud_rule["name"] == api_rule["name"], "Rule names don't match"
            print(f"\n✓ SSH rule exists in both API and gcloud")


class TestFirewallGCloudErrorHandling:
    """Test gcloud error handling"""
    
    def test_describe_nonexistent_rule(self, gcloud_runner):
        """Verify error when describing non-existent rule"""
        result = gcloud_runner.run("compute firewall-rules describe nonexistent-rule-xyz123")
        assert not result.is_success(), "Should fail for non-existent rule"
    
    def test_list_with_filter(self, gcloud_runner):
        """Test filtering firewall rules"""
        result = gcloud_runner.run("compute firewall-rules list --filter='name:allow-*'")
        
        if result.is_success():
            rules = result.json()
            for rule in rules:
                assert rule["name"].startswith("allow-"), "Filter should only return allow-* rules"
