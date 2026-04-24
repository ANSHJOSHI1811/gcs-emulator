"""
Secret Manager storage layer.

Manages secrets, versions, and related operations in memory.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging
from collections import defaultdict

from .models import (
    Secret, SecretVersion, Replication,
    ReplicationPolicy, SecretVersionState,
    generate_random_password
)

logger = logging.getLogger(__name__)


class SecretManagerStorage:
    """In-memory storage for secrets and versions."""

    def __init__(self):
        # Structure: {project: {secret_id: Secret}}
        self.secrets: Dict[str, Dict[str, Secret]] = defaultdict(dict)

    # ========================================================================
    # SECRET OPERATIONS
    # ========================================================================

    def create_secret(
        self,
        project_id: str,
        secret_id: str,
        labels: Optional[Dict[str, str]] = None,
        description: str = "",
        replication_policy: str = ReplicationPolicy.AUTOMATIC,
        replication_locations: Optional[List[str]] = None
    ) -> Secret:
        """Create a new secret."""
        
        # Check if secret already exists
        if secret_id in self.secrets[project_id]:
            raise ValueError(f"Secret '{secret_id}' already exists")
        
        # Create replication config
        replication = Replication(
            policy=replication_policy,
            locations=replication_locations or []
        )
        
        # Create secret
        secret = Secret(
            secret_id=secret_id,
            project_id=project_id,
            labels=labels or {},
            description=description,
            replication=replication
        )
        
        self.secrets[project_id][secret_id] = secret
        
        logger.info(f"Created secret {project_id}/{secret_id}")
        return secret

    def get_secret(self, project_id: str, secret_id: str) -> Optional[Secret]:
        """Get a secret by ID."""
        return self.secrets[project_id].get(secret_id)

    def list_secrets(self, project_id: str) -> List[Secret]:
        """List all secrets in a project."""
        return list(self.secrets[project_id].values())

    def update_secret(
        self,
        project_id: str,
        secret_id: str,
        labels: Optional[Dict[str, str]] = None,
        description: Optional[str] = None
    ) -> Secret:
        """Update secret metadata."""
        
        secret = self.get_secret(project_id, secret_id)
        if not secret:
            raise ValueError(f"Secret '{secret_id}' not found")
        
        if labels is not None:
            secret.labels = labels
        if description is not None:
            secret.description = description
        
        secret.updated_time = datetime.now(timezone.utc)
        
        logger.info(f"Updated secret {project_id}/{secret_id}")
        return secret

    def delete_secret(self, project_id: str, secret_id: str) -> bool:
        """Delete a secret."""
        
        if secret_id not in self.secrets[project_id]:
            return False
        
        del self.secrets[project_id][secret_id]
        
        logger.info(f"Deleted secret {project_id}/{secret_id}")
        return True

    # ========================================================================
    # SECRET VERSION OPERATIONS
    # ========================================================================

    def add_secret_version(
        self,
        project_id: str,
        secret_id: str,
        payload: bytes
    ) -> SecretVersion:
        """Add a new version to a secret."""
        
        secret = self.get_secret(project_id, secret_id)
        if not secret:
            raise ValueError(f"Secret '{secret_id}' not found")
        
        version = secret.add_version(payload)
        
        logger.info(f"Added version {version.version_id} to secret {secret_id}")
        return version

    def get_secret_version(
        self,
        project_id: str,
        secret_id: str,
        version_id: str
    ) -> Optional[SecretVersion]:
        """Get a specific secret version."""
        
        secret = self.get_secret(project_id, secret_id)
        if not secret:
            return None
        
        return secret.versions.get(version_id)

    def list_secret_versions(
        self,
        project_id: str,
        secret_id: str
    ) -> List[SecretVersion]:
        """List all versions of a secret."""
        
        secret = self.get_secret(project_id, secret_id)
        if not secret:
            return []
        
        return list(secret.versions.values())

    def access_secret_version(
        self,
        project_id: str,
        secret_id: str,
        version_id: str = "latest"
    ) -> Optional[SecretVersion]:
        """
        Access (read) a secret version.
        
        If version_id is "latest", returns the current enabled version.
        """
        
        secret = self.get_secret(project_id, secret_id)
        if not secret:
            return None
        
        if version_id == "latest":
            return secret.get_latest_version()
        
        version = secret.versions.get(version_id)
        if version and version.state == SecretVersionState.ENABLED:
            return version
        
        return None

    def disable_secret_version(
        self,
        project_id: str,
        secret_id: str,
        version_id: str
    ) -> Optional[SecretVersion]:
        """Disable a specific secret version."""
        
        version = self.get_secret_version(project_id, secret_id, version_id)
        if not version:
            return None
        
        version.state = SecretVersionState.DISABLED
        
        logger.info(f"Disabled version {version_id} of secret {secret_id}")
        return version

    def enable_secret_version(
        self,
        project_id: str,
        secret_id: str,
        version_id: str
    ) -> Optional[SecretVersion]:
        """Enable a specific secret version."""
        
        version = self.get_secret_version(project_id, secret_id, version_id)
        if not version:
            return None
        
        if version.state == SecretVersionState.DESTROYED:
            raise ValueError(f"Cannot enable destroyed version {version_id}")
        
        version.state = SecretVersionState.ENABLED
        
        # Update secret's current version
        secret = self.get_secret(project_id, secret_id)
        if secret:
            secret.current_version_id = version_id
        
        logger.info(f"Enabled version {version_id} of secret {secret_id}")
        return version

    def destroy_secret_version(
        self,
        project_id: str,
        secret_id: str,
        version_id: str
    ) -> Optional[SecretVersion]:
        """Destroy (permanently delete) a secret version."""
        
        version = self.get_secret_version(project_id, secret_id, version_id)
        if not version:
            return None
        
        version.state = SecretVersionState.DESTROYED
        version.destroy_time = datetime.now(timezone.utc)
        
        logger.info(f"Destroyed version {version_id} of secret {secret_id}")
        return version

    # ========================================================================
    # PASSWORD GENERATION
    # ========================================================================

    def generate_random_password(
        self,
        length: int = 32,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_digits: bool = True,
        include_symbols: bool = True,
        exclude_ambiguous: bool = True
    ) -> str:
        """Generate a random password."""
        return generate_random_password(
            length=length,
            include_uppercase=include_uppercase,
            include_lowercase=include_lowercase,
            include_digits=include_digits,
            include_symbols=include_symbols,
            exclude_ambiguous=exclude_ambiguous
        )

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        total_secrets = sum(len(project_secrets) for project_secrets in self.secrets.values())
        total_versions = sum(
            len(secret.versions)
            for project_secrets in self.secrets.values()
            for secret in project_secrets.values()
        )
        
        return {
            'total_secrets': total_secrets,
            'total_versions': total_versions,
        }

    def clear(self):
        """Clear all storage."""
        self.secrets.clear()
        logger.info("Cleared all secret storage")


# Global storage instance
storage = SecretManagerStorage()
