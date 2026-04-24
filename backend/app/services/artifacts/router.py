"""Artifact Registry (simulated) API."""
from typing import Any, Dict, Optional, List
import random
import threading
import json
import logging
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.database import ArtifactRepository, get_db
from app.core.docker_manager import ensure_local_registry
from .storage import storage as image_storage
from .models import compute_digest, generate_image_id

logger = logging.getLogger(__name__)
router = APIRouter()

_ops_lock = threading.Lock()
_operations: Dict[str, Dict[str, Any]] = {}


def _repo_to_dict(repo: ArtifactRepository, project: str, location: str) -> Dict[str, Any]:
    return {
        "name": f"projects/{project}/locations/{location}/repositories/{repo.name}",
        "format": repo.format,
        "description": repo.description or "",
        "labels": repo.labels or {},
        "createTime": repo.created_at.isoformat() + "Z",
        "updateTime": repo.created_at.isoformat() + "Z",
        "registryHost": "localhost:5000",
        "dockerRepositoryPrefix": f"{location}-docker.pkg.dev/{project}/{repo.name}",
    }


def _operation(project: str, location: str, metadata: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
    op_id = random.randint(1_000_000_000_000, 9_999_999_999_999)
    name = f"projects/{project}/locations/{location}/operations/{op_id}"
    op = {
        "name": name,
        "metadata": metadata,
        "done": True,
        "response": response,
    }
    with _ops_lock:
        _operations[name] = op
        if len(_operations) > 500:
            for k in list(_operations.keys())[:100]:
                _operations.pop(k, None)
    return op


@router.post("/projects/{project}/locations/{location}/repositories", status_code=200)
def create_repository(
    project: str,
    location: str,
    body: Dict[str, Any],
    repository_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    repo_name = repository_id or body.get("repositoryId") or body.get("name", "")
    if "/repositories/" in repo_name:
        repo_name = repo_name.split("/repositories/", 1)[1]
    if not repo_name:
        raise HTTPException(400, "repository_id (query) is required")

    existing = db.query(ArtifactRepository).filter_by(
        project_id=project, location=location, name=repo_name
    ).first()
    if existing:
        raise HTTPException(409, f"Repository '{repo_name}' already exists")

    repo = ArtifactRepository(
        name=repo_name,
        project_id=project,
        location=location,
        format=body.get("format", "DOCKER"),
        description=body.get("description", ""),
        labels=body.get("labels", {}),
    )
    db.add(repo)
    db.commit()

    ensure_local_registry()

    payload = _repo_to_dict(repo, project, location)
    return _operation(
        project,
        location,
        metadata={"verb": "create", "target": f"repositories/{repo_name}"},
        response=payload,
    )


@router.get("/projects/{project}/locations/{location}/repositories")
def list_repositories(project: str, location: str, db: Session = Depends(get_db)):
    repos = db.query(ArtifactRepository).filter_by(project_id=project, location=location).all()
    return {"repositories": [_repo_to_dict(r, project, location) for r in repos]}


@router.get("/projects/{project}/locations/{location}/repositories/{repo_name}")
def get_repository(project: str, location: str, repo_name: str, db: Session = Depends(get_db)):
    repo = db.query(ArtifactRepository).filter_by(
        project_id=project, location=location, name=repo_name
    ).first()
    if not repo:
        raise HTTPException(404, f"Repository '{repo_name}' not found")
    return _repo_to_dict(repo, project, location)


@router.delete("/projects/{project}/locations/{location}/repositories/{repo_name}")
def delete_repository(project: str, location: str, repo_name: str, db: Session = Depends(get_db)):
    repo = db.query(ArtifactRepository).filter_by(
        project_id=project, location=location, name=repo_name
    ).first()
    if not repo:
        raise HTTPException(404, f"Repository '{repo_name}' not found")

    db.delete(repo)
    db.commit()

    return _operation(
        project,
        location,
        metadata={"verb": "delete", "target": f"repositories/{repo_name}"},
        response={"message": f"Repository '{repo_name}' deleted"},
    )


@router.post("/projects/{project}/locations/{location}/repositories/{repo_name}:ensureRegistry")
def ensure_registry(project: str, location: str, repo_name: str, db: Session = Depends(get_db)):
    repo = db.query(ArtifactRepository).filter_by(
        project_id=project, location=location, name=repo_name
    ).first()
    if not repo:
        raise HTTPException(404, f"Repository '{repo_name}' not found")
    reg = ensure_local_registry()
    return {
        "repository": _repo_to_dict(repo, project, location),
        "registry": reg,
        "pushExample": f"docker tag myapp:latest localhost:5000/{project}/{repo_name}/myapp:latest",
    }


@router.get("/projects/{project}/locations/{location}/operations/{operation_id}")
def get_operation(project: str, location: str, operation_id: str):
    full = f"projects/{project}/locations/{location}/operations/{operation_id}"
    with _ops_lock:
        if full in _operations:
            return _operations[full]
        if operation_id in _operations:
            return _operations[operation_id]
    return {
        "name": full,
        "done": True,
        "response": {"message": "operation not found; treated as completed"},
    }


# ============================================================================
# IMAGE MANAGEMENT ENDPOINTS
# ============================================================================

@router.put("/projects/{project}/locations/{location}/repositories/{repo_name}/docker/v2/images")
def push_image(
    project: str,
    location: str,
    repo_name: str,
    body: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """Push (upload) a Docker image to repository."""
    
    # Verify repository exists
    repo = db.query(ArtifactRepository).filter_by(
        project_id=project, location=location, name=repo_name
    ).first()
    if not repo:
        raise HTTPException(404, f"Repository '{repo_name}' not found")
    
    try:
        # Extract image data
        image_digest = body.get("imageDigest")
        if not image_digest:
            # Compute digest from content
            content = json.dumps(body.get("config", {})).encode()
            image_digest = compute_digest(content)
        
        config = body.get("config", {})
        tags = body.get("tags", ["latest"])
        
        # Push image
        result = image_storage.push_image(
            project_id=project,
            location=location,
            repository_id=repo_name,
            image_digest=image_digest,
            config=config,
            tags=tags
        )
        
        return _operation(
            project, location,
            metadata={"verb": "push", "target": f"repositories/{repo_name}"},
            response=result
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error pushing image: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("/projects/{project}/locations/{location}/repositories/{repo_name}/docker/v2/images")
def list_images(
    project: str,
    location: str,
    repo_name: str,
    page_size: int = Query(100),
    db: Session = Depends(get_db),
):
    """List all images in a repository."""
    
    # Verify repository exists
    repo = db.query(ArtifactRepository).filter_by(
        project_id=project, location=location, name=repo_name
    ).first()
    if not repo:
        raise HTTPException(404, f"Repository '{repo_name}' not found")
    
    try:
        images = image_storage.list_images(project, location, repo_name)
        
        return {
            "images": [img.to_dict() for img in images],
            "nextPageToken": None,
        }
    except Exception as e:
        logger.error(f"Error listing images: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("/projects/{project}/locations/{location}/repositories/{repo_name}/docker/v2/images/{image_digest}")
def get_image(
    project: str,
    location: str,
    repo_name: str,
    image_digest: str,
    db: Session = Depends(get_db),
):
    """Get image details by digest."""
    
    # Verify repository exists
    repo = db.query(ArtifactRepository).filter_by(
        project_id=project, location=location, name=repo_name
    ).first()
    if not repo:
        raise HTTPException(404, f"Repository '{repo_name}' not found")
    
    try:
        image = image_storage.get_image(project, location, repo_name, image_digest)
        if not image:
            raise HTTPException(404, f"Image '{image_digest}' not found")
        
        # Include tags for this image
        tags = image_storage.list_tags(project, location, repo_name, image_digest)
        
        response = image.to_dict()
        response['tags'] = [t.to_dict() for t in tags]
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting image: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.delete("/projects/{project}/locations/{location}/repositories/{repo_name}/docker/v2/images/{image_digest}")
def delete_image(
    project: str,
    location: str,
    repo_name: str,
    image_digest: str,
    db: Session = Depends(get_db),
):
    """Delete an image."""
    
    # Verify repository exists
    repo = db.query(ArtifactRepository).filter_by(
        project_id=project, location=location, name=repo_name
    ).first()
    if not repo:
        raise HTTPException(404, f"Repository '{repo_name}' not found")
    
    try:
        deleted = image_storage.delete_image(project, location, repo_name, image_digest)
        if not deleted:
            raise HTTPException(404, f"Image '{image_digest}' not found")
        
        return _operation(
            project, location,
            metadata={"verb": "delete", "target": f"repositories/{repo_name}/images/{image_digest}"},
            response={"deleted": True}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


# ============================================================================
# TAG MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/projects/{project}/locations/{location}/repositories/{repo_name}/docker/v2/tags")
def create_tag(
    project: str,
    location: str,
    repo_name: str,
    body: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """Create or update a tag for an image."""
    
    # Verify repository exists
    repo = db.query(ArtifactRepository).filter_by(
        project_id=project, location=location, name=repo_name
    ).first()
    if not repo:
        raise HTTPException(404, f"Repository '{repo_name}' not found")
    
    try:
        tag_name = body.get("tag")
        image_digest = body.get("imageDigest")
        
        if not tag_name or not image_digest:
            raise HTTPException(400, "Missing 'tag' or 'imageDigest'")
        
        tag = image_storage.create_tag(project, location, repo_name, tag_name, image_digest)
        
        return _operation(
            project, location,
            metadata={"verb": "create", "target": f"repositories/{repo_name}/tags/{tag_name}"},
            response=tag.to_dict()
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tag: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("/projects/{project}/locations/{location}/repositories/{repo_name}/docker/v2/tags")
def list_tags(
    project: str,
    location: str,
    repo_name: str,
    image_digest: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List tags in a repository."""
    
    # Verify repository exists
    repo = db.query(ArtifactRepository).filter_by(
        project_id=project, location=location, name=repo_name
    ).first()
    if not repo:
        raise HTTPException(404, f"Repository '{repo_name}' not found")
    
    try:
        tags = image_storage.list_tags(project, location, repo_name, image_digest)
        
        return {
            "tags": [t.to_dict() for t in tags],
            "nextPageToken": None,
        }
    except Exception as e:
        logger.error(f"Error listing tags: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


@router.delete("/projects/{project}/locations/{location}/repositories/{repo_name}/docker/v2/tags/{tag_name}")
def delete_tag(
    project: str,
    location: str,
    repo_name: str,
    tag_name: str,
    db: Session = Depends(get_db),
):
    """Delete a tag."""
    
    # Verify repository exists
    repo = db.query(ArtifactRepository).filter_by(
        project_id=project, location=location, name=repo_name
    ).first()
    if not repo:
        raise HTTPException(404, f"Repository '{repo_name}' not found")
    
    try:
        deleted = image_storage.delete_tag(project, location, repo_name, tag_name)
        if not deleted:
            raise HTTPException(404, f"Tag '{tag_name}' not found")
        
        return _operation(
            project, location,
            metadata={"verb": "delete", "target": f"repositories/{repo_name}/tags/{tag_name}"},
            response={"deleted": True}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tag: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


# ============================================================================
# PULL OPERATION
# ============================================================================

@router.post("/projects/{project}/locations/{location}/repositories/{repo_name}/docker/v2/:pull")
def pull_image(
    project: str,
    location: str,
    repo_name: str,
    body: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """Pull (retrieve) an image."""
    
    # Verify repository exists
    repo = db.query(ArtifactRepository).filter_by(
        project_id=project, location=location, name=repo_name
    ).first()
    if not repo:
        raise HTTPException(404, f"Repository '{repo_name}' not found")
    
    try:
        image_reference = body.get("imageReference")  # Can be digest or tag
        if not image_reference:
            raise HTTPException(400, "Missing 'imageReference'")
        
        image = image_storage.pull_image(project, location, repo_name, image_reference)
        if not image:
            raise HTTPException(404, f"Image '{image_reference}' not found")
        
        return {
            "image": image.to_dict(),
            "downloadSize": image.size_bytes,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pulling image: {e}")
        raise HTTPException(500, f"Error: {str(e)}")


# ============================================================================
# HEALTH & STATS
# ============================================================================

@router.get("/projects/{project}/locations/{location}/repositories/{repo_name}/images:stats")
def image_stats(
    project: str,
    location: str,
    repo_name: str,
    db: Session = Depends(get_db),
):
    """Get image statistics for a repository."""
    
    # Verify repository exists
    repo = db.query(ArtifactRepository).filter_by(
        project_id=project, location=location, name=repo_name
    ).first()
    if not repo:
        raise HTTPException(404, f"Repository '{repo_name}' not found")
    
    try:
        images = image_storage.list_images(project, location, repo_name)
        tags = image_storage.list_tags(project, location, repo_name)
        
        total_size = sum(img.size_bytes for img in images)
        
        return {
            "repository": repo_name,
            "imageCount": len(images),
            "tagCount": len(tags),
            "totalSizeBytes": total_size,
            "storageStats": image_storage.get_stats(),
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(500, f"Error: {str(e)}")
