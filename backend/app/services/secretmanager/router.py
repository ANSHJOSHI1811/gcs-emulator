"""
Secret Manager API endpoints.

Implements secretmanager.googleapis.com/v1 API for secret management.
"""

from typing import Any, Dict, Optional
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from .storage import storage
from .models import ReplicationPolicy, SecretVersionState

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# SECRET MANAGEMENT
# ============================================================================

@router.post("/projects/{project}/secrets")
async def create_secret(
    project: str,
    body: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a new secret."""
    
    secret_id = body.get("secretId")
    if not secret_id:
        raise HTTPException(400, "secretId is required")
    
    try:
        # Extract replication config
        replication_config = body.get("replication", {})
        replication_policy = ReplicationPolicy.AUTOMATIC
        replication_locations = []
        
        if "userManaged" in replication_config:
            replication_policy = ReplicationPolicy.USER_MANAGED
            replicas = replication_config.get("userManaged", {}).get("replicas", [])
            replication_locations = [r.get("location") for r in replicas if "location" in r]
        
        # Create secret
        secret = storage.create_secret(
            project_id=project,
            secret_id=secret_id,
            labels=body.get("labels", {}),
            description=body.get("description", ""),
            replication_policy=replication_policy,
            replication_locations=replication_locations
        )
        
        return secret.to_dict()
    
    except ValueError as e:
        raise HTTPException(409, str(e))
    except Exception as e:
        logger.error(f"Error creating secret: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("/projects/{project}/secrets/{secret}")
async def get_secret(project: str, secret: str) -> Dict[str, Any]:
    """Get a secret by ID."""
    
    try:
        secret_obj = storage.get_secret(project, secret)
        if not secret_obj:
            raise HTTPException(404, f"Secret '{secret}' not found")
        
        return secret_obj.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting secret: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("/projects/{project}/secrets")
async def list_secrets(
    project: str,
    page_size: int = Query(100),
) -> Dict[str, Any]:
    """List all secrets in a project."""
    
    try:
        secrets_list = storage.list_secrets(project)
        
        return {
            "secrets": [s.to_dict() for s in secrets_list],
            "nextPageToken": None,
        }
    
    except Exception as e:
        logger.error(f"Error listing secrets: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.patch("/projects/{project}/secrets/{secret}")
async def update_secret(
    project: str,
    secret: str,
    body: Dict[str, Any],
) -> Dict[str, Any]:
    """Update secret metadata."""
    
    try:
        # Extract fields to update
        update_data = body.get("secret", {})
        
        secret_obj = storage.update_secret(
            project_id=project,
            secret_id=secret,
            labels=update_data.get("labels"),
            description=update_data.get("description")
        )
        
        return secret_obj.to_dict()
    
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Error updating secret: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.delete("/projects/{project}/secrets/{secret}")
async def delete_secret(project: str, secret: str) -> Dict[str, Any]:
    """Delete a secret."""
    
    try:
        deleted = storage.delete_secret(project, secret)
        if not deleted:
            raise HTTPException(404, f"Secret '{secret}' not found")
        
        return {"deleted": True}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting secret: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


# ============================================================================
# SECRET VERSION MANAGEMENT
# ============================================================================

@router.post("/projects/{project}/secrets/{secret}:addVersion")
async def add_secret_version(
    project: str,
    secret: str,
    body: Dict[str, Any],
) -> Dict[str, Any]:
    """Add a new version to a secret."""
    
    try:
        # Extract payload
        payload_data = body.get("payload", {})
        payload = payload_data.get("data", "").encode() if isinstance(payload_data.get("data"), str) else b""
        
        version = storage.add_secret_version(project, secret, payload)
        
        return {
            "name": version.name,
            "state": version.state,
            "createTime": version.create_time.isoformat() + 'Z',
        }
    
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Error adding version: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("/projects/{project}/secrets/{secret}/versions")
async def list_secret_versions(
    project: str,
    secret: str,
    page_size: int = Query(100),
) -> Dict[str, Any]:
    """List all versions of a secret."""
    
    try:
        versions = storage.list_secret_versions(project, secret)
        
        return {
            "versions": [v.to_dict() for v in versions],
            "nextPageToken": None,
        }
    
    except Exception as e:
        logger.error(f"Error listing versions: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("/projects/{project}/secrets/{secret}/versions/{version}")
async def get_secret_version(
    project: str,
    secret: str,
    version: str,
) -> Dict[str, Any]:
    """Get a specific secret version."""
    
    try:
        version_obj = storage.get_secret_version(project, secret, version)
        if not version_obj:
            raise HTTPException(404, f"Version '{version}' not found")
        
        return version_obj.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting version: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.post("/projects/{project}/secrets/{secret}/versions/{version}:access")
async def access_secret_version(
    project: str,
    secret: str,
    version: str,
) -> Dict[str, Any]:
    """Access (read) a secret version."""
    
    try:
        version_obj = storage.access_secret_version(project, secret, version)
        if not version_obj:
            raise HTTPException(404, f"Version '{version}' not accessible")
        
        return {
            "name": version_obj.name,
            "payload": {
                "data": version_obj.payload.decode() if version_obj.payload else ""
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accessing version: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.post("/projects/{project}/secrets/{secret}/versions/{version}:disable")
async def disable_secret_version(
    project: str,
    secret: str,
    version: str,
) -> Dict[str, Any]:
    """Disable a secret version."""
    
    try:
        version_obj = storage.disable_secret_version(project, secret, version)
        if not version_obj:
            raise HTTPException(404, f"Version '{version}' not found")
        
        return version_obj.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling version: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.post("/projects/{project}/secrets/{secret}/versions/{version}:enable")
async def enable_secret_version(
    project: str,
    secret: str,
    version: str,
) -> Dict[str, Any]:
    """Enable a secret version."""
    
    try:
        version_obj = storage.enable_secret_version(project, secret, version)
        if not version_obj:
            raise HTTPException(404, f"Version '{version}' not found")
        
        return version_obj.to_dict()
    
    except ValueError as e:
        raise HTTPException(409, str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling version: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.post("/projects/{project}/secrets/{secret}/versions/{version}:destroy")
async def destroy_secret_version(
    project: str,
    secret: str,
    version: str,
) -> Dict[str, Any]:
    """Destroy (permanently delete) a secret version."""
    
    try:
        version_obj = storage.destroy_secret_version(project, secret, version)
        if not version_obj:
            raise HTTPException(404, f"Version '{version}' not found")
        
        return version_obj.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error destroying version: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


# ============================================================================
# PASSWORD GENERATION
# ============================================================================

@router.post("/generateRandomPassword")
async def generate_random_password(body: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a random password (no project scope needed)."""
    
    try:
        length = body.get("length", 32)
        include_uppercase = body.get("includeUppercase", True)
        include_lowercase = body.get("includeLowercase", True)
        include_digits = body.get("includeDigits", True)
        include_symbols = body.get("includeSymbols", True)
        exclude_ambiguous = body.get("excludeAmbiguous", True)
        
        password = storage.generate_random_password(
            length=length,
            include_uppercase=include_uppercase,
            include_lowercase=include_lowercase,
            include_digits=include_digits,
            include_symbols=include_symbols,
            exclude_ambiguous=exclude_ambiguous
        )
        
        return {
            "password": password,
            "length": len(password),
        }
    
    except Exception as e:
        logger.error(f"Error generating password: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


# ============================================================================
# HEALTH & STATS
# ============================================================================

@router.get("/secretmanager/health")
async def health_check() -> Dict[str, Any]:
    """Health check for Secret Manager."""
    
    try:
        stats = storage.get_stats()
        return {
            "status": "healthy",
            "stats": stats,
        }
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(500, f"Error: {str(e)}")
