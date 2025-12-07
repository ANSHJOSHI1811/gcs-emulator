"""
Tests for Compute Engine Networking System (Phase 5)
Tests IP allocation, firewall rules, and network metadata
"""

import pytest
import json
from app import create_app
from app.factory import db
from app.models.project import Project
from app.models.compute import Instance, NetworkAllocation, FirewallRule
from app.services.compute_service import ComputeService
from app.services.networking_service import NetworkingService
from app.services.firewall_service import FirewallService


@pytest.fixture
def app():
    """Create test app"""
    import os
    os.environ["FLASK_ENV"] = "testing"
    
    app = create_app(config_name="testing")
    app.config["COMPUTE_DOCKER_ENABLED"] = False  # Disable Docker for tests
    
    with app.app_context():
        db.create_all()
        
        # Create test project
        project = Project(id="test-project", name="Test Project")
        db.session.add(project)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestInternalIPAllocation:
    """Test internal IP allocation from 10.0.0.0/16 pool"""
    
    def test_internal_ip_allocation_sequential(self, app):
        """Test sequential internal IP allocation"""
        with app.app_context():
            project_id = "test-project"
            
            # Allocate first IP
            ip1 = NetworkingService.allocate_internal_ip(project_id)
            assert ip1 == "10.0.0.1"
            
            # Allocate second IP
            ip2 = NetworkingService.allocate_internal_ip(project_id)
            assert ip2 == "10.0.0.2"
            
            # Allocate third IP
            ip3 = NetworkingService.allocate_internal_ip(project_id)
            assert ip3 == "10.0.0.3"
    
    def test_internal_ip_counter_persistence(self, app):
        """Test internal IP counter persists across allocations"""
        with app.app_context():
            project_id = "test-project"
            
            # Allocate multiple IPs
            for i in range(5):
                ip = NetworkingService.allocate_internal_ip(project_id)
                assert ip == f"10.0.0.{i+1}"
            
            # Check counter value
            allocation = NetworkAllocation.query.filter_by(project_id=project_id).first()
            assert allocation.internal_counter == 6  # Next available
    
    def test_internal_ip_no_duplicates(self, app):
        """Test no duplicate internal IPs are allocated"""
        with app.app_context():
            project_id = "test-project"
            
            allocated_ips = set()
            for _ in range(10):
                ip = NetworkingService.allocate_internal_ip(project_id)
                assert ip not in allocated_ips, f"Duplicate IP allocated: {ip}"
                allocated_ips.add(ip)
            
            assert len(allocated_ips) == 10
    
    def test_internal_ip_octet_overflow(self, app):
        """Test internal IP allocation handles octet overflow correctly"""
        with app.app_context():
            project_id = "test-project"
            
            # Pre-set counter to test overflow
            allocation = NetworkingService.ensure_network_allocation(project_id)
            allocation.internal_counter = 255
            db.session.commit()
            
            # Should allocate 10.0.0.255
            ip1 = NetworkingService.allocate_internal_ip(project_id)
            assert ip1 == "10.0.0.255"
            
            # Should allocate 10.0.1.0 (overflow to next octet)
            ip2 = NetworkingService.allocate_internal_ip(project_id)
            assert ip2 == "10.0.1.0"
            
            # Should allocate 10.0.1.1
            ip3 = NetworkingService.allocate_internal_ip(project_id)
            assert ip3 == "10.0.1.1"


class TestExternalIPAllocation:
    """Test external IP allocation from 203.0.113.0/24 pool"""
    
    def test_external_ip_allocation_sequential(self, app):
        """Test sequential external IP allocation"""
        with app.app_context():
            project_id = "test-project"
            
            # Allocate first IP (starts at 10)
            ip1 = NetworkingService.allocate_external_ip(project_id)
            assert ip1 == "203.0.113.10"
            
            # Allocate second IP
            ip2 = NetworkingService.allocate_external_ip(project_id)
            assert ip2 == "203.0.113.11"
            
            # Allocate third IP
            ip3 = NetworkingService.allocate_external_ip(project_id)
            assert ip3 == "203.0.113.12"
    
    def test_external_ip_no_duplicates(self, app):
        """Test no duplicate external IPs are allocated"""
        with app.app_context():
            project_id = "test-project"
            
            allocated_ips = set()
            for _ in range(10):
                ip = NetworkingService.allocate_external_ip(project_id)
                assert ip not in allocated_ips, f"Duplicate IP allocated: {ip}"
                allocated_ips.add(ip)
            
            assert len(allocated_ips) == 10


class TestInstanceNetworking:
    """Test networking integration with instance lifecycle"""
    
    def test_instance_creation_allocates_internal_ip(self, app):
        """Test instance creation allocates internal IP"""
        with app.app_context():
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="test-instance-1",
                machine_type="e2-micro"
            )
            
            assert instance.internal_ip is not None
            assert instance.internal_ip.startswith("10.0.")
    
    def test_instance_creation_allocates_external_ip(self, app):
        """Test instance creation allocates external IP"""
        with app.app_context():
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="test-instance-2",
                machine_type="e2-micro"
            )
            
            assert instance.external_ip is not None
            assert instance.external_ip.startswith("203.0.113.")
    
    def test_instance_external_ip_persists_on_stop(self, app):
        """Test external IP persists when instance is stopped"""
        with app.app_context():
            # Create and get external IP
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="test-instance-3",
                machine_type="e2-micro"
            )
            original_external_ip = instance.external_ip
            
            # Stop instance
            instance = ComputeService.stop_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="test-instance-3"
            )
            
            # External IP should be preserved
            assert instance.external_ip == original_external_ip
    
    def test_instance_external_ip_persists_on_restart(self, app):
        """Test external IP persists when instance is restarted"""
        with app.app_context():
            # Create instance
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="test-instance-4",
                machine_type="e2-micro"
            )
            original_external_ip = instance.external_ip
            
            # Stop instance
            instance = ComputeService.stop_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="test-instance-4"
            )
            
            # Start instance
            instance = ComputeService.start_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="test-instance-4"
            )
            
            # External IP should be preserved
            assert instance.external_ip == original_external_ip
    
    def test_instance_network_interfaces_in_response(self, app):
        """Test instance response includes networkInterfaces"""
        with app.app_context():
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="test-instance-5",
                machine_type="e2-micro"
            )
            
            instance_dict = instance.to_dict()
            
            # Check networkInterfaces exists
            assert "networkInterfaces" in instance_dict
            assert len(instance_dict["networkInterfaces"]) > 0
            
            # Check structure
            interface = instance_dict["networkInterfaces"][0]
            assert "networkIP" in interface
            assert interface["networkIP"] == instance.internal_ip
            
            assert "accessConfigs" in interface
            assert len(interface["accessConfigs"]) > 0
            
            access_config = interface["accessConfigs"][0]
            assert access_config["type"] == "ONE_TO_ONE_NAT"
            assert access_config["natIP"] == instance.external_ip


class TestFirewallRules:
    """Test firewall rule management"""
    
    def test_create_firewall_rule(self, app):
        """Test creating a firewall rule"""
        with app.app_context():
            rule = FirewallService.create_firewall_rule(
                project_id="test-project",
                name="allow-ssh",
                direction="INGRESS",
                protocol="tcp",
                port=22,
                action="ALLOW",
                target_tags=["ssh-server"]
            )
            
            assert rule.name == "allow-ssh"
            assert rule.direction == "INGRESS"
            assert rule.protocol == "tcp"
            assert rule.port == 22
            assert rule.action == "ALLOW"
            assert "ssh-server" in rule.target_tags
    
    def test_list_firewall_rules(self, app):
        """Test listing firewall rules"""
        with app.app_context():
            # Create multiple rules
            FirewallService.create_firewall_rule(
                project_id="test-project",
                name="allow-ssh",
                direction="INGRESS",
                protocol="tcp",
                port=22
            )
            
            FirewallService.create_firewall_rule(
                project_id="test-project",
                name="allow-http",
                direction="INGRESS",
                protocol="tcp",
                port=80
            )
            
            rules = FirewallService.list_firewall_rules("test-project")
            assert len(rules) == 2
            rule_names = [r.name for r in rules]
            assert "allow-ssh" in rule_names
            assert "allow-http" in rule_names
    
    def test_delete_firewall_rule(self, app):
        """Test deleting a firewall rule"""
        with app.app_context():
            # Create rule
            FirewallService.create_firewall_rule(
                project_id="test-project",
                name="allow-ssh",
                direction="INGRESS",
                protocol="tcp",
                port=22
            )
            
            # Delete rule
            result = FirewallService.delete_firewall_rule("test-project", "allow-ssh")
            assert result is True
            
            # Verify deleted
            rules = FirewallService.list_firewall_rules("test-project")
            assert len(rules) == 0
    
    def test_firewall_rule_to_dict(self, app):
        """Test firewall rule JSON serialization"""
        with app.app_context():
            rule = FirewallService.create_firewall_rule(
                project_id="test-project",
                name="allow-https",
                direction="INGRESS",
                protocol="tcp",
                port=443,
                action="ALLOW",
                source_ranges=["0.0.0.0/0"]
            )
            
            rule_dict = rule.to_dict()
            
            assert rule_dict["kind"] == "compute#firewall"
            assert rule_dict["name"] == "allow-https"
            assert rule_dict["direction"] == "INGRESS"
            assert "allowed" in rule_dict
            assert rule_dict["allowed"][0]["IPProtocol"] == "tcp"
            assert "443" in rule_dict["allowed"][0]["ports"]


class TestFirewallAPI:
    """Test firewall rule API endpoints"""
    
    def test_create_firewall_rule_endpoint(self, client):
        """Test POST /compute/v1/projects/{project}/global/firewalls"""
        response = client.post(
            "/compute/v1/projects/test-project/global/firewalls",
            json={
                "name": "allow-ssh",
                "direction": "INGRESS",
                "allowed": [{"IPProtocol": "tcp", "ports": ["22"]}],
                "targetTags": ["ssh-server"],
                "sourceRanges": ["0.0.0.0/0"]
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["kind"] == "compute#operation"
        assert data["status"] == "DONE"
    
    def test_list_firewall_rules_endpoint(self, client):
        """Test GET /compute/v1/projects/{project}/global/firewalls"""
        # Create a rule first
        client.post(
            "/compute/v1/projects/test-project/global/firewalls",
            json={
                "name": "allow-http",
                "direction": "INGRESS",
                "allowed": [{"IPProtocol": "tcp", "ports": ["80"]}]
            }
        )
        
        # List rules
        response = client.get("/compute/v1/projects/test-project/global/firewalls")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["kind"] == "compute#firewallList"
        assert len(data["items"]) > 0
    
    def test_delete_firewall_rule_endpoint(self, client):
        """Test DELETE /compute/v1/projects/{project}/global/firewalls/{firewall}"""
        # Create a rule first
        client.post(
            "/compute/v1/projects/test-project/global/firewalls",
            json={
                "name": "allow-ssh",
                "direction": "INGRESS",
                "allowed": [{"IPProtocol": "tcp", "ports": ["22"]}]
            }
        )
        
        # Delete rule
        response = client.delete("/compute/v1/projects/test-project/global/firewalls/allow-ssh")
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["kind"] == "compute#operation"
        assert data["status"] == "DONE"


class TestIdempotency:
    """Test idempotent operations"""
    
    def test_ip_allocation_is_idempotent(self, app):
        """Test IP allocation produces consistent results"""
        with app.app_context():
            project_id = "test-project"
            
            # Create instances
            for i in range(3):
                instance = ComputeService.create_instance(
                    project_id=project_id,
                    zone="us-central1-a",
                    name=f"instance-{i}",
                    machine_type="e2-micro"
                )
                
                # IPs should be unique and sequential
                assert instance.internal_ip == f"10.0.0.{i+1}"
                assert instance.external_ip == f"203.0.113.{i+10}"
    
    def test_network_allocation_table_created_once(self, app):
        """Test NetworkAllocation is created only once per project"""
        with app.app_context():
            project_id = "test-project"
            
            # Multiple allocations
            for _ in range(5):
                NetworkingService.allocate_internal_ip(project_id)
            
            # Should only have one allocation record
            allocations = NetworkAllocation.query.filter_by(project_id=project_id).all()
            assert len(allocations) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
