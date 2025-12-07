"""
Unit tests for Compute Engine service
Phase 1: Tests for metadata/state management (no Docker logic)
"""
import pytest
from app.models.compute import Instance, InstanceStatus, MachineType
from app.services.compute_service import ComputeService
from app.models.project import Project
from app.factory import db


class TestComputeService:
    """Test Compute Engine service operations"""
    
    @pytest.fixture(autouse=True)
    def setup_project(self, app):
        """Setup test project before each test"""
        with app.app_context():
            project = Project(id="test-project", name="Test Project")
            db.session.add(project)
            db.session.commit()
    
    def test_create_instance_basic(self, app):
        """Test basic instance creation"""
        with app.app_context():
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="test-instance",
                machine_type="e2-medium"
            )
            
            assert instance is not None
            assert instance.name == "test-instance"
            assert instance.zone == "us-central1-a"
            assert instance.machine_type == "e2-medium"
            assert instance.status == InstanceStatus.RUNNING  # Phase 1: Immediately RUNNING
            assert instance.project_id == "test-project"
    
    def test_create_instance_with_metadata(self, app):
        """Test instance creation with metadata and labels"""
        with app.app_context():
            metadata = {"startup-script": "echo hello", "user-data": "test"}
            labels = {"env": "dev", "team": "platform"}
            tags = ["http-server", "https-server"]
            
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="test-instance-meta",
                machine_type="e2-small",
                metadata=metadata,
                labels=labels,
                tags=tags
            )
            
            assert instance.instance_metadata == metadata
            assert instance.labels == labels
            assert instance.tags == tags
    
    def test_create_instance_invalid_project(self, app):
        """Test instance creation with non-existent project"""
        with app.app_context():
            with pytest.raises(ValueError, match="Project .* not found"):
                ComputeService.create_instance(
                    project_id="nonexistent-project",
                    zone="us-central1-a",
                    name="test-instance",
                    machine_type="e2-medium"
                )
    
    def test_create_instance_invalid_machine_type(self, app):
        """Test instance creation with invalid machine type"""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid machine type"):
                ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-central1-a",
                    name="test-instance",
                    machine_type="invalid-type"
                )
    
    def test_create_instance_duplicate_name(self, app):
        """Test creating instance with duplicate name in same zone"""
        with app.app_context():
            # Create first instance
            ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="duplicate-instance",
                machine_type="e2-medium"
            )
            
            # Try to create duplicate
            with pytest.raises(ValueError, match="already exists"):
                ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-central1-a",
                    name="duplicate-instance",
                    machine_type="e2-medium"
                )
    
    def test_create_instance_same_name_different_zone(self, app):
        """Test creating instances with same name in different zones (should work)"""
        with app.app_context():
            # Create first instance in zone A
            instance1 = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="same-name",
                machine_type="e2-medium"
            )
            
            # Create second instance with same name in zone B
            instance2 = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-b",
                name="same-name",
                machine_type="e2-medium"
            )
            
            assert instance1.name == instance2.name
            assert instance1.zone != instance2.zone
            assert instance1.id != instance2.id
    
    def test_list_instances_empty(self, app):
        """Test listing instances when none exist"""
        with app.app_context():
            instances = ComputeService.list_instances("test-project", "us-central1-a")
            assert instances == []
    
    def test_list_instances(self, app):
        """Test listing instances in a zone"""
        with app.app_context():
            # Create multiple instances
            ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="instance-1",
                machine_type="e2-medium"
            )
            ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="instance-2",
                machine_type="e2-small"
            )
            ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-b",
                name="instance-3",
                machine_type="e2-medium"
            )
            
            # List instances in zone A
            instances_a = ComputeService.list_instances("test-project", "us-central1-a")
            assert len(instances_a) == 2
            assert all(i.zone == "us-central1-a" for i in instances_a)
            
            # List instances in zone B
            instances_b = ComputeService.list_instances("test-project", "us-central1-b")
            assert len(instances_b) == 1
            assert instances_b[0].name == "instance-3"
    
    def test_list_instances_all_zones(self, app):
        """Test listing all instances across zones"""
        with app.app_context():
            # Create instances in different zones
            ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="instance-1",
                machine_type="e2-medium"
            )
            ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-b",
                name="instance-2",
                machine_type="e2-medium"
            )
            
            # List all instances (no zone filter)
            all_instances = ComputeService.list_instances("test-project", zone=None)
            assert len(all_instances) == 2
    
    def test_get_instance(self, app):
        """Test getting a specific instance"""
        with app.app_context():
            # Create instance
            created = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="get-test-instance",
                machine_type="e2-medium"
            )
            
            # Get instance
            retrieved = ComputeService.get_instance(
                "test-project",
                "us-central1-a",
                "get-test-instance"
            )
            
            assert retrieved.id == created.id
            assert retrieved.name == created.name
            assert retrieved.zone == created.zone
    
    def test_get_instance_not_found(self, app):
        """Test getting non-existent instance"""
        with app.app_context():
            with pytest.raises(ValueError, match="not found"):
                ComputeService.get_instance(
                    "test-project",
                    "us-central1-a",
                    "nonexistent-instance"
                )
    
    def test_stop_instance(self, app):
        """Test stopping a running instance"""
        with app.app_context():
            # Create instance (starts as RUNNING in Phase 1)
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="stop-test-instance",
                machine_type="e2-medium"
            )
            
            assert instance.status == InstanceStatus.RUNNING
            
            # Stop instance
            stopped = ComputeService.stop_instance(
                "test-project",
                "us-central1-a",
                "stop-test-instance"
            )
            
            assert stopped.status == InstanceStatus.STOPPED
            assert stopped.last_stop_timestamp is not None
    
    def test_stop_already_stopped_instance(self, app):
        """Test stopping an already stopped instance"""
        with app.app_context():
            # Create and stop instance
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="already-stopped",
                machine_type="e2-medium"
            )
            ComputeService.stop_instance("test-project", "us-central1-a", "already-stopped")
            
            # Try to stop again
            with pytest.raises(ValueError, match="already stopped"):
                ComputeService.stop_instance("test-project", "us-central1-a", "already-stopped")
    
    def test_start_instance(self, app):
        """Test starting a stopped instance"""
        with app.app_context():
            # Create, stop, then start instance
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="start-test-instance",
                machine_type="e2-medium"
            )
            ComputeService.stop_instance("test-project", "us-central1-a", "start-test-instance")
            
            # Start instance
            started = ComputeService.start_instance(
                "test-project",
                "us-central1-a",
                "start-test-instance"
            )
            
            assert started.status == InstanceStatus.RUNNING
            assert started.last_start_timestamp is not None
    
    def test_start_already_running_instance(self, app):
        """Test starting an already running instance"""
        with app.app_context():
            # Create instance (already RUNNING)
            ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="already-running",
                machine_type="e2-medium"
            )
            
            # Try to start again
            with pytest.raises(ValueError, match="already running"):
                ComputeService.start_instance("test-project", "us-central1-a", "already-running")
    
    def test_reset_instance(self, app):
        """Test resetting a running instance"""
        with app.app_context():
            # Create instance
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="reset-test-instance",
                machine_type="e2-medium"
            )
            
            original_start = instance.last_start_timestamp
            
            # Reset instance
            reset = ComputeService.reset_instance(
                "test-project",
                "us-central1-a",
                "reset-test-instance"
            )
            
            assert reset.status == InstanceStatus.RUNNING
            assert reset.last_start_timestamp != original_start
            assert reset.last_stop_timestamp is not None
    
    def test_reset_stopped_instance(self, app):
        """Test resetting a stopped instance (should fail)"""
        with app.app_context():
            # Create and stop instance
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="stopped-reset",
                machine_type="e2-medium"
            )
            ComputeService.stop_instance("test-project", "us-central1-a", "stopped-reset")
            
            # Try to reset stopped instance
            with pytest.raises(ValueError, match="must be RUNNING"):
                ComputeService.reset_instance("test-project", "us-central1-a", "stopped-reset")
    
    def test_delete_instance(self, app):
        """Test deleting an instance"""
        with app.app_context():
            # Create instance
            ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="delete-test-instance",
                machine_type="e2-medium"
            )
            
            # Verify it exists
            instance = ComputeService.get_instance("test-project", "us-central1-a", "delete-test-instance")
            assert instance is not None
            
            # Delete it
            ComputeService.delete_instance("test-project", "us-central1-a", "delete-test-instance")
            
            # Verify it's gone
            with pytest.raises(ValueError, match="not found"):
                ComputeService.get_instance("test-project", "us-central1-a", "delete-test-instance")
    
    def test_instance_lifecycle_complete(self, app):
        """Test complete instance lifecycle: create -> stop -> start -> reset -> delete"""
        with app.app_context():
            name = "lifecycle-instance"
            
            # Create
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name=name,
                machine_type="e2-medium"
            )
            assert instance.status == InstanceStatus.RUNNING
            
            # Stop
            stopped = ComputeService.stop_instance("test-project", "us-central1-a", name)
            assert stopped.status == InstanceStatus.STOPPED
            
            # Start
            started = ComputeService.start_instance("test-project", "us-central1-a", name)
            assert started.status == InstanceStatus.RUNNING
            
            # Reset
            reset = ComputeService.reset_instance("test-project", "us-central1-a", name)
            assert reset.status == InstanceStatus.RUNNING
            
            # Delete
            ComputeService.delete_instance("test-project", "us-central1-a", name)
            
            # Verify deleted
            with pytest.raises(ValueError):
                ComputeService.get_instance("test-project", "us-central1-a", name)
    
    def test_get_serial_port_output(self, app):
        """Test getting serial port output (Phase 1: placeholder)"""
        with app.app_context():
            # Create instance
            ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="serial-test",
                machine_type="e2-medium"
            )
            
            # Get serial output
            output = ComputeService.get_instance_serial_port_output(
                "test-project",
                "us-central1-a",
                "serial-test",
                port=1
            )
            
            assert isinstance(output, str)
            assert "serial-test" in output  # Should mention instance name
            assert "Phase 1" in output  # Should indicate Phase 1 placeholder


class TestMachineType:
    """Test MachineType helper class"""
    
    def test_get_all_machine_types(self):
        """Test getting all machine types"""
        types = MachineType.get_all()
        
        assert isinstance(types, dict)
        assert len(types) > 0
        assert "e2-medium" in types
        assert "n1-standard-1" in types
    
    def test_get_specific_machine_type(self):
        """Test getting specific machine type"""
        e2_medium = MachineType.get("e2-medium")
        
        assert e2_medium is not None
        assert e2_medium["cpus"] == 1
        assert e2_medium["memory_mb"] == 4096
    
    def test_is_valid_machine_type(self):
        """Test validating machine types"""
        assert MachineType.is_valid("e2-medium") is True
        assert MachineType.is_valid("n1-standard-2") is True
        assert MachineType.is_valid("invalid-type") is False
    
    def test_to_gce_format(self):
        """Test converting to GCE API format"""
        gce_format = MachineType.to_gce_format("e2-medium", "test-project", "us-central1-a")
        
        assert gce_format is not None
        assert gce_format["kind"] == "compute#machineType"
        assert gce_format["name"] == "e2-medium"
        assert gce_format["guestCpus"] == 1
        assert gce_format["memoryMb"] == 4096
        assert "test-project" in gce_format["zone"]
        assert "us-central1-a" in gce_format["zone"]


class TestInstanceModel:
    """Test Instance model methods"""
    
    @pytest.fixture(autouse=True)
    def setup_project(self, app):
        """Setup test project before each test"""
        with app.app_context():
            project = Project(id="test-project", name="Test Project")
            db.session.add(project)
            db.session.commit()
    
    def test_instance_to_dict(self, app):
        """Test instance serialization to GCE format"""
        with app.app_context():
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="dict-test",
                machine_type="e2-medium",
                metadata={"key": "value"},
                labels={"env": "test"}
            )
            
            instance_dict = instance.to_dict()
            
            # Verify GCE format
            assert instance_dict["kind"] == "compute#instance"
            assert instance_dict["name"] == "dict-test"
            assert instance_dict["status"] == InstanceStatus.RUNNING
            assert "test-project" in instance_dict["zone"]
            assert "machineType" in instance_dict
            assert "metadata" in instance_dict
            assert "labels" in instance_dict
            assert instance_dict["labels"]["env"] == "test"
    
    def test_instance_to_summary_dict(self, app):
        """Test instance lightweight summary serialization"""
        with app.app_context():
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="summary-test",
                machine_type="e2-medium"
            )
            
            summary = instance.to_summary_dict()
            
            # Verify summary has essential fields only
            assert "id" in summary
            assert "name" in summary
            assert "zone" in summary
            assert "status" in summary
            assert "machineType" in summary
            # Should not have detailed fields
            assert "metadata" not in summary
            assert "networkInterfaces" not in summary
    
    def test_get_machine_type_info(self, app):
        """Test getting machine type info from instance"""
        with app.app_context():
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="mt-info-test",
                machine_type="n1-standard-2"
            )
            
            mt_info = instance.get_machine_type_info()
            
            assert mt_info["cpus"] == 2
            assert mt_info["memory_mb"] == 7680
            assert "description" in mt_info
