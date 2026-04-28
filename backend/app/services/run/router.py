"""Cloud Run (simulated) API."""
from typing import Any, Dict, List, Optional
import random
import threading

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.database import (
    CloudRunRevision,
    CloudRunService,
    get_db,
)
from app.core.docker_manager import (
    delete_cloud_run_revision_container,
    deploy_cloud_run_container,
    ensure_local_registry,
    normalize_registry_image,
)

router = APIRouter()

_ops_lock = threading.Lock()
_operations: Dict[str, Dict[str, Any]] = {}


def _op_name(project: str, location: str) -> str:
    suffix = random.randint(1_000_000_000_000, 9_999_999_999_999)
    return f"projects/{project}/locations/{location}/operations/{suffix}"


def _operation(project: str, location: str, metadata: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
    name = _op_name(project, location)
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


def _service_url(service_name: str) -> str:
    return f"http://{service_name}.local.calcs"


def _traffic_to_v2(traffic: List[Dict[str, Any]], latest_ready_revision: Optional[str]) -> List[Dict[str, Any]]:
    out = []
    for t in traffic or []:
        out.append({
            "revision": t.get("revision"),
            "percent": int(t.get("percent", 0)),
            "tag": t.get("tag", ""),
            "latestRevision": bool(latest_ready_revision and t.get("revision") == latest_ready_revision),
        })
    return out


def _service_to_v2(service: CloudRunService, revisions: List[CloudRunRevision], project: str, location: str) -> Dict[str, Any]:
    rev_by_name = {r.name: r for r in revisions}
    latest = rev_by_name.get(service.latest_ready_revision or "")
    traffic = _traffic_to_v2(service.traffic or [], service.latest_ready_revision)
    template = {
        "containers": [{
            "image": latest.image if latest else "",
            "ports": [{"containerPort": latest.container_port if latest else 8080}],
            "env": latest.env_vars if latest else [],
        }]
    }
    return {
        "name": f"projects/{project}/locations/{location}/services/{service.name}",
        "uid": str(service.id),
        "generation": str(max(len(revisions), 1)),
        "labels": service.labels or {},
        "annotations": service.annotations or {},
        "createTime": service.created_at.isoformat() + "Z",
        "updateTime": service.updated_at.isoformat() + "Z" if service.updated_at else None,
        "ingress": service.ingress or "INGRESS_TRAFFIC_ALL",
        "launchStage": "GA",
        "uri": service.uri or _service_url(service.name),
        "latestReadyRevision": (
            f"projects/{project}/locations/{location}/services/{service.name}/revisions/{service.latest_ready_revision}"
            if service.latest_ready_revision else ""
        ),
        "traffic": traffic,
        "template": template,
        "terminalCondition": {"state": "CONDITION_SUCCEEDED"},
        "urls": {
            "simulated": service.uri or _service_url(service.name),
            "activeLocal": f"http://localhost:{latest.host_port}" if latest and latest.host_port else "",
        },
    }


def _resolve_service_name(service_id: Optional[str], body: Dict[str, Any]) -> str:
    if service_id:
        return service_id
    full_name = body.get("name", "")
    if full_name and "/services/" in full_name:
        return full_name.split("/services/", 1)[1]
    metadata_name = body.get("metadata", {}).get("name")
    if metadata_name:
        return metadata_name
    raise HTTPException(400, "serviceId or body.name is required")


def _extract_container_spec(body: Dict[str, Any]) -> Dict[str, Any]:
    # Cloud Run v2 shape
    containers = body.get("template", {}).get("containers", [])
    # Cloud Run v1 shape fallback
    if not containers:
        containers = body.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
    if not containers:
        raise HTTPException(400, "template.containers[0].image is required")

    first = containers[0]
    image = first.get("image")
    if not image:
        raise HTTPException(400, "container image is required")

    env = first.get("env", [])
    ports = first.get("ports", [])
    container_port = 8080
    if ports:
        container_port = int(ports[0].get("containerPort", 8080))

    return {"image": image, "env": env, "container_port": container_port}


def _create_or_update_service(project: str, location: str, service_name: str, body: Dict[str, Any], db: Session) -> Dict[str, Any]:
    spec = _extract_container_spec(body)
    normalized_image = normalize_registry_image(spec["image"], project)

    if normalized_image.startswith("localhost:5000/") or "/pkg.dev/" in spec["image"] or spec["image"].startswith("gcr.io/"):
        ensure_local_registry()

    service = db.query(CloudRunService).filter_by(
        project_id=project, location=location, name=service_name
    ).first()

    rev_count = db.query(CloudRunRevision).filter_by(
        project_id=project, location=location, service_name=service_name
    ).count()
    rev_name = f"{service_name}-{rev_count + 1:05d}"

    deploy_result = deploy_cloud_run_container(
        service_name=service_name,
        revision_name=rev_name,
        image=normalized_image,
        env_vars=spec["env"],
        container_port=spec["container_port"],
    )

    revision = CloudRunRevision(
        name=rev_name,
        service_name=service_name,
        project_id=project,
        location=location,
        image=normalized_image,
        container_port=spec["container_port"],
        status="READY",
        container_id=deploy_result["container_id"],
        host_port=deploy_result["host_port"],
        env_vars=spec["env"],
        percent_traffic=100,
    )
    db.add(revision)

    if not service:
        service = CloudRunService(
            name=service_name,
            project_id=project,
            location=location,
            status="ACTIVE",
            ingress=body.get("ingress", "INGRESS_TRAFFIC_ALL"),
            uri=_service_url(service_name),
            latest_ready_revision=rev_name,
            traffic=[{"revision": rev_name, "percent": 100}],
            labels=body.get("labels", {}),
            annotations=body.get("annotations", {}),
        )
        db.add(service)
    else:
        service.latest_ready_revision = rev_name
        service.uri = service.uri or _service_url(service_name)
        service.traffic = [{"revision": rev_name, "percent": 100}]
        service.annotations = body.get("annotations", service.annotations or {})
        service.labels = body.get("labels", service.labels or {})

    db.commit()

    revisions = db.query(CloudRunRevision).filter_by(
        project_id=project, location=location, service_name=service_name
    ).all()
    return _service_to_v2(service, revisions, project, location)


@router.post("/projects/{project}/locations/{location}/services", status_code=200)
def deploy_service(
    project: str,
    location: str,
    raw_body: Dict[str, Any],
    serviceId: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    service_name = _resolve_service_name(serviceId, raw_body)
    service = _create_or_update_service(project, location, service_name, raw_body, db)
    return _operation(
        project,
        location,
        metadata={"verb": "create", "target": f"services/{service_name}"},
        response=service,
    )


@router.get("/projects/{project}/locations/{location}/services")
def list_services(project: str, location: str, db: Session = Depends(get_db)):
    services = db.query(CloudRunService).filter_by(project_id=project, location=location).all()
    out = []
    for s in services:
        revisions = db.query(CloudRunRevision).filter_by(
            project_id=project, location=location, service_name=s.name
        ).all()
        out.append(_service_to_v2(s, revisions, project, location))
    return {"services": out, "nextPageToken": ""}


@router.get("/projects/{project}/locations/{location}/services/{service_name}")
def get_service(project: str, location: str, service_name: str, db: Session = Depends(get_db)):
    service = db.query(CloudRunService).filter_by(
        project_id=project, location=location, name=service_name
    ).first()
    if not service:
        raise HTTPException(404, f"Service '{service_name}' not found")

    revisions = db.query(CloudRunRevision).filter_by(
        project_id=project, location=location, service_name=service_name
    ).all()
    return _service_to_v2(service, revisions, project, location)


@router.patch("/projects/{project}/locations/{location}/services/{service_name}")
def patch_service(
    project: str,
    location: str,
    service_name: str,
    raw_body: Dict[str, Any],
    updateMask: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    service = db.query(CloudRunService).filter_by(
        project_id=project, location=location, name=service_name
    ).first()
    if not service:
        raise HTTPException(404, f"Service '{service_name}' not found")

    if updateMask and "traffic" in updateMask and "traffic" in raw_body:
        traffic = raw_body.get("traffic", [])
        if not traffic:
            raise HTTPException(400, "traffic must not be empty")

        revisions = db.query(CloudRunRevision).filter_by(
            project_id=project, location=location, service_name=service_name
        ).all()
        rev_map = {r.name: r for r in revisions}

        normalized = []
        max_percent = -1
        active_rev = None
        for t in traffic:
            rev_name = t.get("revision")
            if t.get("latestRevision"):
                rev_name = service.latest_ready_revision
            if not rev_name or rev_name not in rev_map:
                raise HTTPException(400, f"Unknown revision '{rev_name}'")
            pct = int(t.get("percent", 0))
            normalized.append({"revision": rev_name, "percent": pct, "tag": t.get("tag", "")})
            rev_map[rev_name].percent_traffic = pct
            if pct > max_percent:
                max_percent = pct
                active_rev = rev_name

        service.traffic = normalized
        if active_rev:
            service.latest_ready_revision = active_rev
        db.commit()

    revisions = db.query(CloudRunRevision).filter_by(
        project_id=project, location=location, service_name=service_name
    ).all()
    payload = _service_to_v2(service, revisions, project, location)
    return _operation(
        project,
        location,
        metadata={"verb": "patch", "target": f"services/{service_name}"},
        response=payload,
    )


@router.delete("/projects/{project}/locations/{location}/services/{service_name}")
def delete_service(project: str, location: str, service_name: str, db: Session = Depends(get_db)):
    service = db.query(CloudRunService).filter_by(
        project_id=project, location=location, name=service_name
    ).first()
    if not service:
        raise HTTPException(404, f"Service '{service_name}' not found")

    revisions = db.query(CloudRunRevision).filter_by(
        project_id=project, location=location, service_name=service_name
    ).all()
    for r in revisions:
        delete_cloud_run_revision_container(r.container_id)
        db.delete(r)

    db.delete(service)
    db.commit()

    return _operation(
        project,
        location,
        metadata={"verb": "delete", "target": f"services/{service_name}"},
        response={"message": f"Service '{service_name}' deleted"},
    )


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
