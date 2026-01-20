"""
IAM DTOs - Data Transfer Objects for IAM requests and responses
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ServiceAccountCreateRequest:
    """Request DTO for creating a service account"""
    account_id: str  # The account ID (not email)
    display_name: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ServiceAccountUpdateRequest:
    """Request DTO for updating a service account"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    etag: Optional[str] = None


@dataclass
class ServiceAccountKeyCreateRequest:
    """Request DTO for creating a service account key"""
    key_algorithm: str = "KEY_ALG_RSA_2048"
    private_key_type: str = "TYPE_GOOGLE_CREDENTIALS_FILE"


@dataclass
class IAMBindingDTO:
    """DTO for IAM binding"""
    role: str
    members: List[str] = field(default_factory=list)
    condition: Optional[Dict[str, Any]] = None


@dataclass
class IAMPolicyDTO:
    """DTO for IAM policy"""
    version: int = 1
    bindings: List[IAMBindingDTO] = field(default_factory=list)
    etag: Optional[str] = None


@dataclass
class SetIAMPolicyRequest:
    """Request DTO for setting IAM policy"""
    policy: IAMPolicyDTO
    update_mask: Optional[str] = None


@dataclass
class TestIAMPermissionsRequest:
    """Request DTO for testing IAM permissions"""
    permissions: List[str]


@dataclass
class TestIAMPermissionsResponse:
    """Response DTO for testing IAM permissions"""
    permissions: List[str]


@dataclass
class RoleCreateRequest:
    """Request DTO for creating a custom role"""
    role_id: str
    title: str
    description: Optional[str] = None
    included_permissions: List[str] = field(default_factory=list)
    stage: str = "GA"


@dataclass
class RoleUpdateRequest:
    """Request DTO for updating a custom role"""
    title: Optional[str] = None
    description: Optional[str] = None
    included_permissions: Optional[List[str]] = None
    stage: Optional[str] = None
    etag: Optional[str] = None


@dataclass
class RoleListResponse:
    """Response DTO for listing roles"""
    roles: List[Dict[str, Any]]
    next_page_token: Optional[str] = None


@dataclass
class ServiceAccountListResponse:
    """Response DTO for listing service accounts"""
    accounts: List[Dict[str, Any]]
    next_page_token: Optional[str] = None
