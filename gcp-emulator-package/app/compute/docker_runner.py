"""
Docker Runner - Abstraction layer for Docker container management
Phase 3: Adds real execution to Compute Engine instances
"""
import os
import time
import subprocess
from typing import Optional, Dict, List
from app.logging import log_service_stage


# Machine type to Docker image mapping
MACHINE_TYPE_IMAGE_MAP = {
    # E2 Series - Lightweight Python images
    "e2-micro": "python:3.12-slim",
    "e2-small": "python:3.12-slim",
    "e2-medium": "python:3.12-slim",
    "e2-standard-2": "python:3.12-slim",
    "e2-standard-4": "python:3.12-slim",
    "e2-standard-8": "python:3.12-slim",
    
    # N1 Series - Ubuntu images
    "n1-standard-1": "ubuntu:22.04",
    "n1-standard-2": "ubuntu:22.04",
    "n1-standard-4": "ubuntu:22.04",
    "n1-standard-8": "ubuntu:22.04",
    
    # N2 Series - Ubuntu images
    "n2-standard-2": "ubuntu:22.04",
    "n2-standard-4": "ubuntu:22.04",
    "n2-standard-8": "ubuntu:22.04",
}


class DockerError(Exception):
    """Raised when Docker operations fail"""
    pass


class DockerRunner:
    """
    Docker container management abstraction
    Uses subprocess to call docker CLI for maximum compatibility
    """
    
    def __init__(self):
        """Initialize Docker runner"""
        self.docker_host = os.getenv("DOCKER_HOST", None)
    
    def _run_docker_command(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """
        Run a docker command via subprocess
        
        Args:
            args: Docker command arguments (without 'docker' prefix)
            check: Whether to raise exception on non-zero exit
            
        Returns:
            CompletedProcess result
            
        Raises:
            DockerError: If command fails
        """
        cmd = ["docker"] + args
        
        log_service_stage(
            message="Executing docker command",
            details={"command": " ".join(cmd)}
        )
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check,
                timeout=60
            )
            
            if result.returncode != 0:
                log_service_stage(
                    message="Docker command failed",
                    details={
                        "command": " ".join(cmd),
                        "returncode": result.returncode,
                        "stderr": result.stderr
                    },
                    level="ERROR"
                )
                if check:
                    raise DockerError(f"Docker command failed: {result.stderr}")
            
            return result
            
        except subprocess.TimeoutExpired as e:
            log_service_stage(
                message="Docker command timed out",
                details={"command": " ".join(cmd)},
                level="ERROR"
            )
            raise DockerError(f"Docker command timed out: {' '.join(cmd)}")
            
        except FileNotFoundError:
            log_service_stage(
                message="Docker CLI not found",
                details={"command": " ".join(cmd)},
                level="ERROR"
            )
            raise DockerError("Docker CLI not found. Is Docker installed?")
            
        except Exception as e:
            log_service_stage(
                message="Unexpected error running docker command",
                details={"command": " ".join(cmd), "error": str(e)},
                level="ERROR"
            )
            raise DockerError(f"Unexpected error: {str(e)}")
    
    def create_container(
        self,
        image: str,
        name: str,
        env: Optional[Dict[str, str]] = None,
        command: Optional[str] = None
    ) -> str:
        """
        Create a Docker container (but don't start it yet)
        
        Args:
            image: Docker image name
            name: Container name
            env: Environment variables dict
            command: Optional command to run
            
        Returns:
            Container ID
            
        Raises:
            DockerError: If creation fails
        """
        start_time = time.time()
        
        log_service_stage(
            message="Creating Docker container",
            details={"image": image, "name": name}
        )
        
        # Build docker create command
        args = ["create", "--name", name]
        
        # Add environment variables
        if env:
            for key, value in env.items():
                args.extend(["-e", f"{key}={value}"])
        
        # Add image
        args.append(image)
        
        # Add command if provided
        if command:
            args.extend(command.split())
        else:
            # Default: sleep infinity to keep container running
            args.extend(["sleep", "infinity"])
        
        try:
            result = self._run_docker_command(args)
            container_id = result.stdout.strip()
            
            log_service_stage(
                message="Docker container created",
                details={
                    "container_id": container_id,
                    "image": image,
                    "name": name,
                    "duration_ms": (time.time() - start_time) * 1000
                }
            )
            
            return container_id
            
        except DockerError as e:
            log_service_stage(
                message="Failed to create container",
                details={"image": image, "name": name, "error": str(e)},
                level="ERROR"
            )
            raise
    
    def start_container(self, container_id: str) -> None:
        """
        Start a Docker container
        
        Args:
            container_id: Container ID or name
            
        Raises:
            DockerError: If start fails
        """
        start_time = time.time()
        
        log_service_stage(
            message="Starting Docker container",
            details={"container_id": container_id}
        )
        
        try:
            self._run_docker_command(["start", container_id])
            
            log_service_stage(
                message="Docker container started",
                details={
                    "container_id": container_id,
                    "duration_ms": (time.time() - start_time) * 1000
                }
            )
            
        except DockerError as e:
            log_service_stage(
                message="Failed to start container",
                details={"container_id": container_id, "error": str(e)},
                level="ERROR"
            )
            raise
    
    def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """
        Stop a Docker container
        
        Args:
            container_id: Container ID or name
            timeout: Timeout in seconds before force kill
            
        Raises:
            DockerError: If stop fails
        """
        start_time = time.time()
        
        log_service_stage(
            message="Stopping Docker container",
            details={"container_id": container_id, "timeout": timeout}
        )
        
        try:
            self._run_docker_command(["stop", "-t", str(timeout), container_id])
            
            log_service_stage(
                message="Docker container stopped",
                details={
                    "container_id": container_id,
                    "duration_ms": (time.time() - start_time) * 1000
                }
            )
            
        except DockerError as e:
            # If container is already stopped, ignore error
            if "is not running" in str(e).lower() or "no such container" in str(e).lower():
                log_service_stage(
                    message="Container already stopped or does not exist",
                    details={"container_id": container_id},
                    level="WARNING"
                )
                return
            
            log_service_stage(
                message="Failed to stop container",
                details={"container_id": container_id, "error": str(e)},
                level="ERROR"
            )
            raise
    
    def remove_container(self, container_id: str, force: bool = True) -> None:
        """
        Remove a Docker container
        
        Args:
            container_id: Container ID or name
            force: Force removal even if running
            
        Raises:
            DockerError: If removal fails
        """
        start_time = time.time()
        
        log_service_stage(
            message="Removing Docker container",
            details={"container_id": container_id, "force": force}
        )
        
        try:
            args = ["rm"]
            if force:
                args.append("-f")
            args.append(container_id)
            
            self._run_docker_command(args)
            
            log_service_stage(
                message="Docker container removed",
                details={
                    "container_id": container_id,
                    "duration_ms": (time.time() - start_time) * 1000
                }
            )
            
        except DockerError as e:
            # If container doesn't exist, ignore error
            if "no such container" in str(e).lower():
                log_service_stage(
                    message="Container does not exist (already removed)",
                    details={"container_id": container_id},
                    level="WARNING"
                )
                return
            
            log_service_stage(
                message="Failed to remove container",
                details={"container_id": container_id, "error": str(e)},
                level="ERROR"
            )
            raise
    
    def get_container_status(self, container_id: str) -> Optional[str]:
        """
        Get container status
        
        Args:
            container_id: Container ID or name
            
        Returns:
            Status string (running, exited, paused, etc.) or None if not found
        """
        try:
            result = self._run_docker_command(
                ["inspect", "--format", "{{.State.Status}}", container_id],
                check=False
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return None
                
        except DockerError:
            return None
    
    def container_exists(self, container_id: str) -> bool:
        """
        Check if container exists
        
        Args:
            container_id: Container ID or name
            
        Returns:
            True if exists, False otherwise
        """
        return self.get_container_status(container_id) is not None
    
    @staticmethod
    def get_image_for_machine_type(machine_type: str) -> str:
        """
        Get Docker image for a machine type
        
        Args:
            machine_type: Machine type name
            
        Returns:
            Docker image name
        """
        return MACHINE_TYPE_IMAGE_MAP.get(machine_type, "ubuntu:22.04")
    
    def is_docker_available(self) -> bool:
        """
        Check if Docker is available
        
        Returns:
            True if Docker is available, False otherwise
        """
        try:
            result = self._run_docker_command(["info"], check=False)
            return result.returncode == 0
        except DockerError:
            return False
