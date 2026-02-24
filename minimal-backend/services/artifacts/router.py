"""Artifact Registry (simulated) API."""
from typing import Any, Dict, Optional
import random
import threading

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import ArtifactRepository, get_db
from docker_manager import ensure_local_registry

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
