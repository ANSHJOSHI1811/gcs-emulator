"""GKE (Google Kubernetes Engine) API — cluster, node pool, addon management"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, GKECluster, GKENodePool, GKEAddon, SessionLocal
from pydantic import BaseModel
from typing import Optional
import threading, random

router = APIRouter()

_SUPPORTED_VERSIONS = ["1.30", "1.29", "1.28", "1.27"]
_DEFAULT_VERSION = "1.28"


# ─── Serialisers ──────────────────────────────────────────────────────────────

def _cluster_to_dict(c: GKECluster, project: str) -> dict:
    version = c.master_version or "1.28.0"
    return {
        "name": c.name,
        "description": c.description or "",
        "selfLink": (
            f"https://container.googleapis.com/v1/projects/{project}"
            f"/locations/{c.location}/clusters/{c.name}"
        ),
        "status": c.status,
        "masterVersion": version,
        "currentMasterVersion": version,
        "nodeVersion": version,
        "currentNodeVersion": version,
        "location": c.location,
        "zone": c.location,
        "endpoint": c.endpoint or "",
        "network": c.network,
        "subnetwork": c.subnetwork,
        "clusterIpv4Cidr": getattr(c, "cluster_ipv4_cidr", "/17") or "/17",
        "servicesIpv4Cidr": getattr(c, "services_ipv4_cidr", "/20") or "/20",
        "privateClusterConfig": {
            "enablePrivateNodes": getattr(c, "enable_private_nodes", False) or False,
            "enablePrivateEndpoint": False,
        },
        "currentNodeCount": c.node_count,
        "initialNodeCount": c.node_count,
        "nodeConfig": {
            "machineType": c.machine_type,
            "diskSizeGb": c.disk_size_gb,
            "imageType": "COS_CONTAINERD",
            "oauthScopes": ["https://www.googleapis.com/auth/cloud-platform"],
            "preemptible": False,
            "spot": False,
        },
        "clusterType": getattr(c, "cluster_type", "STANDARD") or "STANDARD",
        "autopilot": {
            "enabled": (getattr(c, "cluster_type", "STANDARD") or "STANDARD") == "AUTOPILOT"
        },
        "releaseChannel": {
            "channel": getattr(c, "release_channel", "REGULAR") or "REGULAR"
        },
        "loggingService": getattr(c, "logging_service", "logging.googleapis.com/kubernetes") or "logging.googleapis.com/kubernetes",
        "monitoringService": getattr(c, "monitoring_service", "monitoring.googleapis.com/kubernetes") or "monitoring.googleapis.com/kubernetes",
        "binaryAuthorization": {
            "evaluationMode": getattr(c, "binary_authorization", "DISABLED") or "DISABLED"
        },
        "masterAuth": {
            "clusterCaCertificate": getattr(c, "certificate_authority", "") or "",
        },
        "addonsConfig": {
            "httpLoadBalancing": {"disabled": False},
            "horizontalPodAutoscaling": {"disabled": False},
            "networkPolicyConfig": {"disabled": True},
        },
        "resourceLabels": getattr(c, "resource_labels", {}) or {},
        "createTime": c.created_at.isoformat() + "Z",
        "updateTime": c.updated_at.isoformat() + "Z" if c.updated_at else None,
    }


def _nodepool_to_dict(np: GKENodePool, project: str) -> dict:
    autoscaling_enabled = getattr(np, "autoscaling_enabled", False) or False
    return {
        "name": np.name,
        "status": np.status,
        "clusterName": np.cluster_name,
        "location": np.location,
        "nodeCount": np.node_count,
        "config": {
            "machineType": np.machine_type,
            "diskSizeGb": np.disk_size_gb,
            "imageType": getattr(np, "image_type", "COS_CONTAINERD") or "COS_CONTAINERD",
            "preemptible": getattr(np, "preemptible", False) or False,
            "spot": getattr(np, "spot", False) or False,
            "oauthScopes": ["https://www.googleapis.com/auth/cloud-platform"],
        },
        "autoscaling": {
            "enabled": autoscaling_enabled,
            "minNodeCount": getattr(np, "min_node_count", 1) or 1,
            "maxNodeCount": getattr(np, "max_node_count", 3) or 3,
        },
        "management": {
            "autoRepair":  getattr(np, "management_auto_repair", True),
            "autoUpgrade": getattr(np, "management_auto_upgrade", True),
        },
        "selfLink": (
            f"https://container.googleapis.com/v1/projects/{project}"
            f"/locations/{np.location}/clusters/{np.cluster_name}/nodePools/{np.name}"
        ),
        "createTime": np.created_at.isoformat() + "Z",
    }


def _addon_to_dict(a: GKEAddon) -> dict:
    return {
        "name": a.name,
        "status": a.status,
        "version": a.version or "",
        "clusterName": a.cluster_name,
        "createTime": a.created_at.isoformat() + "Z",
        "updateTime": a.updated_at.isoformat() + "Z" if a.updated_at else None,
    }


def _operation_response(name: str, project: str, location: str, op_type: str) -> dict:
    op_id = f"operation-{random.randint(1_000_000_000_000, 9_999_999_999_999)}"
    return {
        "name": op_id,
        "operationType": op_type,
        "status": "RUNNING",
        "targetLink": (
            f"https://container.googleapis.com/v1/projects/{project}"
            f"/locations/{location}/clusters/{name}"
        ),
        "selfLink": (
            f"https://container.googleapis.com/v1/projects/{project}"
            f"/locations/{location}/operations/{op_id}"
        ),
    }


# ─── Background workers ────────────────────────────────────────────────────────

def _provision_cluster(cluster_id: int):
    """Background thread: spin up k3s, store kubeconfig + CA cert."""
    from docker_manager import create_k3s_cluster, get_k3s_kubeconfig

    db = SessionLocal()
    try:
        cluster = db.query(GKECluster).filter_by(id=cluster_id).first()
        if not cluster:
            return

        k8s_ver = ".".join((cluster.master_version or "1.28").split(".")[:2])
        result = create_k3s_cluster(cluster.name, kubernetes_version=k8s_ver)
        kubeconfig = get_k3s_kubeconfig(result["container_id"], result["endpoint_ip"])

        cluster.container_id      = result["container_id"]
        cluster.endpoint          = result["endpoint_ip"]
        cluster.api_server_port   = result.get("api_server_port")
        cluster.certificate_authority = result.get("certificate_authority", "")
        cluster.kubeconfig        = kubeconfig
        cluster.status            = "RUNNING"
        db.commit()
        print(f"GKE cluster '{cluster.name}' RUNNING ({result['endpoint_ip']})")

        np = db.query(GKENodePool).filter_by(
            cluster_name=cluster.name, project_id=cluster.project_id
        ).first()
        if np:
            np.status = "RUNNING"
            db.commit()
    except Exception as e:
        print(f"Failed to provision cluster id={cluster_id}: {e}")
        db2 = SessionLocal()
        try:
            c = db2.query(GKECluster).filter_by(id=cluster_id).first()
            if c:
                c.status = "ERROR"; db2.commit()
        finally:
            db2.close()
    finally:
        db.close()


def _delete_cluster_bg(cluster_id: int, container_id: Optional[str], cluster_name: str):
    from docker_manager import delete_k3s_cluster

    if container_id:
        delete_k3s_cluster(container_id, cluster_name=cluster_name)

    db = SessionLocal()
    try:
        cluster = db.query(GKECluster).filter_by(id=cluster_id).first()
        if cluster:
            db.query(GKENodePool).filter_by(cluster_name=cluster.name, project_id=cluster.project_id).delete()
            db.query(GKEAddon).filter_by(cluster_name=cluster.name, project_id=cluster.project_id).delete()
            db.delete(cluster); db.commit()
    finally:
        db.close()


def _stop_cluster_bg(cluster_id: int, container_id: str):
    from docker_manager import stop_k3s_cluster

    stop_k3s_cluster(container_id)
    db = SessionLocal()
    try:
        c = db.query(GKECluster).filter_by(id=cluster_id).first()
        if c:
            c.status = "STOPPED"; db.commit()
    finally:
        db.close()


def _start_cluster_bg(cluster_id: int, container_id: str):
    from docker_manager import start_k3s_cluster
    import time

    start_k3s_cluster(container_id)
    time.sleep(5)
    db = SessionLocal()
    try:
        c = db.query(GKECluster).filter_by(id=cluster_id).first()
        if c:
            c.status = "RUNNING"; db.commit()
    finally:
        db.close()


def _delete_nodepool_bg(nodepool_id: int, container_ids: list):
    from docker_manager import delete_k3s_agent

    for cid in (container_ids or []):
        delete_k3s_agent(cid)

    db = SessionLocal()
    try:
        np = db.query(GKENodePool).filter_by(id=nodepool_id).first()
        if np:
            db.delete(np); db.commit()
    finally:
        db.close()


def _provision_nodepool_bg(np_id: int, cluster_id: int, node_count: int, pool_name: str):
    """Background: spin up k3s agent containers for a new node pool."""
    from docker_manager import create_k3s_agents
    import time

    db = SessionLocal()
    try:
        cluster = db.query(GKECluster).filter_by(id=cluster_id).first()
        np = db.query(GKENodePool).filter_by(id=np_id).first()
        if not cluster or not np:
            return
        if not cluster.container_id or not cluster.endpoint:
            # Cluster doesn't have a real container (rare), just mark running
            np.status = "RUNNING"; db.commit(); return

        k8s_ver = (cluster.master_version or "1.28").rsplit(".", 1)[0]  # "1.28.0" → "1.28"
        container_ids = create_k3s_agents(
            cluster_name=cluster.name,
            server_container_id=cluster.container_id,
            server_ip=cluster.endpoint,
            node_count=node_count,
            pool_name=pool_name,
            kubernetes_version=k8s_ver,
        )
        np = db.query(GKENodePool).filter_by(id=np_id).first()
        if np:
            np.container_ids = container_ids
            np.status = "RUNNING"
            db.commit()
    except Exception as e:
        print(f"❌ Node pool provisioning failed: {e}")
        _db2 = SessionLocal()
        try:
            _np = _db2.query(GKENodePool).filter_by(id=np_id).first()
            if _np:
                _np.status = "ERROR"; _db2.commit()
        finally:
            _db2.close()
    finally:
        db.close()


def _resize_nodepool_bg(np_id: int, cluster_id: int, desired: int):
    """Background: scale node pool up or down."""
    from docker_manager import resize_k3s_agents

    db = SessionLocal()
    try:
        cluster = db.query(GKECluster).filter_by(id=cluster_id).first()
        np = db.query(GKENodePool).filter_by(id=np_id).first()
        if not cluster or not np:
            return
        k8s_ver = (cluster.master_version or "1.28").rsplit(".", 1)[0]
        updated_ids = resize_k3s_agents(
            cluster_name=cluster.name,
            server_container_id=cluster.container_id,
            server_ip=cluster.endpoint,
            pool_name=np.name,
            current_container_ids=np.container_ids or [],
            desired_count=desired,
            kubernetes_version=k8s_ver,
        )
        np2 = db.query(GKENodePool).filter_by(id=np_id).first()
        if np2:
            np2.container_ids = updated_ids
            np2.node_count = desired
            np2.status = "RUNNING"
            db.commit()
    except Exception as e:
        print(f"❌ Node pool resize failed: {e}")
    finally:
        db.close()


# ─── Request models ────────────────────────────────────────────────────────────

class CreateClusterRequest(BaseModel):
    cluster: dict

class CreateNodePoolRequest(BaseModel):
    nodePool: dict

class UpdateClusterRequest(BaseModel):
    update: dict

class SetAutoscalingRequest(BaseModel):
    autoscaling: dict

class SetSizeRequest(BaseModel):
    nodeCount: int

class CreateAddonRequest(BaseModel):
    name: str
    version: Optional[str] = ""

class KubectlRequest(BaseModel):
    command: str


# ─── Cluster endpoints ─────────────────────────────────────────────────────────

@router.get("/projects/{project}/locations/{location}/clusters")
def list_clusters(project: str, location: str, db: Session = Depends(get_db)):
    q = db.query(GKECluster).filter_by(project_id=project)
    if location != "-":
        q = q.filter_by(location=location)
    return {"clusters": [_cluster_to_dict(c, project) for c in q.all()]}


@router.post("/projects/{project}/locations/{location}/clusters", status_code=200)
def create_cluster(project: str, location: str, body: CreateClusterRequest, db: Session = Depends(get_db)):
    d = body.cluster
    name = d.get("name")
    if not name:
        raise HTTPException(400, "cluster.name is required")
    if db.query(GKECluster).filter_by(project_id=project, location=location, name=name).first():
        raise HTTPException(409, f"Cluster '{name}' already exists in {location}")

    node_cfg  = d.get("nodeConfig", {})
    autopilot = d.get("autopilot", {}).get("enabled", False)
    raw_ver   = d.get("masterVersion", _DEFAULT_VERSION)
    if len(raw_ver.split(".")) == 2:
        raw_ver += ".0"

    cluster = GKECluster(
        name=name, project_id=project, location=location,
        description=d.get("description", ""),
        master_version=raw_ver,
        node_count=d.get("initialNodeCount", 3),
        machine_type=node_cfg.get("machineType", "e2-medium"),
        disk_size_gb=node_cfg.get("diskSizeGb", 100),
        network=d.get("network", "default"),
        subnetwork=d.get("subnetwork", "default"),
        cluster_type="AUTOPILOT" if autopilot else d.get("clusterType", "STANDARD"),
        release_channel=d.get("releaseChannel", {}).get("channel", "REGULAR"),
        cluster_ipv4_cidr=d.get("clusterIpv4Cidr", "/17"),
        services_ipv4_cidr=d.get("servicesIpv4Cidr", "/20"),
        enable_private_nodes=d.get("privateClusterConfig", {}).get("enablePrivateNodes", False),
        logging_service=d.get("loggingService", "logging.googleapis.com/kubernetes"),
        monitoring_service=d.get("monitoringService", "monitoring.googleapis.com/kubernetes"),
        binary_authorization=d.get("binaryAuthorization", {}).get("evaluationMode", "DISABLED"),
        resource_labels=d.get("resourceLabels", {}),
        status="PROVISIONING",
    )
    db.add(cluster); db.flush()

    pool_name = "default-pool"
    if d.get("nodePools"):
        pool_name = d["nodePools"][0].get("name", "default-pool")

    db.add(GKENodePool(
        name=pool_name, cluster_name=name, project_id=project, location=location,
        node_count=cluster.node_count, machine_type=cluster.machine_type,
        disk_size_gb=cluster.disk_size_gb, status="PROVISIONING",
    ))
    db.commit()

    threading.Thread(target=_provision_cluster, args=(cluster.id,), daemon=True).start()
    return _operation_response(name, project, location, "CREATE_CLUSTER")


@router.get("/projects/{project}/locations/{location}/clusters/{cluster_name}")
def get_cluster(project: str, location: str, cluster_name: str, db: Session = Depends(get_db)):
    c = db.query(GKECluster).filter_by(project_id=project, location=location, name=cluster_name).first()
    if not c:
        raise HTTPException(404, f"Cluster '{cluster_name}' not found")
    return _cluster_to_dict(c, project)


@router.delete("/projects/{project}/locations/{location}/clusters/{cluster_name}")
def delete_cluster(project: str, location: str, cluster_name: str, db: Session = Depends(get_db)):
    c = db.query(GKECluster).filter_by(project_id=project, location=location, name=cluster_name).first()
    if not c:
        raise HTTPException(404, f"Cluster '{cluster_name}' not found")
    c.status = "STOPPING"; db.commit()
    threading.Thread(target=_delete_cluster_bg, args=(c.id, c.container_id, c.name), daemon=True).start()
    return _operation_response(cluster_name, project, location, "DELETE_CLUSTER")


@router.post("/projects/{project}/locations/{location}/clusters/{cluster_name}:stop")
def stop_cluster(project: str, location: str, cluster_name: str, db: Session = Depends(get_db)):
    """Stop a running cluster (container kept, status -> STOPPED)."""
    c = db.query(GKECluster).filter_by(project_id=project, location=location, name=cluster_name).first()
    if not c:
        raise HTTPException(404, f"Cluster '{cluster_name}' not found")
    if c.status != "RUNNING":
        raise HTTPException(400, f"Cluster must be RUNNING to stop (current: {c.status})")
    if not c.container_id:
        raise HTTPException(409, "Cluster has no associated container")
    c.status = "STOPPING"; db.commit()
    threading.Thread(target=_stop_cluster_bg, args=(c.id, c.container_id), daemon=True).start()
    return _operation_response(cluster_name, project, location, "STOP_CLUSTER")


@router.post("/projects/{project}/locations/{location}/clusters/{cluster_name}:start")
def start_cluster(project: str, location: str, cluster_name: str, db: Session = Depends(get_db)):
    """Restart a stopped cluster (container restart, status -> RUNNING)."""
    c = db.query(GKECluster).filter_by(project_id=project, location=location, name=cluster_name).first()
    if not c:
        raise HTTPException(404, f"Cluster '{cluster_name}' not found")
    if c.status != "STOPPED":
        raise HTTPException(400, f"Cluster must be STOPPED to start (current: {c.status})")
    if not c.container_id:
        raise HTTPException(409, "Cluster has no associated container")
    c.status = "RECONCILING"; db.commit()
    threading.Thread(target=_start_cluster_bg, args=(c.id, c.container_id), daemon=True).start()
    return _operation_response(cluster_name, project, location, "START_CLUSTER")


@router.patch("/projects/{project}/locations/{location}/clusters/{cluster_name}")
def update_cluster(
    project: str, location: str, cluster_name: str,
    body: UpdateClusterRequest, db: Session = Depends(get_db),
):
    c = db.query(GKECluster).filter_by(project_id=project, location=location, name=cluster_name).first()
    if not c:
        raise HTTPException(404, f"Cluster '{cluster_name}' not found")
    u = body.update
    if "desiredNodeCount"       in u: c.node_count        = int(u["desiredNodeCount"])
    if "desiredMasterVersion"   in u: c.master_version     = u["desiredMasterVersion"]
    if "desiredReleaseChannel"  in u: c.release_channel    = u["desiredReleaseChannel"].get("channel", c.release_channel)
    if "desiredLoggingService"  in u: c.logging_service    = u["desiredLoggingService"]
    if "desiredMonitoringService" in u: c.monitoring_service = u["desiredMonitoringService"]
    if "desiredResourceLabels"  in u: c.resource_labels    = u["desiredResourceLabels"]
    c.status = "RECONCILING"; db.commit()

    def _finish(cid: int):
        import time; time.sleep(5)
        _db = SessionLocal()
        try:
            _c = _db.query(GKECluster).filter_by(id=cid).first()
            if _c and _c.status == "RECONCILING":
                _c.status = "RUNNING"; _db.commit()
        finally:
            _db.close()

    threading.Thread(target=_finish, args=(c.id,), daemon=True).start()
    return _operation_response(cluster_name, project, location, "UPDATE_CLUSTER")


# ─── Kubeconfig, nodes & kubectl ──────────────────────────────────────────────

@router.get("/projects/{project}/locations/{location}/clusters/{cluster_name}/kubeconfig")
def get_kubeconfig(project: str, location: str, cluster_name: str, db: Session = Depends(get_db)):
    c = db.query(GKECluster).filter_by(project_id=project, location=location, name=cluster_name).first()
    if not c:
        raise HTTPException(404, f"Cluster '{cluster_name}' not found")
    if c.status != "RUNNING":
        raise HTTPException(400, f"Cluster is not RUNNING (status: {c.status})")
    if not c.kubeconfig:
        raise HTTPException(503, "Kubeconfig not yet available")
    return {"kubeconfig": c.kubeconfig}


@router.get("/projects/{project}/locations/{location}/clusters/{cluster_name}/nodes")
def list_cluster_nodes(project: str, location: str, cluster_name: str, db: Session = Depends(get_db)):
    import subprocess, json as _json, tempfile, os

    c = db.query(GKECluster).filter_by(project_id=project, location=location, name=cluster_name).first()
    if not c:
        raise HTTPException(404, f"Cluster '{cluster_name}' not found")
    if not c.kubeconfig:
        raise HTTPException(409, "Cluster kubeconfig not available yet")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(c.kubeconfig); kc_path = f.name
    try:
        result = subprocess.run(
            ["kubectl", "--kubeconfig", kc_path, "get", "nodes", "-o", "json"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return {"nodes": [], "error": result.stderr.strip()}
        data = _json.loads(result.stdout)
        nodes = []
        for item in data.get("items", []):
            meta = item.get("metadata", {})
            stat = item.get("status", {})
            conds = {x["type"]: x["status"] for x in stat.get("conditions", [])}
            addrs = {x["type"]: x["address"] for x in stat.get("addresses", [])}
            info  = stat.get("nodeInfo", {})
            roles = [k.split("/")[-1] for k in meta.get("labels", {}) if k.startswith("node-role.kubernetes.io/")]
            nodes.append({
                "name": meta.get("name", ""),
                "status": "Ready" if conds.get("Ready") == "True" else "NotReady",
                "roles": ",".join(roles) if roles else "none",
                "age": meta.get("creationTimestamp", ""),
                "version": info.get("kubeletVersion", ""),
                "internalIP": addrs.get("InternalIP", ""),
                "osImage": info.get("osImage", ""),
                "containerRuntime": info.get("containerRuntimeVersion", ""),
            })
        return {"nodes": nodes}
    except subprocess.TimeoutExpired:
        return {"nodes": [], "error": "kubectl timed out"}
    finally:
        os.unlink(kc_path)


@router.post("/projects/{project}/locations/{location}/clusters/{cluster_name}/kubectl")
def exec_kubectl(
    project: str, location: str, cluster_name: str,
    body: KubectlRequest, db: Session = Depends(get_db),
):
    """Execute a kubectl command against the cluster and return stdout/stderr."""
    from docker_manager import run_kubectl_command

    c = db.query(GKECluster).filter_by(project_id=project, location=location, name=cluster_name).first()
    if not c:
        raise HTTPException(404, f"Cluster '{cluster_name}' not found")
    if c.status != "RUNNING":
        raise HTTPException(400, f"Cluster is not RUNNING (status: {c.status})")
    if not c.kubeconfig:
        raise HTTPException(409, "Kubeconfig not available yet")
    return run_kubectl_command(c.kubeconfig, body.command)


# ─── Node Pool endpoints ───────────────────────────────────────────────────────

@router.get("/projects/{project}/locations/{location}/clusters/{cluster_name}/nodePools")
def list_node_pools(project: str, location: str, cluster_name: str, db: Session = Depends(get_db)):
    if not db.query(GKECluster).filter_by(project_id=project, location=location, name=cluster_name).first():
        raise HTTPException(404, f"Cluster '{cluster_name}' not found")
    pools = db.query(GKENodePool).filter_by(project_id=project, location=location, cluster_name=cluster_name).all()
    return {"nodePools": [_nodepool_to_dict(np, project) for np in pools]}


@router.post("/projects/{project}/locations/{location}/clusters/{cluster_name}/nodePools", status_code=200)
def create_node_pool(
    project: str, location: str, cluster_name: str,
    body: CreateNodePoolRequest, db: Session = Depends(get_db),
):
    if not db.query(GKECluster).filter_by(project_id=project, location=location, name=cluster_name).first():
        raise HTTPException(404, f"Cluster '{cluster_name}' not found")
    d = body.nodePool
    pool_name = d.get("name")
    if not pool_name:
        raise HTTPException(400, "nodePool.name is required")
    if db.query(GKENodePool).filter_by(project_id=project, location=location, cluster_name=cluster_name, name=pool_name).first():
        raise HTTPException(409, f"Node pool '{pool_name}' already exists")

    cfg = d.get("config", {}); a = d.get("autoscaling", {}); mgmt = d.get("management", {})
    node_count = d.get("initialNodeCount", 3)
    np = GKENodePool(
        name=pool_name, cluster_name=cluster_name, project_id=project, location=location,
        node_count=node_count,
        machine_type=cfg.get("machineType", "e2-medium"),
        disk_size_gb=cfg.get("diskSizeGb", 100),
        image_type=cfg.get("imageType", "COS_CONTAINERD"),
        preemptible=cfg.get("preemptible", False),
        spot=cfg.get("spot", False),
        autoscaling_enabled=a.get("enabled", False),
        min_node_count=a.get("minNodeCount", 1),
        max_node_count=a.get("maxNodeCount", 3),
        management_auto_repair=mgmt.get("autoRepair", True),
        management_auto_upgrade=mgmt.get("autoUpgrade", True),
        status="PROVISIONING",
    )
    db.add(np); db.commit(); db.refresh(np)

    # Look up cluster to get container_id needed for agent provisioning
    cluster_row = db.query(GKECluster).filter_by(
        project_id=project, location=location, name=cluster_name
    ).first()
    threading.Thread(
        target=_provision_nodepool_bg,
        args=(np.id, cluster_row.id, node_count, pool_name),
        daemon=True,
    ).start()
    return _operation_response(cluster_name, project, location, "CREATE_NODE_POOL")


@router.get("/projects/{project}/locations/{location}/clusters/{cluster_name}/nodePools/{pool_name}")
def get_node_pool(project: str, location: str, cluster_name: str, pool_name: str, db: Session = Depends(get_db)):
    np = db.query(GKENodePool).filter_by(project_id=project, location=location, cluster_name=cluster_name, name=pool_name).first()
    if not np:
        raise HTTPException(404, f"Node pool '{pool_name}' not found")
    return _nodepool_to_dict(np, project)


@router.post("/projects/{project}/locations/{location}/clusters/{cluster_name}/nodePools/{pool_name}:setAutoscaling")
def set_node_pool_autoscaling(
    project: str, location: str, cluster_name: str, pool_name: str,
    body: SetAutoscalingRequest, db: Session = Depends(get_db),
):
    """Enable / disable horizontal node pool autoscaling."""
    np = db.query(GKENodePool).filter_by(project_id=project, location=location, cluster_name=cluster_name, name=pool_name).first()
    if not np:
        raise HTTPException(404, f"Node pool '{pool_name}' not found")
    a = body.autoscaling
    np.autoscaling_enabled = a.get("enabled", False)
    np.min_node_count      = a.get("minNodeCount", np.min_node_count)
    np.max_node_count      = a.get("maxNodeCount", np.max_node_count)
    db.commit()
    return _nodepool_to_dict(np, project)


@router.post("/projects/{project}/locations/{location}/clusters/{cluster_name}/nodePools/{pool_name}:setSize")
def set_node_pool_size(
    project: str, location: str, cluster_name: str, pool_name: str,
    body: SetSizeRequest, db: Session = Depends(get_db),
):
    """Resize a node pool — spins up or tears down real k3s agent containers."""
    np = db.query(GKENodePool).filter_by(
        project_id=project, location=location, cluster_name=cluster_name, name=pool_name
    ).first()
    if not np:
        raise HTTPException(404, f"Node pool '{pool_name}' not found")
    if body.nodeCount < 0:
        raise HTTPException(400, "nodeCount must be >= 0")
    cluster_row = db.query(GKECluster).filter_by(
        project_id=project, location=location, name=cluster_name
    ).first()
    if not cluster_row:
        raise HTTPException(404, f"Cluster '{cluster_name}' not found")

    np.status = "RECONCILING"; db.commit()
    threading.Thread(
        target=_resize_nodepool_bg,
        args=(np.id, cluster_row.id, body.nodeCount),
        daemon=True,
    ).start()
    return _operation_response(cluster_name, project, location, "SET_NODE_POOL_SIZE")


@router.delete("/projects/{project}/locations/{location}/clusters/{cluster_name}/nodePools/{pool_name}")
def delete_node_pool(project: str, location: str, cluster_name: str, pool_name: str, db: Session = Depends(get_db)):
    np = db.query(GKENodePool).filter_by(project_id=project, location=location, cluster_name=cluster_name, name=pool_name).first()
    if not np:
        raise HTTPException(404, f"Node pool '{pool_name}' not found")
    np_id = np.id; container_ids = np.container_ids or []
    np.status = "STOPPING"; db.commit()
    threading.Thread(target=_delete_nodepool_bg, args=(np_id, container_ids), daemon=True).start()
    return _operation_response(cluster_name, project, location, "DELETE_NODE_POOL")


# ─── Addon endpoints ───────────────────────────────────────────────────────────

_ADDON_VERSIONS: dict[str, str] = {
    "HttpLoadBalancing":          "1.0.0",
    "HorizontalPodAutoscaling":   "1.0.0",
    "NetworkPolicy":              "1.0.0",
    "KubernetesDashboard":        "2.7.0",
    "GcePersistentDiskCsiDriver": "1.12.0",
    "GcpFilestoreCsiDriver":      "1.5.0",
}


@router.get("/projects/{project}/locations/{location}/clusters/{cluster_name}/addons")
def list_addons(project: str, location: str, cluster_name: str, db: Session = Depends(get_db)):
    if not db.query(GKECluster).filter_by(project_id=project, location=location, name=cluster_name).first():
        raise HTTPException(404, f"Cluster '{cluster_name}' not found")
    addons = db.query(GKEAddon).filter_by(project_id=project, location=location, cluster_name=cluster_name).all()
    return {"addons": [_addon_to_dict(a) for a in addons]}


@router.post("/projects/{project}/locations/{location}/clusters/{cluster_name}/addons", status_code=200)
def create_addon(
    project: str, location: str, cluster_name: str,
    body: CreateAddonRequest, db: Session = Depends(get_db),
):
    if not db.query(GKECluster).filter_by(project_id=project, location=location, name=cluster_name).first():
        raise HTTPException(404, f"Cluster '{cluster_name}' not found")
    if db.query(GKEAddon).filter_by(project_id=project, location=location, cluster_name=cluster_name, name=body.name).first():
        raise HTTPException(409, f"Addon '{body.name}' already installed")
    addon = GKEAddon(
        name=body.name, cluster_name=cluster_name, project_id=project, location=location,
        version=body.version or _ADDON_VERSIONS.get(body.name, "1.0.0"),
        status="ENABLED",
    )
    db.add(addon); db.commit()
    return _addon_to_dict(addon)


@router.delete("/projects/{project}/locations/{location}/clusters/{cluster_name}/addons/{addon_name}")
def delete_addon(project: str, location: str, cluster_name: str, addon_name: str, db: Session = Depends(get_db)):
    addon = db.query(GKEAddon).filter_by(project_id=project, location=location, cluster_name=cluster_name, name=addon_name).first()
    if not addon:
        raise HTTPException(404, f"Addon '{addon_name}' not found")
    db.delete(addon); db.commit()
    return {"message": f"Addon '{addon_name}' deleted"}


# ─── Server Config ─────────────────────────────────────────────────────────────

@router.get("/projects/{project}/locations/{location}/serverConfig")
def get_server_config(project: str, location: str):
    """Return supported Kubernetes versions — used to populate create-cluster dropdowns."""
    return {
        "defaultClusterVersion": "1.28",
        "validMasterVersions":   _SUPPORTED_VERSIONS,
        "validNodeVersions":     _SUPPORTED_VERSIONS,
        "channels": [
            {"channel": "RAPID",   "defaultVersion": "1.30", "validVersions": ["1.30", "1.29"]},
            {"channel": "REGULAR", "defaultVersion": "1.29", "validVersions": ["1.29", "1.28"]},
            {"channel": "STABLE",  "defaultVersion": "1.28", "validVersions": ["1.28", "1.27"]},
        ],
    }


# ─── Operations (gcloud polls these after async calls) ────────────────────────

@router.get("/projects/{project}/locations/{location}/operations/{operation_id}")
def get_operation(project: str, location: str, operation_id: str):
    """Return a DONE operation — gcloud polls this after create/delete/etc."""
    return {
        "name": operation_id,
        "status": "DONE",
        "operationType": "UNKNOWN",
        "selfLink": (
            f"https://container.googleapis.com/v1/projects/{project}"
            f"/locations/{location}/operations/{operation_id}"
        ),
    }
