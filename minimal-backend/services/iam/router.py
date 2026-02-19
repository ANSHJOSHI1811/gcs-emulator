"""
IAM & Admin service router.
Existing: Service Accounts CRUD, SA keys list.
Sprint 3 additions: IAM policy bindings (get/set/add/remove),
                    predefined roles catalog, custom roles CRUD,
                    service account key create/delete.
"""
import base64
import json
import random
import secrets
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import (
    get_db, ServiceAccount,
    IAMPolicyBinding, CustomRole, ServiceAccountKey,
)
from .models import (
    ServiceAccountRequest,
    AddIamBindingRequest, RemoveIamBindingRequest, SetIamPolicyRequest,
    CreateRoleRequest, PatchRoleRequest,
)

router = APIRouter()


# ────────────────────────────────────────────────────────
# Predefined roles catalog (static seed)
# ────────────────────────────────────────────────────────

# A lean but representative set of GCP predefined roles
_PREDEFINED_ROLES = [
    {"name": "roles/owner",              "title": "Owner",              "description": "Full access to all resources"},
    {"name": "roles/editor",             "title": "Editor",             "description": "Edit access to all resources"},
    {"name": "roles/viewer",             "title": "Viewer",             "description": "Read-only access to all resources"},
    {"name": "roles/compute.admin",      "title": "Compute Admin",      "description": "Full control of all Compute Engine resources"},
    {"name": "roles/compute.viewer",     "title": "Compute Viewer",     "description": "Read-only access to Compute Engine"},
    {"name": "roles/compute.instanceAdmin.v1", "title": "Compute Instance Admin", "description": "Full control of Compute Engine instances"},
    {"name": "roles/compute.networkAdmin",     "title": "Compute Network Admin",  "description": "Full control of Compute Engine networking"},
    {"name": "roles/container.admin",    "title": "Kubernetes Engine Admin",    "description": "Full management of GKE clusters and their Kubernetes API objects"},
    {"name": "roles/container.developer","title": "Kubernetes Engine Developer","description": "Full access to Kubernetes API objects inside clusters"},
    {"name": "roles/container.viewer",   "title": "Kubernetes Engine Viewer",   "description": "Read-only access to GKE resources"},
    {"name": "roles/storage.admin",      "title": "Storage Admin",      "description": "Full control of Cloud Storage resources"},
    {"name": "roles/storage.objectViewer","title":"Storage Object Viewer","description": "Read access to Cloud Storage objects"},
    {"name": "roles/iam.serviceAccountAdmin",  "title": "Service Account Admin",  "description": "Create and manage service accounts"},
    {"name": "roles/iam.serviceAccountUser",   "title": "Service Account User",   "description": "Run operations as the service account"},
    {"name": "roles/iam.securityAdmin",        "title": "Security Admin",         "description": "Manage all IAM policies and service accounts"},
    {"name": "roles/iam.roleAdmin",            "title": "Role Administrator",     "description": "Create, update, and delete IAM custom roles"},
    {"name": "roles/logging.admin",      "title": "Logging Admin",      "description": "Full control of all Log resources"},
    {"name": "roles/monitoring.admin",   "title": "Monitoring Admin",   "description": "Full access to Cloud Monitoring"},
]


# ────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────

def _sa_resource(sa: ServiceAccount, project: str) -> dict:
    return {
        "name": f"projects/{project}/serviceAccounts/{sa.id}",
        "email": sa.id,
        "displayName": sa.display_name or "",
        "uniqueId": sa.unique_id,
        "projectId": sa.project_id,
        "disabled": sa.disabled,
        "description": sa.description or "",
    }


def _bindings_for_project(project_id: str, db: Session) -> List[dict]:
    """Return list of {role, members} aggregated from flat rows."""
    rows = db.query(IAMPolicyBinding).filter_by(project_id=project_id).all()
    grouped: Dict[str, List[str]] = {}
    for r in rows:
        grouped.setdefault(r.role, []).append(r.principal)
    return [{"role": role, "members": members} for role, members in grouped.items()]


def _mock_key_data(project: str, sa_email: str, key_id: str) -> str:
    """Generate a base64-encoded mock JSON service account key."""
    payload = {
        "type": "service_account",
        "project_id": project,
        "private_key_id": key_id,
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\n(SIMULATED)\n-----END RSA PRIVATE KEY-----\n",
        "client_email": sa_email,
        "client_id": str(random.randint(10 ** 20, 10 ** 21 - 1)),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    return base64.b64encode(json.dumps(payload).encode()).decode()


# ────────────────────────────────────────────────────────
# Service Accounts
# ────────────────────────────────────────────────────────

@router.get("/projects/{project}/serviceAccounts")
def list_service_accounts(project: str, db: Session = Depends(get_db)):
    accounts = db.query(ServiceAccount).filter_by(project_id=project).all()
    return {"accounts": [_sa_resource(a, project) for a in accounts]}


@router.post("/projects/{project}/serviceAccounts")
def create_service_account(project: str, payload: ServiceAccountRequest,
                            db: Session = Depends(get_db)):
    email = f"{payload.accountId}@{project}.iam.gserviceaccount.com"
    if db.query(ServiceAccount).filter_by(id=email).first():
        raise HTTPException(409, "Service account already exists")
    sa = ServiceAccount(
        id=email, project_id=project, email=email,
        display_name=payload.serviceAccount.displayName if payload.serviceAccount else None,
        description=payload.serviceAccount.description if payload.serviceAccount else None,
        unique_id=str(random.randint(10 ** 20, 10 ** 21 - 1)),
        disabled=False,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    db.add(sa)
    db.commit()
    db.refresh(sa)
    return _sa_resource(sa, project)


@router.get("/projects/{project}/serviceAccounts/{email:path}")
def get_service_account(project: str, email: str, db: Session = Depends(get_db)):
    sa = db.query(ServiceAccount).filter_by(id=email, project_id=project).first()
    if not sa:
        raise HTTPException(404, "Service account not found")
    return _sa_resource(sa, project)


@router.delete("/projects/{project}/serviceAccounts/{email:path}")
def delete_service_account(project: str, email: str, db: Session = Depends(get_db)):
    sa = db.query(ServiceAccount).filter_by(id=email, project_id=project).first()
    if not sa:
        raise HTTPException(404, "Service account not found")
    # Cascade: delete keys and bindings
    db.query(ServiceAccountKey).filter_by(service_account_email=email).delete()
    db.query(IAMPolicyBinding).filter(
        IAMPolicyBinding.project_id == project,
        IAMPolicyBinding.principal == f"serviceAccount:{email}"
    ).delete()
    db.delete(sa)
    db.commit()
    return {}


# ────────────────────────────────────────────────────────
# Sprint 3 — Service Account Keys
# ────────────────────────────────────────────────────────

@router.get("/projects/{project}/serviceAccounts/{email:path}/keys")
def list_sa_keys(project: str, email: str, db: Session = Depends(get_db)):
    sa = db.query(ServiceAccount).filter_by(id=email, project_id=project).first()
    if not sa:
        raise HTTPException(404, "Service account not found")
    keys = db.query(ServiceAccountKey).filter_by(
        service_account_email=email, project_id=project
    ).all()
    return {
        "keys": [{
            "name": f"projects/{project}/serviceAccounts/{email}/keys/{k.id}",
            "keyType": k.key_type,
            "keyAlgorithm": "KEY_ALG_RSA_2048",
            "validAfterTime": k.valid_after_time.isoformat() + "Z",
            "disabled": k.disabled,
        } for k in keys]
    }


@router.post("/projects/{project}/serviceAccounts/{email:path}/keys")
def create_sa_key(project: str, email: str, db: Session = Depends(get_db)):
    sa = db.query(ServiceAccount).filter_by(id=email, project_id=project).first()
    if not sa:
        raise HTTPException(404, "Service account not found")

    key_id = secrets.token_hex(20)
    key_data = _mock_key_data(project, email, key_id)

    key = ServiceAccountKey(
        id=key_id,
        service_account_email=email,
        project_id=project,
        key_type="USER_MANAGED",
        private_key_data=key_data,
        valid_after_time=datetime.utcnow(),
        disabled=False,
    )
    db.add(key)
    db.commit()

    return {
        "name": f"projects/{project}/serviceAccounts/{email}/keys/{key_id}",
        "keyType": "USER_MANAGED",
        "keyAlgorithm": "KEY_ALG_RSA_2048",
        "privateKeyData": key_data,           # base64 — download this
        "validAfterTime": key.valid_after_time.isoformat() + "Z",
    }


@router.delete("/projects/{project}/serviceAccounts/{email:path}/keys/{key_id}")
def delete_sa_key(project: str, email: str, key_id: str, db: Session = Depends(get_db)):
    k = db.query(ServiceAccountKey).filter_by(id=key_id, service_account_email=email).first()
    if not k:
        raise HTTPException(404, "Key not found")
    db.delete(k)
    db.commit()
    return {}


# ────────────────────────────────────────────────────────
# Sprint 3 — IAM Policy (project-level)
# ────────────────────────────────────────────────────────

@router.post("/projects/{project}:getIamPolicy")
def get_iam_policy(project: str, db: Session = Depends(get_db)):
    bindings = _bindings_for_project(project, db)
    return {
        "version": 1,
        "etag": "simulated",
        "bindings": bindings,
    }


@router.post("/projects/{project}:setIamPolicy")
def set_iam_policy(project: str, body: SetIamPolicyRequest, db: Session = Depends(get_db)):
    """Replace all bindings for a project (full replace, not merge)."""
    db.query(IAMPolicyBinding).filter_by(project_id=project).delete()
    for binding in body.policy.get("bindings", []):
        role = binding.get("role", "")
        for member in binding.get("members", []):
            row = IAMPolicyBinding(project_id=project, principal=member, role=role)
            db.add(row)
    db.commit()
    return {
        "version": 1,
        "etag": "simulated",
        "bindings": _bindings_for_project(project, db),
    }


@router.post("/projects/{project}/iam:addBinding")
def add_iam_binding(project: str, body: AddIamBindingRequest, db: Session = Depends(get_db)):
    """Add a single principal → role binding."""
    existing = db.query(IAMPolicyBinding).filter_by(
        project_id=project, principal=body.principal, role=body.role
    ).first()
    if not existing:
        row = IAMPolicyBinding(
            project_id=project, principal=body.principal,
            role=body.role,
            condition=body.condition.dict() if body.condition else None,
        )
        db.add(row)
        db.commit()
    return {
        "version": 1,
        "etag": "simulated",
        "bindings": _bindings_for_project(project, db),
    }


@router.post("/projects/{project}/iam:removeBinding")
def remove_iam_binding(project: str, body: RemoveIamBindingRequest, db: Session = Depends(get_db)):
    """Remove a single principal → role binding."""
    db.query(IAMPolicyBinding).filter_by(
        project_id=project, principal=body.principal, role=body.role
    ).delete()
    db.commit()
    return {
        "version": 1,
        "etag": "simulated",
        "bindings": _bindings_for_project(project, db),
    }


# ────────────────────────────────────────────────────────
# Sprint 3 — Roles
# ────────────────────────────────────────────────────────

@router.get("/roles")
def list_predefined_roles():
    """List GCP predefined roles catalog."""
    return {
        "roles": [
            {**r, "stage": "GA", "deleted": False,
             "selfLink": f"https://iam.googleapis.com/v1/{r['name']}"}
            for r in _PREDEFINED_ROLES
        ]
    }


@router.get("/roles/{role_id:path}")
def get_predefined_role(role_id: str):
    full_name = f"roles/{role_id}" if not role_id.startswith("roles/") else role_id
    for r in _PREDEFINED_ROLES:
        if r["name"] == full_name:
            return {**r, "stage": "GA", "deleted": False,
                    "selfLink": f"https://iam.googleapis.com/v1/{r['name']}"}
    raise HTTPException(404, f"Role {full_name} not found")


@router.get("/projects/{project}/roles")
def list_custom_roles(project: str, db: Session = Depends(get_db)):
    roles = db.query(CustomRole).filter_by(project_id=project, deleted=False).all()
    return {
        "roles": [{
            "name": f"projects/{project}/roles/{r.role_id}",
            "title": r.title,
            "description": r.description or "",
            "includedPermissions": r.permissions or [],
            "stage": r.stage,
            "deleted": r.deleted,
        } for r in roles]
    }


@router.post("/projects/{project}/roles")
def create_custom_role(project: str, body: CreateRoleRequest, db: Session = Depends(get_db)):
    if db.query(CustomRole).filter_by(project_id=project, role_id=body.roleId, deleted=False).first():
        raise HTTPException(409, f"Role {body.roleId} already exists")
    role_data = body.role
    r = CustomRole(
        role_id=body.roleId, project_id=project,
        title=role_data.get("title", body.roleId),
        description=role_data.get("description"),
        permissions=role_data.get("includedPermissions", []),
        stage=role_data.get("stage", "GA"),
        deleted=False,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return {
        "name": f"projects/{project}/roles/{r.role_id}",
        "title": r.title, "description": r.description or "",
        "includedPermissions": r.permissions or [],
        "stage": r.stage, "deleted": r.deleted,
    }


@router.patch("/projects/{project}/roles/{role_id}")
def patch_custom_role(project: str, role_id: str, body: PatchRoleRequest,
                      db: Session = Depends(get_db)):
    r = db.query(CustomRole).filter_by(project_id=project, role_id=role_id, deleted=False).first()
    if not r:
        raise HTTPException(404, f"Custom role {role_id} not found")
    if body.title is not None:
        r.title = body.title
    if body.description is not None:
        r.description = body.description
    if body.permissions is not None:
        r.permissions = body.permissions
    if body.stage is not None:
        r.stage = body.stage
    db.commit()
    return {
        "name": f"projects/{project}/roles/{r.role_id}",
        "title": r.title, "description": r.description or "",
        "includedPermissions": r.permissions or [],
        "stage": r.stage, "deleted": r.deleted,
    }


@router.delete("/projects/{project}/roles/{role_id}")
def delete_custom_role(project: str, role_id: str, db: Session = Depends(get_db)):
    r = db.query(CustomRole).filter_by(project_id=project, role_id=role_id).first()
    if not r:
        raise HTTPException(404, f"Custom role {role_id} not found")
    r.deleted = True
    db.commit()
    return {"name": f"projects/{project}/roles/{role_id}", "deleted": True}
