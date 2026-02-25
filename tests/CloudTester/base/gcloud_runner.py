"""GCloudRunner for executing gcloud CLI commands"""
import subprocess
import json
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class GCloudResult:
    """Result of a gcloud command execution"""
    exit_code: int
    stdout: str
    stderr: str
    
    def is_success(self) -> bool:
        """Check if command succeeded"""
        return self.exit_code == 0
    
    def json(self) -> Dict[str, Any]:
        """Parse stdout as JSON"""
        try:
            return json.loads(self.stdout)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse gcloud output as JSON: {self.stdout}")


class GCloudRunner:
    """Wrapper for executing gcloud CLI commands"""
    
    def __init__(self, project: str = None, zone: str = None):
        self.project = project or os.getenv("TEST_PROJECT", "test-project")
        self.zone = zone or os.getenv("TEST_ZONE", "us-central1-a")
        self.region = zone.rsplit("-", 1)[0] if zone else "us-central1"
        self.gcloud_available = self._check_gcloud_available()
    
    def _check_gcloud_available(self) -> bool:
        """Check if gcloud CLI is installed"""
        try:
            result = subprocess.run(["gcloud", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def run(self, command: str, format: str = "json") -> GCloudResult:
        """Execute gcloud command"""
        if not self.gcloud_available:
            raise RuntimeError("gcloud CLI not available. Install gcloud SDK first.")
        
        # Build full command
        full_command = f"gcloud {command}"
        
        # Add format flag unless already specified
        if format and "--format" not in command:
            full_command += f" --format={format}"
        
        # Add project flag unless already specified
        if "--project" not in command:
            full_command += f" --project={self.project}"
        
        try:
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return GCloudResult(
                exit_code=result.returncode,
                stdout=result.stdout.strip(),
                stderr=result.stderr.strip()
            )
        
        except subprocess.TimeoutExpired:
            return GCloudResult(
                exit_code=1,
                stdout="",
                stderr="Command timed out after 60 seconds"
            )
        except Exception as e:
            return GCloudResult(
                exit_code=1,
                stdout="",
                stderr=str(e)
            )
    
    def set_project(self, project: str):
        """Set active project"""
        self.project = project
    
    def set_zone(self, zone: str):
        """Set active zone"""
        self.zone = zone
        self.region = zone.rsplit("-", 1)[0]
    
    def set_region(self, region: str):
        """Set active region"""
        self.region = region
