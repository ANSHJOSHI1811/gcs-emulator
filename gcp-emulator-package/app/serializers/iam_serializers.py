"""
IAM Serializers - Convert between DTOs and models
"""
from typing import Dict, Any, List
from app.models.service_account import ServiceAccount, ServiceAccountKey
from app.models.iam_policy import IAMPolicy, IAMBinding, Role
from app.dtos.iam_dtos import (
    IAMBindingDTO, IAMPolicyDTO, ServiceAccountCreateRequest,
    ServiceAccountKeyCreateRequest, RoleCreateRequest
)


class ServiceAccountSerializer:
    """Serializer for ServiceAccount model"""
    
    @staticmethod
    def to_dict(service_account: ServiceAccount) -> Dict[str, Any]:
        """Serialize service account to dictionary"""
        return service_account.to_dict()
    
    @staticmethod
    def to_list_item(service_account: ServiceAccount) -> Dict[str, Any]:
        """Serialize service account for list response"""
        return {
            "name": f"projects/{service_account.project_id}/serviceAccounts/{service_account.email}",
            "email": service_account.email,
            "displayName": service_account.display_name,
            "uniqueId": service_account.unique_id,
            "disabled": service_account.disabled,
        }


class ServiceAccountKeySerializer:
    """Serializer for ServiceAccountKey model"""
    
    @staticmethod
    def to_dict(key: ServiceAccountKey, include_private_key: bool = False) -> Dict[str, Any]:
        """Serialize service account key to dictionary"""
        return key.to_dict(include_private_key=include_private_key)


class IAMPolicySerializer:
    """Serializer for IAMPolicy model"""
    
    @staticmethod
    def to_dict(policy: IAMPolicy) -> Dict[str, Any]:
        """Serialize IAM policy to dictionary"""
        return policy.to_dict()
    
    @staticmethod
    def from_dto(dto: IAMPolicyDTO) -> Dict[str, Any]:
        """Convert DTO to dictionary for model creation"""
        return {
            "version": dto.version,
            "bindings": [
                {
                    "role": binding.role,
                    "members": binding.members,
                    "condition": binding.condition
                }
                for binding in dto.bindings
            ],
            "etag": dto.etag
        }


class IAMBindingSerializer:
    """Serializer for IAMBinding model"""
    
    @staticmethod
    def to_dict(binding: IAMBinding) -> Dict[str, Any]:
        """Serialize IAM binding to dictionary"""
        return binding.to_dict()


class RoleSerializer:
    """Serializer for Role model"""
    
    @staticmethod
    def to_dict(role: Role) -> Dict[str, Any]:
        """Serialize role to dictionary"""
        return role.to_dict()
    
    @staticmethod
    def to_list_item(role: Role) -> Dict[str, Any]:
        """Serialize role for list response"""
        return {
            "name": role.name,
            "title": role.title,
            "description": role.description,
            "stage": role.stage,
            "deleted": role.deleted,
        }
