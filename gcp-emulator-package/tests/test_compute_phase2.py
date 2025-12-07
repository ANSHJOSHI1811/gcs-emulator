"""
Unit tests for Compute Engine Phase 2 - Full REST API lifecycle
Tests proper state transitions: PROVISIONING → STAGING → RUNNING → STOPPING → TERMINATED
"""
import pytest
from app.models.compute import Instance, InstanceStatus, MachineType
from app.services.compute_service import (
    ComputeService,
    InvalidStateError,
    InstanceNotFoundError,
    InstanceAlreadyExistsError
)
from app.models.project import Project
from app.factory import db


class TestPhase2Lifecycle:
    """Test Phase 2 instance lifecycle with proper state transitions"""
    
    @pytest.fixture(autouse=True)
    def setup_project(self, app):
        """Setup test project before each test"""
        with app.app_context():
            project = Project(id="test-project", name="Test Project")
            db.session.add(project)
            db.session.commit()
    
    def test_create_instance_state_transition(self, app):
        """Test create follows PROVISIONING → STAGING → RUNNING"""
        with app.app_context():
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="lifecycle-test",
                machine_type="e2-medium"
            )
            
            # Should end in RUNNING state after creation
            assert instance.status == InstanceStatus.RUNNING
            assert instance.last_start_timestamp is not None
            assert instance.name == "lifecycle-test"
    
    def test_create_duplicate_instance_error(self, app):
        """Test creating duplicate instance raises error"""
        with app.app_context():
            # Create first instance
            ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="duplicate-test",
                machine_type="e2-medium"
            )
            
            # Try to create duplicate
            with pytest.raises(InstanceAlreadyExistsError, match="already exists"):
                ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-central1-a",
                    name="duplicate-test",
                    machine_type="e2-medium"
                )
    
    def test_stop_running_instance(self, app):
        """Test stop transitions RUNNING → STOPPING → TERMINATED"""
        with app.app_context():
            # Create instance (starts in RUNNING)
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="stop-test",
                machine_type="e2-medium"
            )
            assert instance.status == InstanceStatus.RUNNING
            
            # Stop instance
            stopped = ComputeService.stop_instance(
                "test-project",
                "us-central1-a",
                "stop-test"
            )
            
            assert stopped.status == InstanceStatus.TERMINATED
            assert stopped.last_stop_timestamp is not None
    
    def test_stop_terminated_instance_error(self, app):
        """Test stopping already terminated instance raises error"""
        with app.app_context():
            # Create and stop instance
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="already-terminated",
                machine_type="e2-medium"
            )
            ComputeService.stop_instance("test-project", "us-central1-a", "already-terminated")
            
            # Try to stop again
            with pytest.raises(InvalidStateError, match="must be in RUNNING state"):
                ComputeService.stop_instance("test-project", "us-central1-a", "already-terminated")
    
    def test_start_terminated_instance(self, app):
        """Test start transitions TERMINATED → STAGING → RUNNING"""
        with app.app_context():
            # Create and stop instance
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="start-test",
                machine_type="e2-medium"
            )
            ComputeService.stop_instance("test-project", "us-central1-a", "start-test")
            
            # Start instance
            started = ComputeService.start_instance(
                "test-project",
                "us-central1-a",
                "start-test"
            )
            
            assert started.status == InstanceStatus.RUNNING
            assert started.last_start_timestamp is not None
    
    def test_start_running_instance_error(self, app):
        """Test starting already running instance raises error"""
        with app.app_context():
            # Create instance (already RUNNING)
            ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="already-running",
                machine_type="e2-medium"
            )
            
            # Try to start again
            with pytest.raises(InvalidStateError, match="must be in TERMINATED state"):
                ComputeService.start_instance("test-project", "us-central1-a", "already-running")
    
    def test_delete_running_instance(self, app):
        """Test deleting RUNNING instance forces stop first"""
        with app.app_context():
            # Create instance (RUNNING)
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="delete-running",
                machine_type="e2-medium"
            )
            assert instance.status == InstanceStatus.RUNNING
            
            # Delete should force stop then remove
            deleted = ComputeService.delete_instance(
                "test-project",
                "us-central1-a",
                "delete-running"
            )
            
            assert deleted is not None
            
            # Verify instance is deleted
            with pytest.raises(InstanceNotFoundError):
                ComputeService.get_instance("test-project", "us-central1-a", "delete-running")
    
    def test_delete_terminated_instance(self, app):
        """Test deleting TERMINATED instance directly"""
        with app.app_context():
            # Create and stop instance
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="delete-terminated",
                machine_type="e2-medium"
            )
            ComputeService.stop_instance("test-project", "us-central1-a", "delete-terminated")
            
            # Delete
            deleted = ComputeService.delete_instance(
                "test-project",
                "us-central1-a",
                "delete-terminated"
            )
            
            assert deleted is not None
            
            # Verify deleted
            with pytest.raises(InstanceNotFoundError):
                ComputeService.get_instance("test-project", "us-central1-a", "delete-terminated")
    
    def test_complete_lifecycle(self, app):
        """Test complete lifecycle: create → stop → start → delete"""
        with app.app_context():
            name = "complete-lifecycle"
            
            # Create (PROVISIONING → STAGING → RUNNING)
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name=name,
                machine_type="e2-medium"
            )
            assert instance.status == InstanceStatus.RUNNING
            
            # Stop (RUNNING → STOPPING → TERMINATED)
            stopped = ComputeService.stop_instance("test-project", "us-central1-a", name)
            assert stopped.status == InstanceStatus.TERMINATED
            
            # Start (TERMINATED → STAGING → RUNNING)
            started = ComputeService.start_instance("test-project", "us-central1-a", name)
            assert started.status == InstanceStatus.RUNNING
            
            # Delete (RUNNING → STOPPING → TERMINATED → removed)
            deleted = ComputeService.delete_instance("test-project", "us-central1-a", name)
            assert deleted is not None
            
            # Verify deleted
            with pytest.raises(InstanceNotFoundError):
                ComputeService.get_instance("test-project", "us-central1-a", name)
    
    def test_list_instances(self, app):
        """Test listing instances"""
        with app.app_context():
            # Create multiple instances
            ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="list-test-1",
                machine_type="e2-medium"
            )
            ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="list-test-2",
                machine_type="e2-small"
            )
            ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-b",
                name="list-test-3",
                machine_type="e2-medium"
            )
            
            # List instances in zone A
            instances_a = ComputeService.list_instances("test-project", "us-central1-a")
            assert len(instances_a) == 2
            assert all(i.zone == "us-central1-a" for i in instances_a)
            
            # List all instances
            all_instances = ComputeService.list_instances("test-project")
            assert len(all_instances) == 3
    
    def test_get_instance(self, app):
        """Test getting specific instance"""
        with app.app_context():
            # Create instance
            created = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="get-test",
                machine_type="e2-medium"
            )
            
            # Get instance
            retrieved = ComputeService.get_instance(
                "test-project",
                "us-central1-a",
                "get-test"
            )
            
            assert retrieved.id == created.id
            assert retrieved.name == created.name
            assert retrieved.status == InstanceStatus.RUNNING
    
    def test_get_nonexistent_instance(self, app):
        """Test getting non-existent instance raises error"""
        with app.app_context():
            with pytest.raises(InstanceNotFoundError, match="not found"):
                ComputeService.get_instance(
                    "test-project",
                    "us-central1-a",
                    "nonexistent"
                )
    
    def test_instance_with_metadata(self, app):
        """Test creating instance with metadata and labels"""
        with app.app_context():
            metadata = {"startup-script": "echo hello", "key": "value"}
            labels = {"env": "dev", "team": "platform"}
            tags = ["http-server", "https-server"]
            
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="metadata-test",
                machine_type="e2-medium",
                metadata=metadata,
                labels=labels,
                tags=tags
            )
            
            assert instance.instance_metadata == metadata
            assert instance.labels == labels
            assert instance.tags == tags
    
    def test_invalid_machine_type(self, app):
        """Test creating instance with invalid machine type"""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid machine type"):
                ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-central1-a",
                    name="invalid-mt",
                    machine_type="invalid-type-99"
                )
    
    def test_invalid_project(self, app):
        """Test creating instance with non-existent project"""
        with app.app_context():
            with pytest.raises(ValueError, match="Project .* not found"):
                ComputeService.create_instance(
                    project_id="nonexistent-project",
                    zone="us-central1-a",
                    name="test",
                    machine_type="e2-medium"
                )
    
    def test_serial_port_output(self, app):
        """Test getting serial port output (Phase 2: placeholder)"""
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
                port=1,
                start=0
            )
            
            assert isinstance(output, str)
            assert "serial-test" in output
            assert "Phase 2" in output
    
    def test_idempotent_operations(self, app):
        """Test that operations are properly validated (not truly idempotent yet)"""
        with app.app_context():
            # Create instance
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="idempotent-test",
                machine_type="e2-medium"
            )
            
            # Calling stop twice should fail second time
            ComputeService.stop_instance("test-project", "us-central1-a", "idempotent-test")
            
            with pytest.raises(InvalidStateError):
                ComputeService.stop_instance("test-project", "us-central1-a", "idempotent-test")
            
            # Calling start twice should fail second time
            ComputeService.start_instance("test-project", "us-central1-a", "idempotent-test")
            
            with pytest.raises(InvalidStateError):
                ComputeService.start_instance("test-project", "us-central1-a", "idempotent-test")


class TestMachineTypeCatalog:
    """Test machine type catalog functionality"""
    
    def test_get_all_machine_types(self):
        """Test getting all machine types"""
        types = MachineType.get_all()
        assert isinstance(types, dict)
        assert len(types) > 0
        assert "e2-medium" in types
        assert "n1-standard-1" in types
    
    def test_validate_machine_type(self):
        """Test machine type validation"""
        assert MachineType.is_valid("e2-medium") is True
        assert MachineType.is_valid("invalid-type") is False
    
    def test_machine_type_to_gce_format(self):
        """Test GCE format conversion"""
        gce_format = MachineType.to_gce_format("e2-medium", "test-project", "us-central1-a")
        
        assert gce_format["kind"] == "compute#machineType"
        assert gce_format["name"] == "e2-medium"
        assert "guestCpus" in gce_format
        assert "memoryMb" in gce_format


class TestInstanceModel:
    """Test Instance model methods"""
    
    @pytest.fixture(autouse=True)
    def setup_project(self, app):
        """Setup test project before each test"""
        with app.app_context():
            project = Project(id="test-project", name="Test Project")
            db.session.add(project)
            db.session.commit()
    
    def test_instance_to_dict_format(self, app):
        """Test instance serialization to GCE format"""
        with app.app_context():
            instance = ComputeService.create_instance(
                project_id="test-project",
                zone="us-central1-a",
                name="format-test",
                machine_type="e2-medium",
                metadata={"key": "value"},
                labels={"env": "test"}
            )
            
            instance_dict = instance.to_dict()
            
            # Verify GCE format
            assert instance_dict["kind"] == "compute#instance"
            assert instance_dict["name"] == "format-test"
            assert instance_dict["status"] == InstanceStatus.RUNNING
            assert "zone" in instance_dict
            assert "machineType" in instance_dict
            assert "metadata" in instance_dict
            assert "labels" in instance_dict
    
    def test_status_transitions_validation(self):
        """Test status transition validation"""
        # Valid transitions
        assert InstanceStatus.can_transition(
            InstanceStatus.PROVISIONING,
            InstanceStatus.STAGING
        ) is True
        
        assert InstanceStatus.can_transition(
            InstanceStatus.STAGING,
            InstanceStatus.RUNNING
        ) is True
        
        assert InstanceStatus.can_transition(
            InstanceStatus.RUNNING,
            InstanceStatus.STOPPING
        ) is True
        
        assert InstanceStatus.can_transition(
            InstanceStatus.STOPPING,
            InstanceStatus.TERMINATED
        ) is True
        
        assert InstanceStatus.can_transition(
            InstanceStatus.TERMINATED,
            InstanceStatus.STAGING
        ) is True
        
        # Invalid transitions
        assert InstanceStatus.can_transition(
            InstanceStatus.RUNNING,
            InstanceStatus.PROVISIONING
        ) is False
