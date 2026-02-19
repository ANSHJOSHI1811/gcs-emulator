"""IAM service — Pydantic request/response models"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# ── Service Accounts ───────────────────────────────────────────────

class ServiceAccountCreate(BaseModel):
    displayName: Optional[str] = None
    description: Optional[str] = None


class ServiceAccountRequest(BaseModel):
    accountId: str
    serviceAccount: Optional[ServiceAccountCreate] = None


# ── IAM Policy Bindings ────────────────────────────────────────────

class IamCondition(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    expression: Optional[str] = None


class IamBinding(BaseModel):
    role: str
    members: List[str]                          # ["user:a@b.com", "serviceAccount:sa@p.iam..."]
    condition: Optional[IamCondition] = None


class SetIamPolicyRequest(BaseModel):
    policy: Dict[str, Any]                      # {bindings: [...], etag: "", version: 1}


class AddIamBindingRequest(BaseModel):
    """Convenience: add a single principal→role binding."""
    principal: str                              # user:email | serviceAccount:... | group:...
    role: str                                   # roles/compute.viewer | projects/p/roles/custom
    condition: Optional[IamCondition] = None


class RemoveIamBindingRequest(BaseModel):
    principal: str
    role: str


# ── Custom Roles ───────────────────────────────────────────────────

class CreateRoleRequest(BaseModel):
    roleId: str
    role: Dict[str, Any]                        # {title, description, permissions, stage}


class PatchRoleRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    stage: Optional[str] = None
