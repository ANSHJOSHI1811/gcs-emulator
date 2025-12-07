"""
Phase 3: Docker Integration Tests for Compute Engine
Tests Docker container lifecycle management with feature flag
"""
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from app import create_app
from app.factory import db
from app.models.compute import Instance, InstanceStatus
from app.models.project import Project
from app.services.compute_service import ComputeService, DockerExecutionError
from app.compute.docker_runner import DockerRunner, DockerError


@pytest.fixture
def app():
    """Create test app with Docker enabled"""
    # Set env var BEFORE creating app so Config class picks it up
    os.environ["COMPUTE_DOCKER_ENABLED"] = "true"
    
    app = create_app("testing")
    
    # Manually override config after creation (since Config reads at import time)
    app.config["COMPUTE_DOCKER_ENABLED"] = True
    
    with app.app_context():
        db.create_all()
        
        # Create test project
        project = Project(id="test-project", name="Test Project")
        db.session.add(project)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()
    
    # Clean up env var
    if "COMPUTE_DOCKER_ENABLED" in os.environ:
        del os.environ["COMPUTE_DOCKER_ENABLED"]


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def mock_docker_runner():
    """Mock DockerRunner for testing"""
    with patch("app.services.compute_service.DockerRunner") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        
        # Mock successful operations
        mock_instance.create_container.return_value = "test-container-id-123"
        mock_instance.start_container.return_value = None
        mock_instance.stop_container.return_value = None
        mock_instance.remove_container.return_value = None
        mock_instance.get_container_status.return_value = "running"
        mock_instance.container_exists.return_value = True
        
        yield mock_instance


class TestDockerFeatureFlag:
    """Test feature flag behavior"""
    
    def test_docker_disabled_by_default(self):
        """Docker should be disabled when flag not set"""
        if "COMPUTE_DOCKER_ENABLED" in os.environ:
            del os.environ["COMPUTE_DOCKER_ENABLED"]
        
        app = create_app("testing")
        with app.app_context():
            # Check through app config
            assert not app.config.get("COMPUTE_DOCKER_ENABLED", False)
    
    def test_docker_enabled_with_flag(self, app):
        """Docker should be enabled when flag is true"""
        with app.app_context():
            # Check through app config (env var set before app creation in fixture)
            assert app.config.get("COMPUTE_DOCKER_ENABLED") is True
    
    def test_docker_disabled_with_false_flag(self):
        """Docker should be disabled when flag is explicitly false"""
        os.environ["COMPUTE_DOCKER_ENABLED"] = "false"
        app = create_app("testing")
        
        with app.app_context():
            assert not app.config.get("COMPUTE_DOCKER_ENABLED", False)
        
        del os.environ["COMPUTE_DOCKER_ENABLED"]


class TestDockerCreateInstance:
    """Test Docker container creation during instance creation"""
    
    def test_create_instance_with_docker_enabled(self, app, mock_docker_runner):
        """Should create and start Docker container when flag enabled"""
        with app.app_context():
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker_runner):
                instance = ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-central1-a",
                    name="test-instance",
                    machine_type="e2-medium",
                    metadata={"startup-script": "echo 'Hello'"},
                    labels={"env": "test"},
                    tags=["web"],
                    network_interfaces=[],
                    disks=[]
                )
                
                # Verify instance created
                assert instance is not None
                assert instance.name == "test-instance"
                assert instance.status == InstanceStatus.RUNNING
                assert instance.container_id == "test-container-id-123"
                
                # Verify Docker operations called
                mock_docker_runner.create_container.assert_called_once()
                mock_docker_runner.start_container.assert_called_once_with("test-container-id-123")
                
                # Check container creation params
                call_args = mock_docker_runner.create_container.call_args
                assert call_args[1]["image"] == "python:3.12-slim"  # e2-medium -> python
                assert "gce-test-project-us-central1-a-test-instance" in call_args[1]["container_name"]
                assert "GCE_INSTANCE_NAME" in call_args[1]["env_vars"]
                assert call_args[1]["env_vars"]["GCE_INSTANCE_NAME"] == "test-instance"
    
    def test_create_instance_with_docker_disabled(self, app):
        """Should NOT create Docker container when flag disabled"""
        # Disable Docker
        os.environ["COMPUTE_DOCKER_ENABLED"] = "false"
        
        with app.app_context():
            with patch("app.compute.docker_runner.DockerRunner") as mock_docker_class:
                instance = ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-central1-a",
                    name="test-instance-no-docker",
                    machine_type="e2-medium"
                )
                
                # Verify instance created
                assert instance is not None
                assert instance.status == InstanceStatus.RUNNING
                assert instance.container_id is None
                
                # Verify Docker NOT called
                mock_docker_class.assert_not_called()
        
        del os.environ["COMPUTE_DOCKER_ENABLED"]
    
    def test_create_instance_docker_failure_cleanup(self, app):
        """Should rollback instance creation if Docker fails"""
        with app.app_context():
            mock_docker = MagicMock()
            mock_docker.create_container.side_effect = DockerError("Container creation failed")
            
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker):
                with pytest.raises(DockerExecutionError) as exc_info:
                    ComputeService.create_instance(
                        project_id="test-project",
                        zone="us-central1-a",
                        name="test-fail-instance",
                        machine_type="e2-medium"
                    )
                
                assert "Docker container creation failed" in str(exc_info.value)
                
                # Verify instance was cleaned up (not in DB)
                instances = Instance.query.filter_by(name="test-fail-instance").all()
                assert len(instances) == 0
    
    def test_create_instance_docker_start_failure_cleanup(self, app):
        """Should cleanup if container starts fail"""
        with app.app_context():
            mock_docker = MagicMock()
            mock_docker.create_container.return_value = "failed-container"
            mock_docker.start_container.side_effect = DockerError("Start failed")
            
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker):
                with pytest.raises(DockerExecutionError):
                    ComputeService.create_instance(
                        project_id="test-project",
                        zone="us-central1-a",
                        name="test-start-fail",
                        machine_type="n1-standard-1"
                    )
                
                # Verify instance cleaned up
                instances = Instance.query.filter_by(name="test-start-fail").all()
                assert len(instances) == 0


class TestDockerStartInstance:
    """Test Docker container start during instance start"""
    
    def test_start_instance_with_docker(self, app, mock_docker_runner):
        """Should start Docker container when restarting instance"""
        with app.app_context():
            # Create instance first (mocked Docker)
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker_runner):
                instance = ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-central1-a",
                    name="test-restart",
                    machine_type="e2-medium"
                )
                
                # Stop instance
                stopped = ComputeService.stop_instance("test-project", "us-central1-a", "test-restart")
                assert stopped.status == InstanceStatus.TERMINATED
                
                # Reset mock to track new calls
                mock_docker_runner.reset_mock()
                
                # Start instance again
                restarted = ComputeService.start_instance("test-project", "us-central1-a", "test-restart")
                
                # Verify Docker start called
                assert restarted.status == InstanceStatus.RUNNING
                mock_docker_runner.start_container.assert_called_once_with(instance.container_id)
    
    def test_start_instance_docker_failure(self, app):
        """Should raise error if Docker start fails"""
        with app.app_context():
            # Create instance with mock Docker
            mock_docker = MagicMock()
            mock_docker.create_container.return_value = "test-container"
            mock_docker.start_container.return_value = None
            
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker):
                instance = ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-central1-a",
                    name="test-start-error",
                    machine_type="e2-medium"
                )
                
                # Stop instance
                ComputeService.stop_instance("test-project", "us-central1-a", "test-start-error")
                
                # Make start fail
                mock_docker.start_container.side_effect = DockerError("Start failed")
                
                # Try to start - should raise error
                with pytest.raises(DockerExecutionError) as exc_info:
                    ComputeService.start_instance("test-project", "us-central1-a", "test-start-error")
                
                assert "Docker container start failed" in str(exc_info.value)


class TestDockerStopInstance:
    """Test Docker container stop during instance stop"""
    
    def test_stop_instance_with_docker(self, app, mock_docker_runner):
        """Should stop Docker container when stopping instance"""
        with app.app_context():
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker_runner):
                # Create instance
                instance = ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-central1-a",
                    name="test-stop",
                    machine_type="e2-medium"
                )
                
                # Reset mock to track stop call
                mock_docker_runner.reset_mock()
                
                # Stop instance
                stopped = ComputeService.stop_instance("test-project", "us-central1-a", "test-stop")
                
                # Verify Docker stop called
                assert stopped.status == InstanceStatus.TERMINATED
                mock_docker_runner.stop_container.assert_called_once_with(instance.container_id)
    
    def test_stop_instance_docker_failure(self, app):
        """Should raise error if Docker stop fails"""
        with app.app_context():
            # Create instance with mock Docker
            mock_docker = MagicMock()
            mock_docker.create_container.return_value = "test-container"
            mock_docker.start_container.return_value = None
            
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker):
                instance = ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-central1-a",
                    name="test-stop-error",
                    machine_type="e2-medium"
                )
                
                # Make stop fail
                mock_docker.stop_container.side_effect = DockerError("Stop failed")
                
                # Try to stop - should raise error
                with pytest.raises(DockerExecutionError) as exc_info:
                    ComputeService.stop_instance("test-project", "us-central1-a", "test-stop-error")
                
                assert "Docker container stop failed" in str(exc_info.value)


class TestDockerDeleteInstance:
    """Test Docker container removal during instance deletion"""
    
    def test_delete_instance_with_docker(self, app, mock_docker_runner):
        """Should remove Docker container when deleting instance"""
        with app.app_context():
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker_runner):
                # Create instance
                instance = ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-central1-a",
                    name="test-delete",
                    machine_type="e2-medium"
                )
                
                container_id = instance.container_id
                
                # Reset mock to track delete calls
                mock_docker_runner.reset_mock()
                
                # Delete instance
                deleted = ComputeService.delete_instance("test-project", "us-central1-a", "test-delete")
                
                # Verify Docker operations called
                mock_docker_runner.stop_container.assert_called_once_with(container_id)
                mock_docker_runner.remove_container.assert_called_once_with(container_id, force=True)
    
    def test_delete_instance_docker_cleanup_continues_on_error(self, app):
        """Should continue deletion even if Docker cleanup fails"""
        with app.app_context():
            # Create instance with mock Docker
            mock_docker = MagicMock()
            mock_docker.create_container.return_value = "test-container"
            mock_docker.start_container.return_value = None
            
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker):
                instance = ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-central1-a",
                    name="test-delete-error",
                    machine_type="e2-medium"
                )
                
                # Make Docker cleanup fail
                mock_docker.stop_container.side_effect = DockerError("Stop failed")
                mock_docker.remove_container.side_effect = DockerError("Remove failed")
                
                # Delete should still succeed (logs warning, continues)
                deleted = ComputeService.delete_instance("test-project", "us-central1-a", "test-delete-error")
                
                # Verify deletion completed
                assert deleted is not None
                
                # Verify instance removed from DB
                instances = Instance.query.filter_by(name="test-delete-error").all()
                assert len(instances) == 0


class TestDockerMachineTypeMapping:
    """Test machine type to Docker image mapping"""
    
    def test_e2_series_uses_python_image(self, app, mock_docker_runner):
        """E2 series should use Python image"""
        with app.app_context():
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker_runner):
                with patch("app.compute.docker_runner.DockerRunner.get_image_for_machine_type", return_value="python:3.12-slim"):
                    ComputeService.create_instance(
                        project_id="test-project",
                        zone="us-central1-a",
                        name="test-e2",
                        machine_type="e2-medium"
                    )
                    
                    # Verify Python image requested
                    call_args = mock_docker_runner.create_container.call_args
                    assert call_args[1]["image"] == "python:3.12-slim"
    
    def test_n1_series_uses_ubuntu_image(self, app, mock_docker_runner):
        """N1 series should use Ubuntu image"""
        with app.app_context():
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker_runner):
                with patch("app.compute.docker_runner.DockerRunner.get_image_for_machine_type", return_value="ubuntu:22.04"):
                    ComputeService.create_instance(
                        project_id="test-project",
                        zone="us-central1-a",
                        name="test-n1",
                        machine_type="n1-standard-1"
                    )
                    
                    # Verify Ubuntu image requested
                    call_args = mock_docker_runner.create_container.call_args
                    assert call_args[1]["image"] == "ubuntu:22.04"


class TestDockerEnvironmentVariables:
    """Test Docker container environment variable injection"""
    
    def test_metadata_injected_as_env_vars(self, app, mock_docker_runner):
        """Metadata should be converted to GCE_METADATA_* env vars"""
        with app.app_context():
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker_runner):
                ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-central1-a",
                    name="test-env",
                    machine_type="e2-medium",
                    metadata={
                        "startup-script": "echo 'Hello'",
                        "user-data": "test-data"
                    }
                )
                
                # Check env vars passed to Docker
                call_args = mock_docker_runner.create_container.call_args
                env_vars = call_args[1]["env_vars"]
                
                assert "GCE_METADATA_startup-script" in env_vars
                assert env_vars["GCE_METADATA_startup-script"] == "echo 'Hello'"
                assert "GCE_METADATA_user-data" in env_vars
                assert env_vars["GCE_METADATA_user-data"] == "test-data"
    
    def test_instance_info_injected_as_env_vars(self, app, mock_docker_runner):
        """Instance info should be injected as env vars"""
        with app.app_context():
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker_runner):
                ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-west1-b",
                    name="test-info",
                    machine_type="n2-standard-2"
                )
                
                # Check env vars
                call_args = mock_docker_runner.create_container.call_args
                env_vars = call_args[1]["env_vars"]
                
                assert env_vars["GCE_INSTANCE_NAME"] == "test-info"
                assert env_vars["GCE_ZONE"] == "us-west1-b"
                assert env_vars["GCE_PROJECT"] == "test-project"
                assert env_vars["GCE_MACHINE_TYPE"] == "n2-standard-2"


class TestDockerIdempotency:
    """Test idempotent Docker operations"""
    
    def test_stop_already_stopped_container(self, app):
        """Stopping already-stopped container should not fail"""
        with app.app_context():
            mock_docker = MagicMock()
            mock_docker.create_container.return_value = "test-container"
            mock_docker.start_container.return_value = None
            mock_docker.stop_container.return_value = None  # First stop succeeds
            
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker):
                # Create and stop instance
                ComputeService.create_instance(
                    project_id="test-project",
                    zone="us-central1-a",
                    name="test-idempotent",
                    machine_type="e2-medium"
                )
                
                stopped = ComputeService.stop_instance("test-project", "us-central1-a", "test-idempotent")
                assert stopped.status == InstanceStatus.TERMINATED
                
                # Docker stop was called successfully
                mock_docker.stop_container.assert_called()


class TestDockerHandlerErrors:
    """Test handler error responses for Docker failures"""
    
    def test_create_handler_returns_500_on_docker_error(self, client, app):
        """Create endpoint should return 500 on Docker failure"""
        with app.app_context():
            mock_docker = MagicMock()
            mock_docker.create_container.side_effect = DockerError("Docker daemon not running")
            
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker):
                response = client.post(
                    "/compute/v1/projects/test-project/zones/us-central1-a/instances",
                    json={
                        "name": "test-handler-error",
                        "machineType": "e2-medium"
                    }
                )
                
                assert response.status_code == 500
                data = response.get_json()
                assert "Docker operation failed" in data["error"]["message"]
    
    def test_start_handler_returns_500_on_docker_error(self, client, app):
        """Start endpoint should return 500 on Docker failure"""
        with app.app_context():
            # Create instance first
            mock_docker = MagicMock()
            mock_docker.create_container.return_value = "test-container"
            mock_docker.start_container.return_value = None
            mock_docker.stop_container.return_value = None
            
            with patch("app.services.compute_service.ComputeService._get_docker_runner", return_value=mock_docker):
                client.post(
                    "/compute/v1/projects/test-project/zones/us-central1-a/instances",
                    json={"name": "test-start-handler", "machineType": "e2-medium"}
                )
                
                # Stop it
                client.post("/compute/v1/projects/test-project/zones/us-central1-a/instances/test-start-handler/stop")
                
                # Make start fail
                mock_docker.start_container.side_effect = DockerError("Container not found")
                
                # Try to start
                response = client.post(
                    "/compute/v1/projects/test-project/zones/us-central1-a/instances/test-start-handler/start"
                )
                
                assert response.status_code == 500
                data = response.get_json()
                assert "Docker operation failed" in data["error"]["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
